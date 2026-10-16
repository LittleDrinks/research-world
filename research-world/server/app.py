from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from .agent_profiles import AgentProfiles
from .config import ROOT, load_settings
from .kernel_http import kernel_graph_router
from .kernel_interface import create_kernel
from .product_sessions import session_router
from .runtime_http import RuntimeHttpClient, RuntimeHttpError
from .session_control import SessionControl
from .project_export import export_project
from .project_control import project_deletion_router
from .project_workspace import workspace_router


def create_product(kernel, runtime, profiles, workspace):
    @asynccontextmanager
    async def lifespan(_app):
        yield
        await runtime.close()

    app = FastAPI(title='Research World', lifespan=lifespan)
    _errors(app)
    _agent_routes(app, runtime, profiles)
    _project_routes(app, kernel, runtime)
    _artifact_routes(app, kernel)
    control=SessionControl(kernel, runtime, profiles, workspace)
    app.include_router(session_router(control))
    app.include_router(project_deletion_router(control))
    app.include_router(workspace_router(control))
    app.include_router(kernel_graph_router(kernel))
    _frontend(app)
    return app


def _errors(app):
    async def invalid(_, error):
        return JSONResponse({'detail': str(error)}, status_code=400)

    async def missing(_, error):
        return JSONResponse({'detail':'not found'}, status_code=404)

    async def runtime_error(_, error):
        return JSONResponse({'detail':str(error)}, status_code=error.status_code)

    for kind in (ValueError, TypeError):
        app.add_exception_handler(kind, invalid)
    for kind in (KeyError, PermissionError, StopIteration):
        app.add_exception_handler(kind, missing)
    app.add_exception_handler(RuntimeHttpError, runtime_error)


def _agent_routes(app, runtime, profiles):
    @app.get('/api/v1/runtime/catalog')
    async def catalog():
        return await runtime.catalog()

    @app.get('/api/v1/agents')
    async def agents():
        return profiles.list((await runtime.catalog())['default_model'])

    @app.put('/api/v1/agents/{agent_id}')
    async def save(agent_id: str, request: Request):
        value = await request.json()
        if value.get('id') != agent_id:
            raise ValueError('Agent id 不匹配')
        await runtime.validate(value)
        return profiles.save(value)


def _project_routes(app, kernel, runtime):
    @app.get('/api/v1/health')
    async def health():
        return {'ok':True}

    @app.get('/api/v1/bootstrap')
    async def bootstrap(project_id: str | None = None):
        projects = kernel.list_projects()
        selected = kernel.get_project(project_id) if project_id else next(iter(projects), None)
        return {'projects':[_project_view(kernel,p) for p in projects],
                'active_project_id': selected.id if selected else None,
                'sessions':kernel.list_sessions(selected.id) if selected else []}

    @app.get('/api/v1/projects/{project_id}/export')
    async def export(project_id: str):
        return Response(await export_project(kernel, runtime, project_id), media_type='application/zip',
                        headers={'Content-Disposition':f'attachment; filename="{project_id}.zip"'})


def _artifact_routes(app, kernel):
    @app.post('/api/v1/projects/{project_id}/artifacts', status_code=201)
    async def capture(project_id: str, request: Request):
        body = await request.json()
        content = body['content'].encode('utf-8')
        if len(content) > 4 * 1024 * 1024:
            raise ValueError('Artifact 超过 4 MiB')
        artifact = kernel.capture_artifact(project_id, content, body.get('media_type', 'text/markdown'))
        return {**asdict(artifact), 'download_url':f'/api/v1/projects/{project_id}/artifacts/{artifact.id}?download=true'}


def _project_view(kernel, project):
    return {**asdict(project), 'node_count':len(kernel.list_records(project.id))}


def _frontend(app):
    @app.get('/{path:path}', include_in_schema=False)
    async def frontend(path: str):
        if path.startswith('api/'):
            raise HTTPException(404)
        dist = (ROOT / 'web/dist').resolve()
        asset = (dist / path).resolve()
        if not asset.is_relative_to(dist):
            raise HTTPException(404)
        return FileResponse(asset if asset.is_file() else dist / 'index.html')


settings = load_settings()
app = create_product(create_kernel(settings.database, settings.artifacts),
                     RuntimeHttpClient(settings.runtime_url),
                     AgentProfiles(settings.database.parent / 'agent-profiles'), settings.projects_root)
