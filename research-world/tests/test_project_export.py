import asyncio
import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.artifacts import ArtifactIntegrityError, ArtifactStore
from server.kernel import KernelQuery, ResearchKernel


VALID_REPORT = (
    b"<!doctype html><html><head><title>Report</title></head><body>"
    b"<h1>Report</h1><h2>Research question</h2><p>Orbit?</p>"
    b"<h2>Conclusions</h2><ul><li><a href=\"#evidence-source\">[Source]</a></li></ul>"
    b"<h2>Evidence and methods</h2><table><tr><th>Source</th><th>Level</th><th>Checked</th></tr>"
    b"<tr id=\"evidence-source\"><td>Source</td><td>published</td><td>2026-08-26</td></tr></table>"
    b"<h2>Limitations and gaps</h2><p>No validated delivery gaps.</p></body></html>"
)


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


def add_report(world, project, content=VALID_REPORT):
    thread = world.create_thread(project["id"], "Trace", "session:export", "agent")
    artifact = artifact_store(world, project).add(content, "text/html")
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
    seed_export_state(world, project)
    archive = export_archive(export_kernel(world, tmp_path), project)
    files, digest_map = archive_files(archive), checksums(archive)
    paths = [entry["path"] for entry in manifest(archive)["files"]]
    assert "checksums.sha256" not in digest_map
    assert digest_map["manifest.json"] == hashlib.sha256(files["manifest.json"]).hexdigest()
    assert paths == sorted(paths)
    for path, digest in digest_map.items():
        assert hashlib.sha256(files[path]).hexdigest() == digest


def test_kernel_export_redacts_credentials_paths_and_temporary_files(world, project, tmp_path):
    seed_export_state(world, project)
    archive = export_archive(export_kernel(world, tmp_path), project)
    names = archive_files(archive)
    assert b"export-secret" not in archive
    assert b"/tmp/export" not in archive
    assert str(project["root"]).encode() not in archive
    assert not any("temporary.tmp" in name for name in names)


