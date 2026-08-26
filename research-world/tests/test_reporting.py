from io import BytesIO

import pytest
from PIL import Image
from latex2mathml import exceptions as latex_errors

from server.report_delivery import artifact_display, render_html, validate_html
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
    content = report_fixture("session_id: s1 GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz /home/research/key")
    assert validate_html(content) == [{"code": "sensitive_data_exposed", "path": "html", "value": None}]


def test_rendered_report_allows_normal_trace_language_and_web_paths():
    content = report_fixture("Trace analysis at /methods.")
    assert validate_html(content) == []


def test_rendered_report_rejects_garbage_without_semantic_structure():
    content = b"<!doctype html><html><body>report</body></html>"
    assert validate_html(content) == [{"code": "rendered_content_invalid", "path": "html", "value": None}]


@pytest.mark.parametrize("content", [
    b"<!doctype html><html><head><title>Orbit</title></head><body></body></html>",
    b"<!doctype html><html><head><title>Orbit</title></head><body></body></html>x",
    b"<!doctype html><html><head><title>Orbit</title></head><body></body></html><html></html>",
])
def test_rendered_report_rejects_incomplete_or_trailing_documents(content):
    assert validate_html(content)[0]["code"] == "rendered_content_invalid"


@pytest.mark.parametrize("suffix", [b"<!--tail-->", b"<?tail?>", b"<!unknown>", b"<![CDATA[tail]]>"])
def test_rendered_report_rejects_non_data_after_document(suffix):
    assert validate_html(report_fixture("Validated") + suffix)[0]["code"] == "rendered_content_invalid"


def report_fixture(text):
    value = projection()
    assessment = assess_delivery(value)
    value["facts"][0]["text"] = text
    value["claims"][0]["text"] = text
    return render_html("Orbit", value, assessment)


def test_formula_evidence_is_renderable_mathml():
    value = projection()
    value["artifacts"][0]["kind"] = "formula"
    value["artifacts"][0]["display"] = {"kind": "formula", "mathml": "<math><mi>E</mi></math>"}
    html = render_html("Orbit", value, assess_delivery(value)).decode()
    assert "<math" in html and "<mtext>" not in html


def test_formula_display_accepts_converter_mathml():
    assert artifact_display({"media_type": "application/x-latex"}, b"x^2")["kind"] == "formula"


def test_formula_display_rejects_foreign_converter_markup(monkeypatch):
    monkeypatch.setattr("server.report_delivery.convert", lambda _text: '<math xmlns="http://www.w3.org/1998/Math/MathML"><script/></math>')
    assert artifact_display({"media_type": "application/x-latex"}, b"x") == {"kind": "invalid"}


@pytest.mark.parametrize("error", [value for value in vars(latex_errors).values() if isinstance(value, type) and issubclass(value, Exception)])
def test_formula_conversion_errors_are_controlled(monkeypatch, error):
    monkeypatch.setattr("server.report_delivery.convert", lambda _text: (_ for _ in ()).throw(error()))
    assert artifact_display({"media_type": "application/x-latex"}, b"x") == {"kind": "invalid"}


def test_chart_display_decodes_pixels_and_rejects_tiny_malformed_fixtures(monkeypatch):
    content = image_bytes((2, 2))
    assert artifact_display({"media_type": "image/png"}, content)["kind"] == "chart"
    assert artifact_display({"media_type": "image/png"}, content[:-8]) == {"kind": "invalid"}
    monkeypatch.setattr("server.report_delivery.MAX_IMAGE_PIXELS", 1)
    assert artifact_display({"media_type": "image/png"}, content) == {"kind": "invalid"}


def test_chart_display_rejects_animated_gif():
    first, second = Image.new("RGB", (2, 2)), Image.new("RGB", (2, 2), "white")
    content = BytesIO()
    first.save(content, format="GIF", save_all=True, append_images=[second])
    assert artifact_display({"media_type": "image/gif"}, content.getvalue()) == {"kind": "invalid"}


def test_chart_display_rejects_pillow_decompression_bombs(monkeypatch):
    monkeypatch.setattr("server.report_delivery.Image.open", lambda _data: (_ for _ in ()).throw(Image.DecompressionBombError("bomb")))
    assert artifact_display({"media_type": "image/png"}, b"png") == {"kind": "invalid"}


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


def image_bytes(size):
    stream = BytesIO()
    Image.new("RGB", size).save(stream, "PNG")
    return stream.getvalue()
