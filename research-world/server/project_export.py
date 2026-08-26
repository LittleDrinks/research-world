from __future__ import annotations

import hashlib
import json
import math
import re
from io import BytesIO
from urllib.parse import parse_qsl, urlsplit
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

from .artifacts import ArtifactStore
from .reporting import safe_artifact_id


FORMAT = "research-world-project-export/v1"
REDACTED = "[redacted]"
MAX_DEPTH = 16
MAX_ITEMS = 10000
_CREDENTIAL = re.compile(r"(?i)\b(?:api[\W_]*key|client[\W_]*secret|secret|token|password|credential|authorization|baseurl|endpoint|dsn)\b\s*[:=]\s*(?:bearer|basic)?\s*[^\s,;]+")
_BEARER = re.compile(r"(?i)\b(?:bearer|basic)\s+[^\s,;]+")
_UNIX_PATH = re.compile(r"(?<![A-Za-z0-9:<])/(?:[^\s\"']+)")
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:[\\/]")
_URI = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
_URI_USERINFO = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s/@]+:[^\s/@]+@")
_TEMPORARY = re.compile(r"(?i)\b[^\s/\\]+\.(?:tmp|temp|swp)\b")
_SENSITIVE_KEY = re.compile(r"(?i)(?:api[\W_]*key|secret|token|password|credential|authorization|cookie|dsn|baseurl|endpoint|continuation)")
_PATH_KEYS = {"path", "root", "workspace", "cwd", "home", "codex_home", "runtime_binding", "provider_session_id"}


async def export_project(world, runtime, project_id: str) -> bytes:
    project = world.project(project_id)
    nodes, threads = world.nodes(project_id), world.project_threads(project_id)
    store = ArtifactStore(world.artifacts_root, project_id)
    artifacts = store.records()
    traces = await _traces(runtime, threads)
    reports, report_files = _reports(world, threads, store)
    snapshot = _snapshot(world, project, nodes, traces, reports)
    _validate_references(snapshot, artifacts)
    return package(project_id, snapshot, artifacts, report_files, _bibtex(store, nodes))


def package(project_id, snapshot, artifacts, report_files, bibtex) -> bytes:
    files = _files(snapshot, artifacts, report_files, bibtex)
    files["manifest.json"] = _json(_manifest(project_id, files))
    files["checksums.sha256"] = _checksums(files)
    return _zip(files)


def _snapshot(world, project, nodes, traces, reports):
    return {
        "project": _clean({"project": project, "nodes": nodes, "edges": world.edges(project["id"])}),
        "runs": _runs(world, project["id"]),
        "traces": traces,
        "reports": reports,
    }


def _runs(world, project_id):
    runs = sorted(world.runs(project_id), key=lambda item: (item["created_at"], item["id"]))
    return [_run(world, item) for item in runs]


def _run(world, run):
    return _clean({**run, "steps": world.steps(run["id"]), "events": world.run_events(run["id"])})


async def _traces(runtime, threads):
    if not threads:
        return []
    if runtime is None:
        raise ValueError("project export requires Runtime Trace")
    return [await _trace(runtime, thread) for thread in sorted(threads, key=lambda item: item["id"])]


async def _trace(runtime, thread):
    trace = await runtime.inspect(thread["session_id"])
    return {"thread": _thread(thread), "trace": _clean(trace)}


def _thread(value):
    fields = ("id", "title", "agent_id", "archived", "created_at", "updated_at", "nodes")
    return _clean({field: value.get(field) for field in fields})


def _reports(world, threads, store):
    publications = _thread_records(world, threads, world.report_publications)
    reports = _thread_records(world, threads, world.reports)
    return _clean({"publications": publications, "reports": reports}), _report_files(store, publications)


def _thread_records(world, threads, reader):
    values = [record for thread in threads for record in reader(thread["project_id"], thread["id"])]
    return sorted(values, key=lambda item: item["id"])


def _report_files(store, publications):
    return {
        _report_member(record): content
        for record in publications
        if (content := _report_content(store, record["artifact_id"])) is not None
    }


def _report_member(record):
    return f"reports/{_member_id(record['id'])}.html"


def _report_content(store, artifact_id):
    record = store.get(artifact_id)
    if record["media_type"] != "text/html":
        return None
    content = store.read(artifact_id)
    return content if _safe_document(content) else None


def _safe_document(content):
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return _clean_text(text) == text


def _bibtex(store, nodes):
    entries = [_bibtex_entry(store, artifact_id) for artifact_id in _source_artifacts(nodes)]
    return "\n".join(entry for entry in entries if entry).encode("utf-8")


def _source_artifacts(nodes):
    values = {
        artifact_id
        for node in nodes
        if node["kind"] == "source" and node["life_state"] == "admitted"
        for artifact_id in node["payload"].get("artifact_ids", [])
        if safe_artifact_id(artifact_id)
    }
    return sorted(values)