def test_export_http_downloads_the_kernel_archive(world, project, tmp_path):
    seed_export_state(world, project)
    kernel = export_kernel(world, tmp_path)
    response = TestClient(create_app(kernel)).get(f"/api/v1/projects/{project['id']}/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert response.headers["content-disposition"] == 'attachment; filename="project-export.zip"'
    assert response.content == export_archive(kernel, project)


def test_kernel_export_rejects_tampered_unreferenced_artifact(world, project, tmp_path):
    state = seed_export_state(world, project)
    Path(state["artifacts"]["measurement"]["path"]).write_bytes(b"tampered")

    with pytest.raises(ArtifactIntegrityError) as captured:
        export_archive(export_kernel(world, tmp_path), project)

    assert captured.value.code == "content_hash_mismatch"
    assert captured.value.artifact_id == state["artifacts"]["measurement"]["id"]


@pytest.mark.parametrize("content,media_type", [
    (b"not a report", "text/html"),
    (VALID_REPORT.replace(b"Orbit?", b"sk-abcdefghijklmnopqrstuvwxyz"), "text/html"),
    (VALID_REPORT, "text/plain"),
])
def test_kernel_export_rejects_claimed_invalid_published_report(world, project, tmp_path, content, media_type):
    thread = world.create_thread(project["id"], "Trace", "session:invalid-report", "agent")
    artifact = artifact_store(world, project).add(content, media_type)
    world.publish_report(project["id"], thread["id"], "Report", artifact["id"])
    bibtex = artifact_store(world, project).add(valid_bibtex().encode(), "application/x-bibtex")
    world.create_node(project["id"], "source", {"artifact_ids": [bibtex["id"]]}, life_state="admitted")

    with pytest.raises(ValueError, match="published report"):
        export_archive(export_kernel(world, tmp_path), project)


@pytest.mark.parametrize("payload", [
    b'<p>{"token":"serialized-secret"}</p>',
    b'<p>{\\"token\\":\\"escaped-secret\\"}</p>',
    b"<p>?sig=relative-secret</p>",
])
def test_kernel_export_rejects_secret_bearing_published_report(world, project, tmp_path, payload):
    content = VALID_REPORT.replace(b"</body>", payload + b"</body>")
    add_report(world, project, content)
    bibtex = artifact_store(world, project).add(valid_bibtex().encode(), "application/x-bibtex")
    world.create_node(project["id"], "source", {"artifact_ids": [bibtex["id"]]}, life_state="admitted")

    with pytest.raises(ValueError, match="unsafe published report"):
        export_archive(export_kernel(world, tmp_path), project)


def test_kernel_export_requires_a_valid_bibtex_entry(world, project, tmp_path):
    with pytest.raises(ValueError, match="at least one valid BibTeX entry"):
        export_archive(export_kernel(world, tmp_path), project)


@pytest.mark.parametrize("value", [
    "file:///home/research/result.txt",
    "https://example.test/download?key=plain-secret&keep=yes",
    "standalone sk-abcdefghijklmnopqrstuvwxyz",
])
def test_kernel_export_redacts_uri_query_and_standalone_secrets(world, project, tmp_path, value):
    seed_export_state(world, project)
    world.create_node(project["id"], "experiment", {"note": value}, life_state="admitted")

    archive = export_archive(export_kernel(world, tmp_path), project)

    assert value.encode() not in archive


def test_kernel_export_redacts_secrets_in_serialized_structures(world, project, tmp_path):
    seed_export_state(world, project)
    world.create_node(project["id"], "experiment", {"encoded": '{"token":"serialized-secret","safe":"kept"}'}, life_state="admitted")

    archive = export_archive(export_kernel(world, tmp_path), project)

    assert b"serialized-secret" not in archive
    assert b'\\"safe\\":\\"kept\\"' in archive


def test_kernel_export_redacts_malformed_serialized_json(world, project, tmp_path):
    seed_export_state(world, project)
    world.create_node(project["id"], "experiment", {"encoded": '{"token":"malformed-secret"'}, life_state="admitted")

    files = archive_files(export_archive(export_kernel(world, tmp_path), project))
    project_file = json.loads(files["project.json"])
    node = next(node for node in project_file["nodes"] if "encoded" in node["payload"])

    assert node["payload"]["encoded"] == "[redacted]"
    assert all(b"malformed-secret" not in content for content in files.values())


def test_kernel_export_redacts_nested_json_and_bibtex_fields(world, project, tmp_path):
    seed_export_state(world, project)
    nested = {"token": "nested-token", "key": "nested-key", "secret": "nested-secret", "bibtex": "@article{orbit, key={bib-key}}", "safe": "kept"}
    world.create_node(project["id"], "experiment", {"encoded": json.dumps({"nested": json.dumps(nested)})}, life_state="admitted")

    files = archive_files(export_archive(export_kernel(world, tmp_path), project))

    assert all(value not in b"".join(files.values()) for value in (b"nested-token", b"nested-key", b"nested-secret", b"bib-key"))
    assert b"kept" in files["project.json"]


def test_kernel_export_redacts_sensitive_bibtex_fields_in_zip_member(world, project, tmp_path):
    store = artifact_store(world, project)
    content = "@article{orbit, key={bib-key}, token={bib-token}, secret={bib-secret}, title={kept}}"
    bibtex = store.add(content.encode(), "application/x-bibtex")
    world.create_node(project["id"], "source", {"artifact_ids": [bibtex["id"]]}, life_state="admitted")

    files = archive_files(export_archive(export_kernel(world, tmp_path), project))

    assert b"bib-key" not in files["references.bib"]
    assert b"bib-token" not in files["references.bib"]
    assert b"bib-secret" not in files["references.bib"]
    assert b"kept" in files["references.bib"]


def test_kernel_export_stays_within_requested_project_scope(world, project, tmp_path):
    state = seed_export_state(world, project)
    other = world.create_project("other", tmp_path / "other", "Foreign question")
    foreign = ArtifactStore(world.artifacts_root, other["id"]).add(b"foreign-only", "text/plain")
    world.create_node(other["id"], "direction", {"text": "foreign-only"}, life_state="admitted")

    archive = export_archive(export_kernel(world, tmp_path), project)

    assert state["artifacts"]["measurement"]["id"].encode() in archive
    assert foreign["id"].encode() not in archive
    assert other["id"].encode() not in archive
    assert b"foreign-only" not in archive


def test_kernel_export_rejects_foreign_artifact_reference(world, project, tmp_path):
    other = world.create_project("other", tmp_path / "other", "Foreign question")
    foreign = ArtifactStore(world.artifacts_root, other["id"]).add(b"foreign-only", "text/plain")
    seed_export_state(world, project)
    world.create_node(project["id"], "experiment", {"artifact_ids": [foreign["id"]]}, life_state="admitted")

    with pytest.raises(ValueError, match="outside project scope"):
        export_archive(export_kernel(world, tmp_path), project)
