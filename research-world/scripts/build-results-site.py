#!/usr/bin/env python3
"""Build the Q001-Q125 contest results static site from evidence/contest-2026/all/.

Usage (deps already in pyproject: markdown, pyyaml):
    cd research-world && uv run python scripts/build-results-site.py [--src DIR] [--out DIR]

Output layout under dist/results-site/:
    index.html          dashboard: 125 rows, filter by qid / terminal / domain
    q001/ .. q125/      one page per question: summary, candidate text, audit, sources
    audit-*/            the 5 audit reports, verbatim
    run/                run.md terminal ledger, verbatim

Publish to GitHub Pages (site is served at /research-world/):
    uv run python scripts/build-results-site.py
    git worktree add --detach /tmp/rw-ghpages origin/gh-pages
    rsync -a --delete dist/results-site/ /tmp/rw-ghpages/
    (cd /tmp/rw-ghpages && git add -A && git commit -m "publish: results site" && git push origin gh-pages)
    git worktree remove /tmp/rw-ghpages
First-time Pages enable:
    gh api -X POST repos/LittleDrinks/research-world/pages -f source[branch]=gh-pages -f source[path]=/
"""

import argparse
import html
import re
import shutil
from pathlib import Path

import markdown
import yaml

MD_KW = {"extensions": ["tables", "fenced_code"]}
SITE_TITLE = "Q001–Q125 结果站"
REPO_URL = "https://github.com/LittleDrinks/research-world"


def esc(value):
    return html.escape(str(value), quote=True)


def scalar_value(raw):
    """Parse a frontmatter scalar; keep the raw string if it is not valid YAML."""
    try:
        return yaml.safe_load(raw.strip())
    except yaml.YAMLError:
        return raw.strip()


def parse_loose_fm(fm_text):
    """Line-based frontmatter fallback: key/value scalars, list items as strings or dicts."""
    data, current_list, current_item = {}, None, None
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        top = re.match(r"^([\w-]+):(.*)$", line)
        item = re.match(r"^\s*-\s+(.*)$", line)
        sub = re.match(r"^\s+([\w-]+):(.*)$", line)
        if top:
            key, raw = top.group(1), top.group(2)
            current_item = None
            if raw.strip():
                data[key] = scalar_value(raw)
            else:
                current_list = data.setdefault(key, [])
        elif item and current_list is not None:
            m = re.match(r"^([\w-]+):(.*)$", item.group(1))
            if m:
                current_item = {m.group(1): scalar_value(m.group(2))}
                current_list.append(current_item)
            else:
                current_item = None
                current_list.append(scalar_value(item.group(1)))
        elif sub and current_item is not None:
            current_item[sub.group(1)] = scalar_value(sub.group(2))
    return data


def read_doc(path):
    """Return (frontmatter dict, body text) for one evidence markdown file."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        try:
            return yaml.safe_load(fm) or {}, body.strip()
        except yaml.YAMLError:
            return parse_loose_fm(fm), body.strip()
    return {}, text


def fix_table_spacing(text):
    """Insert a blank line before tables that directly follow a paragraph."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        prev = out[-1] if out else ""
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        is_table_head = re.match(r"^\s*\|[^|]*\|", line)
        nxt_is_sep = re.match(r"^\s*\|[\s:|-]+\|?\s*$", nxt) and "-" in nxt
        if is_table_head and nxt_is_sep and prev.strip() and not prev.lstrip().startswith("|"):
            out.append("")
        out.append(line)
    return "\n".join(out)


def render_md(text):
    return markdown.markdown(fix_table_spacing(text), **MD_KW)


def render_inline(text):
    """Render a table cell (inline markdown such as `code`) without the <p> wrapper."""
    return re.sub(r"^<p>(.*)</p>$", r"\1", render_md(str(text)).strip(), flags=re.S)


def q_table_rows(body):
    """Extract rows of project tables keyed by qid (handles |q001| and | q001 | styles)."""
    rows = {}
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if re.fullmatch(r"q\d+", cells[0]):
            rows[cells[0]] = cells
    return rows


def badge(terminal):
    return f'<span class="badge {esc(terminal)}">{esc(terminal)}</span>'


def load_audits(src):
    audits = []
    for path in sorted(src.glob("audit-*.md")):
        meta, body = read_doc(path)
        audits.append({"slug": path.stem, "meta": meta,
                       "html": render_md(body), "rows": q_table_rows(body)})
    return audits


def load_questions(src, index_rows, audit_by_q):
    questions = []
    for path in sorted(src.glob("q*.md")):
        meta, body = read_doc(path)
        qid = path.stem
        row = index_rows.get(qid, ["", "", "", "", ""])
        questions.append({
            "qid": qid, "domain": row[1], "question": row[2],
            "terminal": row[3], "summary": row[4],
            "meta": meta, "html": render_md(body),
            "audit": audit_by_q.get(qid),
        })
    return questions


