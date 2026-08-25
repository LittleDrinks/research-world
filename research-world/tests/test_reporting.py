from server.report_delivery import render_html
from server.reporting import assess_delivery


def projection():
    source = {"id": "node:paper", "title": "Paper", "source_level": "published", "checked_at": "2026-08-23T12:00:00+08:00", "anchor": "source-node:paper"}
    claim = {"id": "claim:one", "text": "Transition at 42 K", "source_ids": ["node:paper"]}
    fact = {"text": "Transition at 42 K", "claim_id": "claim:one", "source_ids": ["node:paper"], "artifact_ids": ["artifact:evidence"]}
    artifact = {"id": "artifact:evidence", "media_type": "text/plain", "size": 4, "claim_ids": ["claim:one"], "source_ids": ["node:paper"]}
    return {"facts": [fact], "claims": [claim], "sources": [source], "artifacts": [artifact]}


def test_delivery_accepts_kernel_bound_facts_and_renders_citations():
    value = projection()
    result = assess_delivery(value)
    html = render_html("Orbit", value, result).decode()
    assert result["valid"] is True
    assert 'href="#source-node:paper"' in html
    assert 'id="source-node:paper"' in html
    assert "No validated formulas evidence." in html
    assert "linear-gradient" not in html


def test_delivery_rejects_fabricated_text_and_unlinked_artifact():
    value = projection()
    value["facts"][0]["text"] = "Invented"
    value["facts"][0]["artifact_ids"].append("artifact:other")
    result = assess_delivery(value)
    assert {gap["code"] for gap in result["gaps"]} == {"fact_text_mismatch", "artifact_missing"}
    assert result["accepted_facts"] == []


def test_delivery_reports_exact_source_metadata_gap():
    value = projection()
    value["sources"][0]["checked_at"] = "not-a-date"
    result = assess_delivery(value)
    assert result["gaps"] == [{"code": "source_checked_at_invalid", "path": "sources[node:paper].checked_at", "value": "not-a-date"}]
