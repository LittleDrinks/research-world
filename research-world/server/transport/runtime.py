from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

__all__ = ["runtime_router"]


def runtime_router(runtime) -> APIRouter:
    router = APIRouter()
    _add_event_route(router, runtime)
    _add_cancel_route(router, runtime)
    return router


def _add_event_route(router: APIRouter, runtime) -> None:
    async def endpoint(turn_id: str, after_seq: int = -1):
        return StreamingResponse(
            _event_stream(runtime, turn_id, after_seq), media_type="text/event-stream"
        )

    router.add_api_route("/api/v1/turns/{turn_id}/events", endpoint, methods=["GET"])


def _add_cancel_route(router: APIRouter, runtime) -> None:
    async def endpoint(turn_id: str):
        return await _runtime_call(runtime.cancel, turn_id)

    router.add_api_route("/api/v1/turns/{turn_id}/cancel", endpoint, methods=["POST"])


async def _event_stream(runtime, turn_id: str, after_seq: int):
    try:
        async for event in runtime.subscribe(turn_id, after_seq):
            yield _sse_frame(event["type"], event)
    except Exception as error:  # noqa: BLE001 - stream errors stay observable.
        yield _sse_frame("error", {"detail": str(error)})


def _sse_frame(event_type: str, event: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _runtime_call(operation, *args):
    try:
        return await operation(*args)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