def load_corpus(src):
    index_meta, index_body = read_doc(src / "index.md")
    audits = load_audits(src)
    audit_by_q = {qid: (a, cells) for a in audits for qid, cells in a["rows"].items()}
    index_rows = q_table_rows(index_body)
    questions = load_questions(src, index_rows, audit_by_q)
    run_meta, run_body = read_doc(src / "run.md")
    run = {"meta": run_meta, "html": render_md(run_body)}
    timepoint = str(max((a["meta"].get("audited_at", "") for a in audits)))[:10]
    return {"index_meta": index_meta, "index_body": index_body, "audits": audits,
            "questions": questions, "run": run, "timepoint": timepoint}


def footer_html(index_meta, timepoint):
    counts = ", ".join(f"{k} {index_meta.get(k, 0)}"
                       for k in ("completed", "partial", "waiting_human", "failed"))
    return (f'数据源 <code>evidence/contest-2026/all/</code> · 数据生成时点 {esc(timepoint)} · '
            f'全量保留失败与缺口（{counts}） · '
            f'<a href="{REPO_URL}">LittleDrinks/research-world</a>')


def page_html(title, root, nav, body, footer):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {SITE_TITLE}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
{nav}
<main>
{body}
</main>
<footer>{footer}</footer>
</body>
</html>
"""


def board_row_html(q):
    return (f'<tr data-qid="{q["qid"]}" data-terminal="{esc(q["terminal"])}" '
            f'data-domain="{esc(q["domain"])}">'
            f'<td data-label="题号">{q["qid"]}</td>'
            f'<td data-label="领域">{esc(q["domain"])}</td>'
            f'<td data-label="问题">{esc(q["question"])}</td>'
            f'<td data-label="终态">{badge(q["terminal"])}</td>'
            f'<td data-label="结论">{esc(q["summary"])}</td>'
            f'<td data-label="链接"><a href="{q["qid"]}/">打开 →</a></td></tr>')


def dashboard_filters(terminals, domains):
    t_opts = "".join(f'<option value="{esc(t)}">{esc(t)}</option>' for t in terminals)
    d_opts = "".join(f'<option value="{esc(d)}">{esc(d)}</option>' for d in domains)
    return (f'<div class="filters">'
            f'<input id="f-qid" type="search" placeholder="题号，如 q042" aria-label="按题号筛选">'
            f'<select id="f-terminal" aria-label="按终态筛选">'
            f'<option value="">终态：全部</option>{t_opts}</select>'
            f'<select id="f-domain" aria-label="按领域筛选">'
            f'<option value="">领域：全部</option>{d_opts}</select>'
            f'<span id="match-count"></span></div>')


def aux_links_html(run, audits):
    links = ['<a href="run/">run.md（终态账本）</a>']
    links += [f'<a href="{a["slug"]}/">{a["slug"]}</a>' for a in audits]
    return '<nav class="aux">' + " · ".join(links) + "</nav>"


def dashboard_body(corpus):
    meta, questions = corpus["index_meta"], corpus["questions"]
    terminals = sorted({q["terminal"] for q in questions})
    domains = sorted({q["domain"] for q in questions})
    rows = "\n".join(board_row_html(q) for q in questions)
    count_line = (f'{meta.get("projects", len(questions))} 题 · '
                  + " · ".join(f'{k} {meta.get(k, 0)}' for k in
                               ("completed", "partial", "waiting_human", "failed")))
    gist = corpus["index_body"].split("## 终态口径", 1)
    scope = "<section>" + render_md("## 终态口径" + gist[1]) + "</section>" if len(gist) == 2 else ""
    return (f'<h1>Q001–Q125 结论看板</h1><p class="counts">{esc(count_line)}</p>'
            + dashboard_filters(terminals, domains)
            + '<div class="board-wrap"><table class="board"><thead><tr>'
              '<th>题号</th><th>领域</th><th>问题</th><th>终态</th><th>结论</th><th>链接</th></tr></thead>'
              f'<tbody>{rows}</tbody></table></div>'
            + aux_links_html(corpus["run"], corpus["audits"]) + scope
            + "<script>" + DASHBOARD_JS + "</script>")


def fmt_value(value):
    if isinstance(value, list):
        return "; ".join(esc(v) for v in value)
    return esc(value)


def source_html(s):
    if isinstance(s, str):
        return f"<li>{esc(s)}</li>"
    title_key = next((k for k in ("title", "id", "authority", "organization", "publisher")
                      if s.get(k)), None)
    head = fmt_value(s[title_key]) if title_key else "source"
    if s.get("url"):
        head = f'<a href="{esc(s["url"])}">{head}</a>'
    fields = " · ".join(f"{esc(k)}: {fmt_value(v)}" for k, v in s.items()
                        if k not in ("title", "url") and v not in ("", None, []))
    return f"<li>{head}" + (f" — {fields}" if fields else "") + "</li>"


def sources_section(meta):
    items = [source_html(s) for s in (meta.get("sources") or [])]
    if not items:
        return ""
    return '<section id="sources"><h2>证据链（frontmatter sources）</h2><ul class="sources">' \
           + "".join(items) + "</ul></section>"


def audit_section(audit):
    a, cells = audit
    _, terminal, conclusion, assessment, reason = cells
    audited = esc(a["meta"].get("audited_at", ""))
    return (f'<section id="audit"><h2>独立审计（<a href="../{a["slug"]}/">{a["slug"]}</a>）</h2>'
            f'<p class="meta">审计模型 {esc(a["meta"].get("runtime_model", ""))} · {audited}</p>'
            f'<p>审计终态 {badge(terminal)}</p>'
            f'<p><strong>结论：</strong>{render_inline(conclusion)}</p>'
            f'<p><strong>证据评估：</strong>{render_inline(assessment)}</p>'
            f'<p><strong>判定理由：</strong>{render_inline(reason)}</p></section>')


def question_nav(root, qid, prev_qid, next_qid):
    prev = f'<a href="../{prev_qid}/">{prev_qid}</a> · ' if prev_qid else ""
    nxt = f' · <a href="../{next_qid}/">{next_qid}</a>' if next_qid else ""
    return f'<nav class="top"><a href="{root}">← 总看板</a> · {prev}<strong>{qid}</strong>{nxt}</nav>'


def question_body(q):
    meta = q["meta"]
    header = (f'<p class="meta">{esc(q["domain"])} · 终态 {badge(q["terminal"])} · '
              f'模型 {esc(meta.get("model", ""))} · verified {esc(meta.get("verified", ""))}')
    if meta.get("executed"):
        header += f' · executed {esc(meta["executed"])}'
    header += "</p>"
    summary = f'<blockquote class="summary"><strong>结论摘要：</strong>{esc(q["summary"])}</blockquote>'
    return (f'<h1><code>{q["qid"]}</code> {esc(q["question"])}</h1>{header}{summary}'
            f'<section><h2>作者候选结论（原文）</h2>{q["html"]}</section>'
            + (audit_section(q["audit"]) if q["audit"] else "")
            + sources_section(meta))


def report_body(title, meta, body_html):
    fields = " · ".join(f'{k} {esc(v)}' for k, v in meta.items() if k != "artifact")
    return (f'<h1>{esc(title)}</h1><p class="meta">{fields}</p>'
            f'<div class="prose">{body_html}</div>')


def build_dashboard(corpus, out, footer):
    body = dashboard_body(corpus)
    write_page(out, "index.html", "总看板", "", "", body, footer)


def build_questions(corpus, out, footer):
    qids = [q["qid"] for q in corpus["questions"]]
    for i, q in enumerate(corpus["questions"]):
        prev_qid = qids[i - 1] if i > 0 else None
        next_qid = qids[i + 1] if i + 1 < len(qids) else None
        nav = question_nav("../", q["qid"], prev_qid, next_qid)
        title = f'{q["qid"]} · {q["question"]}'
        write_page(out, f'{q["qid"]}/index.html', title, "../", nav,
                   question_body(q), footer)


def build_reports(corpus, out, footer):
    for a in corpus["audits"]:
        body = report_body(a["slug"], a["meta"], a["html"])
        nav = f'<nav class="top"><a href="../">← 总看板</a> · <strong>{a["slug"]}</strong></nav>'
        write_page(out, f'{a["slug"]}/index.html', a["slug"], "../", nav, body, footer)
    run = corpus["run"]
    body = report_body("run.md（终态账本）", run["meta"], run["html"])
    nav = '<nav class="top"><a href="../">← 总看板</a> · <strong>run</strong></nav>'
    write_page(out, "run/index.html", "run.md", "../", nav, body, footer)


def write_page(out, rel, title, root, nav, body, footer):
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page_html(title, root, nav, body, footer), encoding="utf-8")


def build(src, out):
    corpus = load_corpus(src)
    footer = footer_html(corpus["index_meta"], corpus["timepoint"])
    build_dashboard(corpus, out, footer)
    build_questions(corpus, out, footer)
    build_reports(corpus, out, footer)
    (out / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    pages = sum(1 for _ in out.rglob("index.html"))
    print(f"built {pages} pages from {src} into {out}")


STYLE_CSS = r"""
:root { --fg: #1a1a1a; --muted: #5f6368; --line: #dadce0; --bg: #fff; }
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto,
  "PingFang SC", "Microsoft YaHei", sans-serif; color: var(--fg);
  background: var(--bg); line-height: 1.65; }
