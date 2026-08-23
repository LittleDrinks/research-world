from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AdmissionVerdict:
    decision: Literal["approve", "reject"]
    reason: str = ""
    rebuttal: dict | None = None

    def __post_init__(self) -> None:
        if self.decision not in {"approve", "reject"}:
            raise ValueError("admission decision must be approve or reject")
        if self.decision == "reject" and not self.reason.strip():
            raise ValueError("rejected admission requires a reason")


class AdmissionPolicy(Protocol):
    def review(self, node: dict) -> AdmissionVerdict | None: ...


class PendingAdmissionPolicy:
    def review(self, _node: dict) -> None:
        return None
