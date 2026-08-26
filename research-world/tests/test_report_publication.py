import asyncio
import sqlite3
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Event

import pytest
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from server.artifacts import ArtifactStore
from server.app import create_app
from server.kernel import KernelCommand, KernelQuery, ResearchKernel
from server.report_delivery import validate_html
from server.reporting import REPORT_INPUT_TOKEN_BUDGET
from server.runtime_client import KernelClient


def kernel(world, tmp_path):
    return ResearchKernel(world, projects_root=tmp_path / "projects")


def source_payload(artifact_id=None):
    value = {"title": "Validated measurement", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}
    return {**value, "artifact_ids": [artifact_id]} if artifact_id else value


def admitted_evidence(world, project, artifact_id=None):
    source = admitted_source(world, project, artifact_id)
    claim = {"text": "Measured at 42 K.", "verdict": "supported", "evidence": [source["id"]]}
    direction = world.create_node(project["id"], "direction", {"claims": [claim]})
    world.admit_node(direction["id"])
    return source


def admitted_source(world, project, artifact_id=None):
    source = world.create_node(project["id"], "source", source_payload(artifact_id))
    world.admit_node(source["id"])
    return source


def png():
    return b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")


def png_with_metadata(text):
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", text)
    stream = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(stream, "PNG", pnginfo=info)
    return stream.getvalue()


def report_thread(world, project):
    session_id = f"s-{project['id'][-8:]}"
    return world.create_thread(project["id"], "chat", session_id, "research-assistant")


def publish(value, project, thread, title="Orbit report"):
    values = {"thread_id": thread["id"], "title": title}
    return asyncio.run(value.command(KernelCommand("thread_publish_report", project["id"], values)))


def capture(value, project, content, media_type="text/plain"):
    values = {"content": content, "media_type": media_type}
    return asyncio.run(value.command(KernelCommand("capture_artifact", project["id"], values)))


def broken_readback(monkeypatch, world, method):
    original = getattr(world, method)

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("post-commit readback failed")

    monkeypatch.setattr(world, method, fail)
    return original


