from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import tomllib

from .config import codex_config_path

CONNECTOR_ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
SENSITIVE = re.compile(
    r"authorization|api[-_]?key|token|secret|password|cookie|database[-_]?url|dsn|credential",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Connector:
    id: str
    name: str
    description: str
    transport: str
    config: dict[str, Any]
    source: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "transport": self.transport,
            "source": self.source,
            "available": self.available(),
        }

    def available(self) -> bool:
        try:
            self.resolved_config()
        except RuntimeError:
            return False
        if self.transport != "stdio":
            return True
        command = self.config["command"]
        path = Path(command)
        return (
            path.is_file() and os.access(path, os.X_OK)
            if path.is_absolute()
            else bool(shutil.which(command))
        )

    def resolved_config(self) -> dict[str, Any]:
        return _resolve(self.config)

    def definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "transport": self.transport,
            **self.config,
        }


class ConnectorStore:
    def __init__(self, path: Path):
        self.path = path

    def register(self, value: dict[str, Any]) -> dict[str, Any]:
        connector = parse_connector(value, "runtime")
        rows = self._rows()
        rows[connector.id] = connector.definition()
        self._write(rows)
        return connector.public()

    def all(self) -> dict[str, Connector]:
        return {
            name: parse_connector({**value, "id": name}, "runtime")
            for name, value in self._rows().items()
        }

    def _rows(self) -> dict[str, dict[str, Any]]:
        if not self.path.is_file():
            return {}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        return value.get("connectors", {})

    def _write(self, rows: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        value = json.dumps({"connectors": rows}, ensure_ascii=False, indent=2)
        temporary.write_text(f"{value}\n", encoding="utf-8")
        temporary.replace(self.path)


def discover_connectors(
    workspace: Path, registered: Iterable[Connector] = ()
) -> dict[str, Connector]:
    found = _from_codex()
    found.update(_from_workspace(workspace))
    found.update({item.id: item for item in registered})
    return found


def parse_connector(value: dict[str, Any], source: str) -> Connector:
    row = dict(value)
    connector_id = row.pop("id", "")
    name = row.pop("name", connector_id)
    description = row.pop("description", "")
    transport = row.pop("transport", row.pop("type", _transport(row)))
    config = _normalize(row)
    _validate_connector(connector_id, name, description, transport, config)
    return Connector(connector_id, name, description, transport, config, source)


def _from_workspace(workspace: Path) -> dict[str, Connector]:
    path = workspace / ".mcp.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return _parse_rows(data.get("mcpServers") or {}, "workspace")


def _from_codex() -> dict[str, Connector]:
    path = codex_config_path()
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return _parse_rows(data.get("mcp_servers") or {}, "codex")


def _parse_rows(rows, source) -> dict[str, Connector]:
    return {
        name: parse_connector({**value, "id": name}, source)
        for name, value in rows.items()
    }


def _transport(config: dict[str, Any]) -> str:
    return "http" if config.get("url") else "stdio"


def _normalize(config: dict[str, Any]) -> dict[str, Any]:
    value = dict(config)
    headers = dict(value.pop("http_headers", value.pop("headers", {})))
    headers.update(_env_headers(value.pop("env_http_headers", {})))
    if bearer := value.pop("bearer_token_env_var", None):
        headers["Authorization"] = f"Bearer ${{{bearer}}}"
    if headers:
        value["headers"] = headers
    return value


def _env_headers(values: dict[str, str]) -> dict[str, str]:
    return {header: f"${{{env_name}}}" for header, env_name in values.items()}


def _validate_connector(
    connector_id: str,
    name: str,
    description: str,
    transport: str,
    config: dict[str, Any],
) -> None:
    valid_id = isinstance(connector_id, str) and CONNECTOR_ID.fullmatch(connector_id)
    if not valid_id or len(connector_id) > 64:
        raise ValueError("invalid connector id or name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("invalid connector id or name")
    if not isinstance(description, str):
        raise TypeError("invalid connector description")
    if transport not in {"stdio", "http", "sse"}:
        raise ValueError(f"unsupported connector transport: {transport}")
    _validate_location(transport, config)
    _validate_credentials(config)


def _validate_location(transport: str, config: dict[str, Any]) -> None:
    if transport == "stdio":
        _validate_command(config.get("command"), config.get("args", []))
        return
    parsed = urlparse(str(config.get("url", "")))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("connector url must be absolute http(s)")
    if parsed.username or parsed.password:
        raise ValueError("connector credentials must use environment-backed headers")
    if parsed.query:
        raise ValueError("connector url must not include query parameters")
    if parsed.fragment:
        raise ValueError("connector url must not include a fragment")


def _validate_command(command, args) -> None:
    if not isinstance(command, str) or not command:
        raise ValueError("connector command must be an executable path or name")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError("connector args must be strings")
    path = Path(command)
    if "\0" in command or command in {".", ".."}:
        raise ValueError("connector command must be an executable path or name")
    if not path.is_absolute() and (
        "/" in command or "\\" in command or any(char.isspace() for char in command)
    ):
        raise ValueError("relative connector command must be an executable name")


def _validate_credentials(config: dict[str, Any]) -> None:
    for key, value in config.items():
        if SENSITIVE.search(str(key)):
            _require_reference(key, value)
        elif isinstance(value, dict):
            _validate_credentials(value)


def _require_reference(key: str, value: Any) -> None:
    if SENSITIVE.search(str(key)) and not ENV_REF.search(str(value)):
        raise ValueError(
            f"connector credential must reference an environment variable: {key}"
        )


def _resolve(value):
    if isinstance(value, dict):
        return {key: _resolve(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item) for item in value]
    if not isinstance(value, str):
        return value
    return ENV_REF.sub(_environment_value, value)


def _environment_value(match: re.Match) -> str:
    name = match.group(1)
    if name not in os.environ:
        raise RuntimeError("connector credential is unavailable")
    return os.environ[name]
