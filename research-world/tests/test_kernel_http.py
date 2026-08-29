from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from server.kernel_http import kernel_graph_router
from server.kernel_interface import create_kernel


def _client(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))
    return kernel, TestClient(app)


def _project(kernel, name="Orbit study"):
    return kernel.create_project(name, "Why do planetary orbits remain stable?")


def _record(client, project_id, record_type, content, artifact_ids=()):
    response = client.post(
        f"/api/v1/projects/{project_id}/records",
        json={
            "type": record_type,
            "content": content,
            "artifact_ids": artifact_ids,
        },
    )
    assert response.status_code == 201
    return response.json()


def _connect(client, project_id, source_id, target_id, relation_type="supports"):
    return client.post(
        f"/api/v1/projects/{project_id}/relations",
        json={"source_id": source_id, "target_id": target_id, "type": relation_type},
    )


def test_http_records_and_rejects_cross_project_connections(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    other = _project(kernel, "Other study")
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(client, project.id, "direction", {"text": "Candidate"})
    foreign = _record(client, other.id, "direction", {"text": "Foreign"})

    assert client.get(f"/api/v1/projects/{project.id}/records").json() == [
        source,
        direction,
    ]
    assert _connect(client, project.id, source["id"], foreign["id"]).status_code == 403
    connected = _connect(client, project.id, source["id"], direction["id"])
    assert connected.status_code == 201


def test_http_duplicate_connect_returns_domain_validation_error(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(client, project.id, "direction", {"text": "Candidate"})
    first = _connect(client, project.id, source["id"], direction["id"])

    repeated = _connect(client, project.id, source["id"], direction["id"])

    assert (first.status_code, repeated.status_code) == (201, 422)
    relations = client.get(f"/api/v1/projects/{project.id}/relations")
    assert relations.json() == [first.json()]


def test_http_remove_relation_preserves_records(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(client, project.id, "direction", {"text": "Candidate"})
    relation = _connect(client, project.id, source["id"], direction["id"]).json()

    response = client.delete(
        f"/api/v1/projects/{project.id}/relations/{relation['id']}"
    )

    assert response.status_code == 204
    records = client.get(f"/api/v1/projects/{project.id}/records")
    assert records.json() == [source, direction]
    assert client.get(f"/api/v1/projects/{project.id}/relations").json() == []


def test_http_remove_record_cascades_relation_and_preserves_artifact(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    artifact = kernel.capture_artifact(project.id, b"evidence", "text/plain")
    source = _record(client, project.id, "source", {"title": "Study"}, [artifact.id])
    direction = _record(client, project.id, "direction", {"text": "Candidate"})
    _connect(client, project.id, source["id"], direction["id"])

    response = client.delete(
        f"/api/v1/projects/{project.id}/records/{direction['id']}"
    )

    assert response.status_code == 204
    assert client.get(f"/api/v1/projects/{project.id}/relations").json() == []
    assert client.get(f"/api/v1/projects/{project.id}/records").json() == [source]
    assert kernel.read_artifact(project.id, artifact.id) == b"evidence"


def test_http_record_rejects_storage_and_internal_state_inputs(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)

    response = client.post(
        f"/api/v1/projects/{project.id}/records",
        json={
            "type": "direction",
            "content": {"text": "Candidate"},
            "sql": "opaque",
            "table": "opaque",
            "pending": True,
        },
    )

    assert response.status_code == 422


def test_router_preserves_an_existing_value_error_handler(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    app = FastAPI()

    @app.exception_handler(ValueError)
    async def existing_handler(_request, error):
        return JSONResponse({"existing": str(error)}, status_code=409)

    app.include_router(kernel_graph_router(kernel))

    @app.get("/value-error")
    def value_error():
        raise ValueError("unchanged")

    response = TestClient(app).get("/value-error")
    assert (response.status_code, response.json()) == (409, {"existing": "unchanged"})


def test_router_included_before_fallback_handles_graph_requests(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = _project(kernel)
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))

    @app.get("/{path:path}")
    def fallback(path: str):
        return {"fallback": path}

    response = TestClient(app).get(f"/api/v1/projects/{project.id}/records")
    assert (response.status_code, response.json()) == (200, [])


def test_http_maps_kernel_errors_at_the_endpoint(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(client, project.id, "direction", {"text": "Candidate"})

    missing = client.delete(f"/api/v1/projects/{project.id}/records/missing")
    invalid = _connect(
        client, project.id, source["id"], direction["id"], "reviews"
    )

    assert (missing.status_code, invalid.status_code) == (404, 422)
