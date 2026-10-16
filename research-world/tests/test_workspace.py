from unittest.mock import AsyncMock
import httpx
import pytest
from test_pi_product import setup


@pytest.mark.asyncio
async def test_workspace_routes_bind_existing_project_and_saved_model(tmp_path):
    app,kernel,runtime=setup(tmp_path);project=kernel.create_project('Workspace','Question')
    runtime.workspace=AsyncMock(return_value={'status':'ready','model':'test/model'})
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        assert (await client.get(f'/api/v1/projects/{project.id}/workspace')).status_code==200
        assert (await client.post(f'/api/v1/projects/{project.id}/workspace')).status_code==200
        assert (await client.post(f'/api/v1/projects/{project.id}/workspace/stop')).status_code==200
        assert (await client.post('/api/v1/projects/project:missing/workspace')).status_code==404
    assert runtime.workspace.await_count==3
    assert runtime.workspace.await_args_list[1].args==(project.id,'POST','test/model')
    assert runtime.workspace.await_args_list[2].kwargs=={'stop':True}
