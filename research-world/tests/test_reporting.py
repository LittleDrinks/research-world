from server.report_delivery import render_html, validate_html
from server.reporting import assess_delivery, projection_envelope


SOURCE = "node:" + "a" * 24
OTHER_NODE = "node:" + "b" * 24
DIRECTION = "node:" + "c" * 24
CLAIM = f"claim:{DIRECTION.removeprefix('node:')}:1"
ARTIFACT = "artifact:" + "d" * 64
OTHER_ARTIFACT = "artifact:" + "e" * 64


def projection():
    evidence = {"id": SOURCE, "kind": "source", "artifact_ids": [ARTIFACT]}
    source = {"id": SOURCE, "title": "Paper", "source_level": "published", "checked_at": "2026-08-23T04:00:00+00:00"}
    claim = {"id": CLAIM, "text": "Transition at 42 K", "life_state": "admitted", "verdict": "supported", "evidence": [evidence], "evidence_ids": [SOURCE], "source_ids": [SOURCE], "artifact_ids": [ARTIFACT]}
    fact = {"text": claim["text"], "claim_id": CLAIM, "source_ids": [SOURCE], "artifact_ids": [ARTIFACT]}
    link = {"claim_id": CLAIM, "evidence_id": SOURCE, "source_id": SOURCE}
    artifact = {"id": ARTIFACT, "kind": "code", "size": 4, "links": [link], "display": {"kind": "code", "text": "x=42"}}
    return {"question": "How does the transition behave?", "facts": [fact], "claims": [claim], "sources": [source], "artifacts": [artifact]}


def test_delivery_accepts_kernel_bound_facts_and_renders_citations():
    value = projection()
    result = assess_delivery(value)
    html = render_html("Orbit", value, result).decode()
    assert result["valid"] is True
    assert f'href="#evidence-{SOURCE}"' in html
    assert f'id="evidence-{SOURCE}"' in html
    assert f'<pre><code data-artifact="{ARTIFACT}">x=42</code></pre>' in html
    assert "No validated formulas evidence." in html


def test_delivery_rejects_fabricated_text_and_unlinked_artifact():
    value = projection()
    value["facts"][0]["text"] = "Invented"
    value["facts"][0]["artifact_ids"].append(OTHER_ARTIFACT)
    result = assess_delivery(value)
    assert {gap["code"] for gap in result["gaps"]} >= {"fact_text_mismatch", "claim_artifact_mismatch", "artifact_missing"}
    assert result["accepted_facts"] == []


def test_delivery_reports_safe_source_metadata_gap():
    value = projection()
    value["sources"][0]["checked_at"] = "not-a-date"
    result = assess_delivery(value)
    assert result["gaps"] == [{"code": "source_checked_at_invalid", "path": f"sources[{SOURCE}]", "value": None}]


def test_delivery_rejects_supported_claim_without_source_evidence():
    value = projection()
    value["claims"][0]["evidence"] = [{"id": OTHER_NODE, "kind": "experiment", "artifact_ids": [ARTIFACT]}]
    result = assess_delivery(value)
    assert result["valid"] is False
    assert {gap["code"] for gap in result["gaps"]} >= {"claim_evidence_mismatch", "claim_source_mismatch"}


def test_rendered_report_rejects_credentials_trace_and_paths():
    content = b"<!doctype html><body>session_id: s1 GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz /home/research/key</body></html>"
    assert validate_html(content) == [{"code": "sensitive_data_exposed", "path": "html", "value": None}]


def test_rendered_report_allows_normal_trace_language_and_web_paths():
    content = b"<!doctype html><body>Trace analysis at /methods.</body></html>"
    assert validate_html(content) == []


def test_delivery_rejects_unsafe_narrative_without_returning_its_value():
    value = projection()
    secret = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz"
    value["sources"][0]["title"] = secret
    result = assess_delivery(value)
    assert result["valid"] is False
    assert {gap["code"] for gap in result["gaps"]} == {"source_title_invalid"}
    assert secret not in str(result)


def test_delivery_rejects_artifact_without_its_exact_evidence_link():
    value = projection()
    value["artifacts"][0]["links"] = [{"claim_id": CLAIM, "evidence_id": OTHER_NODE, "source_id": OTHER_NODE}]
    result = assess_delivery(value)
    assert result["gaps"] == [{"code": "artifact_claim_mismatch", "path": "facts[0].artifact_ids", "value": ARTIFACT}]


def test_code_is_escaped_before_output_validation_without_becoming_active_html():
    value = projection()
    value["artifacts"][0]["display"]["text"] = 'print("<script>not markup</script>")'
    result = assess_delivery(value)
    html = render_html("Orbit", value, result)
    assert result["valid"] is True
    assert b"&lt;script&gt;not markup&lt;/script&gt;" in html
    assert validate_html(html) == []


def test_artifact_text_is_validated_separately_from_escaped_output():
    value = projection()
    secret = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz"
    value["artifacts"][0]["display"]["text"] = secret
    result = assess_delivery(value)
    assert {gap["code"] for gap in result["gaps"]} == {"artifact_display_invalid"}
    assert secret not in str(result)


def test_public_envelope_blocks_invalid_narrative_without_projection_payload():
    value = projection()
    secret = "baseurl=https://credentials.example"
    value["question"] = secret
    envelope = projection_envelope(value)
    assert envelope["status"] == "blocked"
    assert "projection" not in envelope
    assert secret not in str(envelope)
