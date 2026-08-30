import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import ResearchKernel
from server.kernel_http import kernel_graph_router
from server.kernel_interface import create_kernel
from server.world import World


def _client(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))
    return kernel, TestClient(app)


def _application_client(tmp_path):
    graph_kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    world = World(tmp_path / "world.db", tmp_path / "world-artifacts")
    app_kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    return TestClient(create_app(app_kernel, graph_kernel=graph_kernel))


def test_application_assembly_requires_graph_kernel(tmp_path):
    world = World(tmp_path / "world.db", tmp_path / "world-artifacts")
    app_kernel = ResearchKernel(world, projects_root=tmp_path / "projects")

    with pytest.raises(TypeError, match="graph_kernel"):
        create_app(app_kernel)


def _create_application_project(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Map assembly", "question": "How does the map share its project?"},
    )
    assert response.status_code == 201
    return response.json()


def _application_graph(client, project):
    source = _record(client, project["id"], "source", {"text": "shared map evidence"})
    direction = _record(client, project["id"], "direction", {"text": "shared map route"})
    relation = _connect(client, project["id"], source["id"], direction["id"])
    local_map = client.post(
        f"/api/v1/projects/{project['id']}/local-map",
        json={"text": "shared map", "limit": 5},
    )
    return source, direction, relation, local_map


def _assert_application_map(local_map, source, direction, relation):
    result = local_map.json()
    assert [record["id"] for record in result["records"]] == [
        source["id"],
        direction["id"],
    ]
    assert result["relations"] == [relation.json()]


def test_application_patch_updates_world_project_without_touching_kernel_project(tmp_path):
    graph_kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    world = World(tmp_path / "world.db", tmp_path / "world-artifacts")
    world_project = world.create_project(
        "Legacy auto", tmp_path / "legacy-project", "Legacy question"
    )
    app_kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(app_kernel, graph_kernel=graph_kernel))
    kernel_project = _create_application_project(client)

    response = client.patch(
        f"/api/v1/projects/{world_project['id']}", json={"auto": True}
    )

    assert response.status_code == 200
    assert response.json() == {**world_project, "auto": 1}
    assert client.get("/api/v1/projects").json() == [kernel_project]


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


def _local_map(client, project_id, record_id):
    return client.post(
        f"/api/v1/projects/{project_id}/local-map",
        json={"record_id": record_id, "limit": 5},
    )


def _artifact_view(artifact):
    return {
        "id": artifact.id,
        "project_id": artifact.project_id,
        "sha256": artifact.sha256,
        "media_type": artifact.media_type,
        "size": artifact.size,
        "created_at": artifact.created_at,
    }


def _assert_local_map(response, direction, relation, artifact):
    assert response.status_code == 200
    assert response.json() == {
        "records": [direction],
        "relations": [relation],
        "artifacts": [_artifact_view(artifact)],
    }


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
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(
        client, project.id, "direction", {"text": "Candidate"}, [artifact.id]
    )
    _connect(client, project.id, source["id"], direction["id"])

    response = client.delete(
        f"/api/v1/projects/{project.id}/records/{direction['id']}"
    )

    assert response.status_code == 204
    assert client.get(f"/api/v1/projects/{project.id}/relations").json() == []
    assert client.get(f"/api/v1/projects/{project.id}/records").json() == [source]
    assert kernel.read_artifact(project.id, artifact.id) == b"evidence"


def test_http_local_map_returns_records_relations_and_artifacts(tmp_path):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    artifact = kernel.capture_artifact(project.id, b"evidence", "text/plain")
    source = _record(client, project.id, "source", {"title": "Study"})
    direction = _record(
        client, project.id, "direction", {"text": "Candidate"}, [artifact.id]
    )
    relation = _connect(client, project.id, source["id"], direction["id"]).json()
    _assert_local_map(_local_map(client, project.id, direction["id"]), direction, relation, artifact)


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"text": " ", "record_id": " "},
        {"text": "orbit", "record_id": "record:any", "limit": 5},
        {"text": "orbit", "limit": 0},
        {"text": "orbit", "limit": -1},
        {"text": "orbit", "limit": True},
        {"text": "orbit", "limit": "1"},
        {"text": "orbit", "limit": 1.0},
        {"text": "orbit", "sql": "SELECT 1"},
        {"text": "orbit", "cypher": "MATCH (n)"},
        {"text": "orbit", "fts": "node_fts"},
        {"text": "orbit", "embedding": [0.1]},
        {"text": "orbit", "mmr": True},
        {"text": "orbit", "reviewer": "review"},
    ),
)
def test_http_local_map_rejects_non_domain_queries(tmp_path, payload):
    kernel, client = _client(tmp_path)
    project = _project(kernel)

    response = client.post(
        f"/api/v1/projects/{project.id}/local-map", json=payload
    )

    assert response.status_code == 422


def test_application_project_bootstrap_and_local_map_share_kernel_owner(tmp_path):
    client = _application_client(tmp_path)
    project = _create_application_project(client)
    bootstrap = client.get("/api/v1/bootstrap", params={"project_id": project["id"]})
    assert bootstrap.status_code == 200
    body = bootstrap.json()
    assert body["projects"] == [project]
    assert set(body) == {"projects", "active_project_id"}
    assert body["active_project_id"] == project["id"]

    source, direction, relation, local_map = _application_graph(client, project)

    assert relation.status_code == 201
    assert local_map.status_code == 200
    _assert_application_map(local_map, source, direction, relation)


@pytest.mark.parametrize(
    "extra_field",
    (
        "action",
        "admission",
        "pipeline",
        "auto",
        "sql",
        "cypher",
        "table",
        "review",
        "review_state",
        "life_state",
        "pending",
        "admitted",
        "ghost",
    ),
)
def test_http_record_rejects_non_domain_inputs(tmp_path, extra_field):
    kernel, client = _client(tmp_path)
    project = _project(kernel)
    response = client.post(
        f"/api/v1/projects/{project.id}/records",
        json={
            "type": "direction",
            "content": {"text": "Candidate"},
            extra_field: "opaque",
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
