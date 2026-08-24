from __future__ import annotations

import base64
import hashlib
import json
import os

import httpx

from .tools import ArtifactDraft, ToolOutcome

TOOL_ID = "lean4"
LEAN_VERSION = "4.33.1"
IMAGE = f"ai4sci-lean4:{LEAN_VERSION}"
SOURCE_LIMIT = 256 * 1024
RUN_LIMITS = {"cpus": 1, "memory_mb": 1024, "pids": 64, "wall_seconds": 30}
VERSION = {
    "type": "function",
    "function": {
        "name": "tool__lean4__version",
        "description": "Read the installed Lean 4 and mathlib version.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}
VERIFY = {
    "type": "function",
    "function": {
        "name": "tool__lean4__verify",
        "description": "Verify Lean 4 source against the installed mathlib release.",
        "parameters": {
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
            "additionalProperties": False,
        },
    },
}


class Lean4Adapter:
    def __init__(self, runner_url: str | None = None):
        self.runner_url = runner_url if runner_url is not None else _runner_url()

    def inspect(self) -> dict:
        return {
            "id": TOOL_ID,
            "name": "Lean 4",
            "description": "Verify formal proofs with Lean 4 and mathlib.",
            "source": "runtime",
            "status": "ready" if _doctor(self.runner_url) else "unavailable",
        }

    async def open(self) -> BoundLean4:
        if not await _async_doctor(self.runner_url):
            raise RuntimeError("Lean 4 sandbox is unavailable")
        return BoundLean4(self.runner_url)


class BoundLean4:
    tool_id = TOOL_ID
    specs = [VERSION, VERIFY]

    def __init__(self, runner_url: str):
        self.runner_url = runner_url

    async def close(self) -> None:
        return None

    async def invoke(self, operation: str, values: dict, session_id: str) -> ToolOutcome:
        if operation == "tool__lean4__version":
            return self._version(values)
        if operation != "tool__lean4__verify":
            raise KeyError(f"unknown Lean 4 operation: {operation}")
        return await self._verify(values, session_id)

    def _version(self, values: dict) -> ToolOutcome:
        _require_fields(values, set())
        return _outcome("ready", [], ())

    async def _verify(self, values: dict, session_id: str) -> ToolOutcome:
        source = _source(values)
        result = await _run(self.runner_url, _verify_spec(source, session_id))
        if result["exit_code"] == 124:
            raise RuntimeError("Lean 4 verification timed out")
        diagnostics = _diagnostics(result)
        status = "verified" if result["exit_code"] == 0 else "rejected"
        return _outcome(status, diagnostics, (ArtifactDraft(source, "text/x-lean"),))


def _runner_url() -> str:
    return os.getenv("RUNNER_CONTROLLER_URL", "").rstrip("/")


def _doctor(url: str) -> bool:
    if not url:
        return False
    try:
        response = httpx.post(f"{url}/images/inspect", json={"image": IMAGE}, timeout=5)
        return response.status_code == 200 and response.json().get("available") is True
    except (httpx.HTTPError, ValueError):
        return False


async def _async_doctor(url: str) -> bool:
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(f"{url}/images/inspect", json={"image": IMAGE})
        response.raise_for_status()
        return response.json().get("available") is True
    except (httpx.HTTPError, ValueError):
        return False


async def _run(url: str, spec: dict) -> dict:
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(f"{url}/run", json=spec)
    response.raise_for_status()
    result = response.json()
    if result.get("failure"):
        raise RuntimeError(f"Lean 4 runner failed: {result['failure']['code']}")
    return result


def _verify_spec(source: str, session_id: str) -> dict:
    digest = hashlib.sha256(source.encode()).hexdigest()
    return {
        "execution_id": f"tool:lean4:{session_id}:{digest}",
        "image": IMAGE,
        "command": ["sh", "-c", _verify_command()],
        "files": {"Main.lean": base64.b64encode(source.encode()).decode()},
        "seed": 0,
        "limits": RUN_LIMITS,
    }


def _verify_command() -> str:
    return "cd /opt/mathlib && exec lake env lean --json -DwarningAsError=true /workspace/Main.lean"


def _source(values: dict) -> str:
    _require_fields(values, {"source"})
    source = values["source"]
    if not isinstance(source, str) or not source:
        raise ValueError("source must be a non-empty string")
    if len(source.encode()) > SOURCE_LIMIT:
        raise ValueError("source exceeds 256 KiB")
    return source


def _require_fields(values: dict, expected: set[str]) -> None:
    if set(values) != expected:
        raise ValueError("unexpected Lean 4 operation fields")


def _diagnostics(result: dict) -> list[dict]:
    values = [_diagnostic(line) for line in result.get("stdout", "").splitlines() if line]
    if result.get("stderr"):
        values.append({"severity": "error", "message": result["stderr"][:65536]})
    return values


def _diagnostic(line: str) -> dict:
    try:
        value = json.loads(line)
    except json.JSONDecodeError as error:
        raise RuntimeError("Lean 4 returned invalid JSON diagnostics") from error
    return {
        key: value[key]
        for key in ("severity", "kind", "fileName", "pos", "endPos", "data")
        if key in value
    }


def _outcome(status: str, diagnostics: list[dict], artifacts: tuple) -> ToolOutcome:
    value = {"status": status, "lean_version": LEAN_VERSION, "diagnostics": diagnostics}
    return ToolOutcome(json.dumps(value, ensure_ascii=False), artifacts=artifacts)
