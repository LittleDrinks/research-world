import asyncio
from base64 import b64encode

import pytest
from fastapi.testclient import TestClient

from server.admission import AdmissionVerdict
from server.app import create_app
from server.kernel import KernelCommand, KernelQuery, ResearchKernel


def execute(kernel, command):
    return asyncio.run(kernel.command(command))


def inspect(kernel, query):
    return asyncio.run(kernel.query(query))


class ApprovingPolicy:
    def review(self, node):
        return AdmissionVerdict("approve", f"reviewed {node['kind']}")


class CatalogRuntime:
    def __init__(self, available):
        self.available = available
        self.kernel = None

    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def recognize(self, _workspace):
        return {"endpoints": [{"id": "primary", "available": self.available}]}


def test_kernel_submission_is_pending_and_admission_is_structured(
    world, project, tmp_path
):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    node = execute(
        kernel,
        KernelCommand(
            "submit_node",
            project["id"],
            {"kind": "direction", "payload": {"text": "Candidate"}},
        ),
    )

    assert node["life_state"] == "pending"
    values = {"node_id": node["id"], "decision": "approve"}
    admitted = execute(
        kernel, KernelCommand("resolve_admission", project["id"], values)
    )
    assert admitted["life_state"] == "admitted"
    with pytest.raises(ValueError, match="only pending"):
        execute(
            kernel,
            KernelCommand(
                "resolve_admission",
                project["id"],
                {"node_id": node["id"], "decision": "reject", "reason": "late"},
            ),
        )
    with pytest.raises(ValueError, match="rejects fields"):
        execute(
            kernel,
            KernelCommand(
                "resolve_admission",
                project["id"],
                {"node_id": node["id"], "decision": "approve", "verdict": {}},
            ),
        )


def test_admission_policy_intercepts_submission(world, project, tmp_path):
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        admission=ApprovingPolicy(),
    )

    node = execute(
        kernel,
        KernelCommand(
            "submit_node",
            project["id"],
            {"kind": "direction", "payload": {"text": "Reviewed"}},
        ),
    )

    assert node["life_state"] == "admitted"


def test_kernel_rejection_records_reason_and_rebuttal(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    node = execute(
        kernel,
        KernelCommand(
            "submit_node",
            project["id"],
            {"kind": "source", "payload": {"title": "Unverified"}},
        ),
    )
    rejected = execute(
        kernel,
        KernelCommand(
            "resolve_admission",
            project["id"],
            {
                "node_id": node["id"],
                "decision": "reject",
                "reason": "missing provenance",
                "rebuttal": {"reviewer": "A"},
            },
        ),
    )

    assert rejected["life_state"] == "ghost"
    assert rejected["rejection_reason"] == "missing provenance"
    assert rejected["rebuttal"] == {"reviewer": "A"}


def test_node_api_submits_pending_and_cannot_mutate_payload(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    created = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": "direction", "payload": {"text": "Candidate"}},
    )
    node = created.json()

    updated = client.patch(
        f"/api/v1/nodes/{node['id']}", json={"payload": {"text": "Revised"}}
    )

    assert created.status_code == 201
    assert node["life_state"] == "pending"
    assert updated.status_code == 405
    assert world.node(node["id"])["payload"] == {"text": "Candidate"}


@pytest.mark.parametrize(
    "claims",
    [
        ["not-an-object"],
        [{"text": "", "verdict": "supported", "evidence": []}],
        [{"text": 42, "verdict": "supported", "evidence": []}],
        [{"text": "Claim", "verdict": "unknown", "evidence": []}],
        [{"text": "Claim", "verdict": "supported", "evidence": "node:s"}],
        [{"text": "Claim", "verdict": "supported", "evidence": [{}]}],
    ],
)
def test_admission_rejects_malformed_claims(world, project, tmp_path, claims):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    created = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": "direction", "payload": {"text": "Candidate", "claims": claims}},
    ).json()

    admitted = client.post(
        f"/api/v1/projects/{project['id']}/nodes/{created['id']}/admission",
        json={"decision": "approve"},
    )
    projection = client.get(f"/api/v1/projects/{project['id']}/report/projection")

    assert admitted.status_code == 400
    assert world.node(created["id"])["life_state"] == "pending"
    assert projection.status_code == 200


def test_admission_rejects_duplicate_project_claim_ids(world, project, tmp_path):
    client = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path / "projects"))
    )
    claims = [
        {"id": "claim:shared", "text": "Claim", "verdict": "supported", "evidence": []}
    ]
    nodes = [
        client.post(
            f"/api/v1/projects/{project['id']}/nodes",
            json={"kind": "direction", "payload": {"text": text, "claims": claims}},
        ).json()
        for text in ("First", "Second")
    ]

    assert admit(client, project, nodes[0]).status_code == 200
    assert admit(client, project, nodes[1]).status_code == 400
    assert world.node(nodes[1]["id"])["life_state"] == "pending"


