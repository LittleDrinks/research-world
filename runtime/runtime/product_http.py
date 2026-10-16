from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from .agent_catalog import catalog, validate_spec, skill_paths


def product_router(runtime):
    router = APIRouter(prefix='/api/v1/runtime')
    router.add_api_route('/catalog', catalog)
    _session_routes(router, runtime)
    _turn_routes(router, runtime)
    _export_route(router, runtime)
    _project_routes(router, runtime)
    return router


def _session_routes(router, runtime):
    @router.get('/sessions/{session_id}')
    async def inspect(session_id: str):
        return runtime.inspect_session(session_id)

    @router.post('/validate')
    async def validate(request: Request):
        value = await request.json()
        validate_spec(value)
        skills = skill_paths()
        from pathlib import Path
        texts = [Path(skills[name]).read_text() for name in value.get('skills', [])]
        return {'instructions': '\n\n'.join([value['instructions'], *texts])}


def _turn_routes(router, runtime):
    @router.get('/turns/{turn_id}')
    async def inspect(turn_id: str):
        return runtime.inspect_turn(turn_id)

    @router.get('/turns/{turn_id}/events')
    async def events(turn_id: str, after_seq: int = -1):
        runtime.inspect_turn(turn_id)
        return StreamingResponse(_events(runtime, turn_id, after_seq), media_type='text/event-stream')

    @router.post('/turns/{turn_id}/cancel')
    async def cancel(turn_id: str):
        return await runtime.cancel(turn_id)


async def _events(runtime, turn_id, after_seq):
    async for event in runtime.subscribe(turn_id, after_seq):
        yield f'id: {event["seq"]}\nevent: {event["type"]}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n'


def _export_route(router, runtime):
    @router.get('/sessions/{session_id}/export')
    async def export(session_id: str):
        return runtime.export_session(session_id)


def _project_routes(router,runtime):
    from .errors import RuntimeConflictError

    @router.delete('/projects/{project_id}')
    async def delete(project_id: str):
        try:return await runtime.delete_project(project_id)
        except RuntimeConflictError as error:raise HTTPException(409,str(error)) from error
