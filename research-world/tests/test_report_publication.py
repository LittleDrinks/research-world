import asyncio

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import KernelCommand, KernelQuery, ResearchKernel


def kernel(world, tmp_path):
    return ResearchKernel(world, projects_root=tmp_path / "projects")


def source_payload(artifact_id=None):
    value = {"title": "Validated measurement", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}
    return {**value, "artifact_ids": [artifact_id]} if artifact_id else value


def admitted_evidence(world, project, artifact_id=None):
    source = world.create_node(project["id"], "source", source_payload(artifact_id))
    world.admit_node(source["id"])
    claim = {"text": "Measured at 42 K.", "verdict": "supported", "evidence": [source["id"]]}
    direction = world.create_node(project["id"], "direction", {"claims": [claim]})
    world.admit_node(direction["id"])
    return source


def publish(value, project_id, title="Orbit report"):
    return asyncio.run(value.command(KernelCommand("publish_report", project_id, {"title": title})))


def capture(value, project, content):
    values = {"content": content, "media_type": "text/plain"}
    return asyncio.run(value.command(KernelCommand("capture_artifact", project["id"], values)))


def test_kernel_rejects_caller_facts_and_fabricated_projection_text(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    with pytest.raises(ValueError, match="facts"):
        publish_facts(value, project["id"])
    monkeypatch.setattr(value, "_report_projection", lambda _id: fabricated_projection())
    result = publish(value, project["id"])
    assert result["status"] == "failed"
    assert result["assessment"]["gaps"][0]["code"] == "fact_text_mismatch"


def publish_facts(value, project_id):
    values = {"title": "x", "facts": []}
    return asyncio.run(value.command(KernelCommand("publish_report", project_id, values)))


def fabricated_projection():
    source = {"id": "node:s", "title": "Paper", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00", "anchor": "source-node:s"}
    claim = {"id": "claim:1", "text": "Measured", "source_ids": ["node:s"]}
    fact = {"text": "Fabricated", "claim_id": "claim:1", "source_ids": ["node:s"], "artifact_ids": []}
    return {"facts": [fact], "claims": [claim], "sources": [source], "artifacts": []}


def test_projection_filters_unsafe_fields_and_unlinked_artifacts(world, project, tmp_path):
    value = kernel(world, tmp_path)
    linked, unrelated = capture(value, project, b"linked"), capture(value, project, b"unrelated")
    source = admitted_evidence(world, project, linked["id"])
    payload = {"artifact_ids": [unrelated["id"]]}
    world.create_node(project["id"], "experiment", payload, life_state="admitted")
    unsafe = {**world.node(source["id"])["payload"], "apikey": "secret", "baseurl": "https://secret", "config_path": "/etc/key", "raw": {"token": "secret"}}
    world.update_node(source["id"], unsafe)
    projection = asyncio.run(value.query(KernelQuery("report_projection", project["id"])))
    assert set(projection["sources"][0]) == {"id", "title", "source_level", "checked_at", "anchor"}
    assert [item["id"] for item in projection["artifacts"]] == [linked["id"]]
    assert "secret" not in str(projection)


def test_failed_validation_has_no_publication_side_effect(world, project, tmp_path):
    value = kernel(world, tmp_path)
    result = publish(value, project["id"])
    assert result["status"] == "failed"
    assert not value._world._rows("SELECT 1 FROM report_publications")


def test_identical_bytes_publish_independently_per_project(world, project, tmp_path):
    value = kernel(world, tmp_path)
    other = world.create_project("other", tmp_path / "other", "Other?")
    value._report_projection = lambda _id: shared_projection()
    first, second = publish(value, project["id"]), publish(value, other["id"])
    assert first["artifact"]["id"] == second["artifact"]["id"]
    assert first["publication"]["project_id"] != second["publication"]["project_id"]


def shared_projection():
    return {"facts": [{"text": "Measured", "claim_id": "claim:1", "source_ids": ["node:s"], "artifact_ids": []}], "claims": [{"id": "claim:1", "text": "Measured", "source_ids": ["node:s"]}], "sources": [{"id": "node:s", "title": "Paper", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00", "anchor": "source-node:s"}], "artifacts": []}


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
