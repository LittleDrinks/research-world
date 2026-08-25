import asyncio
import hashlib
import io
import json
import zipfile
from xml.etree import ElementTree

import pytest
import yaml
from fastapi.testclient import TestClient
from pybtex.database import parse_string

from server.artifacts import ArtifactStore
from server.app import create_app
from server.kernel import KernelQuery, ResearchKernel
from server.project_export import _textual, package


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


class AdversarialRuntime:
    def __init__(self, secret, path):
        self.secret, self.path = secret, path

    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def inspect(self, session_id):
        return {
            "message": f"Authorization: Bearer {self.secret}",
            "config": {"client_secret": "trace-client-secret"},
            "serialized": r'{\"api_key\":\"serialized-secret\"}',
            "paths": ["/2026/study/private data.csv", "/-hidden/private/a", "/数据/private/a", "C:\\work\\private result.txt"],
            "url": "https://example.org/paper",
            "usage": {"prompt_tokens": 17, "cost": 0.02},
        }


def inspect(kernel, project_id):
    return asyncio.run(kernel.query(KernelQuery("project_export", project_id)))


def archive(content):
    return zipfile.ZipFile(io.BytesIO(content))


def add_artifact(store, content, media_type="text/plain"):
    return store.add(content.encode(), media_type)


def export_item(content, media_type, bibtex=False):
    raw = content.encode() if isinstance(content, str) else content
    digest = hashlib.sha256(raw).hexdigest()
    item = {"id": f"artifact:{digest}", "sha256": digest, "media_type": media_type, "size": len(raw), "created_at": "1980-01-01", "content": raw, "bibtex": bibtex}
    return archive(package({"id": "project:test"}, {}, [], {}, [item])), item


def artifact_member(exported, item):
    return exported.read(f"artifacts/{item['sha256']}")


def all_members(exported):
    return b"".join(exported.read(name) for name in exported.namelist())


def test_textual_media_contract_is_exact():
    textual = ("text/markdown", "application/problem+json", "image/svg+xml", "application/json", "application/x-bibtex", "application/xml", "application/javascript", "application/yaml", "application/x-yaml")

    assert all(_textual(media_type) for media_type in textual)
    assert not _textual("application/octet-stream")


def adversarial_export(world, project, tmp_path):
    secret, path = "sk-live-secret", "/home/researcher/Project Files/private result.txt"
    project["question"] = 'Project client_secret=project-client-secret at "/2026/study/private data.csv".'
    store = ArtifactStore(world.artifacts_root, project["id"])
    bibtex = add_artifact(store, f'@article{{orbit, note={{client_secret={secret} "{path}"}}}}', "application/x-bibtex")
    artifact = add_artifact(store, json.dumps({"client_secret": "json-client-secret", "path": "/2026/study/private data.csv"}), "application/json")
    text_bibtex = add_artifact(store, f"@book{{orbit, note={{api_key={secret} \"{path}\"}}}}", "text/x-bibtex")
    text = add_artifact(store, 'The ratio /alpha/beta is dimensionless and the result is stable. Path "/数据/private data.csv".', "text/plain")
    xml = add_artifact(store, "<record><client_secret>xml-secret</client_secret><path>/2026/study/private data.csv</path></record>", "application/xml")
    svg = add_artifact(store, '<svg xmlns="http://www.w3.org/2000/svg"><metadata client_secret="svg-secret" path="/-hidden/private/a" /></svg>', "image/svg+xml")
    yaml_artifact = add_artifact(store, "client_secret: yaml-secret\npath: /数据/private data.csv\n", "application/yaml")
    javascript = add_artifact(store, 'const client_secret = "javascript-secret"; const path = "/-hidden/private/a";', "application/javascript")
    source = world.create_node(project["id"], "source", {"title": "Source", "artifact_ids": [bibtex["id"], text_bibtex["id"]]})
    world.admit_node(source["id"])
    run = world.create_run(project["id"], world.nodes(project["id"])[0]["id"], {"id": "research", "stages": []}, {"artifact_id": artifact["id"], "client_secret": "run-client-secret", "path": "/-hidden/private/a"})
    world.record_run_event(run["id"], "agent", "agent_session", {"session_id": "session:adversarial"})
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=AdversarialRuntime(secret, path))
    sensitive = (secret, "project-client-secret", "json-client-secret", "run-client-secret", "trace-client-secret", "serialized-secret", "xml-secret", "svg-secret", "yaml-secret", "javascript-secret", "/home/researcher", "Project Files", "/2026/study", "/-hidden", "/数据", "private data.csv", "C:\\work")
    artifacts = {"json": artifact, "text": text, "xml": xml, "svg": svg, "yaml": yaml_artifact, "javascript": javascript}
    return inspect(kernel, project["id"]), (bibtex, text_bibtex), sensitive, artifacts


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


