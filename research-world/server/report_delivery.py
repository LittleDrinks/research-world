from __future__ import annotations

import base64
import re
import warnings
from binascii import Error as Base64Error
from xml.etree import ElementTree
from io import BytesIO
from html import escape, unescape
from html.parser import HTMLParser

from PIL import Image, UnidentifiedImageError
from latex2mathml.converter import convert
from latex2mathml.exceptions import (
    DenominatorNotFoundError,
    DoubleSubscriptsError,
    DoubleSuperscriptsError,
    ExtraLeftOrMissingRightError,
    InvalidAlignmentError,
    InvalidStyleForGenfracError,
    InvalidWidthError,
    LimitsMustFollowMathOperatorError,
    MissingEndError,
    MissingSuperScriptOrSubscriptError,
    NoAvailableTokensError,
    NumeratorNotFoundError,
)

from .reporting import contains_restricted_data, evidence_kind, safe_report_text

MAX_EVIDENCE_BYTES = 262144
MAX_IMAGE_DIMENSION = 8192
MAX_IMAGE_PIXELS = 16_777_216
_ACTIVE_TAGS = {"script", "iframe", "object", "embed"}
_ACTIVE_URI = re.compile(r"(?:javascript|vbscript):", re.IGNORECASE)
_DATA_URI = re.compile(r"\bdata:", re.IGNORECASE)
_TEX_ERRORS = (NumeratorNotFoundError, DenominatorNotFoundError, ExtraLeftOrMissingRightError, MissingSuperScriptOrSubscriptError, DoubleSubscriptsError, DoubleSuperscriptsError, NoAvailableTokensError, InvalidStyleForGenfracError, MissingEndError, InvalidAlignmentError, InvalidWidthError, LimitsMustFollowMathOperatorError, RecursionError)


def artifact_display(record: dict, content: bytes) -> dict:
    if len(content) > MAX_EVIDENCE_BYTES:
        return {"kind": "invalid"}
    kind = evidence_kind(record["media_type"])
    if kind in {"code", "formula"}:
        return _text_display(kind, content)
    if kind == "chart":
        return _chart_display(record["media_type"], content)
    return {"kind": "invalid"}


def _text_display(kind: str, content: bytes) -> dict:
    try:
        text = safe_report_text(content.decode("utf-8"))
    except UnicodeDecodeError:
        text = None
    if not text:
        return {"kind": "invalid"}
    return {"kind": "code", "text": text} if kind == "code" else _formula_display(text)


def _formula_display(text: str) -> dict:
    try:
        mathml = convert(text)
        return {"kind": "formula", "mathml": mathml} if _safe_mathml(mathml) else {"kind": "invalid"}
    except _TEX_ERRORS + (ElementTree.ParseError, TypeError, ValueError):
        return {"kind": "invalid"}


def _chart_display(media_type: str, content: bytes) -> dict:
    image = _decoded_image(media_type, content)
    if image is None:
        return {"kind": "invalid"}
    encoded = _encode_image(image)
    if encoded is None:
        return {"kind": "invalid"}
    source = base64.b64encode(encoded).decode("ascii")
    return {"kind": "chart", "src": f"data:image/png;base64,{source}"}


