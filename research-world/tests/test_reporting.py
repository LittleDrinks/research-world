from base64 import b64decode
from io import BytesIO

import pytest
from PIL import Image, PngImagePlugin
from latex2mathml import exceptions as latex_errors
from latex2mathml.converter import convert

from server.report_delivery import MAX_EVIDENCE_BYTES, artifact_display, render_html, validate_html
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


def test_rendered_report_rejects_non_chart_data_uri():
    content = report_fixture("Validated").replace(b"</body>", b'<a href="data:text/html,%3Cscript%3E">x</a></body>')
    assert validate_html(content) == [{"code": "data_uri_exposed", "path": "html", "value": None}]


def test_rendered_report_rejects_entity_encoded_active_uri():
    content = report_fixture("Validated").replace(b"</body>", b'<a href=" java&#x73;cript:alert(1)">x</a></body>')
    assert validate_html(content) == [{"code": "active_content_exposed", "path": "html", "value": None}]


@pytest.mark.parametrize(("attribute", "codes"), [
    ('title="/javascript: literal"', []),
    ('href="https://example.test/docs/javascript: literal"', ["sensitive_data_exposed"]),
])
def test_rendered_report_allows_javascript_in_non_scheme_attributes(attribute, codes):
    content = report_fixture("Validated").replace(b"</body>", f"<p {attribute}>x</p></body>".encode())
    assert [gap["code"] for gap in validate_html(content)] == codes


def test_rendered_report_allows_visible_javascript_text_and_escaped_code():
    value = projection()
    value["facts"][0]["text"] = "The literal javascript: protocol is evidence."
    value["claims"][0]["text"] = value["facts"][0]["text"]
    value["artifacts"][0]["display"]["text"] = '<a href="javascript:alert(1)">example</a>'
    assessment = assess_delivery(value)
    content = render_html("Orbit", value, assessment)
    assert assessment["valid"] is True
    assert b"&lt;a href=&quot;javascript:alert(1)&quot;&gt;example&lt;/a&gt;" in content
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


def test_formula_display_accepts_current_converter_phantom_and_colons():
    formula = r"\phantom{x}+y"
    expected = convert(formula)
    assert "<mphantom>" in expected
    assert artifact_display({"media_type": "application/x-latex"}, formula.encode()) == {"kind": "formula", "mathml": expected}
    assert all(artifact_display({"media_type": "text/x-tex"}, value)["kind"] == "formula" for value in (b"a:b", b"x:=y"))


def test_formula_display_rejects_foreign_converter_markup(monkeypatch):
    monkeypatch.setattr("server.report_delivery.convert", lambda _text: '<math xmlns="http://www.w3.org/1998/Math/MathML"><script/></math>')
    assert artifact_display({"media_type": "application/x-latex"}, b"x") == {"kind": "invalid"}


@pytest.mark.parametrize("mathml", [
    '<math xmlns="http://www.w3.org/1998/Math/MathML"><mtext>data: text</mtext></math>',
    '<math xmlns="urn:foreign"><mi>x</mi></math>',
    '<math xmlns="http://www.w3.org/1998/Math/MathML"><evil:mi xmlns:evil="urn:foreign">x</evil:mi></math>',
    '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi xmlns:evil="urn:foreign" evil:href="x">x</mi></math>',
])
def test_formula_display_rejects_unsafe_mathml_boundaries(monkeypatch, mathml):
    monkeypatch.setattr("server.report_delivery.convert", lambda _text: mathml)
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


@pytest.mark.parametrize("media_type", ["image/png", "image/gif", "image/jpeg", "image/webp"])
def test_chart_reencoding_uses_only_visible_rgba_pixels(media_type):
    content, marker = chart_fixture(media_type)
    display = artifact_display({"media_type": media_type}, content)
    delivered = chart_bytes(display)
    assert display["src"].startswith("data:image/png;base64,")
    assert len(delivered) <= MAX_EVIDENCE_BYTES
    assert not marker or marker in content
    assert not marker or marker not in delivered
    assert opened_chart(delivered) == ("PNG", "RGBA", *opened_rgba(content))


def test_chart_reencoding_preserves_transparent_png_pixels():
    content, _marker = transparent_png()
    delivered = chart_bytes(artifact_display({"media_type": "image/png"}, content))
    assert opened_chart(delivered) == ("PNG", "RGBA", *opened_rgba(content))


@pytest.mark.parametrize("media_type", ["image/png", "image/gif", "image/jpeg", "image/webp"])
def test_output_validation_accepts_only_sanitized_static_charts(media_type):
    value = chart_projection(media_type)
    assessment = assess_delivery(value)
    assert assessment["valid"] is True
    assert validate_html(render_html("Orbit", value, assessment)) == []


@pytest.mark.parametrize(("text", "codes"), [
    ("data:image/jpeg;base64,sk-abcdefghijklmnopqrstuvwxyz", ["data_uri_exposed", "sensitive_data_exposed"]),
    ("https://credentials.example", ["sensitive_data_exposed"]),
])
def test_output_validation_scans_untrusted_data_and_urls(text, codes):
    assert [gap["code"] for gap in validate_html(report_fixture(text))] == codes


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


def chart_fixture(media_type):
    return {"image/png": indexed_png, "image/gif": transparent_gif, "image/jpeg": jpeg_chart, "image/webp": webp_chart}[media_type]()


def indexed_png():
    marker = b"PALETTE-ONLY-SECRET"
    image = Image.new("P", (2, 1))
    palette = bytearray(768)
    palette[:6], palette[512:512 + len(marker)] = b"\x0a\x14\x1e\x28\x32\x3c", marker
    image.putpalette(palette)
    image.putdata([0, 1])
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", marker.decode())
    return saved_image(image, "PNG", pnginfo=info) + marker, marker


def transparent_gif():
    image = Image.new("P", (2, 1))
    image.putpalette(b"\x00\x00\x00\xff\x00\x00")
    image.putdata([0, 1])
    return saved_image(image, "GIF", transparency=0), b""


def transparent_png():
    image = Image.new("RGBA", (2, 1))
    image.putdata([(12, 24, 36, 0), (48, 60, 72, 128)])
    return saved_image(image, "PNG"), b""


def jpeg_chart():
    return saved_image(Image.new("RGB", (2, 1), (14, 28, 42)), "JPEG"), b""


def webp_chart():
    return saved_image(Image.new("RGBA", (2, 1), (12, 24, 36, 128)), "WEBP"), b""


def saved_image(image, image_format, **options):
    stream = BytesIO()
    image.save(stream, image_format, **options)
    return stream.getvalue()


def chart_bytes(display):
    return b64decode(display["src"].split(",", 1)[1])


def opened_chart(content):
    with Image.open(BytesIO(content)) as image:
        image.load()
        return image.format, image.mode, image.size, image.convert("RGBA").tobytes()


def opened_rgba(content):
    with Image.open(BytesIO(content)) as image:
        image.load()
        return image.size, image.convert("RGBA").tobytes()


def chart_projection(media_type):
    content, _marker = chart_fixture(media_type)
    value = projection()
    value["artifacts"][0].update(kind="chart", size=len(content), display=artifact_display({"media_type": media_type}, content))
    return value