def test_node_submission_requires_object_payload(world, project, tmp_path):
    client = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path / "projects"))
    )

    response = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": "direction", "payload": ["not", "an", "object"]},
    )

    assert response.status_code == 400


def test_artifact_then_observation_uses_one_kernel_path(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    artifact = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        json={"content_base64": "cmVzdWx0", "media_type": "text/plain"},
    ).json()
    assert set(artifact) == {"id", "sha256", "media_type", "size", "created_at"}
    observation = observation_record(artifact["id"])

    response = client.post(
        f"/api/v1/projects/{project['id']}/observations", json=observation
    )

    assert response.status_code == 201
    assert response.json()["life_state"] == "pending"
    assert response.json()["payload"]["artifact_ids"] == [artifact["id"]]
    admitted = client.post(
        f"/api/v1/projects/{project['id']}/nodes/{response.json()['id']}/admission",
        json={"decision": "approve"},
    )
    assert admitted.status_code == 200
    assert admitted.json()["life_state"] == "admitted"


def test_observation_cannot_reference_another_projects_artifact(
    world, project, tmp_path
):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    artifact = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        json={"content_base64": "cmVzdWx0", "media_type": "text/plain"},
    ).json()
    other = world.create_project("other", tmp_path / "other", "Other question")

    response = client.post(
        f"/api/v1/projects/{other['id']}/observations",
        json=observation_record(artifact["id"]),
    )

    assert response.status_code == 404


@pytest.mark.parametrize("life_state", ["pending", "ghost"])
def test_edge_api_rejects_unadmitted_endpoint(world, project, tmp_path, life_state):
    source = world.create_node(project["id"], "source", {"title": "unreviewed"})
    if life_state == "ghost":
        world.ghost_node(source["id"], "rejected")
    target = world.nodes(project["id"])[0]
    response = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path))
    ).post(
        f"/api/v1/projects/{project['id']}/edges",
        json={"source": source["id"], "target": target["id"], "polarity": "supports"},
    )
    assert response.status_code == 404
    assert world.edges(project["id"]) == []


def test_edge_api_accepts_admitted_endpoints(world, project, tmp_path):
    source = world.create_node(project["id"], "source", {"title": "reviewed"})
    world.admit_node(source["id"])
    target = world.nodes(project["id"])[0]
    response = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path))
    ).post(
        f"/api/v1/projects/{project['id']}/edges",
        json={"source": source["id"], "target": target["id"], "polarity": "supports"},
    )
    assert response.status_code == 201
    assert response.json()["polarity"] == "supports"


def test_kernel_builds_human_gate_signals(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    run = waiting_run(world, project, {"kind": "review", "node_id": "node:test"})
    values = {"run_id": run["id"], "decision": "approve", "reason": "reviewed"}

    resolved = execute(kernel, KernelCommand("resolve_run", values=values))

    assert resolved["payload"]["_signal"] == {
        "kind": "review",
        "node_id": "node:test",
        "decision": "approve",
        "reason": "reviewed",
    }


def test_kernel_confirms_execution_gate(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    run = waiting_run(world, project, {"kind": "confirm_step"})

    confirmed = execute(
        kernel, KernelCommand("confirm_run", values={"run_id": run["id"]})
    )

    assert confirmed["payload"]["_signal"] == {"kind": "confirm_step"}


def test_report_projection_exposes_only_safe_cited_source_fields(world, project, tmp_path):
    source = world.create_node(
        project["id"],
        "source",
        {"title": "Paper", "source_level": "published", "checked_at": "2026-08-23T12:00:00+08:00", "apikey": "secret"},
    )
    world.admit_node(source["id"])
    direction = world.create_node(project["id"], "direction", {"claims": [{"text": "Stable", "verdict": "supported", "evidence": [source["id"]]}]})
    world.admit_node(direction["id"])
    projection = inspect(
        ResearchKernel(world, projects_root=tmp_path / "projects"),
        KernelQuery("report_projection", project["id"]),
    )
    assert projection["sources"][0]["id"] == source["id"]
    assert set(projection["sources"][0]) == {"id", "title", "source_level", "checked_at", "anchor"}


def test_bibtex_export_reads_only_admitted_source_artifact(world, project, tmp_path):
    client = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path / "projects"))
    )
    artifact, source = create_bibtex_source(client, project, valid_bibtex())
    admit(client, project, source)
    response = client.get(
        f"/api/v1/projects/{project['id']}/report/bibtex",
        params={"artifact_id": artifact["id"]},
    )
    assert response.status_code == 200
    assert response.json() == {"id": artifact["id"], "content": valid_bibtex()}


