import asyncio
import hashlib
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
from pybtex.database import parse_string

from server.app import create_app
from server.artifacts import ArtifactStore
from server.kernel import KernelQuery, ResearchKernel
from server.project_export import package


class TraceRuntime:
    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def inspect(self, session_id):
        return {"session_id": session_id, "token": "trace-secret", "path": "C:\\work\\secret.txt"}


def inspect(kernel, project_id):
    return asyncio.run(kernel.query(KernelQuery("project_export", project_id)))


def archive(content):
    return zipfile.ZipFile(io.BytesIO(content))


def item(content, media_type="text/plain", bibtex=False):
    raw = content.encode() if isinstance(content, str) else content
    digest = hashlib.sha256(raw).hexdigest()
    return {"id": f"artifact:{digest}", "sha256": digest, "media_type": media_type, "size": len(raw), "created_at": "1980-01-01", "content": raw, "bibtex": bibtex}


def exported(content, media_type="text/plain", bibtex=False):
    artifact = item(content, media_type, bibtex)
    return archive(package({"id": "project:test"}, {}, [], {}, [artifact])), artifact


def members(content):
    return b"".join(content.read(name) for name in content.namelist())


def test_artifacts_never_copy_raw_bytes_for_all_media():
    values = [(b"text-secret /home/a/b", "text/plain"), (b"@preamble{secret}", "application/x-bibtex"), (b"<x xmlns='https://secret/x'/>", "application/xml"), (b"token: yaml-secret", "application/yaml"), (b"\x00binary-secret", "application/unknown")]
    for raw, media_type in values:
        content, artifact = exported(raw, media_type)
        assert raw not in members(content)
        assert json.loads(content.read(f"artifacts/{artifact['sha256']}"))["omitted"] == "raw_content"


def test_bibtex_member_is_metadata_only_and_parseable():
    content, artifact = exported("@article{x, author={Secret Person}}", "application/x-bibtex")
    record = content.read(f"bibtex/{artifact['sha256']}.bib")

    assert b"Secret Person" not in members(content)
    assert artifact["sha256"].encode() in record
    assert parse_string(record.decode(), "bibtex").entries == {}


@pytest.mark.parametrize("text", [
    "API---KEY = quoted secret suffix", "client___secret: [bracketed secret suffix]",
    "ToKeN=unquoted secret suffix", "ratio (/alpha/beta) and C:/Users/Alice/private.txt",
    "path /数据/2026-private/result file.txt", "https://example.org/a/b",
])
def test_safe_text_removes_secrets_and_paths_without_url_damage(text):
    content = package({"id": "project:test", "note": text}, {}, [], {}, [])
    value = archive(content).read("project.json")

    assert b"suffix" not in value and b"Alice" not in value and b"/alpha/beta" not in value
    if text.startswith("https"):
        assert text.encode() in value


def test_public_metadata_never_leaks_malformed_values():
    artifact = item(b"body", "text/plain; token=media-secret")
    content = package({"id": "/private/project"}, {}, [], {}, [artifact])

    assert b"media-secret" not in members(archive(content))
    assert b"/private/project" not in members(archive(content))


def test_safe_transform_marks_unsafe_structures_and_nan():
    cycle = []
    cycle.append(cycle)
    content = package({"id": "project:test"}, {"bad": {1: "key"}, "cycle": cycle}, [{"nan": float("nan")}], {"binary": b"secret"}, [])
    files = archive(content)

    assert b"secret" not in members(files)
    assert json.loads(files.read("project.json"))["graph"]["bad"] == "[REDACTED]"
    assert json.loads(files.read("pipeline-runs.json"))[0]["nan"] == "[REDACTED]"


def test_package_is_deterministic_with_valid_manifest():
    first, artifact = exported("raw artifact", "application/octet-stream")
    second, _ = exported("raw artifact", "application/octet-stream")
    manifest = json.loads(first.read("manifest.json"))

    assert first.fp.getvalue() == second.fp.getvalue()
    assert first.namelist() == sorted(first.namelist())
    for record in manifest["files"]:
        assert record["sha256"] == hashlib.sha256(first.read(record["path"])).hexdigest()
    assert f"artifacts/{artifact['sha256']}" in first.namelist()


def test_kernel_export_sanitizes_facts_and_preserves_inventory(world, project, tmp_path):
    store = ArtifactStore(world.artifacts_root, project["id"])
    saved = store.add(b"artifact-secret /tmp/path", "application/octet-stream")
    project["question"] = "Authorization: project-secret at /tmp/project"
    content = inspect(ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceRuntime()), project["id"])
    files = archive(content)

    assert b"secret" not in members(files) and b"/tmp/" not in members(files)
    inventory = json.loads(files.read("artifacts.json"))
    assert inventory[0]["sha256"] == saved["sha256"]


def test_export_requires_runtime_for_referenced_trace(world, project, tmp_path):
    world.create_thread(project["id"], "Discussion", "session:thread", "research-assistant")
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")

    with pytest.raises(ValueError, match="Runtime Trace"):
        inspect(kernel, project["id"])


def test_export_rejects_artifacts_outside_project_scope(world, project, tmp_path):
    other = world.create_project("other", tmp_path / "other", "Other question")
    foreign = ArtifactStore(world.artifacts_root, other["id"]).add(b"foreign", "text/plain")
    node = world.nodes(project["id"])[0]
    world.create_run(project["id"], node["id"], {"id": "run", "stages": []}, {"artifact_id": foreign["id"]})
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=TraceRuntime())

    with pytest.raises(ValueError, match="outside project scope"):
        inspect(kernel, project["id"])


def test_project_export_downloads_zip(world, project, tmp_path):
    client = TestClient(create_app(ResearchKernel(world, projects_root=tmp_path / "projects")))
    response = client.get(f"/api/v1/projects/{project['id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
