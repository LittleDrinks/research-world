from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.kernel_http import kernel_graph_routes
from server.kernel_interface import create_kernel


def _client(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    app = FastAPI()
    kernel_graph_routes(app, kernel)
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
            "sql": "DELETE FROM kernel_records",
            "table": "kernel_records",
            "pending": True,
        },
    )

    assert response.status_code == 422