def test_bibtex_export_rejects_malformed_content(world, project, tmp_path):
    client = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path / "projects"))
    )
    artifact, source = create_bibtex_source(client, project, "not bibtex")
    admit(client, project, source)
    response = client.get(
        f"/api/v1/projects/{project['id']}/report/bibtex",
        params={"artifact_id": artifact["id"]},
    )
    assert response.status_code == 400
    assert "BibTeX" in response.json()["detail"]


def test_bibtex_export_hides_unadmitted_and_cross_project_artifacts(
    world, project, tmp_path
):
    client = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path / "projects"))
    )
    artifact, _source = create_bibtex_source(client, project, valid_bibtex())
    other = world.create_project("other-bib", tmp_path / "other-bib", "Other?")
    pending = client.get(
        f"/api/v1/projects/{project['id']}/report/bibtex",
        params={"artifact_id": artifact["id"]},
    )
    foreign = client.get(
        f"/api/v1/projects/{other['id']}/report/bibtex",
        params={"artifact_id": artifact["id"]},
    )
    assert pending.status_code == 404
    assert foreign.status_code == 404


def observation_record(artifact_id):
    return {
        "kind": "source",
        "payload": {"title": "Manual measurement"},
        "provenance": {"actor": "researcher:li", "method": "four-probe"},
        "observed_at": "2026-08-23T09:30:00+08:00",
        "artifact_ids": [artifact_id],
    }


def create_bibtex_source(client, project, content):
    artifact = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        json={
            "content_base64": b64encode(content.encode()).decode(),
            "media_type": "application/x-bibtex",
        },
    ).json()
    source = client.post(
        f"/api/v1/projects/{project['id']}/observations",
        json={
            **observation_record(artifact["id"]),
            "payload": {
                "title": "Citable paper",
                "source_level": "published",
                "checked_at": "2026-08-23T12:00:00+08:00",
            },
        },
    ).json()
    return artifact, source


def admit(client, project, node):
    return client.post(
        f"/api/v1/projects/{project['id']}/nodes/{node['id']}/admission",
        json={"decision": "approve"},
    )


def valid_bibtex():
    return "@article{orbit, title={Stable Orbits}, author={Li, Ada}, year={2026}}"


def waiting_run(world, project, gate):
    definition = {"id": "test", "name": "Test", "stages": []}
    node = world.nodes(project["id"])[0]
    run = world.create_run(project["id"], node["id"], definition)
    payload = {"_pipeline": {"gate": gate}}
    return world.update_run(run["id"], "gate", "waiting_human", payload)


@pytest.mark.parametrize(
    "field", ["life_state", "direction_status", "working", "lineage_id"]
)
def test_node_submission_rejects_internal_state(world, project, tmp_path, field):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    response = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": "direction", "payload": {"text": "Candidate"}, field: "x"},
    )

    assert response.status_code == 400
    assert field in response.json()["detail"]


def test_node_submission_rejects_cross_project_parent(world, project, tmp_path):
    other = world.create_project("other", tmp_path / "other", "Other question")
    parent = world.nodes(other["id"])[0]
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))

    response = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={
            "kind": "source",
            "payload": {"title": "Paper"},
            "parent_id": parent["id"],
        },
    )

    assert response.status_code == 400
    assert "belong to the project" in response.json()["detail"]


@pytest.mark.parametrize("life_state", ["pending", "ghost"])
def test_node_submission_requires_admitted_parent(world, project, tmp_path, life_state):
    parent = world.create_node(project["id"], "direction", {"text": "unreviewed"})
    if life_state == "ghost":
        world.ghost_node(parent["id"], "rejected")
    response = TestClient(
        create_app(ResearchKernel(world, projects_root=tmp_path))
    ).post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={
            "kind": "source",
            "payload": {"title": "Paper"},
            "parent_id": parent["id"],
        },
    )
    assert response.status_code == 400
    assert world.nodes(project["id"])[-1]["id"] == parent["id"]


@pytest.mark.parametrize("field", ["life_state", "direction_status", "working"])
def test_node_patch_rejects_internal_state(world, project, tmp_path, field):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = TestClient(create_app(kernel))
    node = world.create_node(project["id"], "direction", {"text": "Candidate"})

    response = client.patch(f"/api/v1/nodes/{node['id']}", json={field: "x"})

    assert response.status_code == 405
    assert world.node(node["id"])["life_state"] == "pending"
