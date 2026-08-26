from __future__ import annotations

import base64
import re
from html import escape, unescape

from .reporting import contains_restricted_data, evidence_kind, safe_report_text

MAX_EVIDENCE_BYTES = 262144
_ACTIVE_CONTENT = r"<\s*(?:script|iframe|object|embed)\b|\son[a-z]+\s*=|\b(?:javascript|vbscript):"


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
    return {"kind": kind, "text": text} if text else {"kind": "invalid"}


def _chart_display(media_type: str, content: bytes) -> dict:
    encoded = base64.b64encode(content).decode("ascii")
    return {"kind": "chart", "src": f"data:{media_type};base64,{encoded}"}


def render_html(title: str, projection: dict, assessment: dict) -> bytes:
    sources = {source["id"]: source for source in projection["sources"]}
    artifacts = {item["id"]: item for item in projection["artifacts"]}
    body = _question(projection["question"]) + _findings(assessment["accepted_facts"], sources)
    body += _methods(assessment["accepted_facts"], sources, artifacts, projection["claims"])
    body += _limitations(assessment["gaps"])
    return _document(title, body).encode("utf-8")


def validate_html(content: bytes) -> list[dict]:
    text = content.decode("utf-8", errors="replace")
    required = ("<!doctype html>", "</body></html>")
    gaps = [_html_gap("rendered_content_invalid") for value in required if value not in text.lower()]
    if re.search(_ACTIVE_CONTENT, text, re.IGNORECASE):
        gaps.append(_html_gap("active_content_exposed"))
    return gaps + ([_html_gap("sensitive_data_exposed")] if contains_restricted_data(unescape(text), opaque=False) else [])


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
    content = escape(item["display"]["text"])
    return _figure(item, f'<div class="formula" data-artifact="{escape(item["id"])}"><math><mtext>{content}</mtext></math></div>')


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
