import os
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import ResearchKernel


def client(world, tmp_path):
    root = tmp_path / "projects"
    kernel = ResearchKernel(world, projects_root=root)
    return TestClient(create_app(kernel)), root


def test_project_api_allocates_workspace(world, tmp_path):
    api, root = client(world, tmp_path)
    response = api.post(
        "/api/v1/projects", json={"name": "New study", "question": "Why?"}
    )
    workspace = Path(response.json()["root"])
    assert response.status_code == 201
    assert workspace.parent == root.resolve()
    assert workspace.is_dir()


def test_project_api_transfers_workspace_to_projects_root_owner(
    world, tmp_path, monkeypatch
):
    api, root = client(world, tmp_path)
    calls = []
    monkeypatch.setattr(os, "chown", lambda path, uid, gid: calls.append((path, uid, gid)))

    response = api.post(
        "/api/v1/projects", json={"name": "New study", "question": "Why?"}
    )

    workspace = Path(response.json()["root"])
    owner = root.stat()
    assert calls == [(workspace, owner.st_uid, owner.st_gid)]


def test_project_api_rejects_browser_supplied_root(world, tmp_path):
    api, _ = client(world, tmp_path)
    response = api.post(
        "/api/v1/projects",
        json={"name": "Bad", "question": "Why?", "root": "/tmp/injected"},
    )
    assert response.status_code == 400
    assert world.projects() == []


def test_project_creation_failure_removes_allocated_workspace(world, project, tmp_path):
    api, root = client(world, tmp_path)
    api = TestClient(api.app, raise_server_exceptions=False)

    response = api.post(
        "/api/v1/projects", json={"name": project["name"], "question": "Duplicate"}
    )

    assert response.status_code == 500
    assert list(root.iterdir()) == []