def test_export_redacts_adversarial_text_without_damaging_urls(world, project, tmp_path):
    content, bibtex_artifacts, sensitive, artifacts = adversarial_export(world, project, tmp_path)
    exported = archive(content)
    files = {name: exported.read(name) for name in exported.namelist()}
    copies = b"".join(files.values())

    assert all(value.encode() not in content for value in sensitive)
    assert all(value.encode() not in copies for value in sensitive)
    assert b"https://example.org/paper" in files["traces.json"]
    assert b'"prompt_tokens": 17' in files["traces.json"] and b'"cost": 0.02' in files["traces.json"]
    assert b"The ratio /alpha/beta is dimensionless and the result is stable." in files[f"artifacts/{artifacts['text']['sha256']}"]
    assert json.loads(files[f"artifacts/{artifacts['json']['sha256']}"])
    assert yaml.safe_load(files[f"artifacts/{artifacts['yaml']['sha256']}"])
    assert b'const path = "[REDACTED]"' in files[f"artifacts/{artifacts['javascript']['sha256']}"]
    for kind in ("xml", "svg"):
        ElementTree.fromstring(files[f"artifacts/{artifacts[kind]['sha256']}"])
    for item in bibtex_artifacts:
        assert files[f"artifacts/{item['sha256']}"] == files[f"bibtex/{item['sha256']}.bib"]
        assert sensitive[0].encode() not in files[f"bibtex/{item['sha256']}.bib"]
        parse_string(files[f"bibtex/{item['sha256']}.bib"].decode(), "bibtex")


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


def test_bracketed_and_forward_slash_windows_paths_redact_without_ratio_crash():
    exported, item = export_item("The ratio (/alpha/beta) is dimensionless. [C:/Users/Alice/private.txt]", "text/plain")
    member = artifact_member(exported, item)

    assert b"The ratio (/alpha/beta) is dimensionless." in member
    assert b"Alice" not in member and b"[REDACTED]" in member


@pytest.mark.parametrize(("media_type", "content"), [
    ("application/json", '{"client_secret":"json-secret"'),
    ("application/xml", "<record><token>xml-secret</record>"),
    ("application/yaml", "token: !vault yaml-secret\n"),
])
def test_unparseable_structured_artifacts_are_complete_safe_records(media_type, content):
    exported, item = export_item(content, media_type)
    member = artifact_member(exported, item)

    assert b"secret" not in all_members(exported)
    if "json" in media_type:
        assert json.loads(member)["redacted"] is True
    elif "xml" in media_type:
        assert ElementTree.fromstring(member).tag == "redacted"
    else:
        assert yaml.safe_load(member)["redacted"] is True


def test_nested_escaped_json_is_structurally_redacted():
    exported, item = export_item(json.dumps(json.dumps({"client-secret": "twice-secret"})), "application/json")
    member = artifact_member(exported, item)

    assert b"twice-secret" not in all_members(exported)
    assert json.loads(json.loads(member))["client-secret"] == "[REDACTED]"


def test_credential_key_variants_redact_in_every_declared_format():
    contents = [("text/plain", "client-secret=plain-secret api-key=key-secret token=one-secret tokens=two-secret"), ("application/json", '{"api-key":"json-secret"}'), ("application/xml", "<x><client-secret>xml-secret</client-secret></x>"), ("image/svg+xml", '<svg api-key="svg-secret"/>'), ("application/yaml", "tokens: yaml-secret\n")]
    exported = [export_item(content, media_type)[0] for media_type, content in contents]
    raw = (b"plain-secret", b"key-secret", b"one-secret", b"two-secret", b"json-secret", b"xml-secret", b"svg-secret", b"yaml-secret")

    assert all(value not in b"".join(all_members(item) for item in exported) for value in raw)


def test_valid_bibtex_stays_parseable_and_redacts_each_copy():
    exported, item = export_item("@article{x, password = {bib secret}}", "application/x-bibtex", True)
    artifact, bibtex = artifact_member(exported, item), exported.read(f"bibtex/{item['sha256']}.bib")

    assert artifact == bibtex and b"bib secret" not in all_members(exported)
    assert parse_string(bibtex.decode(), "bibtex").entries["x"].fields["password"] == "[REDACTED]"


def test_malformed_bibtex_becomes_parseable_safe_record():
    exported, item = export_item("@article{x, password = {bib-secret}", "application/x-bibtex")
    member = artifact_member(exported, item)

    assert b"bib-secret" not in all_members(exported)
    assert parse_string(member.decode(), "bibtex").entries == {}


def test_binary_artifact_is_metadata_only_omission():
    raw = b"binary-secret\x00C:/Users/Alice/private.bin"
    exported, item = export_item(raw, "application/octet-stream")
    member, metadata = artifact_member(exported, item), json.loads(exported.read("artifacts.json"))

    assert raw not in all_members(exported) and b"Alice" not in member
    assert json.loads(member)["omitted"] == "opaque_binary"
    assert metadata[0]["sha256"] == item["sha256"] and metadata[0]["redacted"] is True


def test_mixed_key_yaml_is_deterministic_and_parseable():
    first, item = export_item("1: one\na: two\n", "application/yaml")
    second, _ = export_item("1: one\na: two\n", "application/yaml")

    assert artifact_member(first, item) == artifact_member(second, item)
    assert yaml.safe_load(artifact_member(first, item)) == {1: "one", "a": "two"}


def test_xml_retains_comments_and_processing_instructions():
    exported, item = export_item("<root><?status ready?><!--token=comment-secret--><![CDATA[token=cdata-secret]]><token>xml-secret</token></root>", "application/xml")
    member = artifact_member(exported, item)

    assert b"<!--token=[REDACTED]-->" in member and b"<?status ready?>" in member
    assert b"xml-secret" not in member and b"cdata-secret" not in member
    assert ElementTree.fromstring(member).tag == "root"
