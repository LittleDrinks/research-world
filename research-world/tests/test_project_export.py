import asyncio
import hashlib
import io
import json
import zipfile

import pytest
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
            "usage": {"prompt_tokens": 17, "cost": 0.02},
            "messages": ["Authorization: trace-secret at /tmp/trace"],
            "tool": {"arguments": {"path": "C:\\work\\result.txt"}, "result": "api_key=trace-key"},
        }


def inspect(kernel, project_id):
    return asyncio.run(kernel.query(KernelQuery("project_export", project_id)))


def archive(content):
    return zipfile.ZipFile(io.BytesIO(content))


def add_artifact(store, content, media_type="text/plain"):
    return store.add(content.encode(), media_type)


def test_export_redacts_embedded_text_and_preserves_artifact_identity(world, project, tmp_path):
    store = ArtifactStore(world.artifacts_root, project["id"])
    report = add_artifact(store, "<p>api_key=artifact-key /tmp/report.txt</p>", "text/html")
    bibtex = add_artifact(store, "@article{orbit, title={Stable orbit}}", "application/x-bibtex")
    source = world.create_node(project["id"], "source", {"title": "Source", "artifact_ids": [bibtex["id"]]})
    world.admit_node(source["id"])
    run = world.create_run(project["id"], world.nodes(project["id"])[0]["id"], {"id": "research", "stages": []}, {"artifact_id": report["id"]})
    world.record_run_event(run["id"], "agent", "agent_session", {"session_id": "session:run"})
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceRuntime())

    content = inspect(kernel, project["id"])
    exported = archive(content)
    metadata = json.loads(exported.read("artifacts.json"))
    report_metadata = next(item for item in metadata if item["id"] == report["id"])

    assert b"trace-secret" not in content and b"artifact-key" not in content
    assert b"/tmp/" not in content and b"C:\\work" not in content
    assert json.loads(exported.read("traces.json"))["session:run"]["usage"]["prompt_tokens"] == 17
    assert report_metadata["sha256"] == report["sha256"]
    assert report_metadata["export_sha256"] != report["sha256"]
    assert report_metadata["redacted"] is True
    assert f"reports/{report['sha256']}.html" not in exported.namelist()


def test_export_includes_run_trace_and_saved_artifacts_only_from_project(world, project, tmp_path):
    store = ArtifactStore(world.artifacts_root, project["id"])
    run_artifact = add_artifact(store, "run")
    step_artifact = add_artifact(store, "step")
    event_artifact = add_artifact(store, "event")
    trace_artifact = add_artifact(store, "trace")
    saved = add_artifact(store, "saved report")
    other = world.create_project("other", tmp_path / "other", "Other question")
    foreign = add_artifact(ArtifactStore(world.artifacts_root, other["id"]), "foreign")
    run = world.create_run(project["id"], world.nodes(project["id"])[0]["id"], {"id": "research", "stages": []}, {"artifact_id": run_artifact["id"]})
    world.add_step(run["id"], 0, "prompt", {"artifact_id": step_artifact["id"]}, False)
    world.record_run_event(run["id"], "agent", "agent_session", {"session_id": "session:run", "artifact_id": event_artifact["id"]})

    class TraceArtifactRuntime(TraceRuntime):
        async def inspect(self, session_id):
            return {"session_id": session_id, "result": {"artifact_id": trace_artifact["id"]}}

    content = inspect(ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceArtifactRuntime()), project["id"])
    names = set(archive(content).namelist())

    for artifact in (run_artifact, step_artifact, event_artifact, trace_artifact, saved):
        assert f"artifacts/{artifact['sha256']}" in names
    assert f"artifacts/{foreign['sha256']}" not in names


def test_export_requires_runtime_for_referenced_trace(world, project, tmp_path):
    world.create_thread(project["id"], "Discussion", "session:thread", "research-assistant")
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")

    with pytest.raises(ValueError, match="Runtime Trace"):
        inspect(kernel, project["id"])


def test_export_has_stable_zip_metadata_and_manifest(world, project, tmp_path):
    store = ArtifactStore(world.artifacts_root, project["id"])
    bibtex = add_artifact(store, "@article{orbit, title={Stable orbit}}", "application/x-bibtex")
    source = world.create_node(project["id"], "source", {"title": "Source", "artifact_ids": [bibtex["id"]]})
    world.admit_node(source["id"])
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceRuntime())

    first, second = inspect(kernel, project["id"]), inspect(kernel, project["id"])
    exported = archive(first)
    manifest = json.loads(exported.read("manifest.json"))

    assert first == second
    assert exported.namelist() == sorted(exported.namelist())
    assert f"bibtex/{bibtex['sha256']}.bib" in exported.namelist()
    assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in exported.infolist())
    assert all(info.create_system == 3 and info.external_attr == 0o100600 << 16 for info in exported.infolist())
    assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in exported.infolist())
    assert all(item["path"] != "manifest.json" for item in manifest["files"])
    for item in manifest["files"]:
        assert item["sha256"] == hashlib.sha256(exported.read(item["path"])).hexdigest()


def test_project_export_downloads_zip_with_attachment_header(world, project, tmp_path):
    client = TestClient(create_app(ResearchKernel(world, projects_root=tmp_path / "projects")))
    response = client.get(f"/api/v1/projects/{project['id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=\"project-" in response.headers["content-disposition"]
