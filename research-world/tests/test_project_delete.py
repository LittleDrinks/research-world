import hashlib
from unittest.mock import AsyncMock
import httpx
import pytest
from test_pi_product import setup
from server.runtime_http import RuntimeHttpError


def populate(kernel,root,name):
    project=kernel.create_project(name,'Question')
    artifact=kernel.capture_artifact(project.id,b'original','text/plain')
    record=kernel.record(project.id,'direction',{'text':'candidate'},(artifact.id,))
    kernel.remove_record(project.id,record.id)
    session=kernel.create_session(project.id,name,'Chat')
    kernel.append_user_message(project.id,session.id,'test')
    kernel.archive_session(project.id,session.id)
    directory=root/'workspaces'/project.id;directory.mkdir(parents=True)
    (directory/'file').write_text('workspace')
    return project,artifact


@pytest.mark.asyncio
async def test_delete_cleans_scope_and_preserves_other_project(tmp_path):
    app,kernel,runtime=setup(tmp_path);runtime.delete_project=AsyncMock()
    project,artifact=populate(kernel,tmp_path,'Delete');other,other_artifact=populate(kernel,tmp_path,'Keep')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        path=f'/api/v1/projects/{project.id}'
        assert (await client.delete(path)).status_code==204
        assert (await client.delete(path)).status_code==204
        assert (await client.get(path+'/records')).status_code==404
    runtime.delete_project.assert_awaited_once_with(project.id)
    assert kernel.list_projects()==[other]
    assert kernel.read_artifact(other.id,other_artifact.id)==b'original'
    assert not (tmp_path/'artifacts'/hashlib.sha256(project.id.encode()).hexdigest()).exists()
    assert not (tmp_path/'workspaces'/project.id).exists()
    assert (tmp_path/'workspaces'/other.id/'file').read_text()=='workspace'


@pytest.mark.asyncio
async def test_running_or_unavailable_runtime_does_not_delete_graph(tmp_path):
    app,kernel,runtime=setup(tmp_path);project,artifact=populate(kernel,tmp_path,'Keep')
    runtime.delete_project=AsyncMock(side_effect=RuntimeHttpError(409,'running','先停止任务'))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        response=await client.delete(f'/api/v1/projects/{project.id}')
    assert response.status_code==409
    assert kernel.get_project(project.id)==project
    assert kernel.read_artifact(project.id,artifact.id)==b'original'
    assert (tmp_path/'workspaces'/project.id/'file').exists()
