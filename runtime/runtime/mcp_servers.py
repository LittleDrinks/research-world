from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import codex_config_path


@dataclass(frozen=True)
class McpServer:
    id: str
    transport: str
    config: dict[str, Any]
    source: str

    def public(self) -> dict[str, Any]:
        value = {"id": self.id, "transport": self.transport, "source": self.source}
        value.update(_safe_config(self.config))
        return value


def discover_mcp(workspace: Path) -> dict[str, McpServer]:
    found = _from_workspace(workspace)
    for name, server in _from_codex().items():
        found.setdefault(name, server)
    return found


def _from_workspace(workspace: Path) -> dict[str, McpServer]:
    path = workspace / ".mcp.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("mcpServers") or {}
    return {name: _server(name, value, "workspace") for name, value in rows.items()}


def _from_codex() -> dict[str, McpServer]:
    path = codex_config_path()
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    rows = data.get("mcp_servers") or {}
    return {name: _server(name, value, "codex") for name, value in rows.items()}


def _server(name: str, value: dict[str, Any], source: str) -> McpServer:
    transport = value.get("type") or ("http" if value.get("url") else "stdio")
    return McpServer(name, transport, dict(value), source)


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    safe = {key: config[key] for key in ("url", "command") if config.get(key)}
    if config.get("env"):
        safe["env_keys"] = sorted(config["env"])
    if config.get("headers"):
        safe["header_names"] = sorted(config["headers"])
    return safe
