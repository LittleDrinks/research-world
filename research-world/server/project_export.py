from __future__ import annotations

import hashlib
import json
import math
import re
from html import unescape
from io import BytesIO
from urllib.parse import parse_qsl, urlsplit
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

from .artifacts import ArtifactStore
from .report_delivery import validate_html
from .reporting import safe_artifact_id


FORMAT = "research-world-project-export/v1"
REDACTED = "[redacted]"
MAX_DEPTH = 16
MAX_ITEMS = 10000
_CREDENTIAL = re.compile(r"(?i)\b(?:key|token|secret|password|credential|authorization|[a-z][a-z0-9_]*(?:key|token|secret|password|credential|authorization)|api[\W_]*key|client[\W_]*secret|baseurl|endpoint|dsn)\b\s*[:=]\s*(?:bearer|basic)?\s*[^\s,;]+")
_BEARER = re.compile(r"(?i)\b(?:bearer|basic)\s+[^\s,;]+")
_KNOWN_SECRET = re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{8,}|AKIA[0-9A-Z]{16}|(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}|xox[baprs]-[A-Za-z0-9-]{8,})\b")
_UNIX_PATH = re.compile(r"(?<![A-Za-z0-9:<])/(?:[^\s\"']+)")
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:[\\/]")
_URI = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
_URI_USERINFO = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s/@]+:[^\s/@]+@")
_FILE_URI = re.compile(r"(?i)\bfile:(?:/{1,3}|[a-z]:[\\/]|\\\\)")
_TEMPORARY = re.compile(r"(?i)\b[^\s/\\]+\.(?:tmp|temp|swp)\b")
_SENSITIVE_KEY = re.compile(r"(?i)(?:\bkey\b|api[\W_]*key|secret|token|password|credential|authorization|cookie|dsn|baseurl|endpoint|continuation)")
_PATH_KEYS = {"path", "root", "workspace", "cwd", "home", "codex_home", "runtime_binding", "provider_session_id"}
_QUERY_SECRET_KEYS = {"key", "apikey", "accesskey", "accesstoken", "auth", "authtoken", "authorization", "clientsecret", "credential", "password", "secret", "signature", "sig", "token", "xapikey"}
_RELATIVE_QUERY = re.compile(r"\?([^\s\"'<>#]+)")
_SERIALIZED_KEY = re.compile(r"(?i)[\"']?(?:key|token|secret|password|credential|authorization|api[\W_]*key|client[\W_]*secret)[\"']?\s*:")


async def export_project(world, runtime, project_id: str) -> bytes:
    project = world.project(project_id)
    nodes = sorted(world.nodes(project_id), key=lambda item: item["id"])
    threads = sorted(world.project_threads(project_id), key=lambda item: item["id"])
    store = ArtifactStore(world.artifacts_root, project_id)
    artifacts = _verified_artifacts(store)
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
        "project": _clean({"project": project, "nodes": nodes, "edges": _edges(world, project)}),
        "runs": _runs(world, project["id"]),
        "traces": traces,
        "reports": reports,
    }


def _edges(world, project):
    fields = ("source", "target", "polarity", "created_at")
    return sorted(world.edges(project["id"]), key=lambda item: tuple(item[field] for field in fields))


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
    record = {field: value.get(field) for field in fields}
    record["nodes"] = sorted(value.get("nodes", []), key=lambda item: item["id"])
    return _clean(record)


def _reports(world, threads, store):
    publications = _thread_records(world, threads, world.report_publications)
    reports = _thread_records(world, threads, world.reports)
    return _clean({"publications": publications, "reports": reports}), _report_files(store, publications)


def _thread_records(world, threads, reader):
    values = [record for thread in threads for record in reader(thread["project_id"], thread["id"])]
    return sorted(values, key=lambda item: item["id"])


def _report_files(store, publications):
    return {_report_member(record): _report_content(store, record["artifact_id"]) for record in publications}


