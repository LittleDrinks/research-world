import io
import json
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from runtime.workspace.config import pi_configuration,configuration_archive
from runtime.workspace.manager import Workspaces
from runtime.errors import RuntimeConflictError

PID='project:'+'a'*24


def test_configuration_copies_only_selected_provider_and_model(tmp_path):
    providers={'selected':{'apiKey':'private-key','models':[{'id':'one'},{'id':'two'}]},'other':{'apiKey':'other-key','models':[{'id':'three'}]}}
    (tmp_path/'models.json').write_text(json.dumps({'providers':providers}))
    (tmp_path/'auth.json').write_text(json.dumps({'selected':{'key':'auth-key'},'other':{'key':'excluded'}}))
    files=pi_configuration(tmp_path,'selected/one')
    assert list(files['models.json']['providers'])==['selected']
    assert files['models.json']['providers']['selected']['models']==[{'id':'one'}]
    assert files['auth.json']=={'selected':{'key':'auth-key'}}
    assert files['settings.json']['defaultModel']=='one'
    with tarfile.open(fileobj=io.BytesIO(configuration_archive(files))) as archive:
        assert all(m.mode==0o600 and m.uid==1000 and m.gid==1000 for m in archive.getmembers())
        assert set(archive.getnames())=={'models.json','settings.json','auth.json'}


def test_workspaces_mount_only_their_project_volumes(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces();manager._client=MagicMock()
    labels={'rw.owner':manager.prefix,'rw.project':PID}
    manager._client.volumes.get.return_value.attrs={'Labels':labels}
    manager._create(PID,'provider/model')
    kwargs=manager._client.containers.create.call_args.kwargs
    assert {v['bind'] for v in kwargs['volumes'].values()}=={'/workspace','/home/runtime'}
    assert kwargs['user']=='1000:1000' and kwargs['ports']=={'8888/tcp':('127.0.0.1',None)}
    assert manager.name(PID)!=manager.name('project:'+'b'*24)
    assert list(kwargs['environment'])==['JUPYTER_TOKEN']
    with pytest.raises(ValueError):manager.name('../../other')


def test_running_workspace_cannot_be_deleted(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces();manager._client=MagicMock()
    container=manager._client.containers.get.return_value
    container.labels={'rw.owner':manager.prefix,'rw.project':PID};container.status='running'
    with pytest.raises(RuntimeConflictError,match='先停止'):manager.remove(PID)
    container.remove.assert_not_called();manager._client.volumes.get.assert_not_called()


def test_foreign_container_or_volume_is_not_adopted(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces();manager._client=MagicMock()
    manager._client.containers.get.return_value.labels={'rw.owner':'other','rw.project':PID}
    with pytest.raises(RuntimeConflictError):manager.container(PID)
    manager._client.volumes.get.return_value.attrs={'Labels':{'rw.project':PID,'rw.owner':'other'}}
    with pytest.raises(RuntimeConflictError):manager._volume('test',{'rw.project':PID,'rw.owner':manager.prefix})


@pytest.mark.asyncio
async def test_cancellation_keeps_lifecycle_lock_until_thread_finishes(tmp_path,monkeypatch):
    import asyncio,threading
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces()
    entered=threading.Event();release=threading.Event()
    def start(*_):entered.set();release.wait(5)
    manager._start=start;manager.status=lambda _: {'status':'ready'}
    task=asyncio.create_task(manager.start(PID,'provider/model'))
    assert await asyncio.to_thread(entered.wait,2)
    task.cancel();await asyncio.sleep(0)
    assert manager.locks[PID].locked()
    release.set()
    with pytest.raises(asyncio.CancelledError):await task
    assert not manager.locks[PID].locked()


def test_failed_configuration_removes_only_new_container(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces()
    container=MagicMock();container.put_archive.side_effect=OSError('failed')
    manager._create=lambda *_:container
    with pytest.raises(OSError):manager._launch(PID,'provider/model',{})
    container.remove.assert_called_once_with(force=True)
    container.start.assert_not_called()


def test_delete_validates_all_volume_owners_before_any_deletion(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path));manager=Workspaces();manager._client=MagicMock()
    container=manager._client.containers.get.return_value
    container.labels={'rw.owner':manager.prefix,'rw.project':PID};container.status='exited'
    first=MagicMock();first.attrs={'Labels':{'rw.owner':manager.prefix,'rw.project':PID}}
    second=MagicMock();second.attrs={'Labels':{'rw.owner':'foreign','rw.project':PID}}
    manager._client.volumes.get.side_effect=[first,second]
    with pytest.raises(RuntimeConflictError):manager.remove(PID)
    container.remove.assert_not_called();first.remove.assert_not_called()
