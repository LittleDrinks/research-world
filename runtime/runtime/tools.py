from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from acp.interfaces import Client

from .connectors import Connector
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
GRAPH_QUERY = {
    "type": "function",
    "function": {
        "name": "graph_query",
        "description": "Search project nodes or read one node by id.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "search"]},
                "node_id": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["action"],
        },
    },
}
REPORT_VALIDATE = {
    "type": "function",
    "function": {
        "name": "report_validate",
        "description": "Validate report facts and citations against Research Kernel.",
        "parameters": {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "claim_id": {"type": "string"},
                            "source_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["text", "claim_id", "source_ids"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["facts"],
            "additionalProperties": False,
        },
    },
}
EXPORT_BIBTEX = {
    "type": "function",
    "function": {
        "name": "export_bibtex",
        "description": "Export an admitted source artifact as validated BibTeX.",
        "parameters": {
            "type": "object",
            "properties": {"artifact_id": {"type": "string"}},
            "required": ["artifact_id"],
            "additionalProperties": False,
        },
    },
}
REPORT_PROJECTION = {
    "type": "function",
    "function": {
        "name": "report_projection",
        "description": "Read the admitted report projection from Research Kernel.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}
SUBMIT_OBSERVATION = {
    "type": "function",
    "function": {
        "name": "submit_observation",
        "description": "Submit a human observation to Research Kernel admission.",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["source", "experiment"]},
                "payload": {"type": "object"},
                "provenance": {"type": "object"},
                "observed_at": {"type": "string"},
                "artifact_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "parent_id": {"type": "string"},
            },
            "required": [
                "kind",
                "payload",
                "provenance",
                "observed_at",
                "artifact_ids",
            ],
            "additionalProperties": False,
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
    "graph_query": GRAPH_QUERY,
    "report_projection": REPORT_PROJECTION,
    "report_validate": REPORT_VALIDATE,
    "export_bibtex": EXPORT_BIBTEX,
    "submit_observation": SUBMIT_OBSERVATION,
    "read_file": READ_FILE,
    "write_file": WRITE_FILE,
}


class ToolBox:
    def __init__(
        self,
        workspace: Path,
        skills: dict[str, Skill],
        selected_tools: tuple[str, ...],
        servers: list[Connector],
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
            return await self._call_connector(name, values)
        return await getattr(self, f"_{name}")(session_id, values)

    async def _call_connector(self, name: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide artifact capture")
        content, failed = await self.mcp.call(name, values)
        if failed:
            raise RuntimeError(content)
        capture = {
            "content": content,
            "media_type": _media_type(content),
            "connector_tool": name,
        }
        artifact = await self.client.ext_method("research/capture_artifact", capture)
        return _captured_result(artifact["id"], content, capture["media_type"])

    async def _read_skill(self, session_id: str, values: dict) -> str:
        return self.skills[values["name"]].body()

    async def _read_resource(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide project resources")
        result = await self.client.read_text_file(
            session_id=session_id, path=f"@{values['node_id'].lstrip('@')}"
        )
        return result.content

    async def _graph_query(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide a research graph")
        result = await self.client.ext_method("research/graph_query", values)
        return json.dumps(result, ensure_ascii=False)

    async def _report_validate(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide report validation")
        if set(values) != {"facts"}:
            raise ValueError("unexpected report validation fields")
        result = await self.client.ext_method("research/report_validate", values)
        return json.dumps(result, ensure_ascii=False)

    async def _export_bibtex(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide BibTeX export")
        if set(values) != {"artifact_id"}:
            raise ValueError("unexpected BibTeX export fields")
        result = await self.client.ext_method("research/export_bibtex", values)
        return json.dumps(result, ensure_ascii=False)

    async def _report_projection(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide report projection")
        result = await self.client.ext_method("research/report_projection", values)
        return json.dumps(result, ensure_ascii=False)

    async def _submit_observation(self, session_id: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide observation submission")
        result = await self.client.ext_method("research/submit_observation", values)
        return json.dumps(result, ensure_ascii=False)

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


def _media_type(content: str) -> str:
    try:
        json.loads(content)
    except json.JSONDecodeError:
        return "text/plain"
    return "application/json"


def _captured_result(artifact_id: str, content: str, media_type: str) -> str:
    original = json.loads(content) if media_type == "application/json" else content
    value = {"artifact_id": artifact_id, "content": original}
    return json.dumps(value, ensure_ascii=False)
