from fastapi import APIRouter
from .workspace_presence import presence_route, start_workspace


def workspace_router(control):
    router=APIRouter(prefix='/api/v1/projects/{project_id}/workspace')
    _routes(router,control)
    presence_route(router,control)
    return router


def _routes(router,control):
    @router.get('')
    async def status(project_id: str):
        control.kernel.get_project(project_id)
        return await control.runtime.workspace(project_id)

    @router.post('')
    async def start(project_id: str):
        return await start_workspace(control,project_id)

    @router.post('/stop')
    async def stop(project_id: str):
        async with control.project_locks[project_id]:
            control.kernel.get_project(project_id)
            return await control.runtime.workspace(project_id,'POST',stop=True)
