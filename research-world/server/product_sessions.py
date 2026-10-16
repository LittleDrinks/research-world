import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str
    message_id: str
    agent_id: str = 'research-assistant'


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str
    message_id: str | None = None


def session_router(control):
    router = APIRouter(prefix='/api/v1/projects/{project_id}/sessions')
    _session_routes(router, control)
    _turn_routes(router, control)
    _archive_route(router, control)
    return router


def _session_routes(router, control):
    @router.get('')
    async def sessions(project_id: str):
        return control.kernel.list_sessions(project_id)

    @router.post('', status_code=201)
    async def create(project_id: str, body: SessionRequest):
        async with control.project_locks[project_id]:
            return await control.start(project_id, body.agent_id, body.content, body.message_id)

    @router.get('/{session_id}')
    async def detail(project_id: str, session_id: str):
        return await control.detail(project_id, session_id)

    @router.post('/{session_id}/messages', status_code=202)
    async def submit(project_id: str, session_id: str, body: MessageRequest):
        async with control.project_locks[project_id]:
            return await control.submit(project_id, session_id, body.content, body.message_id)


def _turn_routes(router, control):
    @router.get('/{session_id}/turns/{turn_id}/events')
    async def events(project_id: str, session_id: str, turn_id: str, request: Request, after_seq: int = -1):
        await control.require_turn(project_id, session_id, turn_id)
        cursor = int(request.headers.get('Last-Event-ID', after_seq))
        stream = control.events(project_id, session_id, turn_id, cursor)
        return StreamingResponse(_frames(stream), media_type='text/event-stream')

    @router.post('/{session_id}/turns/{turn_id}/cancel')
    async def cancel(project_id: str, session_id: str, turn_id: str):
        await control.require_turn(project_id, session_id, turn_id)
        return await control.runtime.cancel(turn_id)


async def _frames(events):
    async for event in events:
        yield f'id: {event["seq"]}\nevent: {event["type"]}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n'


def _archive_route(router, control):
    @router.delete('/{session_id}', status_code=204)
    async def archive(project_id: str, session_id: str):
        await control.archive(project_id, session_id)
