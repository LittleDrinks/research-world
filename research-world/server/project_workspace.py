from fastapi import APIRouter


def workspace_router(control):
    router=APIRouter(prefix='/api/v1')
    projects=APIRouter(prefix='/projects/{project_id}/workspace')
    _routes(projects,control)
    router.include_router(projects)

    @router.get('/workspaces',response_model=dict[str,str])
    async def statuses():
        states=await control.runtime.workspaces()
        return {p.id:states.get(p.id,'not_started') for p in control.kernel.list_projects()}

    return router


async def start_workspace(control,project_id):
    async with control.project_locks[project_id]:
        control.kernel.get_project(project_id)
        catalog=await control.runtime.catalog()
        agent=control.profiles.get('research-assistant',catalog['default_model'])
        return await control.runtime.workspace(project_id,'POST',agent['model'])


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
