import asyncio
import hashlib
import io
import json
import zipfile

from fastapi.testclient import TestClient

from server.artifacts import ArtifactStore
from server.app import create_app
from server.kernel import KernelQuery, ResearchKernel


class TraceRuntime:
    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def inspect(self, session_id):
        return {
            "session_id": session_id,
            "workspace": "/tmp/runtime-workspace",
            "api_key": "secret-value",
            "events": [{"path": "C:\\\\absolute\\\\result.txt"}],
        }


def inspect(kernel, project_id):
    return asyncio.run(kernel.query(KernelQuery("project_export", project_id)))


def exported(kernel, project):
    return zipfile.ZipFile(io.BytesIO(inspect(kernel, project["id"])))


def test_project_export_is_deterministic_complete_and_redacted(world, project, tmp_path):
    store = ArtifactStore(world.artifacts_root, project["id"])
    report = store.add(b"<h1>Report</h1>", "text/html")
    bibtex = store.add(b"@article{orbit, title={Stable orbit}}", "application/x-bibtex")
    source = world.create_node(project["id"], "source", {
        "title": "Orbit source", "artifact_ids": [bibtex["id"]], "api_key": "node-secret",
    })
    experiment = world.create_node(project["id"], "experiment", {"artifact_ids": [report["id"]]})
    world.admit_node(source["id"])
    world.admit_node(experiment["id"])
    question = world.nodes(project["id"])[0]
    run = world.create_run(project["id"], question["id"], {"id": "research", "stages": []})
    world.record_run_event(run["id"], "agent", "agent_session", {"session_id": "session:run"})
    world.create_thread(project["id"], "Discussion", "session:thread", "research-assistant")
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceRuntime())

    first, second = inspect(kernel, project["id"]), inspect(kernel, project["id"])
    archive = zipfile.ZipFile(io.BytesIO(first))
    names = archive.namelist()
    manifest = json.loads(archive.read("manifest.json"))

    assert first == second
    assert names == sorted(names)
    assert {"project.json", "pipeline-runs.json", "traces.json", "artifacts.json", "manifest.json"} <= set(names)
    assert f"reports/{report['sha256']}.html" in names
    assert f"bibtex/{bibtex['sha256']}.bib" in names
    assert json.loads(archive.read("traces.json"))["session:run"]["workspace"] == "[REDACTED]"
    assert json.loads(archive.read("project.json"))["project"]["root"] == "[REDACTED]"
    assert b"secret-value" not in first and b"node-secret" not in first and b"/tmp/" not in first
    assert all(entry["path"] != "manifest.json" for entry in manifest["files"])
    for entry in manifest["files"]:
        content = archive.read(entry["path"])
        assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        assert entry["size"] == len(content)


def test_project_export_downloads_zip_with_attachment_header(world, project, tmp_path):
    client = TestClient(create_app(ResearchKernel(world, projects_root=tmp_path / "projects")))

    response = client.get(f"/api/v1/projects/{project['id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=\"project-" in response.headers["content-disposition"]
    assert zipfile.is_zipfile(io.BytesIO(response.content))
