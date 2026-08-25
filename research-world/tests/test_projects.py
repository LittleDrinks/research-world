from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import create_app
from server.cli import main
from server.kernel import ResearchKernel


def client(world, tmp_path):
    root = tmp_path / "projects"
    kernel = ResearchKernel(world, projects_root=root)
    return TestClient(create_app(kernel)), root


def test_project_api_allocates_workspace(world, tmp_path):
    api, root = client(world, tmp_path)
    response = api.post(
        "/api/v1/projects", json={"name": "New study", "title": "New study", "question": "Why?"}
    )
    workspace = Path(response.json()["root"])
    assert response.status_code == 201
    assert workspace.parent == root.resolve()
    assert workspace.is_dir()


def test_project_api_rejects_browser_supplied_root(world, tmp_path):
    api, _ = client(world, tmp_path)
    response = api.post(
        "/api/v1/projects",
        json={"name": "Bad", "title": "Bad", "question": "Why?", "root": "/tmp/injected"},
    )
    assert response.status_code == 400
    assert world.projects() == []


def test_cli_imports_q049_with_its_explicit_title(world, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    source = Path(__file__).parents[1] / "projects/q049/project.json"
    output, error = StringIO(), StringIO()

    assert main(["project", "create", "--file", str(source)], kernel, output, error) == 0

    question = world.nodes(world.projects()[0]["id"])[0]
    assert question["payload"]["title"] == "Planetary Orbit Decay"


def test_project_creation_failure_removes_allocated_workspace(world, project, tmp_path):
    api, root = client(world, tmp_path)
    api = TestClient(api.app, raise_server_exceptions=False)

    response = api.post(
        "/api/v1/projects", json={"name": project["name"], "title": "Duplicate", "question": "Duplicate"}
    )

    assert response.status_code == 500
    assert list(root.iterdir()) == []
