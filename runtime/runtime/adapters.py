from __future__ import annotations

import json
import os
import re
import shutil
import tomllib
from collections.abc import Iterable
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from .config import codex_config_path
from .tools import BUILTINS

TOOL_ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
MODEL_FUNCTION = re.compile(r"^[a-zA-Z0-9_-]+$")
ENV_REF = re.compile(r"\$\{([A-Za-z_][a-zA-Z0-9_]*)\}")
SENSITIVE = re.compile(
    r"authorization|api[-_]?key|token|secret|password|cookie|database[-_]?url|dsn|credential",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ToolDefinition:
    """Adapter 私有配置：transport、位置与凭证永不越过 Runtime seam。"""

    id: str
    name: str
    description: str
    transport: str
    config: dict[str, Any]
    source: str

    def status(self) -> str:
        try:
            self.resolved_config()
        except RuntimeError:
            return "unavailable"
        if self.transport != "stdio":
            return "ready"
        return "ready" if _executable(self.config["command"]) else "unavailable"

    def resolved_config(self) -> dict[str, Any]:
        return _resolve(self.config)


class McpAdapter:
    """ToolAdapter seam：把一个 MCP server 定义投影为一个 Tool。"""

    def __init__(self, definition: ToolDefinition):
        self.definition = definition

    def inspect(self) -> dict[str, Any]:
        value = self.definition
        return {
            "id": value.id,
            "name": value.name,
            "description": value.description,
            "source": value.source,
            "status": value.status(),
        }

    async def open(self) -> BoundMcp:
        bound = BoundMcp(self.definition)
        await bound.open()
        return bound


class BoundMcp:
    def __init__(self, definition: ToolDefinition):
        self.definition = definition
        self.tool_id = definition.id
        self.stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.operations: dict[str, str] = {}
        self.specs: list[dict] = []

    async def open(self) -> None:
        await self.stack.__aenter__()
        try:
            await self._connect()
        except BaseException as error:  # noqa: BLE001 - cancellation must close sessions
            await self._abort(error)

    async def close(self) -> None:
        await self.stack.aclose()

    async def invoke(
        self, operation: str, values: dict, session_id: str = ""
    ) -> tuple[str, bool]:
        result = await self.session.call_tool(self.operations[operation], values)
        content = [
            item.model_dump(by_alias=True, exclude_none=True) for item in result.content
        ]
        return json.dumps(content, ensure_ascii=False), bool(result.isError)

    async def _connect(self) -> None:
        streams = await self.stack.enter_async_context(
            _client_transport(self.stack, self.definition)
        )
        read, write = streams[:2]
        session = await self.stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.session = session
        await self._load_operations(session)

    async def _abort(self, error: BaseException) -> None:
        message = f"tool failed to open: {self.definition.id}"
        try:
            await self.stack.aclose()
        except BaseException as cleanup_error:
            raise RuntimeError(message) from cleanup_error
        raise RuntimeError(message) from error

    async def _load_operations(self, session: ClientSession) -> None:
        cursor = None
        while True:
            result = await session.list_tools(cursor=cursor)
            for tool in result.tools:
                self._add_operation(tool)
            cursor = result.nextCursor
            if cursor is None:
                return

    def _add_operation(self, tool) -> None:
        public = f"tool__{self.definition.id}__{tool.name}"
        if len(public) > 64 or not MODEL_FUNCTION.fullmatch(public):
            raise ValueError(f"invalid tool operation name: {tool.name}")
        self.operations[public] = tool.name
        self.specs.append(_operation_spec(public, tool))


def discover_adapters(
    workspace: Path, extra: Iterable[ToolDefinition] = ()
) -> dict[str, McpAdapter]:
    found: dict[str, ToolDefinition] = {}
    sources = [_from_codex(), _from_workspace(workspace), {item.id: item for item in extra}]
    for source in sources:
        for key, value in source.items():
            if key in found or key in BUILTINS:
                raise ValueError(f"duplicate tool id: {key}")
            found[key] = value
    return {key: McpAdapter(value) for key, value in found.items()}


def parse_definition(value: dict[str, Any], source: str) -> ToolDefinition:
    row = dict(value)
    tool_id = row.pop("id", "")
    name = row.pop("name", tool_id)
    description = row.pop("description", "")
    transport = row.pop("transport", row.pop("type", _transport(row)))
    config = _normalize(row)
    _validate_definition(tool_id, name, description, transport, config)
    return ToolDefinition(tool_id, name, description, transport, config, source)


def _from_workspace(workspace: Path) -> dict[str, ToolDefinition]:
    path = workspace / ".mcp.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return _parse_rows(data.get("mcpServers") or {}, "workspace")


def _from_codex() -> dict[str, ToolDefinition]:
    path = codex_config_path()
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return _parse_rows(data.get("mcp_servers") or {}, "codex")


def _parse_rows(rows, source) -> dict[str, ToolDefinition]:
    return {
        name: parse_definition({**value, "id": name}, source)
        for name, value in rows.items()
    }


def _client_transport(stack: AsyncExitStack, definition: ToolDefinition):
    config = definition.resolved_config()
    if definition.transport == "stdio":
        params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env"),
        )
        return stdio_client(params)
    if definition.transport == "sse":
        return sse_client(config["url"], headers=config.get("headers"))
    client = httpx.AsyncClient(headers=config.get("headers"))
    stack.push_async_callback(client.aclose)
    return streamable_http_client(config["url"], http_client=client)


