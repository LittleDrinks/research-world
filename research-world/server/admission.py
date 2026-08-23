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


def validate_claims(value) -> list[dict]:
    if not isinstance(value, list):
        raise TypeError("claims must be a list")
    for claim in value:
        _validate_claim(claim)
    return value


def _validate_claim(claim) -> None:
    if not isinstance(claim, dict):
        raise TypeError("each claim must be an object")
    if not _text(claim.get("text")):
        raise ValueError("each claim requires non-empty text")
    if claim.get("verdict") not in {"supported", "refuted", "uncertain"}:
        raise ValueError("each claim requires a supported/refuted/uncertain verdict")
    if not _string_list(claim.get("evidence")):
        raise TypeError("each claim requires a string evidence list")
    if "id" in claim and not _text(claim["id"]):
        raise ValueError("claim id must be non-empty text")


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)
