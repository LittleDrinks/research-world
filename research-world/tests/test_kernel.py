import pytest
from fastapi.testclient import TestClient

from server.admission import AdmissionVerdict
from server.app import create_app
from server.kernel import ResearchKernel


class ApprovingPolicy:
    def review(self, node):
        return AdmissionVerdict("approve", f"reviewed {node['kind']}")


def test_kernel_submission_is_pending_and_admission_is_structured(world, project):
    kernel = ResearchKernel(world)
    node = kernel.submit_node(
        project["id"], {"kind": "direction", "payload": {"text": "Candidate"}}
    )

    assert node["life_state"] == "pending"
    admitted = kernel.resolve_admission(node["id"], AdmissionVerdict("approve"))
    assert admitted["life_state"] == "admitted"
    with pytest.raises(ValueError, match="only pending"):
        kernel.resolve_admission(node["id"], AdmissionVerdict("reject", "late"))
    with pytest.raises(TypeError, match="AdmissionVerdict"):
        kernel.resolve_admission(node["id"], {"decision": "reject"})


def test_admission_policy_intercepts_submission(world, project):
    kernel = ResearchKernel(world, ApprovingPolicy())

    node = kernel.submit_node(
        project["id"], {"kind": "direction", "payload": {"text": "Reviewed"}}
    )

    assert node["life_state"] == "admitted"


def test_kernel_rejection_records_reason_and_rebuttal(world, project):
    kernel = ResearchKernel(world)
    node = kernel.submit_node(
        project["id"], {"kind": "source", "payload": {"title": "Unverified"}}
    )
    verdict = AdmissionVerdict("reject", "missing provenance", {"reviewer": "A"})

    rejected = kernel.resolve_admission(node["id"], verdict)

    assert rejected["life_state"] == "ghost"
    assert rejected["rejection_reason"] == "missing provenance"
    assert rejected["rebuttal"] == {"reviewer": "A"}


def test_node_api_submits_pending_and_updates_only_payload(world, project):
    client = TestClient(create_app(world))
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
    assert updated.status_code == 200
    assert updated.json()["payload"] == {"text": "Revised"}
    assert updated.json()["life_state"] == "pending"


@pytest.mark.parametrize(
    "field", ["life_state", "direction_status", "working", "lineage_id"]
)
def test_node_submission_rejects_internal_state(world, project, field):
    client = TestClient(create_app(world))
    response = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": "direction", "payload": {"text": "Candidate"}, field: "x"},
    )

    assert response.status_code == 400
    assert field in response.json()["detail"]


def test_node_submission_rejects_cross_project_parent(world, project, tmp_path):
    other = world.create_project("other", tmp_path / "other", "Other question")
    parent = world.nodes(other["id"])[0]
    client = TestClient(create_app(world))

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


@pytest.mark.parametrize("field", ["life_state", "direction_status", "working"])
def test_node_patch_rejects_internal_state(world, project, field):
    client = TestClient(create_app(world))
    node = world.create_node(project["id"], "direction", {"text": "Candidate"})

    response = client.patch(f"/api/v1/nodes/{node['id']}", json={field: "x"})

    assert response.status_code == 400
    assert world.node(node["id"])["life_state"] == "pending"