def _decoded_image(media_type: str, content: bytes):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                if not _image_valid(image, media_type):
                    return None
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
                return _image_pixels(image)
    except (KeyError, UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return None


def _image_valid(image, media_type: str) -> bool:
    return image.format == _image_formats.get(media_type) and getattr(image, "n_frames", 1) == 1 and _image_size_valid(image)


def _image_pixels(image):
    pixels = image.convert("RGBA").tobytes()
    return Image.frombytes("RGBA", image.size, pixels)


def _encode_image(image) -> bytes | None:
    output = BytesIO()
    image.save(output, format="PNG", compress_level=9)
    content = output.getvalue()
    return content if len(content) <= MAX_EVIDENCE_BYTES else None


def _image_size_valid(image) -> bool:
    width, height = image.size
    return 0 < width <= MAX_IMAGE_DIMENSION and 0 < height <= MAX_IMAGE_DIMENSION and width * height <= MAX_IMAGE_PIXELS


def render_html(title: str, projection: dict, assessment: dict) -> bytes:
    sources = {source["id"]: source for source in projection["sources"]}
    artifacts = {item["id"]: item for item in projection["artifacts"]}
    body = _question(projection["question"]) + _findings(assessment["accepted_facts"], sources)
    body += _methods(assessment["accepted_facts"], sources, artifacts, projection["claims"])
    body += _limitations(assessment["gaps"])
    return _document(title, body).encode("utf-8")


def validate_html(content: bytes) -> list[dict]:
    text = content.decode("utf-8", errors="replace")
    safety_text = _html_safety_text(text)
    valid, active_content = _semantic_html(text)
    gaps = [] if valid else [_html_gap("rendered_content_invalid")]
    if active_content:
        gaps.append(_html_gap("active_content_exposed"))
    if _DATA_URI.search(safety_text):
        gaps.append(_html_gap("data_uri_exposed"))
    return gaps + ([_html_gap("sensitive_data_exposed")] if contains_restricted_data(safety_text, opaque=False) else [])


def _html_safety_text(text: str) -> str:
    sanitized = _strip_static_chart_payloads(text)
    return unescape(sanitized).replace('xmlns="http://www.w3.org/1998/Math/MathML"', "")


def _strip_static_chart_payloads(text: str) -> str:
    return _static_chart_source.sub(_strip_static_chart, text)


def _strip_static_chart(match) -> str:
    source = match.group(2)
    payload = "static-chart" if _is_static_chart(source) else source
    return f"{match.group(1)}{payload}{match.group(3)}"


def _is_static_chart(source: str) -> bool:
    try:
        content = base64.b64decode(source.removeprefix("data:image/png;base64,"), validate=True)
    except (Base64Error, ValueError):
        return False
    image = _decoded_image("image/png", content) if len(content) <= MAX_EVIDENCE_BYTES else None
    encoded = _encode_image(image) if image is not None else None
    return encoded == content


def _semantic_html(text: str) -> tuple[bool, bool]:
    parser = _ReportStructure()
    try:
        parser.feed(text)
        parser.close()
    except (AssertionError, ValueError):
        return False, False
    return parser.valid(), parser.active_content


def _html_gap(code: str) -> dict:
    return {"code": code, "path": "html", "value": None}


def _document(title: str, body: str) -> str:
    safe = escape(title)
    style = "body{font:16px system-ui;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.5rem}code,math{background:#eee;padding:.15rem .3rem}figure{margin:1rem 0}img{max-width:100%;height:auto}"
    return f"<!doctype html><html><head><meta charset=utf-8><title>{safe}</title><style>{style}</style></head><body><h1>{safe}</h1>{body}</body></html>"


def _question(question: str) -> str:
    return f"<h2>Research question</h2><p>{escape(question)}</p>"


def _findings(facts: list[dict], sources: dict) -> str:
    rows = "".join(_finding(fact, sources) for fact in facts)
    return f"<h2>Conclusions</h2><ul>{rows}</ul>"


def _finding(fact: dict, sources: dict) -> str:
    citations = ", ".join(_citation(sources[source]) for source in fact["source_ids"])
    return f"<li>{escape(fact['text'])} {citations}</li>"


def _citation(source: dict) -> str:
    identifier, title = escape(source["id"]), escape(source["title"])
    return f'<a href="#evidence-{identifier}">[{title}]</a>'


def _methods(facts: list[dict], sources: dict, artifacts: dict, claims: list[dict]) -> str:
    return "<h2>Evidence and methods</h2>" + _evidence(facts, sources) + _experiment_anchors(facts, claims) + _evidence_sections(facts, artifacts)


def _evidence(facts: list[dict], sources: dict) -> str:
    ids = sorted({source for fact in facts for source in fact["source_ids"]})
    rows = "".join(_source_row(sources[source]) for source in ids)
    return f"<table><tr><th>Source</th><th>Level</th><th>Checked</th></tr>{rows}</table>"


def _source_row(source: dict) -> str:
    identifier, title = escape(source["id"]), escape(source["title"])
    level, checked = escape(source["source_level"]), escape(source["checked_at"])
    return f'<tr id="evidence-{identifier}"><td>{title}</td><td>{level}</td><td>{checked}</td></tr>'


def _experiment_anchors(facts: list[dict], claims: list[dict]) -> str:
    claim_ids = {fact["claim_id"] for fact in facts}
    evidence = [item for claim in claims if claim["id"] in claim_ids for item in claim["evidence"] if item["kind"] == "experiment"]
    rows = "".join(f'<li id="evidence-{escape(item["id"])}">Experiment evidence {escape(item["id"])}</li>' for item in evidence)
    return f"<ul>{rows}</ul>" if rows else ""


def _evidence_sections(facts: list[dict], artifacts: dict) -> str:
    selected = _selected_artifacts(facts, artifacts)
    return "".join(_section(name, selected, kind) for name, kind in (("Code", "code"), ("Formulas", "formula"), ("Charts", "chart")))


def _selected_artifacts(facts: list[dict], artifacts: dict) -> list[dict]:
    ids = {artifact for fact in facts for artifact in fact["artifact_ids"]}
    return [artifacts[artifact_id] for artifact_id in sorted(ids)]


def _section(name: str, artifacts: list[dict], kind: str) -> str:
    items = [artifact for artifact in artifacts if artifact["display"]["kind"] == kind]
    if not items:
        return f"<h3>{name}</h3><p>No validated {name.lower()} evidence.</p>"
    return f"<h3>{name}</h3>" + "".join(_artifact(item) for item in items)


def _artifact(item: dict) -> str:
    kind = item["display"]["kind"]
    return _artifact_html[kind](item)


def _code(item: dict) -> str:
    content = escape(item["display"]["text"])
    return _figure(item, f'<pre><code data-artifact="{escape(item["id"])}">{content}</code></pre>')


def _formula(item: dict) -> str:
    content = item["display"]["mathml"]
    return _figure(item, f'<div class="formula" data-artifact="{escape(item["id"])}">{content}</div>')


def _chart(item: dict) -> str:
    artifact_id = escape(item["id"])
    source = escape(item["display"]["src"], quote=True)
    return _figure(item, f'<img src="{source}" alt="Chart evidence {artifact_id}">')


def _figure(item: dict, content: str) -> str:
    return f'<figure id="artifact-{escape(item["id"])}"><figcaption>{_caption(item)}</figcaption>{content}</figure>'


def _caption(item: dict) -> str:
    links = "; ".join(_link_caption(link) for link in item["links"])
    return f"Artifact {escape(item['id'])}; {links}"


def _link_caption(link: dict) -> str:
    evidence = escape(link["evidence_id"])
    return f'<a href="#evidence-{evidence}">Evidence {evidence}</a>'


def _limitations(gaps: list[dict]) -> str:
    return "<h2>Limitations and gaps</h2><p>No validated delivery gaps.</p>" if not gaps else "<h2>Limitations and gaps</h2><p>Delivery validation failed.</p>"


_artifact_html = {"code": _code, "formula": _formula, "chart": _chart}
_image_formats = {"image/png": "PNG", "image/jpeg": "JPEG", "image/gif": "GIF", "image/webp": "WEBP"}
_static_chart_source = re.compile(r'(<img\b[^>]*\bsrc=")(?P<source>data:image/png;base64,[A-Za-z0-9+/=]+)(")', re.IGNORECASE)


class _ReportStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.stack, self.headings = set(), [], []
        self.doctype, self.evidence, self.formula, self.active_content, self.invalid = 0, False, False, False, False
        self.title, self.heading = [], []

    def handle_decl(self, decl):
        self.doctype += decl.lower() == "doctype html"
        self.invalid |= self.doctype != 1 or bool(self.stack)

    def handle_starttag(self, tag, attrs):
        self.active_content |= tag in _ACTIVE_TAGS or _active_attributes(attrs)
        self.invalid |= not self._start_allowed(tag)
        if self.invalid:
            return
        self.tags.add(tag)
        if tag not in _void_tags:
            self.stack.append(tag)
        values = dict(attrs)
        self.evidence |= tag == "a" and values.get("href", "").startswith("#evidence-")
        self.formula |= tag == "div" and values.get("class") == "formula"
        self.heading = [] if tag == "h2" else self.heading

    def handle_endtag(self, tag):
        self.invalid |= tag in _void_tags or not self.stack or self.stack[-1] != tag
        if not self.invalid:
            self.stack.pop()
            self.headings += ["".join(self.heading).strip()] if tag == "h2" else []

    def handle_data(self, data):
        self.invalid |= not self.stack and bool(data.strip())
        if self.stack and self.stack[-1] == "title":
            self.title.append(data)
        if self.stack and "h2" in self.stack:
            self.heading.append(data)

    def handle_comment(self, _data):
        self.invalid = True

    def handle_pi(self, _data):
        self.invalid = True

    def unknown_decl(self, _data):
        self.invalid = True

    def _start_allowed(self, tag) -> bool:
        if tag in _void_tags:
            return bool(self.stack)
        if tag == "html":
            return self.doctype == 1 and not self.stack and "html" not in self.tags
        if tag == "head":
            return self.stack == ["html"] and "head" not in self.tags
        if tag == "body":
            return self.stack == ["html"] and "head" in self.tags and "body" not in self.tags
        if tag == "title":
            return self.stack == ["html", "head"] and "title" not in self.tags
        return bool(self.stack) and ("body" in self.stack or self.stack == ["html", "head"])

    def valid(self) -> bool:
        required = {"html", "head", "title", "body", "h1", "h2", "table", "th", "td"}
        return not self.invalid and self.doctype == 1 and not self.stack and required <= self.tags and self.evidence and self.headings == list(_sections) and bool("".join(self.title).strip()) and (not self.formula or "math" in self.tags)


def _active_attributes(attrs) -> bool:
    return any(name.startswith("on") or _ACTIVE_URI.match((value or "").lstrip()) for name, value in attrs)


_sections = ("Research question", "Conclusions", "Evidence and methods", "Limitations and gaps")
_void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_MATHML = "http://www.w3.org/1998/Math/MathML"
_MATH_ELEMENTS = {"math", "mrow", "mi", "mn", "mo", "mtext", "mspace", "mphantom", "msup", "msub", "msubsup", "mfrac", "msqrt", "mroot", "mover", "munder", "munderover", "mtable", "mtr", "mtd", "mstyle", "mpadded", "menclose"}
_MATH_ATTRIBUTES = {"display", "mathvariant", "mathsize", "mathcolor", "mathbackground", "scriptlevel", "displaystyle", "accent", "accentunder", "stretchy", "fence", "form", "separator", "lspace", "rspace", "symmetric", "largeop", "movablelimits", "minsize", "maxsize", "width", "height", "depth", "voffset", "linethickness", "bevelled", "numalign", "denomalign", "columnalign", "rowalign", "columnspacing", "rowspacing", "columnlines", "rowlines", "framespacing", "equalrows", "equalcolumns", "side", "minlabelspacing", "notation", "open", "close", "separators", "linebreak"}
_MATH_URI = re.compile(r"(?i)\b(?:data|javascript|vbscript|file|mailto):|\b[a-z][a-z0-9+.-]{1,31}://|\bwww\.|url\(")


def _safe_mathml(value: str) -> bool:
    if not isinstance(value, str) or "<!" in value or "<?" in value:
        return False
    root = ElementTree.fromstring(value)
    return _math_tree_safe(root) and not any(_unsafe_math_text(text) for text in root.itertext())


def _math_tree_safe(root) -> bool:
    return all(_math_element_safe(element) for element in root.iter())


def _math_element_safe(element) -> bool:
    namespace, _, tag = element.tag.rpartition("}")
    return namespace == f"{{{_MATHML}" and tag in _MATH_ELEMENTS and all(_math_attribute_safe(key, value) for key, value in element.attrib.items())


def _math_attribute_safe(key: str, value: str) -> bool:
    return key in _MATH_ATTRIBUTES and not _unsafe_math_attribute(value)


def _unsafe_math_text(value: str) -> bool:
    return not isinstance(value, str) or _MATH_URI.search(value) is not None


def _unsafe_math_attribute(value: str) -> bool:
    return not isinstance(value, str) or ":" in value or "url(" in value.lower()
