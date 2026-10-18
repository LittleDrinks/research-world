import asyncio
from unittest.mock import AsyncMock,MagicMock

import httpx
import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from server.app import create_product
from server.agent_profiles import AgentProfiles
from server.kernel_interface import create_kernel
from server.runtime_http import RuntimeHttpClient
from test_pi_product import setup


@pytest.fixture
def batch(tmp_path):
    kernel=create_kernel(tmp_path/'graph.db',tmp_path/'artifacts')
    projects=[kernel.create_project(name,'Question') for name in ['Ready','Stopped','Missing']]
    states={projects[0].id:'ready',projects[1].id:'exited','project:'+'f'*24:'running'}
    handler=MagicMock(return_value=httpx.Response(200,json=states))
    runtime=RuntimeHttpClient('http://runtime',transport=httpx.MockTransport(handler))
    runtime.workspace=AsyncMock(side_effect=AssertionError('Unexpected single Project call'))
    runtime.catalog=AsyncMock(side_effect=AssertionError('Unexpected catalog read'))
    app=create_product(kernel,runtime,AgentProfiles(tmp_path/'profiles'),tmp_path/'workspaces')
    return app,kernel,runtime,handler,projects


def test_batch_filters_existing_projects_and_uses_one_runtime_request(batch):
    app,_,runtime,handler,projects=batch
    with TestClient(app) as client:response=client.get('/api/v1/workspaces')
    assert response.status_code==200
    assert response.json()==dict(zip([p.id for p in projects],['ready','exited','not_started']))
    handler.assert_called_once()
    request=handler.call_args.args[0]
    assert request.method=='GET' and request.url.path=='/api/v1/runtime/workspaces'
    assert not request.content
    runtime.workspace.assert_not_awaited();runtime.catalog.assert_not_awaited()


def test_batch_reads_current_kernel_projects_each_time(batch):
    app,kernel,_,handler,projects=batch
    with TestClient(app) as client:
        assert projects[1].id in client.get('/api/v1/workspaces').json()
        kernel.delete_project(projects[1].id)
        added=kernel.create_project('New','Question')
        assert client.get('/api/v1/workspaces').json()=={
            projects[0].id:'ready',projects[2].id:'not_started',added.id:'not_started'}
    assert handler.call_count==2


def test_runtime_failure_never_becomes_missing_or_stopped(batch):
    app,_,runtime,handler,_=batch
    handler.return_value=httpx.Response(503,json={'detail':'工作区容器服务不可用'})
    with TestClient(app) as client:response=client.get('/api/v1/workspaces')
    assert response.status_code==503
    assert set(response.json())=={'detail'}
    assert 'not_started' not in response.text and 'exited' not in response.text
    runtime.workspace.assert_not_awaited()


def test_refresh_and_control_shutdown_do_not_stop_workspace(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Workspace','Question')
    runtime.workspace=AsyncMock(return_value={'status':'ready'})
    path=f'/api/v1/projects/{project.id}/workspace'
    with TestClient(app) as client:
        assert client.post(path).json()=={'status':'ready'}
        for _ in range(3):assert client.get(path).json()=={'status':'ready'}
    assert [call.args for call in runtime.workspace.await_args_list]==[
        (project.id,'POST','test/model'),(project.id,),(project.id,),(project.id,)]
    assert not any(call.kwargs.get('stop') for call in runtime.workspace.await_args_list)


def test_removed_presence_route_never_starts_or_stops(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Workspace','Question')
    runtime.workspace=AsyncMock()
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f'/api/v1/projects/{project.id}/workspace/presence'):pass
        assert client.get(f'/api/v1/projects/{project.id}/workspace/presence').status_code==404
    runtime.workspace.assert_not_awaited()


@pytest.mark.parametrize(('method','suffix'),[('GET',''),('POST',''),('POST','/stop')])
def test_missing_project_never_reaches_runtime(tmp_path,method,suffix):
    app,_,runtime=setup(tmp_path)
    runtime.workspace=AsyncMock()
    with TestClient(app) as client:
        assert client.request(method,'/api/v1/projects/missing/workspace'+suffix).status_code==404
    runtime.workspace.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancelled_control_request_does_not_send_stop(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Workspace','Question')
    entered=asyncio.Event()
    async def work(*_,**__):entered.set();await asyncio.Event().wait()
    runtime.workspace=AsyncMock(side_effect=work)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        task=asyncio.create_task(client.post(f'/api/v1/projects/{project.id}/workspace'))
        await asyncio.wait_for(entered.wait(),2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
    runtime.workspace.assert_awaited_once_with(project.id,'POST','test/model')
