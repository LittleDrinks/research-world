#!/usr/bin/env python3
"""Archive paper-like docs references and fixed supplemental sources."""

import argparse
import hashlib
import html
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


REPO = Path(__file__).resolve().parents[3]
DOCS = REPO / "docs"
CORPUS = REPO / "datasets" / "research-kernel-papers"
REFERENCES = CORPUS / "references"
MARKDOWN = CORPUS / "markdown"
MANIFEST = CORPUS / "docs-references.manifest.json"
SUPPLEMENTAL = CORPUS / "issue-139.sources.json"
SCRIPT_PATH = "datasets/research-kernel-papers/scripts/archive_doc_references.py"
SUPPLEMENTAL_PATH = "datasets/research-kernel-papers/issue-139.sources.json"
SUPPLEMENTAL_SOURCE_LIST = "https://github.com/LittleDrinks/research-world/issues/139#issuecomment-5434636802"
URL_RE = re.compile(r"https?://[^\s<>\"`)]*")
TRAILING = ",.;:!?]}'"
RUNTIME_FIELDS = {
    "status",
    "pdf_path",
    "markdown_path",
    "local_path",
    "sha256",
    "failure_stage",
    "failure_reason",
}
WEB_DOC_HOSTS = {
    "code.claude.com",
    "docs.anthropic.com",
    "developers.openai.com",
    "learn.chatgpt.com",
    "moonshotai.github.io",
    "nanopub.net",
    "www.w3.org",
    "www.researchobject.org",
    "a2a-protocol.org",
    "csrc.nist.gov",
    "www.who.int",
}
LICENSE_HOSTS = {"creativecommons.org"}
MODEL_HOSTS = {"huggingface.co"}
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
PRODUCT_HOSTS = {
    "networkx.org",
    "inspect.aisi.org.uk",
    "university.aliyun.com",
    "help.aliyun.com",
    "www.anthropic.com",
    "openai.com",
    "open-design.ai",
    "multica.ai",
    "ccswitch.io",
    "www.conductor.build",
    "x.com",
}
DOI_DOWNLOADS = {
    "doi-10-1038-s41524-020-00406-3": "https://www.nature.com/articles/s41524-020-00406-3.pdf",
    "doi-10-1109-vis47514-2020-00030": "http://xplorestaging.ieee.org/ielx7/9329359/9331017/09331264.pdf?arnumber=9331264",
    "doi-10-18653-v1-2022-findings-emnlp-347": "https://aclanthology.org/2022.findings-emnlp.347.pdf",
    "doi-10-1126-sciadv-adn5290": "https://www.science.org/doi/pdf/10.1126/sciadv.adn5290",
}


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "li" and attributes.get("id", "").startswith("ref-"):
            self.current = {"id": attributes["id"], "text": [], "hrefs": []}
        if self.current is not None and tag == "a" and attributes.get("href"):
            self.current["hrefs"].append(attributes["href"])

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)

    def handle_endtag(self, tag):
        if tag != "li" or self.current is None:
            return
        self.current["text"] = " ".join(" ".join(self.current["text"]).split())
        self.items.append(self.current)
        self.current = None


