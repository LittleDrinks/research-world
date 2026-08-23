from __future__ import annotations

from .admission import AdmissionPolicy, AdmissionVerdict, PendingAdmissionPolicy
from .world import World

SUBMISSION_KEYS = {"kind", "payload", "parent_id"}
PATCH_KEYS = {"payload"}


class ResearchKernel:
    def __init__(self, world: World, admission: AdmissionPolicy | None = None):
        self._world = world
        self._admission = admission or PendingAdmissionPolicy()

    def node(self, node_id: str) -> dict:
        return self._world.node(node_id)

    def submit_node(self, project_id: str, value: dict) -> dict:
        _validate_fields(value, SUBMISSION_KEYS, {"kind", "payload"})
        self._validate_parent(project_id, value.get("parent_id"))
        state = {"parent_id": value["parent_id"]} if value.get("parent_id") else {}
        node = self._world.create_node(
            project_id, value["kind"], value["payload"], **state
        )
        verdict = self._admission.review(node)
        return self.resolve_admission(node["id"], verdict) if verdict else node

    def update_node(self, node_id: str, value: dict) -> dict:
        _validate_fields(value, PATCH_KEYS, {"payload"})
        return self._world.update_node(node_id, value["payload"])

    def resolve_admission(self, node_id: str, verdict: AdmissionVerdict) -> dict:
        if not isinstance(verdict, AdmissionVerdict):
            raise TypeError("admission requires an AdmissionVerdict")
        return self._world.apply_admission(node_id, verdict)

    def _validate_parent(self, project_id: str, parent_id: str | None) -> None:
        if parent_id and self._world.node(parent_id)["project_id"] != project_id:
            raise ValueError("node parent must belong to the project")


def _validate_fields(value: dict, allowed: set[str], required: set[str]) -> None:
    if not isinstance(value, dict):
        raise ValueError("node command must be an object")
    if missing := required - set(value):
        raise ValueError(f"node command missing fields: {', '.join(sorted(missing))}")
    if unknown := set(value) - allowed:
        raise ValueError(f"node command rejects fields: {', '.join(sorted(unknown))}")
