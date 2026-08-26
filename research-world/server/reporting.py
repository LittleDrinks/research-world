from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime

SOURCE_LEVELS = {"preprint": 1, "conference": 2, "published": 3, "primary_data": 4}
REPORT_SECTIONS = ("Research question", "Conclusions", "Evidence and methods", "Limitations and gaps")
REPORT_INPUT_TOKEN_BUDGET = 2048
EVIDENCE_KINDS = {"code", "formula", "chart"}
_TOP_FIELDS = {"question", "facts", "claims", "sources", "artifacts"}
_NODE_ID = re.compile(r"node:[0-9a-f]{24}\Z")
_ARTIFACT_ID = re.compile(r"artifact:[0-9a-f]{64}\Z")
_CLAIM_ID = re.compile(r"claim:[0-9a-f]{24}:[1-9][0-9]*\Z")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_URI = re.compile(r"(?i)\b[a-z][a-z0-9+.-]{1,31}://|\bwww\.")
_PATH = re.compile(r"(?i)(?<![<\w.-])/(?:[a-z0-9._-]+/)+|(?<![\w.-])/(?:home|users|tmp|var|etc|root|mnt|opt|private)(?:/|\b)|[a-z]:[\\/]|\\\\")
_METADATA = re.compile(r"(?i)(?:^|[,{\s])[\"']?(?:session|thread|turn|trace|event)[a-z0-9_]*[\"']?\s*[:=]")
_ENVIRONMENT = re.compile(r"(?m)^\s*[A-Z][A-Z0-9_]{2,}\s*=")
_CREDENTIAL = re.compile(r"(?i)\b(?:[a-z][a-z0-9_]*(?:key|token|secret|password|credential|authorization)|api[_-]?key|baseurl|endpoint|transport(?:_url)?|url)\s*[:=]")
_KNOWN_SECRET = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{8,}|AKIA[0-9A-Z]{16}|(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}|xox[baprs]-[A-Za-z0-9-]{8,})\b")
_OPAQUE = re.compile(r"\b[A-Za-z0-9_=-]{24,}\b")


def safe_narrative(value) -> str | None:
    return _safe_text(value, 4096)


def safe_report_text(value) -> str | None:
    return _safe_text(value, 65536)


def contains_restricted_data(value, opaque: bool = True) -> bool:
    return isinstance(value, str) and _restricted(value, opaque)


