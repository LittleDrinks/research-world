from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from .kernel_interface import KernelInterface

__all__ = ["kernel_graph_routes"]


class RecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    content: dict
    artifact_ids: tuple[str, ...] = ()


class RelationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    target_id: str
    type: str


def kernel_graph_routes(app: FastAPI, kernel: KernelInterface) -> None:
    app.add_exception_handler(KeyError, _not_found)
    app.add_exception_handler(PermissionError, _forbidden)
    app.add_exception_handler(ValueError, _invalid)
    _add_record_routes(app, kernel)
    _add_relation_routes(app, kernel)


def _add_record_routes(app: FastAPI, kernel: KernelInterface) -> None:
    path = "/api/v1/projects/{project_id}/records"
    app.add_api_route(path, _record(kernel), methods=["POST"], status_code=201)
    app.add_api_route(path, _records(kernel), methods=["GET"])
    app.add_api_route(
        f"{path}/{{record_id}}", _remove_record(kernel), methods=["DELETE"]
    )


def _add_relation_routes(app: FastAPI, kernel: KernelInterface) -> None:
    path = "/api/v1/projects/{project_id}/relations"
    app.add_api_route(path, _connect(kernel), methods=["POST"], status_code=201)
    app.add_api_route(path, _relations(kernel), methods=["GET"])
    app.add_api_route(
        f"{path}/{{relation_id}}", _remove_relation(kernel), methods=["DELETE"]
    )


def _record(kernel: KernelInterface):
    def endpoint(project_id: str, request: RecordRequest):
        return kernel.record(
            project_id, request.type, request.content, request.artifact_ids
        )

    return endpoint


def _records(kernel: KernelInterface):
    def endpoint(project_id: str):
        return kernel.list_records(project_id)

    return endpoint


def _remove_record(kernel: KernelInterface):
    def endpoint(project_id: str, record_id: str):
        kernel.remove_record(project_id, record_id)
        return Response(status_code=204)

    return endpoint


def _connect(kernel: KernelInterface):
    def endpoint(project_id: str, request: RelationRequest):
        return kernel.connect(
            project_id, request.source_id, request.target_id, request.type
        )

    return endpoint


def _relations(kernel: KernelInterface):
    def endpoint(project_id: str):
        return kernel.list_relations(project_id)

    return endpoint


def _remove_relation(kernel: KernelInterface):
    def endpoint(project_id: str, relation_id: str):
        kernel.remove_relation(project_id, relation_id)
        return Response(status_code=204)

    return endpoint


async def _not_found(_request, error: KeyError):
    return JSONResponse({"detail": str(error)}, status_code=404)


async def _forbidden(_request, error: PermissionError):
    return JSONResponse({"detail": str(error)}, status_code=403)


async def _invalid(_request, error: ValueError):
    return JSONResponse({"detail": str(error)}, status_code=422)
