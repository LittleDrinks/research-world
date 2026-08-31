from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from .errors import RuntimeConflictError
from .run_store import RunStoreConflictError, RunStoreError
from .runtime import Runtime

__all__ = [
    "LaunchRequest",
    "SubmitRequest",
    "RuntimeHTTPError",
    "install_error_handlers",
    "runtime_router",
]


class LaunchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_spec: dict[str, Any]
    session_id: str | None = None


class SubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    message: dict[str, Any]


class RuntimeHTTPError(HTTPException):
    def __init__(self, status_code: int, code: str, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RuntimeHTTPError, _runtime_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(RunStoreError, _storage_error)


async def _runtime_error(_, error: RuntimeHTTPError):
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "detail": error.detail},
    )


async def _validation_error(_, error: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": "invalid_request", "detail": jsonable_encoder(error.errors())},
    )


async def _storage_error(_, __):
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "detail": "internal server error"},
    )


def runtime_router(runtime: Runtime) -> APIRouter:
    router = APIRouter(prefix="/api/v1/runtime")
    router.add_api_route("/launch", _launch(runtime), methods=["POST"])
    router.add_api_route("/submit", _submit(runtime), methods=["POST"], status_code=202)
    return router


def _launch(runtime: Runtime):
    async def endpoint(request: LaunchRequest):
        return await _call(runtime.launch, request.agent_spec, session_id=request.session_id)

    return endpoint


def _submit(runtime: Runtime):
    async def endpoint(request: SubmitRequest):
        return await _call(runtime.submit, request.session_id, request.message)

    return endpoint


async def _call(operation, *args, **kwargs):
    try:
        return await operation(*args, **kwargs)
    except KeyError as error:
        raise RuntimeHTTPError(404, "not_found", str(error)) from error
    except (RuntimeConflictError, RunStoreConflictError) as error:
        raise RuntimeHTTPError(409, "conflict", str(error)) from error
    except RunStoreError:
        raise
    except (TypeError, ValueError) as error:
        raise RuntimeHTTPError(422, "invalid_request", str(error)) from error
