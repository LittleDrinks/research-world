from __future__ import annotations

from html import escape


def render_html(title: str, projection: dict, assessment: dict) -> bytes:
    facts = assessment["accepted_facts"]
    sources = {source["id"]: source for source in projection["sources"]}
    body = "".join((_facts(facts), _evidence(facts, sources), _figures(projection.get("artifacts", []))))
    return _document(title, body).encode("utf-8")


def _document(title: str, body: str) -> str:
    safe = escape(title)
    return f"<!doctype html><html><head><meta charset=utf-8><title>{safe}</title><style>body{{font:16px system-ui;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:.5rem}}code{{background:#eee;padding:.15rem .3rem}}figure{{border:1px solid #bbb;padding:1rem;margin:1rem 0}}.chart{{height:72px;background:linear-gradient(90deg,#246 0 45%,#6a9 45% 72%,#bd7 72%)}}</style></head><body><h1>{safe}</h1><p>Delivery: validated admitted evidence.</p>{body}</body></html>"


def _facts(facts: list[dict]) -> str:
    rows = "".join(f"<li>{escape(fact['text'])} [{', '.join(map(escape, fact['source_ids']))}]</li>" for fact in facts)
    return f"<h2>Findings</h2><ul>{rows}</ul><h2>Method</h2><pre><code>projection -&gt; validation -&gt; publication</code></pre><p>e^(i*pi) + 1 = 0</p>"


def _evidence(facts: list[dict], sources: dict) -> str:
    ids = sorted({item for fact in facts for item in fact["source_ids"]})
    rows = "".join(f"<tr><td>{escape(key)}</td><td>{escape(str(sources[key].get('source_level', 'unknown')))}</td></tr>" for key in ids)
    return f"<h2>Evidence</h2><table><tr><th>Source</th><th>Level</th></tr>{rows}</table>"


def _figures(artifacts: list[dict]) -> str:
    figures = "".join(f"<figure><div class=chart></div><figcaption>Artifact id: {escape(item['id'])}</figcaption></figure>" for item in artifacts)
    return f"<h2>Artifacts</h2>{figures or '<p>No associated artifacts.</p>'}"