def _safe_text(value, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or len(text.encode("utf-8")) > maximum or _restricted(text, True):
        return None
    return text


def _restricted(text: str, opaque: bool) -> bool:
    patterns = (_CONTROL, _URI, _PATH, _METADATA, _ENVIRONMENT, _CREDENTIAL, _KNOWN_SECRET)
    return any(pattern.search(text) for pattern in patterns) or opaque and _opaque_secret(text)


def _opaque_secret(text: str) -> bool:
    return any(_entropy(token) >= 3.4 for token in _OPAQUE.findall(text))


def _entropy(value: str) -> float:
    length = len(value)
    return -sum((value.count(char) / length) * math.log2(value.count(char) / length) for char in set(value))


def evidence_kind(media_type) -> str | None:
    if media_type == "text/plain" or isinstance(media_type, str) and media_type.startswith("text/x-"):
        return "code"
    if media_type in {"application/x-latex", "text/x-tex"}:
        return "formula"
    return "chart" if media_type in {"image/png", "image/jpeg", "image/gif", "image/webp"} else None


def safe_node_id(value) -> str | None:
    return value if isinstance(value, str) and _NODE_ID.fullmatch(value) else None


def safe_artifact_id(value) -> str | None:
    return value if isinstance(value, str) and _ARTIFACT_ID.fullmatch(value) else None


def safe_claim_id(value) -> str | None:
    return value if isinstance(value, str) and _CLAIM_ID.fullmatch(value) else None


def normalized_checked_at(value) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.astimezone(UTC).isoformat() if parsed.tzinfo else None


def projection_envelope(projection: dict) -> dict:
    assessment = assess_delivery(projection, require_display=False)
    contract = assessment["contract"]
    return {"status": "ready", "projection": projection, "contract": contract} if assessment["valid"] else {"status": "blocked", "gaps": assessment["gaps"], "contract": contract}


def blocked_projection(tokens: int) -> dict:
    return {"status": "blocked", "gaps": [_gap("projection_budget_exceeded", "projection", tokens)], "contract": _contract(tokens)}


def assess_delivery(projection: dict, require_display: bool = True) -> dict:
    records = _records(projection)
    if records is None:
        return _invalid_assessment(projection)
    facts, claims, sources, artifacts = records
    gaps = _top_gaps(projection) + _model_gaps(facts, claims, sources, artifacts, require_display)
    gaps += _budget_gaps(projection)
    return _assessment(facts if not gaps else [], sources, gaps, projection)


def _records(projection):
    if not isinstance(projection, dict) or any(not isinstance(projection.get(key), list) for key in _TOP_FIELDS - {"question"}):
        return None
    facts = projection["facts"]
    indexes = tuple(_index(projection[key]) for key in ("claims", "sources", "artifacts"))
    return (facts, *indexes) if all(index is not None for index in indexes) else None


def _index(rows):
    result = {}
    for row in rows:
        identifier = row.get("id") if isinstance(row, dict) else None
        if not isinstance(identifier, str) or identifier in result:
            return None
        result[identifier] = row
    return result


def _invalid_assessment(projection) -> dict:
    return _assessment([], {}, [_gap("projection_invalid", "projection")], projection)


def _top_gaps(projection: dict) -> list[dict]:
    gaps = [] if set(projection) == _TOP_FIELDS else [_gap("projection_fields_invalid", "projection")]
    return gaps if safe_narrative(projection.get("question")) is not None else gaps + [_gap("question_invalid", "question")]


def _model_gaps(facts, claims, sources, artifacts, require_display) -> list[dict]:
    gaps = _claim_gaps(claims) + _source_record_gaps(sources)
    gaps += _artifact_record_gaps(artifacts, require_display)
    return gaps + _fact_gaps(facts, claims, sources, artifacts)


def _claim_gaps(claims: dict) -> list[dict]:
    return [gap for claim in claims.values() for gap in _one_claim_gaps(claim)]


def _one_claim_gaps(claim: dict) -> list[dict]:
    expected = {"id", "text", "life_state", "verdict", "evidence", "evidence_ids", "source_ids", "artifact_ids"}
    gaps = _keys_gaps(claim, expected, "claims")
    checks = ((safe_claim_id(claim.get("id")), "claim_id_invalid"), (safe_narrative(claim.get("text")), "claim_text_invalid"), (claim.get("life_state") == "admitted", "claim_not_admitted"), (claim.get("verdict") in {"supported", "refuted", "uncertain"}, "claim_verdict_invalid"))
    gaps += [_gap(code, f"claims[{claim.get('id')}]") for passed, code in checks if not passed]
    return gaps + _evidence_gaps(claim)


def _evidence_gaps(claim: dict) -> list[dict]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return [_gap("claim_evidence_missing", "claims.evidence")]
    gaps = [gap for item in evidence for gap in _one_evidence_gaps(item)]
    return gaps + _claim_relation_gaps(claim, evidence)


def _one_evidence_gaps(item) -> list[dict]:
    if not isinstance(item, dict) or set(item) != {"id", "kind", "artifact_ids"}:
        return [_gap("evidence_fields_invalid", "claims.evidence")]
    identifiers = item.get("artifact_ids")
    valid = safe_node_id(item.get("id")) and item.get("kind") in {"source", "experiment"}
    return [] if valid and _id_list(identifiers, safe_artifact_id, allow_empty=True) else [_gap("evidence_invalid", "claims.evidence")]


def _claim_relation_gaps(claim: dict, evidence: list[dict]) -> list[dict]:
    records = [item for item in evidence if isinstance(item, dict)]
    evidence_ids = [item["id"] for item in records if isinstance(item.get("id"), str)]
    source_ids = [item["id"] for item in records if item.get("kind") == "source"]
    artifact_ids = sorted({artifact for item in records for artifact in item.get("artifact_ids", []) if isinstance(artifact, str)})
    checks = ((claim.get("evidence_ids") == evidence_ids, "claim_evidence_mismatch"), (claim.get("source_ids") == source_ids, "claim_source_mismatch"), (claim.get("artifact_ids") == artifact_ids, "claim_artifact_mismatch"))
    return [_gap(code, f"claims[{claim.get('id')}]") for passed, code in checks if not passed]


def _source_record_gaps(sources: dict) -> list[dict]:
    return [gap for source in sources.values() for gap in _one_source_record_gaps(source)]


def _one_source_record_gaps(source: dict) -> list[dict]:
    expected = {"id", "title", "source_level", "checked_at"}
    gaps = _keys_gaps(source, expected, "sources")
    checks = ((safe_node_id(source.get("id")), "source_id_invalid"), (safe_narrative(source.get("title")), "source_title_invalid"), (source.get("source_level") in SOURCE_LEVELS, "source_level_invalid"), (normalized_checked_at(source.get("checked_at")) == source.get("checked_at"), "source_checked_at_invalid"))
    return gaps + [_gap(code, f"sources[{source.get('id')}]") for passed, code in checks if not passed]


def _artifact_record_gaps(artifacts: dict, require_display: bool) -> list[dict]:
    return [gap for artifact in artifacts.values() for gap in _one_artifact_record_gaps(artifact, require_display)]


def _one_artifact_record_gaps(artifact: dict, require_display: bool) -> list[dict]:
    expected = {"id", "kind", "size", "links"} | ({"display"} if require_display else set())
    gaps = _keys_gaps(artifact, expected, "artifacts")
    valid = safe_artifact_id(artifact.get("id")) and artifact.get("kind") in EVIDENCE_KINDS
    valid = valid and isinstance(artifact.get("size"), int) and 0 <= artifact["size"] <= 262144
    gaps += [] if valid and isinstance(artifact.get("links"), list) and artifact["links"] else [_gap("artifact_invalid", "artifacts")]
    return gaps + (_display_gaps(artifact) if require_display else [])


def _display_gaps(artifact: dict) -> list[dict]:
    display, kind = artifact.get("display"), artifact.get("kind")
    if not isinstance(display, dict) or display.get("kind") != kind:
        return [_gap("artifact_display_invalid", "artifacts")]
    if kind == "code":
        return [] if set(display) == {"kind", "text"} and safe_report_text(display.get("text")) else [_gap("artifact_display_invalid", "artifacts")]
    if kind == "formula":
        return [] if set(display) == {"kind", "mathml"} and _mathml(display.get("mathml")) else [_gap("artifact_display_invalid", "artifacts")]
    return [] if set(display) == {"kind", "src"} and _chart_source(display.get("src")) else [_gap("artifact_display_invalid", "artifacts")]


def _mathml(value) -> bool:
    return isinstance(value, str) and value.startswith("<math") and value.endswith("</math>")


def _chart_source(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=]+", value) is not None


def _fact_gaps(facts, claims, sources, artifacts) -> list[dict]:
    if not facts:
        return [_gap("facts_missing", "facts")]
    return [gap for index, fact in enumerate(facts) for gap in _one_fact_gaps(index, fact, claims, sources, artifacts)]


def _one_fact_gaps(index, fact, claims, sources, artifacts) -> list[dict]:
    path = f"facts[{index}]"
    expected = {"text", "claim_id", "source_ids", "artifact_ids"}
    gaps = _keys_gaps(fact, expected, path)
    if not _fact_shape_valid(fact):
        return gaps + [_gap("fact_invalid", path)]
    claim = claims.get(fact["claim_id"])
    if claim is None:
        return gaps + [_gap("claim_missing", f"{path}.claim_id", fact["claim_id"])]
    return gaps + _fact_claim_gaps(fact, claim, path) + _fact_source_gaps(fact, claim, sources, path) + _fact_artifact_gaps(fact, claim, artifacts, path)


def _fact_shape_valid(fact: dict) -> bool:
    return isinstance(fact, dict) and safe_narrative(fact.get("text")) is not None and safe_claim_id(fact.get("claim_id")) is not None and _id_list(fact.get("source_ids"), safe_node_id) and _id_list(fact.get("artifact_ids"), safe_artifact_id, allow_empty=True)


def _fact_claim_gaps(fact, claim, path) -> list[dict]:
    checks = ((fact["text"] == claim.get("text"), "fact_text_mismatch"), (fact["source_ids"] == claim.get("source_ids"), "claim_source_mismatch"), (fact["artifact_ids"] == claim.get("artifact_ids"), "claim_artifact_mismatch"), (claim.get("life_state") == "admitted" and claim.get("verdict") == "supported", "claim_not_supported"))
    return [_gap(code, path) for passed, code in checks if not passed]


def _fact_source_gaps(fact, claim, sources, path) -> list[dict]:
    evidence = {item["id"]: item for item in claim.get("evidence", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    return [gap for source_id in fact["source_ids"] for gap in _one_source_gap(source_id, evidence, sources, path)]


def _one_source_gap(source_id, evidence, sources, path) -> list[dict]:
    if source_id not in sources:
        return [_gap("source_missing", f"{path}.source_ids", source_id)]
    return [] if evidence.get(source_id, {}).get("kind") == "source" else [_gap("source_claim_mismatch", f"{path}.source_ids", source_id)]


def _fact_artifact_gaps(fact, claim, artifacts, path) -> list[dict]:
    evidence = {item["id"]: item for item in claim.get("evidence", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    return [gap for artifact_id in fact["artifact_ids"] for gap in _one_artifact_gap(artifact_id, claim, evidence, artifacts, path)]


def _one_artifact_gap(artifact_id, claim, evidence, artifacts, path) -> list[dict]:
    artifact = artifacts.get(artifact_id)
    if artifact is None:
        return [_gap("artifact_missing", f"{path}.artifact_ids", artifact_id)]
    return [] if any(_link_matches(link, claim, evidence, artifact_id) for link in artifact.get("links", [])) else [_gap("artifact_claim_mismatch", f"{path}.artifact_ids", artifact_id)]


def _link_matches(link, claim, evidence, artifact_id) -> bool:
    if not isinstance(link, dict) or link.get("claim_id") != claim.get("id"):
        return False
    item = evidence.get(link.get("evidence_id"))
    if item is None or artifact_id not in item.get("artifact_ids", []):
        return False
    return link.get("source_id") == item["id"] if item["kind"] == "source" else set(link) == {"claim_id", "evidence_id"}


def _keys_gaps(value, expected, path) -> list[dict]:
    return [] if isinstance(value, dict) and set(value) == expected else [_gap("projection_fields_invalid", path)]


def _id_list(value, checker, allow_empty: bool = False) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and len(value) == len(set(value)) and all(checker(item) is not None for item in value)


def _budget_gaps(projection) -> list[dict]:
    tokens = input_tokens(projection)
    return [] if tokens <= REPORT_INPUT_TOKEN_BUDGET else [_gap("projection_budget_exceeded", "projection", tokens)]


def input_tokens(projection) -> int:
    payload = _metadata_projection(projection)
    return math.ceil(len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) / 4)


def _metadata_projection(projection) -> dict:
    if not isinstance(projection, dict):
        return {}
    artifacts = [{key: item.get(key) for key in ("id", "kind", "size", "links")} for item in projection.get("artifacts", []) if isinstance(item, dict)]
    return {key: projection.get(key) for key in ("question", "facts", "claims", "sources")} | {"artifacts": artifacts}


def _assessment(facts, sources, gaps, projection) -> dict:
    source_ids = sorted({source for fact in facts for source in fact["source_ids"]})
    levels = [sources[source]["source_level"] for source in source_ids if source in sources]
    return {"valid": not gaps, "delivery_level": 4 if not gaps else 0, "accepted_facts": facts, "minimum_source_level": min(levels, key=SOURCE_LEVELS.get) if levels else None, "gaps": gaps, "contract": _contract(input_tokens(projection))}


def _contract(tokens: int) -> dict:
    return {"sections": list(REPORT_SECTIONS), "input_budget_tokens": REPORT_INPUT_TOKEN_BUDGET, "input_tokens": tokens}


def _gap(code: str, path: str, value=None) -> dict:
    return {"code": code, "path": path, "value": _safe_gap_value(value)}


def _safe_gap_value(value):
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if safe_node_id(value) or safe_artifact_id(value) or safe_claim_id(value):
        return value
    return None
