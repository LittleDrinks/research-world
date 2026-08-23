from __future__ import annotations

from datetime import datetime

SOURCE_LEVELS = {
    "preprint": 1,
    "conference": 2,
    "published": 3,
    "primary_data": 4,
}


def assess_delivery(projection: dict) -> dict:
    facts = _records(projection, "facts")
    claims = _index(_records(projection, "claims"), "claims")
    sources = _index(_records(projection, "sources"), "sources")
    checks = [
        _fact_gaps(index, fact, claims, sources) for index, fact in enumerate(facts)
    ]
    accepted = [fact for fact, gaps in zip(facts, checks) if not gaps]
    citation_gaps = [item for gaps in checks for item in gaps]
    source_ids = _source_ids(accepted)
    source_gaps = [item for key in source_ids for item in _source_gaps(sources[key])]
    endpoint = _endpoint_ready(projection)
    gaps = _all_gaps(facts, citation_gaps, source_gaps, endpoint)
    return _assessment(facts, accepted, sources, source_ids, gaps, endpoint)


def _assessment(facts, accepted, sources, source_ids, gaps, endpoint) -> dict:
    citations_ok = bool(facts) and len(accepted) == len(facts)
    source_gaps = [gap for gap in gaps if gap["code"].startswith("source_")]
    metadata_ok = not source_gaps
    return {
        "valid": not any(gap["blocking"] for gap in gaps),
        "delivery_level": _delivery_level(
            bool(facts), citations_ok, endpoint, metadata_ok
        ),
        "accepted_facts": accepted,
        "minimum_source_level": _minimum_level(sources, source_ids),
        "gaps": gaps,
    }


def _fact_gaps(index: int, fact: dict, claims: dict, sources: dict) -> list[dict]:
    path = f"facts[{index}]"
    gaps = _fact_shape_gaps(fact, path)
    if not _text(fact.get("claim_id")):
        return gaps
    claim = claims.get(fact.get("claim_id"))
    if claim is None:
        gaps.append(_gap("claim_missing", f"{path}.claim_id"))
        return gaps
    gaps.extend(_claim_gaps(claim, path))
    for source_id in _list_value(fact.get("source_ids")):
        gaps.extend(_citation_gaps(source_id, claim, sources, path))
    return gaps


def _fact_shape_gaps(fact: dict, path: str) -> list[dict]:
    gaps = []
    if not _text(fact.get("text")):
        gaps.append(_gap("fact_text_missing", f"{path}.text"))
    if not _text(fact.get("claim_id")):
        gaps.append(_gap("claim_id_missing", f"{path}.claim_id"))
    if not _string_list(fact.get("source_ids")):
        gaps.append(_gap("source_ids_missing", f"{path}.source_ids"))
    return gaps


def _claim_gaps(claim: dict, path: str) -> list[dict]:
    gaps = []
    if claim.get("life_state") != "admitted":
        gaps.append(_gap("claim_not_admitted", f"{path}.claim_id"))
    if claim.get("verdict") != "supported":
        gaps.append(_gap("claim_not_supported", f"{path}.claim_id"))
    if not _string_list(claim.get("source_ids")):
        gaps.append(_gap("claim_sources_missing", f"{path}.claim_id"))
    return gaps


def _citation_gaps(source_id: str, claim: dict, sources: dict, path: str) -> list[dict]:
    source = sources.get(source_id)
    if source is None:
        return [_gap("source_missing", f"{path}.source_ids", source_id)]
    gaps = []
    if source_id not in _list_value(claim.get("source_ids")):
        gaps.append(_gap("claim_source_mismatch", f"{path}.source_ids", source_id))
    if source.get("kind") != "source":
        gaps.append(_gap("source_kind_invalid", f"{path}.source_ids", source_id))
    if source.get("life_state") != "admitted":
        gaps.append(_gap("source_not_admitted", f"{path}.source_ids", source_id))
    return gaps


def _source_gaps(source: dict) -> list[dict]:
    path = f"sources[{source['id']}]"
    level = source.get("source_level")
    gaps = []
    if level is None:
        gaps.append(_gap("source_level_missing", f"{path}.source_level"))
    elif level not in SOURCE_LEVELS:
        gaps.append(_gap("source_level_invalid", f"{path}.source_level"))
    elif level == "preprint":
        gaps.append(_gap("source_not_final", f"{path}.source_level"))
    if source.get("checked_at") is None:
        gaps.append(_gap("source_checked_at_missing", f"{path}.checked_at"))
    elif not _aware_timestamp(source.get("checked_at")):
        gaps.append(_gap("source_checked_at_invalid", f"{path}.checked_at"))
    return gaps


def _all_gaps(facts, citation_gaps, source_gaps, endpoint) -> list[dict]:
    gaps = [*citation_gaps, *source_gaps]
    if not facts:
        gaps.append(_gap("facts_missing", "facts"))
    if not endpoint:
        gaps.append(_gap("endpoint_missing", "endpoint_ready", blocking=False))
    return gaps


def _delivery_level(has_facts, citations_ok, endpoint, metadata_ok) -> int:
    if not has_facts:
        return 0
    if not citations_ok:
        return 1
    if not endpoint:
        return 2
    return 4 if metadata_ok else 3


def _minimum_level(sources: dict, source_ids: list[str]) -> str | None:
    levels = [sources[key].get("source_level") for key in source_ids]
    known = [level for level in levels if level in SOURCE_LEVELS]
    return min(known, key=SOURCE_LEVELS.get) if known else None


def _source_ids(facts: list[dict]) -> list[str]:
    values = {source_id for fact in facts for source_id in fact["source_ids"]}
    return sorted(values)


def _records(projection: dict, field: str) -> list[dict]:
    value = projection.get(field)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"report projection requires a {field} list")
    return value


def _index(records: list[dict], field: str) -> dict:
    if not all(_text(record.get("id")) for record in records):
        raise ValueError(f"report projection {field} require ids")
    index = {record["id"]: record for record in records}
    if len(index) != len(records):
        raise ValueError(f"report projection {field} ids must be unique")
    return index


def _endpoint_ready(projection: dict) -> bool:
    value = projection.get("endpoint_ready", False)
    if not isinstance(value, bool):
        raise TypeError("report projection endpoint_ready must be boolean")
    return value


def _aware_timestamp(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _gap(code: str, path: str, value=None, blocking: bool = True) -> dict:
    gap = {"code": code, "path": path, "blocking": blocking}
    return {**gap, "value": value} if value is not None else gap


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value) -> bool:
    return (
        isinstance(value, list) and bool(value) and all(_text(item) for item in value)
    )


def _list_value(value) -> list:
    return value if isinstance(value, list) else []
