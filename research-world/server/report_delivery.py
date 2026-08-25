from __future__ import annotations

from html import escape


def render_html(title: str, projection: dict, assessment: dict) -> bytes:
    sources = {source["id"]: source for source in projection["sources"]}
    artifacts = {item["id"]: item for item in projection["artifacts"]}
    body = _findings(assessment["accepted_facts"], sources)
    body += _evidence(assessment["accepted_facts"], sources)
    body += _evidence_sections(assessment["accepted_facts"], artifacts)
    return _document(title, body).encode("utf-8")


def _document(title: str, body: str) -> str:
    safe = escape(title)
    style = "body{font:16px system-ui;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.5rem}code{background:#eee;padding:.15rem .3rem}"
    return f"<!doctype html><html><head><meta charset=utf-8><title>{safe}</title><style>{style}</style></head><body><h1>{safe}</h1>{body}</body></html>"


def _findings(facts: list[dict], sources: dict) -> str:
    rows = "".join(_finding(fact, sources) for fact in facts)
    return f"<h2>Findings</h2><ul>{rows}</ul>"


def _finding(fact: dict, sources: dict) -> str:
    citations = ", ".join(_citation(sources[source]) for source in fact["source_ids"])
    return f"<li>{escape(fact['text'])} {citations}</li>"


def _citation(source: dict) -> str:
    anchor, title = escape(source["anchor"]), escape(source["title"])
    return f'<a href="#{anchor}">[{title}]</a>'


def _evidence(facts: list[dict], sources: dict) -> str:
    ids = sorted({source for fact in facts for source in fact["source_ids"]})
    rows = "".join(_source_row(sources[source]) for source in ids)
    return f"<h2>Evidence</h2><table><tr><th>Source</th><th>Level</th><th>Checked</th></tr>{rows}</table>"


def _source_row(source: dict) -> str:
    anchor, title = escape(source["anchor"]), escape(source["title"])
    level, checked = escape(source["source_level"]), escape(source["checked_at"])
    return f'<tr id="{anchor}"><td>{title}</td><td>{level}</td><td>{checked}</td></tr>'


def _evidence_sections(facts: list[dict], artifacts: dict) -> str:
    selected = [artifacts[item] for fact in facts for item in fact["artifact_ids"]]
    return _section("Code", selected, _is_code) + _section("Formulas", selected, _is_formula) + _section("Charts", selected, _is_chart)


def _section(name: str, artifacts: list[dict], predicate) -> str:
    items = [artifact for artifact in artifacts if predicate(artifact["media_type"])]
    if not items:
        return f"<h2>{name}</h2><p>No validated {name.lower()} evidence.</p>"
    rows = "".join(f"<li>{escape(item['id'])} ({escape(item['media_type'])})</li>" for item in items)
    return f"<h2>{name}</h2><ul>{rows}</ul>"


def _is_code(media_type: str) -> bool:
    return media_type.startswith("text/x-") or media_type == "text/plain"


def _is_formula(media_type: str) -> bool:
    return media_type in {"application/x-latex", "text/x-tex"}


def _is_chart(media_type: str) -> bool:
    return media_type.startswith("image/")