class MarkdownSnapshotParser(HTMLParser):
    """Keep readable document content while dropping navigation and scripts."""

    SKIP_TAGS = {"aside", "footer", "form", "header", "nav", "script", "style", "svg"}
    HEADING_TAGS = {f"h{level}": level for level in range(1, 7)}
    BLOCK_TAGS = {
        "blockquote",
        "dd",
        "div",
        "dt",
        "li",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.depth = 0
        self.scope_depth = None
        self.main_seen = False
        self.skip_depth = 0
        self.blocks = []
        self.buffer = []
        self.heading = None
        self.list_item = False
        self.pre = False

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        if self.skip_depth or tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag == "main":
            self.main_seen = True
            self.active = True
            self.scope_depth = self.depth
            self.blocks = []
            self.buffer = []
            return
        if tag == "body" and not self.main_seen:
            self.active = True
            self.scope_depth = self.depth
        if self.active:
            self.open_tag(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            self.depth -= 1
            return
        if self.active:
            self.close_tag(tag)
            if tag == "main" and self.main_seen:
                self.flush()
                self.active = False
            if tag == "body" and not self.main_seen:
                self.flush()
                self.active = False
        self.depth -= 1

    def handle_data(self, data):
        if self.active and not self.skip_depth:
            value = data if self.pre else " ".join(data.split())
            self.buffer.append(value if self.pre else f" {value} ")

    def open_tag(self, tag):
        if tag in self.HEADING_TAGS:
            self.flush()
            self.heading = self.HEADING_TAGS[tag]
        elif tag == "li":
            self.flush()
            self.list_item = True
        elif tag == "pre":
            self.flush()
            self.pre = True
            self.blocks.append("```")
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag in self.HEADING_TAGS:
            self.flush()
            self.heading = None
        elif tag == "li":
            self.flush()
            self.list_item = False
        elif tag == "pre":
            self.pre = False
            self.flush()
            self.blocks.append("```")
        elif tag in self.BLOCK_TAGS:
            self.flush()

    def flush(self):
        raw = "".join(self.buffer)
        self.buffer = []
        value = raw.strip("\n") if self.pre else " ".join(raw.split())
        if not value:
            return
        if self.heading:
            value = f"{'#' * self.heading} {value}"
        elif self.list_item:
            value = f"- {value}"
        self.blocks.append(value)

    def render(self):
        self.flush()
        return "\n\n".join(block for block in self.blocks if block.strip()).strip()


def clean_url(value):
    return value.rstrip(TRAILING)


def doc_files():
    return sorted(
        path
        for path in DOCS.rglob("*")
        if path.is_file() and path.suffix in {".md", ".html", ".json"}
    )


def source_kind(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    path = parsed.path
    rules = (
        (host == "arxiv.org" and re.search(r"/(abs|pdf)/\d{4}\.\d{4,5}(?:v\d+)?$", path), "arxiv"),
        (host == "pmc.ncbi.nlm.nih.gov" and re.fullmatch(r"/articles/PMC\d+/?", path), "pmc"),
        (host == "aclanthology.org" and re.fullmatch(r"/[\w.-]+/?", path), "acl"),
        (host == "proceedings.iclr.cc" and "/paper_files/paper/" in path, "iclr"),
        (host == "ceur-ws.org" and path.lower().endswith(".pdf"), "ceur"),
        (host == "joelchan.me" and path.lower().endswith(".pdf"), "joelchan"),
        (host == "doi.org" and path.startswith("/10."), "doi"),
        (host in {"nature.com", "www.nature.com"} and re.fullmatch(r"/articles/s\d+-\d+-[\w-]+(?:\.pdf)?", path), "nature"),
        (host == "iris.who.int" and "/server/api/core/bitstreams/" in path, "who"),
    )
    return next((kind for matched, kind in rules if matched), None)


def canonical_id(url, kind):
    path = urlparse(url).path.rstrip("/")
    if kind == "arxiv": return f"arxiv-{re.sub(r'v\d+$', '', path.rsplit('/', 1)[-1].removesuffix('.pdf'))}"
    if kind == "pmc": return f"pmc-{path.split('/')[-1].removeprefix('PMC')}".lower()
    if kind == "acl": return f"acl-{path.strip('/')}".lower()
    if kind == "iclr":
        digest = path.rsplit("/", 1)[-1].split("-", 1)[0]
        return f"iclr-2025-{digest[:12]}"
    if kind == "ceur": return "ceur-vol-1155-paper-07"
    if kind == "joelchan": return "joelchan-discourse-graphs"
    if kind == "doi":
        doi = path.removeprefix("/").lower()
        return "doi-" + re.sub(r"[^a-z0-9]+", "-", doi).strip("-")
    if kind == "nature": return "nature-" + path.split("/articles/", 1)[1].removesuffix(".pdf")
    if kind == "who": return "who-9789240062702"
    raise ValueError(f"unsupported source kind: {kind}")


def context_title(lines, line_number, url):
    line = re.sub(r"<[^>]+>", " ", lines[line_number - 1]).replace(url, " ")
    match = re.search(r"title:\s*[\"']?(.+?)[\"']?\s*$", line, re.I)
    if match:
        return match.group(1).strip(" \"'")
    return " ".join(line.split()).strip(" -:[]()")[:180] or None


def exclusion_reason(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in LOCAL_HOSTS:
        return "本地服务地址"
    if host in LICENSE_HOSTS:
        return "许可证页面"
    if host in MODEL_HOSTS:
        return "模型或数据仓库"
    if host == "github.com" or host.endswith(".github.com"):
        return "代码仓库或 Issue"
    if "/issues/" in parsed.path:
        return "Issue"
    if host in WEB_DOC_HOSTS:
        return "纯网页文档"
    if host in PRODUCT_HOSTS:
        return "产品页或其他非论文网页"
    if host.endswith(".githubusercontent.com") or host == "raw.githubusercontent.com":
        return "代码仓库资产"
    return None


def scan_line(line, location, sources, excluded):
    for match in URL_RE.finditer(line):
        url = clean_url(match.group(0))
        kind = source_kind(url)
        if kind is None:
            reason = exclusion_reason(url)
            if reason:
                excluded.setdefault(url, {"url": url, "locations": [], "reason": reason})
                excluded[url]["locations"].append(location)
            continue
        key = canonical_id(url, kind)
        item = sources.setdefault(key, {"id": key, "kind": kind, "source_urls": [], "locations": [], "title": None})
        if url not in item["source_urls"]:
            item["source_urls"].append(url)
        item["locations"].append(location)
        item["title"] = item["title"] or context_title([line], 1, url)


def scan_doc(path, sources, excluded):
    relative = path.relative_to(REPO).as_posix()
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        scan_line(line, {"path": relative, "line": number}, sources, excluded)


def extract_sources():
    sources = {}
    excluded = {}
    for path in doc_files():
        scan_doc(path, sources, excluded)
    return list(sources.values()), list(excluded.values()), unresolved_citations()


def unresolved_citations():
    path = DOCS / "design-explainer.html"
    parser = ReferenceParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return [unresolved_record(item) for item in parser.items if not item["hrefs"]]


def unresolved_record(item):
    return {
        "id": f"design-{item['id']}",
        "citation": item["text"],
        "source_url": None,
        "status": "unresolved",
        "failure_stage": "source-discovery",
        "failure_reason": "设计说明只保留 Zotero 条目或题名，没有可下载的原 URL",
        "retry_command": f"补录原 URL 后执行: {retry_base_command()}",
        "locations": [{"path": "docs/design-explainer.html", "anchor": item["id"]}],
    }


def download_url(item):
    kind = item["kind"]
    source = item["source_urls"][0]
    parsed = urlparse(source)
    if kind == "arxiv": return f"https://arxiv.org/pdf/{parsed.path.rsplit('/', 1)[-1].removesuffix('.pdf')}"
    if kind == "pmc":
        if item["id"] == "pmc-4530550":
            return "https://europepmc.org/articles/PMC4530550?pdf=render"
        return "https://pmc.ncbi.nlm.nih.gov/articles/PMC4536833/pdf/nihms486779.pdf"
    if kind == "acl": return source.rstrip("/") + ".pdf"
    if kind == "iclr": return re.sub(r"/hash/([^/]+)-Abstract-Conference\.html$", r"/file/\1-Paper-Conference.pdf", source)
    if kind == "doi": return DOI_DOWNLOADS.get(item["id"], source)
    if kind == "nature": return source if source.endswith(".pdf") else source + ".pdf"
    return source


def retry_base_command():
    return f"python3 {SCRIPT_PATH} --supplemental {SUPPLEMENTAL_PATH}"


def retry_command(item_id):
    return f"{retry_base_command()} --id {item_id}"


def base_record(item):
    return {
        **item,
        "origin": "docs",
        "source_url": item["source_urls"][0],
        "version": None,
        "format": "pdf+markdown",
        "title": item.get("title") or item["id"],
        "download_url": download_url(item),
        "status": "pending",
        "pdf_path": None,
        "markdown_path": None,
        "sha256": None,
        "failure_stage": None,
        "failure_reason": None,
        "retry_command": retry_command(item["id"]),
    }


def supplemental_record(item):
    record = {
        **item,
        "origin": "issue-139",
        "kind": "fixed-source" if item["format"] == "source" else "webpage",
        "source_urls": [item["source_url"]],
        "locations": [{"issue": 139}],
        "status": "pending",
        "sha256": None,
        "failure_stage": None,
        "failure_reason": None,
        "retry_command": retry_command(item["id"]),
    }
    if item["local_path"].endswith(".md"):
        record["markdown_path"] = item["local_path"]
    return record


def load_supplemental(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [supplemental_record(item) for item in data]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_pdf(path):
    if not path.is_file() or path.stat().st_size <= 1024:
        return False
    with path.open("rb") as stream:
        return stream.read(4) == b"%PDF"


def nonempty(path):
    return path.is_file() and path.stat().st_size > 0 and bool(path.read_text(encoding="utf-8", errors="replace").strip())


def curl_to(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    command = [
        "curl", "-sS", "-L", "--fail", "--retry", "5", "--retry-all-errors", "--max-time", "180",
        "-A", "ai4sci-issue-138/1.0", url, "-o", str(partial),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, OSError) as error:
        output = getattr(error, "stderr", "") or str(error)
        partial.unlink(missing_ok=True)
        raise RuntimeError(" ".join(output.split())[-1000:]) from error
    if not partial.is_file() or partial.stat().st_size == 0:
        partial.unlink(missing_ok=True)
        raise RuntimeError("下载响应为空")
    partial.replace(target)


def download_pdf(url, target):
    curl_to(url, target)
    if valid_pdf(target):
        return
    with target.open("rb") as stream:
        header = stream.read(120).decode("utf-8", errors="replace")
    target.unlink(missing_ok=True)
    raise RuntimeError(f"下载响应不是有效 PDF，响应头片段: {header!r}")


def convert_pdf(pdf, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="issue138-odl-") as output_dir:
        command = ["opendataloader-pdf", "-q", "-o", output_dir, "-f", "markdown", "--image-output", "off", str(pdf)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, OSError) as error:
            output = getattr(error, "stderr", "") or str(error)
            raise RuntimeError(" ".join(output.split())[-1000:]) from error
        outputs = sorted(Path(output_dir).glob("*.md"))
        if len(outputs) != 1 or not nonempty(outputs[0]):
            raise RuntimeError("opendataloader-pdf 未生成非空 Markdown")
        write_atomic(target, normalize_markdown(outputs[0].read_text(encoding="utf-8", errors="replace")))


def ensure_pdf(record, pdf, relative):
    if not valid_pdf(pdf):
        download_pdf(record["download_url"], pdf)
    record.update(pdf_path=relative, sha256=sha256(pdf))


def ensure_markdown(pdf, markdown, relative):
    if not nonempty(markdown):
        convert_pdf(pdf, markdown)
    if not nonempty(markdown):
        raise RuntimeError("Markdown 为空")
    return relative


def process_pdf(record):
    pdf_relative = f"datasets/research-kernel-papers/references/{record['id']}.pdf"
    markdown_relative = f"datasets/research-kernel-papers/markdown/{record['id']}.md"
    pdf = REPO / pdf_relative
    markdown = REPO / markdown_relative
    try:
        ensure_pdf(record, pdf, pdf_relative)
    except Exception as error:
        record.update(status="failed", failure_stage="download", failure_reason=str(error))
        return record
    try:
        record["markdown_path"] = ensure_markdown(pdf, markdown, markdown_relative)
        record["status"] = "ready"
    except Exception as error:
        record.update(status="failed", failure_stage="convert", failure_reason=str(error))
    return record


def html_title(source):
    match = re.search(r"<title[^>]*>(.*?)</title>", source, re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", match.group(1)) if match else ""
    return " ".join(html.unescape(value).split())


def normalize_markdown(source):
    lines = [line.rstrip() for line in source.splitlines()]
    return "\n".join(lines).rstrip("\n") + "\n"


def html_snapshot(source):
    parser = MarkdownSnapshotParser()
    parser.feed(source)
    body = parser.render()
    title = html_title(source)
    if title and not re.search(r"^#\s+", body, re.M):
        body = f"# {title}\n\n{body}"
    if len(body.strip()) < 200:
        raise RuntimeError("网页正文解析后过短，未生成可审阅 Markdown")
    return body.strip() + "\n"


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(content, encoding="utf-8")
    partial.replace(path)


def download_supplemental(record, target):
    if not nonempty(target):
        curl_to(record["download_url"], target)


def fetch_webpage(record):
    with tempfile.TemporaryDirectory(prefix="issue138-web-") as directory:
        source = Path(directory) / "source.html"
        curl_to(record["download_url"], source)
        return source.read_text(encoding="utf-8", errors="replace")


def mark_snapshot_ready(record, target):
    if not nonempty(target):
        raise RuntimeError("快照为空")
    record.update(status="ready", sha256=sha256(target))


def finish_webpage(record, target, source):
    try:
        write_atomic(target, html_snapshot(source))
        mark_snapshot_ready(record, target)
    except Exception as error:
        record.update(status="failed", failure_stage="snapshot", failure_reason=str(error))
    return record


def process_webpage(record, target):
    if nonempty(target):
        mark_snapshot_ready(record, target)
        return record
    try:
        source = fetch_webpage(record)
    except Exception as error:
        record.update(status="failed", failure_stage="download", failure_reason=str(error))
        return record
    return finish_webpage(record, target, source)


def process_supplemental(record):
    target = REPO / record["local_path"]
    if record["format"] == "webpage":
        return process_webpage(record, target)
    try:
        if record["format"] != "source":
            raise RuntimeError(f"不支持的补充来源格式: {record['format']}")
        download_supplemental(record, target)
        mark_snapshot_ready(record, target)
    except Exception as error:
        record.update(status="failed", failure_stage="download", failure_reason=str(error))
        return record
    return record


def process(record):
    return process_pdf(record) if record["origin"] == "docs" else process_supplemental(record)


def read_previous(path):
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload.get("entries", [])}


def reset_record(record):
    record.update(status="pending", sha256=None, failure_stage=None, failure_reason=None)
    if record["origin"] == "docs":
        record.update(pdf_path=None, markdown_path=None)


def merge_previous(records, previous, selected):
    for record in records:
        old = previous.get(record["id"])
        if old:
            for field in RUNTIME_FIELDS:
                if field in old:
                    record[field] = old[field]
        if record["id"] in selected:
            reset_record(record)


def write_manifest(path, records, excluded, unresolved):
    payload = {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "included": "docs 中指向论文、会议论文、学术文章或研究报告的来源，以及 #139 指定的一手固定源码和网页规范",
            "excluded": "产品页、代码仓库、Issue、纯网页文档和社交媒体（#139 明确指定的固定来源除外）",
            "pdf_conversion": "opendataloader-pdf -f markdown --image-output off",
            "web_snapshot_conversion": "Python stdlib html.parser -> Markdown",
            "html_output": False,
        },
        "inputs": {
            "docs_root": "docs",
            "supplemental": SUPPLEMENTAL_PATH,
            "supplemental_issue": 139,
            "supplemental_source_list": SUPPLEMENTAL_SOURCE_LIST,
        },
        "audit_exceptions": [
            {
                "path": "datasets/research-kernel-papers/snapshots/issue-139/pi-compaction.md",
                "status": "expected-source-whitespace",
                "reason": "固定 commit 的原始 Markdown 保留两处空行尾空格；SHA-256 按原始快照校验，.gitattributes 仅免除 diff whitespace 告警。",
            },
        ],
        "entries": records,
        "excluded_sources": excluded,
        "unresolved_citations": unresolved,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def collect_records(supplemental_path):
    discovered, excluded, unresolved = extract_sources()
    records = [base_record(item) for item in discovered]
    records.extend(load_supplemental(supplemental_path))
    records.sort(key=lambda item: item["id"])
    return records, excluded, unresolved


def selected_ids(records, requested):
    all_ids = {item["id"] for item in records}
    selected = set(requested or all_ids)
    if not selected <= all_ids:
        missing = ", ".join(sorted(selected - all_ids))
        raise SystemExit(f"未知归档 ID: {missing}")
    return selected


def run_selected(path, records, excluded, unresolved, selected):
    write_manifest(path, records, excluded, unresolved)
    for record in records:
        if record["id"] not in selected:
            continue
        process(record)
        write_manifest(path, records, excluded, unresolved)
        print(f"{record['id']}\t{record['status']}")
    pending = [item["id"] for item in records if item["id"] in selected and item["status"] == "pending"]
    if pending:
        raise SystemExit(f"未处理条目: {', '.join(pending)}")


def print_summary(records, excluded, unresolved):
    ready = sum(item["status"] == "ready" for item in records)
    failed = sum(item["status"] == "failed" for item in records)
    summary = {"entries": len(records), "ready": ready, "failed": failed, "excluded": len(excluded), "unresolved": len(unresolved)}
    print(json.dumps(summary, ensure_ascii=False))
    return failed


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", action="append", dest="ids", help="只重试指定的归档 ID，可重复")
    parser.add_argument("--manifest", type=Path, default=MANIFEST, help="manifest 输出路径")
    parser.add_argument("--supplemental", type=Path, default=SUPPLEMENTAL, help="固定补充来源 JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    records, excluded, unresolved = collect_records(args.supplemental)
    selected = selected_ids(records, args.ids)
    previous = read_previous(args.manifest)
    if args.ids and not previous:
        raise SystemExit("指定 --id 重试需要已有 manifest")
    merge_previous(records, previous, selected)
    run_selected(args.manifest, records, excluded, unresolved, selected)
    return 1 if print_summary(records, excluded, unresolved) else 0


if __name__ == "__main__":
    raise SystemExit(main())
