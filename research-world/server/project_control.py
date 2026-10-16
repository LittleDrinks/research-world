import shutil
from fastapi import APIRouter


def project_deletion_router(control):
    router=APIRouter()

    @router.delete('/api/v1/projects/{project_id}',status_code=204)
    async def delete(project_id: str):
        async with control.project_locks[project_id]:
            if not any(p.id==project_id for p in control.kernel.list_projects()):return
            await control.runtime.delete_project(project_id)
            workspace=control.workspace/project_id
            if workspace.is_symlink():workspace.unlink()
            elif workspace.exists():shutil.rmtree(workspace)
            control.kernel.delete_project(project_id)
    return router