def _report_member(record):
    return f"reports/{_member_id(record['id'])}.html"


def _report_content(store, artifact_id):
    record = store.get(artifact_id)
    if record["media_type"] != "text/html":
        raise ValueError("project export contains invalid published report")
    content = store.read(artifact_id)
    if not _safe_document(content):
        raise ValueError("project export contains unsafe published report")
    return content


def _safe_document(content):
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return not validate_html(content) and not _unsafe_report_data(text)


def _unsafe_report_data(value):
    text = unescape(value)
    return _relative_query_secret(text) or _serialized_secret(text)


def _bibtex(store, nodes):
    entries = [_bibtex_entry(store, artifact_id) for artifact_id in _source_artifacts(nodes)]
    valid = [entry for entry in entries if entry]
    if not valid:
        raise ValueError("project export requires at least one valid BibTeX entry")
    return "\n".join(valid).encode("utf-8")


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
        bibliography = parse_string(text, "bibtex")
    except (PybtexError, UnicodeDecodeError) as error:
        raise ValueError("project export contains invalid BibTeX") from error
    if not bibliography.entries:
        raise ValueError("project export contains no valid BibTeX entries")
    return text if _clean_text(text) == text else _redact_bibtex(bibliography)


def _redact_bibtex(bibliography):
    for entry in bibliography.entries.values():
        entry.fields = {key: _bibtex_value(key, value) for key, value in entry.fields.items()}
    return bibliography.to_string("bibtex")


def _bibtex_value(key, value):
    if _hidden_key(key):
        return REDACTED
    return _clean_text(value) if isinstance(value, str) else REDACTED


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
        "media_type": _clean(record["media_type"]),
        "size": _clean(record["size"]),
        "created_at": _clean(record["created_at"]),
        "omitted": "raw_content",
    }


def _verified_artifacts(store):
    records = store.records()
    for record in records:
        store.read(record["id"])
    return records


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
    return _clean_serialized(value) if _serialized_candidate(value) else REDACTED if _unsafe_text(value) else value


def _serialized_candidate(value):
    stripped = value.lstrip()
    if stripped.startswith(("{", "[")):
        return True
    return stripped.startswith('"') and stripped[1:].lstrip().startswith(("{", "["))


def _clean_serialized(value):
    candidate, layers = value, 0
    for _ in range(MAX_DEPTH):
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, RecursionError):
            candidate = candidate.replace(r'\"', '"')
            if candidate == value:
                return REDACTED
            continue
        if isinstance(parsed, str) and _serialized_candidate(parsed):
            candidate, layers = parsed, layers + 1
            continue
        rendered = _json(_clean(parsed)).decode("utf-8")
        for _ in range(layers):
            rendered = _json(rendered).decode("utf-8")
        return rendered
    return REDACTED


def _unsafe_text(value):
    return bool(_CREDENTIAL.search(value) or _BEARER.search(value) or _KNOWN_SECRET.search(value) or _FILE_URI.search(value) or _temporary(value) or _absolute_path(value) or _uri_secret(value) or _relative_query_secret(value) or _serialized_secret(value))


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
    return any(_query_key(key) for key, _value in parse_qsl(query, keep_blank_values=True))


def _query_key(key):
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in _QUERY_SECRET_KEYS or _hidden_key(key)


def _relative_query_secret(value):
    return any(_query_secret(query) for query in _RELATIVE_QUERY.findall(unescape(value)))


def _serialized_secret(value):
    return _unsafe_json_fragment(value.replace(r'\"', '"'))


def _unsafe_json_fragment(value):
    decoder = json.JSONDecoder()
    for index, character in enumerate(value):
        if character not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(value[index:])
        except (json.JSONDecodeError, RecursionError):
            if _SERIALIZED_KEY.search(value[index:]):
                return True
            continue
        if _clean(parsed) != parsed:
            return True
    return False


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