def _operation_spec(name, tool) -> dict:
    data = tool.model_dump(by_alias=True, exclude_none=True)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": data.get("description", ""),
            "parameters": data.get("inputSchema", {}),
        },
    }


def _executable(command: str) -> bool:
    path = Path(command)
    if path.is_absolute():
        return path.is_file() and os.access(path, os.X_OK)
    return bool(shutil.which(command))


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


def _validate_definition(
    tool_id: str,
    name: str,
    description: str,
    transport: str,
    config: dict[str, Any],
) -> None:
    valid_id = isinstance(tool_id, str) and TOOL_ID.fullmatch(tool_id)
    if not valid_id or len(tool_id) > 64:
        raise ValueError("invalid tool id or name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("invalid tool id or name")
    if not isinstance(description, str):
        raise TypeError("invalid tool description")
    if transport not in {"stdio", "http", "sse"}:
        raise ValueError(f"unsupported tool transport: {transport}")
    _validate_location(transport, config)
    _validate_credentials(config)


def _validate_location(transport: str, config: dict[str, Any]) -> None:
    if transport == "stdio":
        _validate_command(config.get("command"), config.get("args", []))
        return
    parsed = urlparse(str(config.get("url", "")))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("tool url must be absolute http(s)")
    if parsed.username or parsed.password:
        raise ValueError("tool credentials must use environment-backed headers")
    if parsed.query:
        raise ValueError("tool url must not include query parameters")
    if parsed.fragment:
        raise ValueError("tool url must not include a fragment")


def _validate_command(command, args) -> None:
    if not isinstance(command, str) or not command:
        raise ValueError("tool command must be an executable path or name")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError("tool args must be strings")
    path = Path(command)
    if "\0" in command or command in {".", ".."}:
        raise ValueError("tool command must be an executable path or name")
    if not path.is_absolute() and (
        "/" in command or "\\" in command or any(char.isspace() for char in command)
    ):
        raise ValueError("relative tool command must be an executable name")


def _validate_credentials(config: dict[str, Any]) -> None:
    for key, value in config.items():
        if SENSITIVE.search(str(key)):
            _require_reference(key, value)
        elif isinstance(value, dict):
            _validate_credentials(value)


def _require_reference(key: str, value: Any) -> None:
    if SENSITIVE.search(str(key)) and not ENV_REF.search(str(value)):
        raise ValueError(
            f"tool credential must reference an environment variable: {key}"
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
        raise RuntimeError("tool credential is unavailable")
    return os.environ[name]
