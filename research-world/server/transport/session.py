from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..kernel_interface import KernelInterface

__all__ = ["session_router"]


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = ""


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    content: str
    message_id: str | None = None


def session_router(kernel: KernelInterface, runtime) -> APIRouter:
    router = APIRouter()
    _add_session_routes(router, kernel)
    _add_message_route(router, kernel, runtime)
    return router


def _add_session_routes(router: APIRouter, kernel: KernelInterface) -> None:
    path = "/api/v1/projects/{project_id}/sessions"
    router.add_api_route(path, _sessions(kernel), methods=["GET"])
    router.add_api_route(path, _create_session(kernel), methods=["POST"], status_code=201)
    router.add_api_route(f"{path}/{{session_id}}", _session(kernel), methods=["GET"])


def _add_message_route(router: APIRouter, kernel: KernelInterface, runtime) -> None:
    path = "/api/v1/projects/{project_id}/sessions/{session_id}/messages"
    router.add_api_route(
        path, _submit_message(kernel, runtime), methods=["POST"], status_code=202
    )


def _sessions(kernel: KernelInterface):
    def endpoint(project_id: str):
        return _kernel_call(kernel.list_sessions, project_id)

    return endpoint


def _create_session(kernel: KernelInterface):
    def endpoint(project_id: str, request: SessionRequest):
        return _kernel_call(kernel.create_session, project_id, request.title)

    return endpoint


def _session(kernel: KernelInterface):
    def endpoint(project_id: str, session_id: str):
        return _kernel_call(kernel.get_session, project_id, session_id)

    return endpoint


def _submit_message(kernel: KernelInterface, runtime):
    async def endpoint(project_id: str, session_id: str, request: MessageRequest):
        message = _append_message(kernel, project_id, session_id, request)
        turn = await _runtime_call(
            runtime.submit, request.run_id, {"id": message.id, "content": message.content}
        )
        _watch_main_turn(runtime, kernel, project_id, session_id, message.id, turn)
        return {"message": message, "turn": turn}

    return endpoint


def _append_message(kernel, project_id, session_id, request):
    return _kernel_call(
        kernel.append_user_message,
        project_id,
        session_id,
        request.content,
        request.message_id,
    )


def _watch_main_turn(runtime, kernel, project_id, session_id, message_id, turn):
    if turn["session_id"] == session_id:
        asyncio.create_task(
            _project_response(runtime, kernel, project_id, session_id, message_id, turn["id"])
        )


async def _project_response(runtime, kernel, project_id, session_id, message_id, turn_id):
    async for event in runtime.subscribe(turn_id):
        if event["type"] != "turn_end":
            continue
        data = event["data"]
        if data["status"] in {"completed", "limit"} and data.get("result_text") is not None:
            _kernel_call(kernel.project_assistant_response, project_id, session_id, message_id, data["result_text"])
        return


def _kernel_call(operation, *args):
    try:
        return operation(*args)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


async def _runtime_call(operation, *args):
    try:
        return await operation(*args)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
