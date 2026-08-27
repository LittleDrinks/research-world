#!/usr/bin/env python3
"""Audit the local docs-reference archive without network access."""

import hashlib
import importlib.util
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
CORPUS = REPO / "datasets" / "research-kernel-papers"
MANIFEST = CORPUS / "docs-references.manifest.json"
SOURCE_LIST = CORPUS / "issue-139.sources.json"
ARCHIVE_SCRIPT = CORPUS / "scripts" / "archive_doc_references.py"
EXPECTED_EXCEPTION = "datasets/research-kernel-papers/snapshots/issue-139/pi-compaction.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def archive_module():
    spec = importlib.util.spec_from_file_location("archive_doc_references", ARCHIVE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require_relative(value):
    assert value and not Path(value).is_absolute()


def check_pdf(path):
    assert path.is_file() and path.stat().st_size > 1024
    with path.open("rb") as stream:
        assert stream.read(4) == b"%PDF"


def check_markdown(path):
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    assert text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    assert any(re.match(r"^#{1,6}\s+", line) for line in lines)
    assert any(not re.match(r"^#{1,6}\s+", line) for line in lines)


def check_whitespace(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    assert not any(line.endswith((" ", "\t")) for line in text.splitlines())
    assert path.read_bytes().endswith(b"\n")
    assert not path.read_bytes().endswith(b"\n\n")


def check_entry(item):
    assert item["source_url"] in item["source_urls"]
    assert item["retry_command"]
    if item["status"] == "failed":
        assert item["failure_stage"] and item["failure_reason"] and item["download_url"]
        return
    assert item["status"] == "ready" and item["sha256"]
    if item["origin"] == "docs":
        pdf = REPO / item["pdf_path"]
        markdown = REPO / item["markdown_path"]
        require_relative(item["pdf_path"])
        require_relative(item["markdown_path"])
        check_pdf(pdf)
        check_markdown(markdown)
        assert digest(pdf) == item["sha256"]
        return
    require_relative(item["local_path"])
    local = REPO / item["local_path"]
    assert local.is_file() and local.read_bytes()
    assert digest(local) == item["sha256"]
    assert item["version"] and item["format"] and item["snapshot_format"]
    if item.get("markdown_path"):
        check_markdown(REPO / item["markdown_path"])


def check_issue139(entries):
    source_items = load(SOURCE_LIST)
    expected = {item["id"]: item for item in source_items}
    actual = {item["id"]: item for item in entries if item["origin"] == "issue-139"}
    assert set(actual) == set(expected) and len(actual) == 13
    for item_id, source in expected.items():
        entry = actual[item_id]
        for field in ("source_url", "download_url", "version", "format", "snapshot_format", "local_path"):
            assert entry[field] == source[field]


def check_scope_coverage(entries, payload):
    sources, excluded, _ = archive_module().extract_sources()
    expected_sources = {url for item in sources for url in item["source_urls"]}
    actual_sources = {url for item in entries if item["origin"] == "docs" for url in item["source_urls"]}
    assert actual_sources == expected_sources
    expected_excluded = {item["url"] for item in excluded}
    actual_excluded = {item["url"] for item in payload["excluded_sources"]}
    assert actual_excluded == expected_excluded


def check_exception(payload):
    exceptions = payload["audit_exceptions"]
    assert len(exceptions) == 1
    assert exceptions[0]["path"] == EXPECTED_EXCEPTION
    assert exceptions[0]["status"] == "expected-source-whitespace"
    path = REPO / EXPECTED_EXCEPTION
    count = sum(line.endswith((" ", "\t")) for line in path.read_text(encoding="utf-8").splitlines())
    assert count == 2


def check_generated_files():
    markdown = list((CORPUS / "markdown").glob("*.md"))
    assert len(markdown) == 82
    for path in markdown:
        check_whitespace(path)
    snapshot_dir = CORPUS / "snapshots" / "issue-139"
    for path in snapshot_dir.iterdir():
        assert path.suffix != ".html"
        if path.name != "pi-compaction.md" and path.suffix == ".md":
            check_whitespace(path)


def main():
    payload = load(MANIFEST)
    entries = payload["entries"]
    assert payload["version"] == 2 and payload["scope"]["html_output"] is False
    assert len(entries) == 98 and len({item["id"] for item in entries}) == 98
    assert sum(item["origin"] == "docs" for item in entries) == 85
    assert sum(item["status"] == "ready" for item in entries) == 95
    assert sum(item["status"] == "failed" for item in entries) == 3
    assert len(payload["unresolved_citations"]) == 17
    assert len(payload["excluded_sources"]) == 96
    for item in entries:
        check_entry(item)
    check_issue139(entries)
    check_scope_coverage(entries, payload)
    check_exception(payload)
    check_generated_files()
    print(json.dumps({"errors": 0, "entries": 98, "ready": 95, "failed": 3, "pdf_markdown_pairs": 82, "issue139": 13, "unresolved": 17, "excluded": 96}, ensure_ascii=False))


if __name__ == "__main__":
    main()