nav.top, nav.aux { max-width: 960px; margin: 0 auto; padding: .8rem 1rem 0; font-size: .92rem; }
nav.aux { padding: .4rem 1rem; color: var(--muted); }
main { max-width: 960px; margin: 0 auto; padding: 1rem; }
footer { max-width: 960px; margin: 0 auto; padding: 1rem; color: var(--muted);
  font-size: .82rem; border-top: 1px solid var(--line); margin-top: 2rem; }
h1 { font-size: 1.5rem; line-height: 1.3; }
h2 { font-size: 1.15rem; margin-top: 1.6rem; border-bottom: 1px solid var(--line); padding-bottom: .2rem; }
code { background: #f1f3f4; padding: .05rem .3rem; border-radius: 4px; font-size: .9em; }
blockquote.summary { margin: 1rem 0; padding: .6rem 1rem; background: #f8f9fa;
  border-left: 4px solid var(--line); }
p.meta { color: var(--muted); font-size: .9rem; }
.counts { color: var(--muted); }
.badge { display: inline-block; padding: .05rem .5rem; border-radius: 999px;
  font-size: .82rem; white-space: nowrap; }
.badge.completed { background: #e6f4ea; color: #137333; }
.badge.partial { background: #fef7e0; color: #b06000; }
.badge.waiting_human { background: #e8f0fe; color: #1967d2; }
.badge.failed { background: #fce8e6; color: #c5221f; }
.filters { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center;
  margin: 1rem 0; position: sticky; top: 0; background: var(--bg); padding: .4rem 0;
  border-bottom: 1px solid var(--line); z-index: 1; }
.filters input, .filters select { padding: .35rem .5rem; border: 1px solid var(--line);
  border-radius: 6px; font-size: .95rem; background: var(--bg); color: var(--fg); }
#match-count { color: var(--muted); font-size: .85rem; }
.board-wrap { overflow-x: auto; }
table.board { border-collapse: collapse; width: 100%; }
table.board th, table.board td { border: 1px solid var(--line); padding: .45rem .6rem;
  vertical-align: top; text-align: left; font-size: .92rem; }
table.board th { background: #f8f9fa; }
table.board td[data-label="结论"] { min-width: 24rem; }
.prose table { border-collapse: collapse; width: 100%; display: block; overflow-x: auto; }
.prose th, .prose td { border: 1px solid var(--line); padding: .4rem .55rem;
  vertical-align: top; font-size: .9rem; text-align: left; }
.prose img { max-width: 100%; }
ul.sources { padding-left: 1.2rem; }
ul.sources li { margin: .3rem 0; word-break: break-word; }
@media (max-width: 720px) {
  table.board thead { display: none; }
  table.board tr { display: block; border: 1px solid var(--line); border-radius: 8px;
    margin: .6rem 0; padding: .4rem .6rem; }
  table.board td { display: block; border: none; padding: .18rem 0; }
  table.board td[data-label="结论"] { min-width: 0; }
  table.board td::before { content: attr(data-label) "："; font-weight: 600;
    color: var(--muted); margin-right: .3rem; }
}
"""

DASHBOARD_JS = """
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr'));
  var fq = document.getElementById('f-qid');
  var ft = document.getElementById('f-terminal');
  var fd = document.getElementById('f-domain');
  var count = document.getElementById('match-count');
  function apply() {
    var q = fq.value.trim().toLowerCase(), t = ft.value, d = fd.value, n = 0;
    rows.forEach(function (r) {
      var ok = (!q || r.dataset.qid.indexOf(q) === 0)
            && (!t || r.dataset.terminal === t)
            && (!d || r.dataset.domain === d);
      r.hidden = !ok;
      if (ok) n++;
    });
    count.textContent = n + ' / ' + rows.length;
  }
  [fq, ft, fd].forEach(function (el) { el.addEventListener('input', apply); });
  apply();
})();
"""


def main():
    parser = argparse.ArgumentParser(description="Build the contest results static site.")
    parser.add_argument("--src", type=Path, default=Path("evidence/contest-2026/all"))
    parser.add_argument("--out", type=Path, default=Path("dist/results-site"))
    args = parser.parse_args()
    if args.out.exists():
        shutil.rmtree(args.out)
    build(args.src, args.out)


if __name__ == "__main__":
    main()
