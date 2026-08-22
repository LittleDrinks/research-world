from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from acp.interfaces import Client

from .mcp_servers import McpServer
from .mcp_tools import McpTools
from .skills import Skill

READ_SKILL = {
    "type": "function",
    "function": {
        "name": "read_skill",
        "description": "Read the instructions for one available skill when they are needed.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
}
READ_RESOURCE = {
    "type": "function",
    "function": {
        "name": "read_resource",
        "description": "Read a referenced Research World node by its @node_id.",
        "parameters": {
            "type": "object",
            "properties": {"node_id": {"type": "string"}},
            "required": ["node_id"],
        },
    },
}
READ_FILE = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a UTF-8 file inside the session workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}
WRITE_FILE = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write a UTF-8 file inside the session workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
}
BUILTINS = {
    "read_skill": READ_SKILL,
    "read_resource": READ_RESOURCE,
    "read_file": READ_FILE,
    "write_file": WRITE_FILE,
}


class ToolBox:
    def __init__(
        self,
        workspace: Path,
        skills: dict[str, Skill],
        selected_tools: tuple[str, ...],
        servers: list[McpServer],
        client: Client | None,
    ):
        self.workspace = workspace.resolve()
        self.skills = skills
        self.selected_tools = selected_tools
        self.client = client
        self.mcp = McpTools(servers)

    async def __aenter__(self) -> Self:
        await self.mcp.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.mcp.__aexit__(exc_type, exc, tb)

    def specs(self) -> list[dict]:
        selected = list(self.selected_tools)
        if self.skills and "read_skill" not in selected:
            selected.append("read_skill")
        values = [BUILTINS[name] for name in selected if name in BUILTINS]
        return [*values, *self.mcp.specs]

    async def call(
        self, session_id: str, name: str, arguments: str
    ) -> tuple[str, bool]:
        try:
            values = json.loads(arguments or "{}")
            return await self._call(session_id, name, values), False
        except Exception as error:  # noqa: BLE001 - tool errors become model-visible results.
            return f"{type(error).__name__}: {error}", True

    async def _call(self, session_id: str, name: str, values: dict) -> str:
        if name in self.mcp.names:
            content, failed = await self.mcp.call(name, values)
            if failed:
                raise RuntimeError(content)
            return content
        return await getattr(self, f"_{name}")(session_id, values)

    async def _read_skill(self, session_id: str, values: dict) -> str:
        return self.skills[values["name"]].body()

    async def _read_resource(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide project resources")
        result = await self.client.read_text_file(
            session_id=session_id, path=f"@{values['node_id'].lstrip('@')}"
        )
        return result.content

    async def _read_file(self, session_id: str, values: dict) -> str:
        return self._path(values["path"]).read_text(encoding="utf-8")

    async def _write_file(self, session_id: str, values: dict) -> str:
        path = self._path(values["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(values["content"], encoding="utf-8")
        return str(path.relative_to(self.workspace))

    def _path(self, value: str) -> Path:
        path = (self.workspace / value).resolve()
        if not path.is_relative_to(self.workspace):
            raise ValueError("path escapes workspace")
        return path
