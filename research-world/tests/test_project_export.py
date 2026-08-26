import asyncio
import hashlib
import json
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from server.app import create_app
from server.artifacts import ArtifactStore
from server.kernel import KernelQuery, ResearchKernel


def inspect(kernel, query):
    return asyncio.run(kernel.query(query))


class ExportRuntime:
    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def inspect(self, session_id):
        return trace(session_id)


def trace(session_id):
    return {
        "session": {"id": session_id, "workspace": "/tmp/export-workspace"},
        "events": [{"message": "Authorization: Bearer export-secret"}],
    }


def export_kernel(world, tmp_path):
    return ResearchKernel(
        world, projects_root=tmp_path / "projects", runtime=ExportRuntime()
    )


def artifact_store(world, project):
    return ArtifactStore(world.artifacts_root, project["id"])


def add_artifacts(world, project):
    store = artifact_store(world, project)
    artifacts = {
        "measurement": store.add(b"measurement", "text/plain"),
        "bibtex": store.add(valid_bibtex().encode(), "application/x-bibtex"),
        "secret": store.add(b"apikey=export-secret", "text/plain"),
    }
    (store.root / "temporary.tmp").write_text("omit", encoding="utf-8")
    return artifacts


def add_project_facts(world, project, artifacts):
    direction = world.create_node(
        project["id"],
        "direction",
        {"text": "Stable orbit", "apikey": "export-secret", "path": "/tmp/export"},
    )
    source = world.create_node(
        project["id"], "source", {"title": "Citation", "artifact_ids": [artifacts["bibtex"]["id"]]}
    )
    world.admit_node(direction["id"])
    world.admit_node(source["id"])
    return direction


def add_pipeline_run(world, project, node):
    definition = {"id": "research", "name": "Research", "stages": []}
    run = world.create_run(project["id"], node["id"], definition)
    world.add_step(run["id"], 0, "research", {"cwd": "/tmp/export"}, False)
    return run


def add_report(world, project):
    thread = world.create_thread(project["id"], "Trace", "session:export", "agent")
    artifact = artifact_store(world, project).add(b"<!doctype html><title>Report</title>", "text/html")
    publication = world.publish_report(project["id"], thread["id"], "Report", artifact["id"])
    world.save_report(project["id"], thread["id"], "V1", publication["id"])
    return thread


def seed_export_state(world, project):
    artifacts = add_artifacts(world, project)
    node = add_project_facts(world, project, artifacts)
    run = add_pipeline_run(world, project, node)
    thread = add_report(world, project)
    return {"artifacts": artifacts, "run": run, "thread": thread}


def export_archive(kernel, project):
    return inspect(kernel, KernelQuery("project_export", project["id"]))


def archive_files(archive):
    with ZipFile(BytesIO(archive)) as bundle:
        return {name: bundle.read(name) for name in bundle.namelist()}


def manifest(archive):
    return json.loads(archive_files(archive)["manifest.json"])


def checksums(archive):
    lines = archive_files(archive)["checksums.sha256"].decode().splitlines()
    return {path: digest for digest, path in (line.split("  ") for line in lines)}


def valid_bibtex():
    return "@article{orbit, title={Stable Orbits}, author={Li, Ada}, year={2026}}"


def test_kernel_export_is_deterministic_and_complete(world, project, tmp_path):
    kernel, state = export_kernel(world, tmp_path), seed_export_state(world, project)
    first, second = export_archive(kernel, project), export_archive(kernel, project)
    files = archive_files(first)
    assert first == second
    assert manifest(first)["format"] == "research-world-project-export/v1"
    assert manifest(first)["project_id"] == project["id"]
    assert json.loads(files["project.json"])["project"]["question"] == project["question"]
    assert json.loads(files["pipeline-runs.json"])[0]["id"] == state["run"]["id"]
    assert any(name.startswith("traces/") for name in files)
    assert any(name.startswith("artifacts/") for name in files)
    assert any(name.startswith("reports/") for name in files)
    assert state["artifacts"]["measurement"]["id"].encode() in first
    assert b"measurement" not in first
    assert files["references.bib"].decode() == valid_bibtex()


def test_kernel_export_manifest_checks_every_payload(world, project, tmp_path):
    archive = export_archive(export_kernel(world, tmp_path), project)
    files, digest_map = archive_files(archive), checksums(archive)
    paths = [entry["path"] for entry in manifest(archive)["files"]]
    assert "checksums.sha256" not in digest_map
    assert digest_map["manifest.json"] == hashlib.sha256(files["manifest.json"]).hexdigest()
    assert paths == sorted(paths)
    for path, digest in digest_map.items():
        assert hashlib.sha256(files[path]).hexdigest() == digest


def test_kernel_export_redacts_credentials_paths_and_temporary_files(world, project, tmp_path):
    archive = export_archive(export_kernel(world, tmp_path), project)
    names = archive_files(archive)
    assert b"export-secret" not in archive
    assert b"/tmp/export" not in archive
    assert str(project["root"]).encode() not in archive
    assert not any("temporary.tmp" in name for name in names)


def test_export_http_downloads_the_kernel_archive(world, project, tmp_path):
    kernel = export_kernel(world, tmp_path)
    response = TestClient(create_app(kernel)).get(f"/api/v1/projects/{project['id']}/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert response.headers["content-disposition"] == 'attachment; filename="project-export.zip"'
    assert response.content == export_archive(kernel, project)
