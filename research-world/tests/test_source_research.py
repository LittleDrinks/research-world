import asyncio
from functools import partial

import pytest

from server.artifacts import ArtifactStore
from server.kernel import KernelCommand, ResearchKernel
from server.source_candidates import validate_source_candidate
from server.workflows import PipelineEngine


PIPELINE = {
    "id": "source-research",
    "name": "文献检索与全文核验",
    "stages": [
        {"id": "collect", "type": "prompt", "prompt": "collect-sources", "agent": "source-researcher"},
        {"id": "submit", "type": "tool", "tool": "submit-sources"},
    ],
}


class SourceAgents:
    def __init__(self, candidates):
        self.candidates = candidates

    def validate(self, _pipeline):
        return None

    def collect_sources(self, _context, _agent, _operation):
        return {"source_candidates": self.candidates}


def candidate(direction_id, artifact=None, *, use="supports"):
    unavailable = artifact is None
    return {
        "title": "Auditable source",
        "authors": ["Ada Researcher"],
        "year": 2026,
        "venue": "Journal of Evidence",
        "doi": "10.1000/evidence",
        "url": "https://example.test/evidence",
        "source_type": "journal_article",
        "license": "CC-BY-4.0" if artifact else "unknown",
        "access_status": "full_text_unavailable" if unavailable else "open",
        "artifact": artifact,
        "relationship": relationship(direction_id, unavailable, use),
        "retrieval": retrieval(),
        "unresolved_questions": ["No independent replication."],
    }


def relationship(direction_id, unavailable, use):
    return {
        "direction_id": direction_id,
        "use": "background" if unavailable else use,
        "relevance": "Tests the Direction directly.",
        "claims": [] if unavailable else ["The Direction is supported."],
        "locations": [] if unavailable else [
            {"locator": "Results, paragraph 2", "quote": "Measured evidence."}
        ],
    }


def retrieval():
    return {
        "query": "auditable evidence",
        "database": "Crossref; OpenAlex",
        "verified_at": "2026-08-24T03:00:00Z",
    }


def full_text(world, project, content=b"Complete article text"):
    path = project_path(project, "sources/evidence.txt")
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    record = ArtifactStore(world.artifacts_root, project["id"]).add(content, "text/plain")
    return {"id": record["id"], "project_file": "sources/evidence.txt",
            "media_type": record["media_type"], "sha256": record["sha256"]}


def project_path(project, relative):
    from pathlib import Path

    return Path(project["root"]) / relative


def admitted_direction(world, project):
    node = world.create_node(project["id"], "direction", {"title": "Direction", "text": "Test it."})
    return world.admit_node(node["id"])


def execute(kernel, command):
    return asyncio.run(kernel.command(command))


def test_source_candidate_schema_is_strict(world, project):
    direction = admitted_direction(world, project)
    value = {**candidate(direction["id"]), "summary": "Abstract-only evidence"}

    with pytest.raises(ValueError, match="Additional properties"):
        validate_source_candidate(value)


def test_full_text_unavailable_is_background_without_claims(world, project):
    direction = admitted_direction(world, project)
    value = candidate(direction["id"])

    assert validate_source_candidate(value) == value
    value["relationship"]["use"] = "supports"
    with pytest.raises(ValueError, match="background use"):
        validate_source_candidate(value)


def test_pipeline_submits_pending_sources_and_admission_creates_edges(
    world, project, tmp_path
):
    direction = admitted_direction(world, project)
    artifact = full_text(world, project)
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    run = world.create_run(project["id"], direction["id"], PIPELINE, {})
    submit = partial(kernel._submit_source_candidate, project["id"])
    engine = PipelineEngine(world, SourceAgents([candidate(direction["id"], artifact)]), None, None, None, submit)

    completed = engine.run(run["id"])

    source = completed["payload"]["_pipeline"]["values"]["sources"][0]
    assert source["life_state"] == "pending"
    assert world.edges(project["id"]) == []
    admitted = execute(kernel, KernelCommand("resolve_admission", project["id"], {"node_id": source["id"], "decision": "approve"}))
    assert admitted["life_state"] == "admitted"
    assert world.edges(project["id"]) == [{"source": source["id"], "target": direction["id"], "polarity": "supports", "created_at": world.edges(project["id"])[0]["created_at"]}]


def test_kernel_rejects_artifact_from_another_project(world, project, tmp_path):
    other_root = tmp_path / "other"
    other_root.mkdir()
    other = world.create_project("other", other_root, "Other question")
    direction = admitted_direction(world, project)
    foreign = full_text(world, other, b"Foreign article")
    run = world.create_run(project["id"], direction["id"], PIPELINE, {})
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")

    with pytest.raises(KeyError):
        kernel._submit_source_candidate(
            project["id"], run["id"], 0, direction["id"], candidate(direction["id"], foreign)
        )


def test_rejected_source_becomes_ghost_without_direction_edge(world, project, tmp_path):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], PIPELINE, {})
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    source = kernel._submit_source_candidate(
        project["id"], run["id"], 0, direction["id"], candidate(direction["id"])
    )

    ghost = execute(kernel, KernelCommand("resolve_admission", project["id"], {
        "node_id": source["id"], "decision": "reject", "reason": "not relevant",
    }))

    assert ghost["life_state"] == "ghost"
    assert world.edges(project["id"]) == []
