from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StrictInt

from .kernel_interface import KernelInterface, LocalMapQuery

__all__ = ["kernel_graph_router"]


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


class LocalMapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str | None = None
    record_id: str | None = None
    limit: StrictInt = 20


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    question: str


def kernel_graph_router(kernel: KernelInterface) -> APIRouter:
    router = APIRouter()
    _add_project_routes(router, kernel)
    _add_record_routes(router, kernel)
    _add_relation_routes(router, kernel)
    _add_local_map_route(router, kernel)
    return router


def _add_project_routes(router: APIRouter, kernel: KernelInterface) -> None:
    path = "/api/v1/projects"
    router.add_api_route(path, _projects(kernel), methods=["GET"])
    router.add_api_route(path, _create_project(kernel), methods=["POST"], status_code=201)
    router.add_api_route("/api/v1/bootstrap", _bootstrap(kernel), methods=["GET"])


def _projects(kernel: KernelInterface):
    def endpoint():
        return kernel.list_projects()

    return endpoint


def _create_project(kernel: KernelInterface):
    def endpoint(request: ProjectRequest):
        return _kernel_call(kernel.create_project, request.name, request.question)

    return endpoint


def _bootstrap(kernel: KernelInterface):
    def endpoint(project_id: str | None = None):
        projects = kernel.list_projects()
        selected = _kernel_call(_select_project, kernel, projects, project_id)
        return _bootstrap_value(projects, selected)

    return endpoint


def _select_project(kernel, projects, project_id):
    return kernel.get_project(project_id) if project_id else (projects[0] if projects else None)


def _bootstrap_value(projects, selected):
    return {
        "projects": projects,
        "active_project_id": selected.id if selected else None,
    }


def _add_record_routes(router: APIRouter, kernel: KernelInterface) -> None:
    path = "/api/v1/projects/{project_id}/records"
    router.add_api_route(path, _record(kernel), methods=["POST"], status_code=201)
    router.add_api_route(path, _records(kernel), methods=["GET"])
    router.add_api_route(
        f"{path}/{{record_id}}", _remove_record(kernel), methods=["DELETE"]
    )


def _add_relation_routes(router: APIRouter, kernel: KernelInterface) -> None:
    path = "/api/v1/projects/{project_id}/relations"
    router.add_api_route(path, _connect(kernel), methods=["POST"], status_code=201)
    router.add_api_route(path, _relations(kernel), methods=["GET"])
    router.add_api_route(
        f"{path}/{{relation_id}}", _remove_relation(kernel), methods=["DELETE"]
    )


def _add_local_map_route(router: APIRouter, kernel: KernelInterface) -> None:
    router.add_api_route(
        "/api/v1/projects/{project_id}/local-map", _local_map(kernel), methods=["POST"]
    )


def _record(kernel: KernelInterface):
    def endpoint(project_id: str, request: RecordRequest):
        return _kernel_call(
            kernel.record,
            project_id, request.type, request.content, request.artifact_ids
        )

    return endpoint


def _records(kernel: KernelInterface):
    def endpoint(project_id: str):
        return _kernel_call(kernel.list_records, project_id)

    return endpoint


def _remove_record(kernel: KernelInterface):
    def endpoint(project_id: str, record_id: str):
        _kernel_call(kernel.remove_record, project_id, record_id)
        return Response(status_code=204)

    return endpoint


def _connect(kernel: KernelInterface):
    def endpoint(project_id: str, request: RelationRequest):
        return _kernel_call(
            kernel.connect,
            project_id, request.source_id, request.target_id, request.type
        )

    return endpoint


def _relations(kernel: KernelInterface):
    def endpoint(project_id: str):
        return _kernel_call(kernel.list_relations, project_id)

    return endpoint


def _remove_relation(kernel: KernelInterface):
    def endpoint(project_id: str, relation_id: str):
        _kernel_call(kernel.remove_relation, project_id, relation_id)
        return Response(status_code=204)

    return endpoint


def _local_map(kernel: KernelInterface):
    def endpoint(project_id: str, request: LocalMapRequest):
        query = LocalMapQuery(request.text, request.record_id, request.limit)
        return _kernel_call(kernel.local_map, project_id, query)

    return endpoint


def _kernel_call(operation, *args):
    try:
        return operation(*args)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
