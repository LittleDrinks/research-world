import asyncio
import threading
from unittest.mock import MagicMock

import docker
import httpx
import pytest
from fastapi.testclient import TestClient

from runtime.runtime import Runtime
from runtime.server import create_app
from runtime.workspace.manager import Workspaces

PID='project:'+'a'*24
OTHER='project:'+'b'*24


def container_for(manager,project=PID,state='running',health='healthy'):
    container=MagicMock()
    container.name=manager.name(project)
    container.labels={'rw.owner':manager.prefix,'rw.project':project,'rw.model':object()}
    container.status=state
    container.attrs={'State':{'Health':{'Status':health}},'NetworkSettings':{'Ports':{}}}
    container.stop.side_effect=lambda **_:setattr(container,'status','exited')
    return container


@pytest.fixture
def workspace(tmp_path,monkeypatch):
    monkeypatch.setenv('RUNTIME_DATA',str(tmp_path))
    manager=Workspaces();manager._client=MagicMock()
    manager.token=MagicMock(side_effect=AssertionError('Unexpected credential read'))
    container=container_for(manager)
    container.labels.pop('rw.model')
    manager.client.containers.list.return_value=[container]
    manager.client.containers.get.return_value=container
    return manager,container,create_app(Runtime(tmp_path/'runtime',{}),workspaces=manager)


def test_batch_is_read_only_and_checks_owner_project_and_name(workspace):
    manager,container,app=workspace
    other=container_for(manager,OTHER,'exited')
    foreign=container_for(manager);foreign.labels['rw.owner']='foreign'
    invalid=container_for(manager);invalid.labels['rw.project']='invalid'
    wrong_name=container_for(manager);wrong_name.name='unrelated'
    manager.client.containers.list.return_value=[container,other,foreign,invalid,wrong_name]
    manager.status=MagicMock(side_effect=AssertionError('Unexpected detailed status read'))
    with TestClient(app) as client:response=client.get('/api/v1/runtime/workspaces')
    assert response.status_code==200 and response.json()=={PID:'ready',OTHER:'exited'}
    manager.client.containers.list.assert_called_once_with(all=True,filters={'label':f'rw.owner={manager.prefix}'})
    manager.client.containers.get.assert_not_called();manager.client.containers.create.assert_not_called()
    manager.token.assert_not_called();manager.status.assert_not_called()
    for item in [container,other,foreign,invalid,wrong_name]:
        item.start.assert_not_called();item.stop.assert_not_called();item.remove.assert_not_called()
    assert not manager.root.exists()


@pytest.mark.parametrize(('state','health','expected'),[
    ('running','healthy','ready'),('running','starting','running'),
    ('running','unhealthy','unhealthy'),('created',None,'created'),
    ('exited','healthy','exited'),('dead',None,'dead'),
    ('restarting','healthy','restarting'),('paused','healthy','paused'),
])
def test_batch_reports_actual_container_state(workspace,state,health,expected):
    manager,container,app=workspace
    container.status=state;container.attrs['State']['Health']['Status']=health
    with TestClient(app) as client:
        assert client.get('/api/v1/runtime/workspaces').json()=={PID:expected}


@pytest.mark.parametrize('error',[docker.errors.DockerException,docker.errors.APIError,docker.errors.NotFound])
def test_docker_failure_is_unavailable_not_stopped(workspace,error):
    manager,_,app=workspace
    manager.client.containers.list.side_effect=error('internal diagnostic')
    with TestClient(app) as client:response=client.get('/api/v1/runtime/workspaces')
    assert response.status_code==503
    assert response.json()=={'detail':'工作区容器服务不可用'}
    manager.token.assert_not_called()


def test_empty_docker_result_is_an_empty_map(workspace):
    manager,_,app=workspace
    manager.client.containers.list.return_value=[]
    with TestClient(app) as client:
        assert client.get('/api/v1/runtime/workspaces').json()=={}


def test_repeated_http_start_reuses_running_container(workspace):
    manager,container,app=workspace
    with TestClient(app) as client:
        for _ in range(2):
            response=client.post(f'/api/v1/runtime/projects/{PID}/workspace',json={'model':'test/model'})
            assert response.status_code==200 and response.json()['status']=='ready'
    manager.client.containers.create.assert_not_called()
    container.start.assert_not_called();container.remove.assert_not_called();container.stop.assert_not_called()
    assert container.reload.call_count==2


@pytest.mark.parametrize('initial',['running','created'])
def test_stop_changes_only_target_project_and_single_routes_remain(workspace,initial):
    manager,container,app=workspace
    container.status=initial
    other=container_for(manager,OTHER)
    manager.client.containers.list.return_value=[container,other]
    with TestClient(app) as client:
        assert client.get(f'/api/v1/runtime/projects/{PID}/workspace').json()['status']==('ready' if initial=='running' else initial)
        assert client.post(f'/api/v1/runtime/projects/{PID}/workspace/stop').json()['status']=='exited'
        assert client.get('/api/v1/runtime/workspaces').json()=={PID:'exited',OTHER:'ready'}
    container.stop.assert_called_once_with(timeout=10);other.stop.assert_not_called()
    manager.client.containers.get.assert_called_with(manager.name(PID))


def test_failed_stop_keeps_real_running_state(workspace):
    manager,container,app=workspace
    container.stop.side_effect=docker.errors.APIError('internal diagnostic')
    with TestClient(app) as client:
        assert client.post(f'/api/v1/runtime/projects/{PID}/workspace/stop').status_code==503
        assert client.get('/api/v1/runtime/workspaces').json()=={PID:'ready'}


@pytest.mark.asyncio
async def test_cancelled_http_start_finishes_without_stopping(workspace):
    manager,container,app=workspace
    entered=threading.Event();release=threading.Event()
    def ready(_):entered.set();release.wait(5)
    manager._ready=ready
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        task=asyncio.create_task(client.post(f'/api/v1/runtime/projects/{PID}/workspace',json={'model':'test/model'}))
        try:
            assert await asyncio.to_thread(entered.wait,2)
            task.cancel();await asyncio.sleep(0)
            assert manager.locks[PID].locked()
        finally:release.set()
        with pytest.raises(asyncio.CancelledError):await task
        assert (await client.get('/api/v1/runtime/workspaces')).json()=={PID:'ready'}
    assert not manager.locks[PID].locked()
    container.stop.assert_not_called();container.remove.assert_not_called()


@pytest.mark.asyncio
async def test_stop_waits_for_inflight_start_lock(workspace):
    manager,container,app=workspace
    entered=threading.Event();release=threading.Event()
    def ready(_):entered.set();release.wait(5)
    manager._ready=ready
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        path=f'/api/v1/runtime/projects/{PID}/workspace'
        start=asyncio.create_task(client.post(path,json={'model':'test/model'}))
        try:
            assert await asyncio.to_thread(entered.wait,2)
            stop=asyncio.create_task(client.post(path+'/stop'));await asyncio.sleep(0)
            assert manager.locks[PID].locked() and not stop.done()
            container.stop.assert_not_called()
        finally:release.set()
        assert (await start).json()['status']=='ready'
        assert (await stop).json()['status']=='exited'
    container.stop.assert_called_once_with(timeout=10)
