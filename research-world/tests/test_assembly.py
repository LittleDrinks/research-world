from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.library import DEFAULT_ASSEMBLY, resolve_assembly


@pytest.fixture
def client(world):
    return TestClient(create_app(world))


def hook(arguments: dict) -> dict:
    return {"tool": "graph_query", "arguments": arguments, "session_id": "s1", "turn_id": "t1"}


def test_project_defaults_to_builtin_assembly(project):
    assert project["assembly"] == DEFAULT_ASSEMBLY


def test_project_stores_specified_assembly(world, tmp_path):
    project = world.create_project("custom", tmp_path / "custom", "Why?", assembly=["graph-query"])
    assert project["assembly"] == ["graph-query"]


def test_create_project_rejects_unknown_package(world, tmp_path):
    with pytest.raises(ValueError, match="unknown capability packages"):
        world.create_project("bad", tmp_path / "bad", "Why?", assembly=["warp-drive"])


def test_resolve_assembly_returns_package_definitions():
    packages = resolve_assembly(["graph-query"])
    assert packages[0]["tools"][0]["path"] == "/api/v1/tools/graph-query"


def test_library_endpoint_lists_builtin_packages(client):
    packages = client.get("/api/v1/library").json()
    assert {"fs", "graph-query"} <= {package["name"] for package in packages}


def test_create_project_api_rejects_unknown_package(client, tmp_path):
    response = client.post("/api/v1/projects", json={
        "name": "bad-api", "root": str(tmp_path), "question": "Why?", "assembly": ["nope"]})
    assert response.status_code == 400


def test_graph_query_get_returns_full_payload(client, world, project):
    node = world.create_node(project["id"], "direction", {"text": "Resonance", "quality": 0.7})
    response = client.post("/api/v1/tools/graph-query",
                           json=hook({"action": "get", "project_id": project["id"],
                                      "node_id": node["id"]}))
    assert response.status_code == 200
    assert response.json() == {"text": "Resonance", "quality": 0.7}


def test_graph_query_get_rejects_cross_project(client, world, project, tmp_path):
    other = world.create_project("other", tmp_path / "other", "Other?")
    node = world.create_node(other["id"], "direction", {"text": "Secret"})
    response = client.post("/api/v1/tools/graph-query",
                           json=hook({"action": "get", "project_id": project["id"],
                                      "node_id": node["id"]}))
    assert response.status_code == 404


def test_graph_query_search_returns_summaries(client, world, project):
    node = world.create_node(project["id"], "direction", {"text": "orbital resonance stability"})
    world.create_node(project["id"], "direction", {"text": "unrelated chaos theory"})
    response = client.post("/api/v1/tools/graph-query",
                           json=hook({"action": "search", "project_id": project["id"],
                                      "query": "resonance"}))
    hits = response.json()
    assert [hit["id"] for hit in hits] == [node["id"]]
    assert hits[0]["kind"] == "direction"
    assert hits[0]["life_state"] == "pending"
    assert "orbital resonance stability" in hits[0]["summary"]


def test_graph_query_rejects_unknown_action(client, project):
    response = client.post("/api/v1/tools/graph-query",
                           json=hook({"action": "delete", "project_id": project["id"]}))
    assert response.status_code == 400
