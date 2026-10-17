import asyncio
import docker
from fastapi import APIRouter,HTTPException,Response
from pydantic import BaseModel,ConfigDict
from ..errors import RuntimeConflictError
from .operations import settle


class StartWorkspace(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model: str


def workspace_router(runtime,workspaces):
    router=APIRouter(prefix='/api/v1/runtime/projects/{project_id}')
    _workspace_routes(router,workspaces)
    _delete_route(router,runtime,workspaces)
    _proxy_route(router,workspaces)
    return router


def _workspace_routes(router,workspaces):
    @router.get('/workspace')
    async def status(project_id: str):
        return await _call(asyncio.to_thread(workspaces.status,project_id))

    @router.post('/workspace')
    async def start(project_id: str,body: StartWorkspace):
        return await _call(workspaces.start(project_id,body.model))

    @router.post('/workspace/stop')
    async def stop(project_id: str):
        return await _call(workspaces.stop(project_id))


def _delete_route(router,runtime,workspaces):
    @router.delete('')
    async def delete(project_id: str):
        return await _call(settle(_delete_project(runtime,workspaces,project_id)))


async def _delete_project(runtime,workspaces,project_id):
    async with workspaces.locks[project_id]:
        await asyncio.to_thread(workspaces.require_stopped,project_id)
        return await runtime.delete_project(project_id,lambda: asyncio.to_thread(workspaces.remove,project_id))


async def _call(operation):
    try:return await operation
    except RuntimeConflictError as error:raise HTTPException(409,str(error)) from error
    except docker.errors.DockerException:raise HTTPException(503,'工作区容器服务不可用') from None


def _proxy_route(router,workspaces):
    @router.get('/workspace/upstream')
    async def upstream(project_id: str):
        value=await _call(asyncio.to_thread(workspaces.upstream,project_id))
        return Response(status_code=204,headers={'X-Workspace-Upstream':value})
