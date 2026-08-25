from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import PurePath, PureWindowsPath

_SECRET = re.compile(r"api.?key|authorization|credential|password|secret|token", re.I)
_TEMPORARY = re.compile(r"^(tmp|temp|temporary)(_|$)", re.I)


def package(project: dict, graph: dict, runs: list[dict], traces: dict, artifacts: list[dict]) -> bytes:
    files = _records(project, graph, runs, traces, artifacts)
    manifest = {"schema_version": 1, "project_id": project["id"], "files": _checksums(files)}
    files["manifest.json"] = _json(manifest)
    return _archive(files)


def _records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    values = {
        "project.json": _json({"project": _clean(project), "graph": _clean(graph)}),
        "pipeline-runs.json": _json(_clean(runs)),
        "traces.json": _json(_clean(traces)),
        "artifacts.json": _json(_clean([{key: value for key, value in item.items() if key != "content"} for item in artifacts])),
    }
    for artifact in artifacts:
        values[_artifact_name(artifact)] = artifact["content"]
    return values


def _artifact_name(artifact: dict) -> str:
    digest = artifact["sha256"]
    media_type = artifact["media_type"]
    if media_type == "text/html":
        return f"reports/{digest}.html"
    if artifact.get("bibtex"):
        return f"bibtex/{digest}.bib"
    return f"artifacts/{digest}"


def _checksums(files: dict[str, bytes]) -> list[dict]:
    return [
        {"path": path, "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
        for path, content in sorted(files.items())
    ]


def _archive(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in sorted(files.items()):
            entry = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o600 << 16
            archive.writestr(entry, content)
    return output.getvalue()


def _json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"


def _clean(value, key: str = ""):
    if _SECRET.search(key) or key == "root" or _TEMPORARY.match(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {item: _clean(child, item) for item, child in sorted(value.items())}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, str) and _absolute_path(value):
        return "[REDACTED]"
    return value


def _absolute_path(value: str) -> bool:
    return PurePath(value).is_absolute() or PureWindowsPath(value).is_absolute()
