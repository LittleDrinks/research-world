from __future__ import annotations

from datetime import datetime

SOURCE_LEVELS = {"preprint": 1, "conference": 2, "published": 3, "primary_data": 4}


def assess_delivery(projection: dict) -> dict:
    facts, claims, sources = _records(projection)
    gaps = _fact_gaps(facts, claims, sources) + _artifact_gaps(facts, projection)
    accepted = facts if not gaps else []
    return _assessment(accepted, sources, gaps)


def _records(projection: dict) -> tuple[list[dict], dict, dict]:
    facts = _record_list(projection, "facts")
    claims = _record_index(projection, "claims")
    sources = _record_index(projection, "sources")
    return facts, claims, sources


def _record_list(projection: dict, field: str) -> list[dict]:
    value = projection.get(field)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"report projection requires a {field} list")
    return value


def _record_index(projection: dict, field: str) -> dict[str, dict]:
    rows = _record_list(projection, field)
    result = {row.get("id"): row for row in rows if _text(row.get("id"))}
    if len(result) != len(rows):
        raise ValueError(f"report projection {field} require unique ids")
    return result


def _fact_gaps(facts: list[dict], claims: dict, sources: dict) -> list[dict]:
    gaps = [_fact_gap(index, fact, claims, sources) for index, fact in enumerate(facts)]
    return [gap for group in gaps for gap in group] or _missing_facts(facts)


def _missing_facts(facts: list[dict]) -> list[dict]:
    return [] if facts else [_gap("facts_missing", "facts")]


def _fact_gap(index: int, fact: dict, claims: dict, sources: dict) -> list[dict]:
    path, claim = f"facts[{index}]", claims.get(fact.get("claim_id"))
    if claim is None:
        return [_gap("claim_missing", f"{path}.claim_id", fact.get("claim_id"))]
    gaps = _claim_match_gaps(fact, claim, path)
    return gaps + _source_gaps(fact, sources, path)


def _claim_match_gaps(fact: dict, claim: dict, path: str) -> list[dict]:
    checks = (("text", "fact_text_mismatch"), ("source_ids", "claim_source_mismatch"))
    gaps = [_gap(code, f"{path}.{field}", fact.get(field)) for field, code in checks if fact.get(field) != claim.get(field)]
    return gaps + _claim_evidence_gaps(claim, path)


def _claim_evidence_gaps(claim: dict, path: str) -> list[dict]:
    checks = (("life_state", "claim_not_admitted", "admitted"), ("verdict", "claim_not_supported", "supported"))
    gaps = [_gap(code, f"{path}.claim_id", claim.get(field)) for field, code, expected in checks if claim.get(field) != expected]
    if not _string_list(claim.get("source_ids")):
        gaps.append(_gap("claim_sources_missing", f"{path}.source_ids", claim.get("source_ids")))
    if not _string_list(claim.get("evidence_ids")):
        gaps.append(_gap("claim_evidence_missing", f"{path}.claim_id", claim.get("id")))
    return gaps


def _source_gaps(fact: dict, sources: dict, path: str) -> list[dict]:
    return [gap for source_id in fact.get("source_ids", []) for gap in _one_source_gaps(source_id, sources, path)]


def _one_source_gaps(source_id: str, sources: dict, path: str) -> list[dict]:
    source = sources.get(source_id)
    if source is None:
        return [_gap("source_missing", f"{path}.source_ids", source_id)]
    checks = _source_checks(source)
    return [_gap(code, f"sources[{source_id}].{field}", source.get(field)) for field, code in checks if not valid(field, source.get(field))]


def _source_checks(source: dict) -> list[tuple[str, str]]:
    return [("title", "source_title_missing"), ("anchor", "source_anchor_missing"), ("source_level", "source_level_invalid"), ("checked_at", "source_checked_at_invalid")]


def valid(field: str, value) -> bool:
    if field == "source_level":
        return value in SOURCE_LEVELS
    if field == "checked_at" and isinstance(value, str):
        try:
            return datetime.fromisoformat(value).tzinfo is not None
        except ValueError:
            return False
    return _text(value)


def _artifact_gaps(facts: list[dict], projection: dict) -> list[dict]:
    artifacts = _record_index(projection, "artifacts")
    return [gap for index, fact in enumerate(facts) for gap in _fact_artifact_gaps(index, fact, artifacts)]


def _fact_artifact_gaps(index: int, fact: dict, artifacts: dict) -> list[dict]:
    path = f"facts[{index}].artifact_ids"
    return [gap for artifact_id in fact.get("artifact_ids", []) for gap in _one_artifact_gap(artifact_id, fact, artifacts, path)]


def _one_artifact_gap(artifact_id: str, fact: dict, artifacts: dict, path: str) -> list[dict]:
    artifact = artifacts.get(artifact_id)
    if artifact is None:
        return [_gap("artifact_missing", path, artifact_id)]
    if fact["claim_id"] not in artifact.get("claim_ids", []):
        return [_gap("artifact_claim_mismatch", path, artifact_id)]
    return []


def _assessment(facts: list[dict], sources: dict, gaps: list[dict]) -> dict:
    source_ids = sorted({source for fact in facts for source in fact["source_ids"]})
    levels = [sources[source]["source_level"] for source in source_ids]
    return {"valid": not gaps, "delivery_level": 4 if not gaps else 0, "accepted_facts": facts, "minimum_source_level": min(levels, key=SOURCE_LEVELS.get) if levels else None, "gaps": gaps}


def _gap(code: str, path: str, value=None) -> dict:
    return {"code": code, "path": path, "value": value}


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)
