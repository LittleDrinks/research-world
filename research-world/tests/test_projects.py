from pathlib import Path

from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import ResearchKernel


class CatalogRuntime:
    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def recognize(self, workspace):
        self.workspace = workspace
        return {"endpoints": [], "models": [], "skills": [], "tools": [], "presets": []}


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
    existing = set(root.iterdir())

    response = api.post(
        "/api/v1/projects", json={"name": project["name"], "question": "Duplicate"}
    )

    assert response.status_code == 500
    assert set(root.iterdir()) == existing


def test_runtime_workspace_uses_canonical_project_storage(world, tmp_path):
    stale = tmp_path / "old-worktree" / "0123456789abcdef01234567"
    project = world.create_project("Moved", stale, "Why?")
    root = tmp_path / "canonical-projects"
    runtime = CatalogRuntime()
    kernel = ResearchKernel(world, projects_root=root, runtime=runtime)
    assert (root / stale.name).is_dir()

    response = TestClient(create_app(kernel)).get(
        "/api/v1/runtime/catalog", params={"project_id": project["id"]}
    )

    assert response.status_code == 200
    assert Path(runtime.workspace) == root / stale.name
    assert Path(runtime.workspace).is_dir()