def test_kernel_rejects_caller_facts_and_fabricated_projection_text(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    thread = report_thread(world, project)
    with pytest.raises(ValueError, match="facts"):
        publish_facts(value, project, thread)
    monkeypatch.setattr(value, "_publication_projection", lambda _id: ready_projection(fabricated_projection()))
    result = publish(value, project, thread)
    assert result["status"] == "failed"
    assert result["assessment"]["gaps"][0]["code"] == "fact_text_mismatch"


def publish_facts(value, project, thread):
    values = {"thread_id": thread["id"], "title": "x", "facts": []}
    return asyncio.run(value.command(KernelCommand("thread_publish_report", project["id"], values)))


def fabricated_projection():
    source_id = "node:" + "a" * 24
    claim_id = "claim:" + "b" * 24 + ":1"
    evidence = {"id": source_id, "kind": "source", "artifact_ids": []}
    source = {"id": source_id, "title": "Paper", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}
    claim = {"id": claim_id, "text": "Measured", "life_state": "admitted", "verdict": "supported", "evidence": [evidence], "evidence_ids": [source_id], "source_ids": [source_id], "artifact_ids": []}
    fact = {"text": "Fabricated", "claim_id": claim_id, "source_ids": [source_id], "artifact_ids": []}
    return {"question": "How does it behave?", "facts": [fact], "claims": [claim], "sources": [source], "artifacts": []}


def ready_projection(projection):
    return {"status": "ready", "projection": projection, "contract": {}}


def test_projection_filters_unsafe_fields_and_unlinked_artifacts(world, project, tmp_path):
    value = kernel(world, tmp_path)
    linked, unrelated = capture(value, project, b"linked"), capture(value, project, b"unrelated")
    source = admitted_evidence(world, project, linked["id"])
    payload = {"artifact_ids": [unrelated["id"]]}
    world.create_node(project["id"], "experiment", payload, life_state="admitted")
    unsafe = {**world.node(source["id"])["payload"], "apikey": "secret", "baseurl": "https://secret", "config_path": "/etc/key", "raw": {"token": "secret"}}
    world.update_node(source["id"], unsafe)
    envelope = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    assert envelope["status"] == "ready"
    projection = envelope["projection"]
    assert set(projection["sources"][0]) == {"id", "title", "source_level", "checked_at"}
    assert [item["id"] for item in projection["artifacts"]] == [linked["id"]]
    assert "secret" not in str(projection)
    assert all(field not in str(envelope) for field in ("apikey", "baseurl", "config_path", "raw"))


def test_publication_renders_typed_evidence_with_exact_source_links(world, project, tmp_path):
    value = kernel(world, tmp_path)
    sources, projection = typed_projection(value, world, project)
    assert_exact_source_links(projection, sources)
    thread = report_thread(world, project)
    content = read(value, project, thread, publish(value, project, thread)["publication"]).decode()
    assert_rendered_evidence(content, projection)


def typed_projection(value, world, project):
    code = capture(value, project, b"result = 42")
    formula = capture(value, project, b"E = mc^2", "application/x-latex")
    chart = capture(value, project, png(), "image/png")
    sources = [admitted_source(world, project, item["id"]) for item in (code, formula, chart)]
    claim = {"text": "Three independent measurements agree.", "verdict": "supported", "evidence": [item["id"] for item in sources]}
    direction = world.create_node(project["id"], "direction", {"claims": [claim]})
    world.admit_node(direction["id"])
    envelope = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    assert envelope["status"] == "ready"
    return sources, envelope["projection"]


def assert_exact_source_links(projection, sources):
    claim_id = projection["facts"][0]["claim_id"]
    links = {tuple(sorted(item["links"][0].items())) for item in projection["artifacts"]}
    expected = {tuple(sorted({"claim_id": claim_id, "evidence_id": source["id"], "source_id": source["id"]}.items())) for source in sources}
    assert links == expected


def assert_rendered_evidence(content, projection):
    assert '<pre><code data-artifact=' in content
    assert '<div class="formula"' in content
    assert '<img src="data:image/png;base64,' in content
    assert all(item["id"] in content for item in projection["artifacts"])


def test_publication_reencodes_chart_without_input_metadata(world, project, tmp_path):
    value, secret = kernel(world, tmp_path), "report-image-sensitive"
    artifact = capture(value, project, png_with_metadata(secret), "image/png")
    admitted_evidence(world, project, artifact["id"])
    thread = report_thread(world, project)
    content = read(value, project, thread, publish(value, project, thread)["publication"])
    delivered = b64decode(content.split(b"data:image/png;base64,", 1)[1].split(b'"', 1)[0])
    assert secret.encode() not in content and secret.encode() not in delivered
    with Image.open(BytesIO(delivered)) as image:
        image.load()
        assert image.format == "PNG" and image.size == (2, 2)
        assert image.getpixel((0, 0)) == (0, 0, 255, 255)


def test_publication_rejects_invalid_declared_png(world, project, tmp_path):
    value = kernel(world, tmp_path)
    artifact = capture(value, project, b"not a png", "image/png")
    admitted_evidence(world, project, artifact["id"])
    result = publish(value, project, report_thread(world, project))
    assert result["stages"][-1] == {"name": "citation_validation", "status": "failed"}
    assert result["assessment"]["gaps"][0]["code"] == "artifact_display_invalid"


def test_persistence_failure_keeps_internal_artifact_without_visible_records(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = report_thread(world, project)
    stored, original = [], ArtifactStore.add

    def add(store, content, media_type):
        record = original(store, content, media_type)
        stored.append(record["id"])
        return record

    monkeypatch.setattr(ArtifactStore, "add", add)
    monkeypatch.setattr(world, "publish_report", lambda *_: (_ for _ in ()).throw(OSError("db down")))
    result = publish(value, project, thread)
    assert result["stages"][-1] == {"name": "persistence", "status": "failed"}
    assert not world.report_publications(project["id"], thread["id"])
    assert not world.reports(project["id"], thread["id"])
    assert ArtifactStore(world.artifacts_root, project["id"]).get(stored[-1])["id"] == stored[-1]


def test_persistence_insert_failure_has_no_publication_content_url(world, project, tmp_path, monkeypatch):
    value, thread = kernel(world, tmp_path), report_thread(world, project)
    admitted_evidence(world, project)
    monkeypatch.setattr(world, "publish_report", lambda *_: (_ for _ in ()).throw(sqlite3.OperationalError("insert failed")))
    client = TestClient(create_app(value))
    response = client.post(f"/api/v1/threads/{thread['id']}/report/publish", json={"title": "Orbit"})
    assert response.status_code == 422 and response.json()["status"] == "failed"
    assert response.json()["stages"][-1] == {"name": "persistence", "status": "failed"}
    assert not world.report_publications(project["id"], thread["id"])
    assert client.get(f"/api/v1/threads/{thread['id']}/report/publication:missing/content").status_code == 404


def test_publish_returns_committed_record_when_postcommit_readback_fails(world, project, tmp_path, monkeypatch):
    value, thread = kernel(world, tmp_path), report_thread(world, project)
    admitted_evidence(world, project)
    original = broken_readback(monkeypatch, world, "publication")
    result = publish(value, project, thread)
    monkeypatch.setattr(world, "publication", original)
    assert result["status"] == "published"
    assert world.report_publications(project["id"], thread["id"]) == [result["publication"]]
    assert read(value, project, thread, result["publication"]).startswith(b"<!doctype html>")


def test_save_returns_committed_record_when_postcommit_readback_fails(world, project, tmp_path, monkeypatch):
    value, thread = kernel(world, tmp_path), report_thread(world, project)
    admitted_evidence(world, project)
    publication = publish_thread(value, project, thread)
    original = broken_readback(monkeypatch, world, "report")
    saved = save(value, project, thread, publication, "V1")
    monkeypatch.setattr(world, "report", original)
    assert saved["publication_id"] == publication["id"]
    assert world.reports(project["id"], thread["id"]) == [saved]


def test_publication_rejects_secrets_before_the_rendering_model(world, project, tmp_path):
    value = kernel(world, tmp_path)
    artifact = capture(value, project, b"result = 42")
    source = admitted_evidence(world, project, artifact["id"])
    payload = {**world.node(source["id"])["payload"], "title": "baseurl=https://secret.example"}
    world.update_node(source["id"], payload)
    projection = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    thread = report_thread(world, project)
    result = publish(value, project, thread)
    assert "secret" not in str(projection)
    assert "secret" not in str(result)
    assert result["status"] == "failed"
    assert result["stages"] == [{"name": "projection", "status": "failed"}]
    assert not world.report_publications(project["id"], thread["id"])


@pytest.mark.parametrize("content", [b"OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz", b"baseurl=https://credentials.example", b"session_id: temporary-session", b"/tmp/report-secret.txt"])
def test_publication_rejects_restricted_artifact_text_without_leaking_it(world, project, tmp_path, content):
    value = kernel(world, tmp_path)
    artifact = capture(value, project, content)
    admitted_evidence(world, project, artifact["id"])
    thread = report_thread(world, project)
    envelope = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    result = publish(value, project, thread)
    assert envelope["status"] == "ready"
    assert result["stages"] == [{"name": "projection", "status": "completed"}, {"name": "citation_validation", "status": "failed"}]
    assert content.decode() not in str(result)
    assert not world.report_publications(project["id"], thread["id"])


def test_failed_validation_has_no_publication_side_effect(world, project, tmp_path):
    value = kernel(world, tmp_path)
    thread = report_thread(world, project)
    result = publish(value, project, thread)
    assert result["status"] == "failed"
    assert result["stages"] == [{"name": "projection", "status": "failed"}]
    assert not world.report_publications(project["id"], thread["id"])


def test_publication_ignores_unprojected_admitted_payload(world, project, tmp_path):
    value = kernel(world, tmp_path)
    marker = "bounded-artifact"
    world.create_node(project["id"], "experiment", {"notes": marker * (REPORT_INPUT_TOKEN_BUDGET + 1)}, life_state="admitted")
    thread = report_thread(world, project)
    result = publish(value, project, thread)
    assert result["stages"] == [{"name": "projection", "status": "failed"}]
    assert result["assessment"]["gaps"][0]["code"] == "facts_missing"
    assert marker not in str(result)
    assert not world.report_publications(project["id"], thread["id"])


def test_publication_anchors_experiment_owned_artifacts_to_the_exact_claim(world, project, tmp_path):
    value = kernel(world, tmp_path)
    source = admitted_source(world, project)
    artifact = capture(value, project, b"experiment = 42")
    experiment = world.create_node(project["id"], "experiment", {"artifact_ids": [artifact["id"]]}, life_state="admitted")
    direction = world.create_node(project["id"], "direction", {"claims": [{"text": "Experiment supports the result.", "verdict": "supported", "evidence": [source["id"], experiment["id"]]}]})
    world.admit_node(direction["id"])
    envelope = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    projection = envelope["projection"]
    link = projection["artifacts"][0]["links"][0]
    thread = report_thread(world, project)
    result = publish(value, project, thread)
    content = read(value, project, thread, result["publication"]).decode()
    assert link == {"claim_id": projection["facts"][0]["claim_id"], "evidence_id": experiment["id"]}
    assert f'id="evidence-{experiment["id"]}"' in content
    assert f'href="#evidence-{experiment["id"]}"' in content


def test_publication_saved_content_passes_the_actual_output_validator(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = report_thread(world, project)
    publication = publish(value, project, thread)["publication"]
    assert validate_html(read(value, project, thread, publication)) == []


def test_identical_bytes_publish_independently_per_project(world, project, tmp_path):
    value = kernel(world, tmp_path)
    other = world.create_project("other", tmp_path / "other", "Other?")
    value._publication_projection = lambda _id: ready_projection(shared_projection())
    first = publish(value, project, report_thread(world, project))
    second = publish(value, other, report_thread(world, other))
    assert first["artifact"]["id"] == second["artifact"]["id"]
    assert first["publication"]["project_id"] != second["publication"]["project_id"]


def shared_projection():
    source_id = "node:" + "f" * 24
    claim_id = "claim:" + "1" * 24 + ":1"
    evidence = {"id": source_id, "kind": "source", "artifact_ids": []}
    claim = {"id": claim_id, "text": "Measured", "life_state": "admitted", "verdict": "supported", "evidence": [evidence], "evidence_ids": [source_id], "source_ids": [source_id], "artifact_ids": []}
    fact = {"text": "Measured", "claim_id": claim_id, "source_ids": [source_id], "artifact_ids": []}
    source = {"id": source_id, "title": "Paper", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}
    return {"question": "How does it behave?", "facts": [fact], "claims": [claim], "sources": [source], "artifacts": []}


def test_named_save_is_immutable_and_duplicate_names_are_actionable(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = world.create_thread(project["id"], "chat", "session:1", "research-assistant")
    publication = publish_thread(value, project, thread)
    saved = save(value, project, thread, publication, "V1")
    before = read(value, project, thread, publication)
    assert asyncio.run(value.query(KernelQuery("report", project["id"], {"report_id": saved["id"]}))) == saved
    assert before == read(value, project, thread, publication)
    with pytest.raises(ValueError, match="report_name_taken"):
        save(value, project, thread, publication, "V1")
    assert world.reports(project["id"], thread["id"]) == [saved]


def publish_thread(value, project, thread):
    values = {"thread_id": thread["id"], "title": "Orbit"}
    return asyncio.run(value.command(KernelCommand("thread_publish_report", project["id"], values)))["publication"]


def save(value, project, thread, publication, title):
    values = {"thread_id": thread["id"], "publication_id": publication["id"], "title": title}
    return asyncio.run(value.command(KernelCommand("save_report", project["id"], values)))


def read(value, project, thread, publication):
    values = {"thread_id": thread["id"], "publication_id": publication["id"]}
    return asyncio.run(value.query(KernelQuery("report_content", project["id"], values)))


def test_report_content_rejects_foreign_thread(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    first = world.create_thread(project["id"], "one", "session:1", "research-assistant")
    second = world.create_thread(project["id"], "two", "session:2", "research-assistant")
    publication = publish_thread(value, project, first)
    with pytest.raises(KeyError):
        read(value, project, second, publication)


def test_http_thread_publication_save_and_scoped_download(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = world.create_thread(project["id"], "chat", "session:1", "research-assistant")
    client = TestClient(create_app(value))
    publish = client.post(f"/api/v1/threads/{thread['id']}/report/publish", json={"title": "Orbit"})
    publication = publish.json()["publication"]
    save = client.post(f"/api/v1/threads/{thread['id']}/report/save", json={"title": "V1", "publication_id": publication["id"]})
    path = f"/api/v1/threads/{thread['id']}/report/{publication['id']}/content"
    download = client.get(f"{path}?download=true")
    assert publish.status_code == save.status_code == 201
    assert "sandbox" in client.get(path).headers["content-security-policy"]
    assert download.headers["content-disposition"].startswith("attachment")
    assert client.post(f"/api/v1/threads/{thread['id']}/report/save", json={"title": "V1", "publication_id": publication["id"]}).status_code == 409


def test_http_failed_publication_is_not_created(world, project, tmp_path):
    value = kernel(world, tmp_path)
    thread = report_thread(world, project)
    response = TestClient(create_app(value)).post(f"/api/v1/threads/{thread['id']}/report/publish", json={"title": "Orbit"})
    assert response.status_code == 422
    assert response.json()["status"] == "failed"
    assert response.json()["stages"] == [{"name": "projection", "status": "failed"}]
    assert "publication" not in response.json()


def test_concurrent_same_content_failure_keeps_successful_publication_artifact(world, project, tmp_path, monkeypatch):
    value, first, second, entered, release = concurrent_publish_fixture(world, project, tmp_path, monkeypatch)
    failed_result, success_result = competing_publications(value, project, first, second, entered, release)
    assert failed_result["status"] == "failed"
    assert success_result["status"] == "published"
    artifact = ArtifactStore(world.artifacts_root, project["id"]).get(success_result["artifact"]["id"])
    assert artifact["id"] == success_result["artifact"]["id"]


def concurrent_publish_fixture(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    first = report_thread(world, project)
    second = world.create_thread(project["id"], "chat", "s-second", "research-assistant")
    entered, release = Event(), Event()
    callback = fail_first_publish(world.publish_report, entered, release)
    monkeypatch.setattr(world, "publish_report", callback)
    return value, first, second, entered, release


def fail_first_publish(original, entered, release):
    def callback(*args):
        if entered.is_set():
            return original(*args)
        entered.set()
        release.wait(timeout=2)
        raise OSError("first insert fails")

    return callback


def competing_publications(value, project, first, second, entered, release):
    with ThreadPoolExecutor(max_workers=2) as executor:
        failed = executor.submit(publish, value, project, first)
        assert entered.wait(timeout=2)
        succeeded = executor.submit(publish, value, project, second)
        release.set()
        return failed.result(timeout=2), succeeded.result(timeout=2)


def test_failed_publication_keeps_concurrently_captured_content(world, project, tmp_path, monkeypatch):
    value, thread = kernel(world, tmp_path), report_thread(world, project)
    entered, release, copied = Event(), Event(), {}
    original = ArtifactStore.add

    def block_report_add(store, content, media_type):
        record = original(store, content, media_type)
        if media_type == "text/html" and not entered.is_set():
            copied["content"] = content
            entered.set()
            release.wait(timeout=2)
        return record

    admitted_evidence(world, project)
    monkeypatch.setattr(ArtifactStore, "add", block_report_add)
    monkeypatch.setattr(world, "publish_report", lambda *_: (_ for _ in ()).throw(OSError("db down")))
    with ThreadPoolExecutor(max_workers=2) as executor:
        failed = executor.submit(publish, value, project, thread)
        assert entered.wait(timeout=2)
        captured = executor.submit(capture, value, project, copied["content"], "text/html").result(timeout=2)
        release.set()
        result = failed.result(timeout=2)
    assert result["status"] == "failed" and not world.report_publications(project["id"], thread["id"])
    assert ArtifactStore(world.artifacts_root, project["id"]).get(captured["id"])["id"] == captured["id"]


def test_http_rejects_body_thread_and_cross_thread_save(world, project, tmp_path):
    value = kernel(world, tmp_path)
    client = TestClient(create_app(value))
    admitted_evidence(world, project)
    first, second = report_thread(world, project), world.create_thread(project["id"], "two", "s-two", "research-assistant")
    path = f"/api/v1/threads/{first['id']}/report/publish"
    assert client.post(path, json={"title": "Orbit", "thread_id": second["id"]}).status_code == 400
    publication = client.post(path, json={"title": "Orbit"}).json()["publication"]
    save = f"/api/v1/threads/{second['id']}/report/save"
    assert client.post(save, json={"title": "V1", "publication_id": publication["id"]}).status_code == 404
    assert not value._world.reports(project["id"], second["id"])


def test_http_report_content_rejects_a_get_body(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = report_thread(world, project)
    publication = publish_thread(value, project, thread)
    path = f"/api/v1/threads/{thread['id']}/report/{publication['id']}/content"
    response = TestClient(create_app(value)).request("GET", path, content=b"{}")
    assert response.status_code == 400
    assert response.json()["detail"] == "report content request accepts no body"


@pytest.mark.asyncio
async def test_runtime_session_publication_uses_owning_thread(world, project, tmp_path):
    value = kernel(world, tmp_path)
    admitted_evidence(world, project)
    thread = world.create_thread(project["id"], "chat", "s-runtime", "research-assistant")
    client = KernelClient(value, project["id"], "s-runtime")
    result = await client.ext_method("research/publish_report", {"title": "Orbit", "_session_id": "s-runtime"})
    saved = await value.command(KernelCommand("save_report", project["id"], {"thread_id": thread["id"], "title": "V1", "publication_id": result["publication"]["id"]}))
    assert result["publication"]["thread_id"] == thread["id"]
    assert world.reports(project["id"], thread["id"])[0]["id"] == saved["id"]
