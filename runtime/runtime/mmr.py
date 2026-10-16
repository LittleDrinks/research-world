from __future__ import annotations

import math
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def select_mmr(values: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(values, Mapping):
        raise TypeError("mmr input must be a mapping")
    candidates = _candidates(values["candidates"])
    similarities = _similarities(values["similarities"], candidates)
    count = _count(values["count"])
    weight = _weight(values["diversity_weight"])
    selected = []
    remaining = list(candidates)
    while remaining and len(selected) < count:
        candidate = _next_candidate(remaining, selected, similarities, weight)
        selected.append(candidate)
        remaining.remove(candidate)
    return deepcopy(selected)


def _candidates(value) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("mmr candidates must be a nonempty list")
    candidates = [_candidate(item) for item in value]
    if len({item["id"] for item in candidates}) != len(candidates):
        raise ValueError("mmr candidate ids must be unique")
    return candidates


def _candidate(value) -> dict[str, Any]:
    if not isinstance(value, Mapping) or "id" not in value or "relevance" not in value:
        raise ValueError("mmr candidates require id and relevance")
    if not isinstance(value["id"], str) or not value["id"]:
        raise ValueError("mmr candidate id must be nonempty text")
    _number(value["relevance"], "relevance")
    return dict(value)


def _similarities(value, candidates) -> dict[str, dict[str, float]]:
    if not isinstance(value, Mapping):
        raise ValueError("mmr similarities must be a mapping")
    ids = tuple(item["id"] for item in candidates)
    return {left: _similarity_row(value, left, ids) for left in ids}


def _similarity_row(value, left, ids) -> dict[str, float]:
    row = value.get(left)
    if not isinstance(row, Mapping):
        raise ValueError("mmr similarities must cover every candidate")
    result = {}
    for right in ids:
        if right != left:
            result[right] = _required_similarity(row, right)
    return result


def _required_similarity(row, candidate_id) -> float:
    if candidate_id not in row:
        raise ValueError("mmr similarities must cover every candidate pair")
    return _number(row[candidate_id], "similarity")


def _count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("mmr count must be a positive integer")
    return value


def _weight(value) -> float:
    return _number(value, "diversity_weight", minimum=0.0)


def _number(value, label, minimum=None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"mmr {label} must be a number")
    result = float(value)
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise ValueError(f"mmr {label} must be finite and valid")
    return result


def _next_candidate(remaining, selected, similarities, weight):
    return min(
        remaining,
        key=lambda item: (
            -_score(item, selected, similarities, weight),
            item["id"],
        ),
    )


def _score(candidate, selected, similarities, weight) -> float:
    penalty = max(
        (similarities[candidate["id"]][item["id"]] for item in selected),
        default=0.0,
    )
    return float(candidate["relevance"]) - weight * penalty
