import asyncio

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import KernelCommand, KernelQuery, ResearchKernel


def kernel(world, tmp_path):
    return ResearchKernel(world, projects_root=tmp_path / "projects")


def projection():
    return {"endpoint_ready": True, "facts": [{"text": "Measured at 42 K.", "claim_id": "claim:1", "source_ids": ["node:source"]}], "claims": [{"id": "claim:1", "life_state": "admitted", "verdict": "supported", "source_ids": ["node:source"]}], "sources": [{"id": "node:source", "kind": "source", "life_state": "admitted", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}], "artifacts": [{"id": "artifact:evidence"}]}


async def publish(value, project_id, title="Orbit report", facts=None):
    payload = {"title": title, "facts": facts or projection()["facts"]}
    return await value.command(KernelCommand("publish_report", project_id, payload))


def test_publication_is_validated_deterministic_and_save_is_immutable(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    async def projected(query): return projection()
    monkeypatch.setattr(value, "_query_report_projection", projected)
    first = asyncio.run(publish(value, project["id"]))
    second = asyncio.run(publish(value, project["id"]))
    assert first["status"] == "published"
    assert first["artifact"]["id"] == second["artifact"]["id"]
    saved = asyncio.run(value.command(KernelCommand("save_report", project["id"], {"title": "V1", "artifact_id": first["artifact"]["id"]})))
    assert asyncio.run(value.query(KernelQuery("report", project["id"], {"report_id": saved["id"]}))) == saved


def test_failed_validation_creates_no_output(world, project, tmp_path, monkeypatch):
    value = kernel(world, tmp_path)
    bad = projection(); bad["facts"][0]["source_ids"] = ["node:missing"]
    async def projected(query): return bad
    monkeypatch.setattr(value, "_query_report_projection", projected)
    result = asyncio.run(publish(value, project["id"], facts=bad["facts"]))
    assert result["status"] == "failed"
    assert result["assessment"]["gaps"][0]["code"] == "source_missing"


def test_report_content_is_project_scoped(world, project, tmp_path):
    value = kernel(world, tmp_path)
    artifact = asyncio.run(value.command(KernelCommand("capture_artifact", project["id"], {"content": b"x", "media_type": "text/html"})))
    world.publish_report(project["id"], artifact["id"])
    with pytest.raises(PermissionError):
        asyncio.run(value.query(KernelQuery("report_content", "project:other", {"artifact_id": artifact["id"]})))


def test_preview_and_download_headers(world, project, tmp_path):
    value = kernel(world, tmp_path)
    artifact = asyncio.run(value.command(KernelCommand("capture_artifact", project["id"], {"content": b"<h1>report</h1>", "media_type": "text/html"})))
    world.publish_report(project["id"], artifact["id"])
    client = TestClient(create_app(value))
    path = f"/api/v1/projects/{project['id']}/report/content/{artifact['id']}"
    preview, download = client.get(path), client.get(f"{path}?download=true")
    assert "sandbox" in preview.headers["content-security-policy"]
    assert preview.headers["content-type"].startswith("text/html")
    assert download.headers["content-disposition"].startswith("attachment")