def _bibtex_entry(store, artifact_id):
    record = store.get(artifact_id)
    if record["media_type"] not in {"application/x-bibtex", "text/x-bibtex"}:
        return ""
    try:
        text = store.read(artifact_id).decode("utf-8")
        parse_string(text, "bibtex")
    except (PybtexError, UnicodeDecodeError) as error:
        raise ValueError("project export contains invalid BibTeX") from error
    if _clean_text(text) != text:
        raise ValueError("project export contains unsafe BibTeX")
    return text


def _files(snapshot, artifacts, report_files, bibtex):
    values = {
        "project.json": _json(snapshot["project"]),
        "pipeline-runs.json": _json(snapshot["runs"]),
        "traces.json": _json(_trace_index(snapshot["traces"])),
        "artifacts.json": _json(_artifact_inventory(artifacts)),
        "reports.json": _json(snapshot["reports"]),
        "references.bib": bibtex,
    }
    return values | _trace_files(snapshot["traces"]) | _artifact_files(artifacts) | report_files


def _trace_index(traces):
    return [{"thread_id": value["thread"]["id"], "path": _trace_member(value)} for value in traces]


def _trace_files(traces):
    return {_trace_member(value): _json(value) for value in traces}


def _trace_member(value):
    return f"traces/{_member_id(value['thread']['id'])}.json"


def _artifact_inventory(artifacts):
    return [_artifact_metadata(record) for record in artifacts]


def _artifact_files(artifacts):
    return {f"artifacts/{record['sha256']}.json": _json(_artifact_metadata(record)) for record in artifacts}


def _artifact_metadata(record):
    return {
        "id": record["id"],
        "sha256": record["sha256"],
        "media_type": _clean_text(record["media_type"]),
        "size": record["size"],
        "created_at": record["created_at"],
        "omitted": "raw_content",
    }


def _validate_references(snapshot, artifacts):
    known = {record["id"] for record in artifacts}
    missing = _artifact_references(snapshot) - known
    if missing:
        raise ValueError("project export references artifact outside project scope")


def _artifact_references(value):
    if isinstance(value, str):
        return {value} if safe_artifact_id(value) else set()
    if isinstance(value, dict):
        return set().union(*(_artifact_references(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_artifact_references(item) for item in value))
    return set()


def _clean(value, depth=0):
    if depth > MAX_DEPTH:
        return REDACTED
    if isinstance(value, dict):
        return _clean_mapping(value, depth)
    if isinstance(value, (list, tuple)):
        return _clean_sequence(value, depth)
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, float) and not math.isfinite(value):
        return REDACTED
    return value if value is None or isinstance(value, (bool, int, float)) else REDACTED


def _clean_mapping(value, depth):
    if len(value) > MAX_ITEMS or any(not isinstance(key, str) for key in value):
        return REDACTED
    return {key: _clean(value[key], depth + 1) for key in sorted(value) if _safe_key(key)}


def _clean_sequence(value, depth):
    if len(value) > MAX_ITEMS:
        return REDACTED
    return [_clean(item, depth + 1) for item in value]


def _hidden_key(key):
    lowered = key.lower()
    return bool(_SENSITIVE_KEY.search(key)) or lowered in _PATH_KEYS or "path" in lowered


def _safe_key(key):
    return not _hidden_key(key) and _clean_text(key) == key


def _clean_text(value):
    return REDACTED if _unsafe_text(value) else value


def _unsafe_text(value):
    return bool(_CREDENTIAL.search(value) or _BEARER.search(value) or _temporary(value) or _absolute_path(value) or _uri_secret(value))


def _temporary(value):
    return _TEMPORARY.search(value) is not None


def _absolute_path(value):
    plain = _URI.sub("", value)
    return bool(_UNIX_PATH.search(plain) or _WINDOWS_PATH.search(plain))


def _uri_secret(value):
    if _URI_USERINFO.search(value):
        return True
    return any(_parsed_uri_secret(uri) for uri in _URI.findall(value))


def _parsed_uri_secret(value):
    try:
        parsed = urlsplit(value)
    except ValueError:
        return True
    return parsed.username is not None or parsed.password is not None or _query_secret(parsed.query)


def _query_secret(query):
    return any(_hidden_key(key) for key, _value in parse_qsl(query, keep_blank_values=True))


def _manifest(project_id, files):
    records = [{"path": path, "size": len(content), "sha256": _digest(content)} for path, content in sorted(files.items())]
    return {"format": FORMAT, "project_id": project_id, "files": records}


def _checksums(files):
    return "".join(f"{_digest(content)}  {path}\n" for path, content in sorted(files.items()) if path != "checksums.sha256").encode()


def _zip(files):
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for path, content in sorted(files.items()):
            archive.writestr(_zip_info(path), content)
    return output.getvalue()


def _zip_info(path):
    value = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
    value.create_system, value.external_attr, value.compress_type = 3, 0o100644 << 16, ZIP_STORED
    return value


def _member_id(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(content):
    return hashlib.sha256(content).hexdigest()
