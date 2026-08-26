from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from acp.interfaces import Client

from . import literature
from .skills import Skill


@dataclass(frozen=True)
class ArtifactDraft:
    content: str
    media_type: str


@dataclass(frozen=True)
class ToolOutcome:
    content: str
    failed: bool = False
    artifacts: tuple[ArtifactDraft, ...] = ()

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
CROSSREF = {
    "type": "function",
    "function": {
        "name": "crossref",
        "description": "Search Crossref or verify one DOI metadata record.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "get"]},
                "query": {"type": "string"},
                "doi": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["action"],
        },
    },
}
OPENALEX = {
    "type": "function",
    "function": {
        "name": "openalex",
        "description": "Search OpenAlex or read one work and its open-access locations.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "get"]},
                "query": {"type": "string"},
                "id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["action"],
        },
    },
}
ARXIV = {
    "type": "function",
    "function": {
        "name": "arxiv",
        "description": "Search arXiv primary records or read one record by arXiv id.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "get"]},
                "query": {"type": "string"},
                "id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["action"],
        },
    },
}
PUBMED = {
    "type": "function",
    "function": {
        "name": "pubmed",
        "description": "Search PubMed, verify PubMed metadata, or retrieve PMC full-text XML.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "metadata", "full_text"]},
                "query": {"type": "string"},
                "id": {"type": "string"},
                "pmcid": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["action"],
        },
    },
}
PROJECT_FILES = {
    "type": "function",
    "function": {
        "name": "project_files",
        "description": "Read a Project File or store complete source text as a Project File and immutable Artifact.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["store", "read"]},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "media_type": {"type": "string"},
            },
            "required": ["action", "path"],
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
    "crossref": CROSSREF,
    "openalex": OPENALEX,
    "arxiv": ARXIV,
    "pubmed": PUBMED,
    "project_files": PROJECT_FILES,
}
BUILTIN_NAMES = {
    "read_skill": "读取 Skill",
    "read_resource": "读取引用节点",
    "graph_query": "查询研究图谱",
    "report_projection": "读取报告投影",
    "report_validate": "校验科研报告",
    "export_bibtex": "导出 BibTeX",
    "submit_observation": "提交人工观测",
    "read_file": "读取工作区文件",
    "write_file": "写入工作区文件",
    "crossref": "Crossref",
    "openalex": "OpenAlex",
    "arxiv": "arXiv",
    "pubmed": "PubMed / PMC",
    "project_files": "Project Files",
}


class BuiltinAdapter:
    """ToolAdapter seam：内置函数投影为单 operation 的 Tool。"""

    def __init__(self, tool_id: str):
        self.tool_id = tool_id

    def inspect(self) -> dict:
        spec = BUILTINS[self.tool_id]["function"]
        return {
            "id": self.tool_id,
            "name": BUILTIN_NAMES[self.tool_id],
            "description": spec["description"],
            "source": "runtime",
            "status": "ready",
        }

    async def open(self, workspace, skills, client) -> BoundBuiltin:
        return BoundBuiltin(self.tool_id, workspace, skills, client)


class BoundBuiltin:
    def __init__(self, tool_id: str, workspace, skills, client):
        self.tool_id = tool_id
        self.workspace = Path(workspace).resolve()
        self.skills = skills
        self.client = client
        self.specs = [BUILTINS[tool_id]]

    async def close(self) -> None:
        return None

    async def invoke(self, operation: str, values: dict, session_id: str) -> str:
        return await _HANDLERS[self.tool_id](self, session_id, values)


class ToolBox:
    """Session 级 Tool 聚合：统一打开、路由与 Artifact capture。"""

    def __init__(
        self,
        workspace: Path,
        skills: dict[str, Skill],
        selected_tools: tuple[str, ...],
        adapters: dict,
        client: Client | None,
    ):
        self.workspace = workspace
        self.skills = skills
        self.client = client
        self.selected = _with_skill_reader(selected_tools, skills)
        self.adapters = adapters
        self._bound: list = []
        self._routes: dict[str, object] = {}
        self._external: set[str] = set()

    async def __aenter__(self) -> Self:
        try:
            for tool_id in self.selected:
                await self._open(tool_id)
        except BaseException:  # noqa: BLE001 - open failure rolls back opened tools
            await self._rollback()
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb):
        for bound in reversed(self._bound):
            await bound.close()

    def specs(self) -> list[dict]:
        return [spec for bound in self._bound for spec in bound.specs]

    def plan(self) -> list[dict]:
        return [
            {"id": bound.tool_id, "operations": [s["function"] for s in bound.specs]}
            for bound in self._bound
        ]

    async def _rollback(self) -> None:
        for bound in reversed(self._bound):
            await bound.close()

    async def call(
        self, session_id: str, name: str, arguments: str
    ) -> tuple[str, bool]:
        try:
            values = json.loads(arguments or "{}")
            return await self._invoke(session_id, name, values), False
        except Exception as error:  # noqa: BLE001 - tool errors become model-visible results.
            return f"{type(error).__name__}: {error}", True

    async def _open(self, tool_id: str) -> None:
        if tool_id in BUILTINS:
            adapter = BuiltinAdapter(tool_id)
            bound = await adapter.open(self.workspace, self.skills, self.client)
            self._bind(bound, external=False)
            return
        bound = await self.adapters[tool_id].open()
        self._bind(bound, external=True)

    def _bind(self, bound, external: bool) -> None:
        self._bound.append(bound)
        for spec in bound.specs:
            name = spec["function"]["name"]
            self._routes[name] = bound
            if external:
                self._external.add(name)

    async def _invoke(self, session_id: str, name: str, values: dict) -> str:
        if name not in self._routes:
            raise KeyError(f"unknown tool operation: {name}")
        if name in self._external:
            return await self._invoke_external(session_id, name, values)
        return await self._routes[name].invoke(name, values, session_id)

    async def _invoke_external(self, session_id: str, name: str, values: dict) -> str:
        if self.client is None:
            raise RuntimeError("client does not provide artifact capture")
        raw = await self._routes[name].invoke(name, values, session_id)
        outcome = _tool_outcome(raw)
        if outcome.failed:
            raise RuntimeError(outcome.content)
        drafts = outcome.artifacts or (
            ArtifactDraft(outcome.content, _media_type(outcome.content)),
        )
        artifact_ids = [await self._capture(name, draft) for draft in drafts]
        return _captured_result(artifact_ids, outcome.content)

    async def _capture(self, name: str, draft: ArtifactDraft) -> str:
        capture = {"content": draft.content, "media_type": draft.media_type, "tool": name}
        artifact = await self.client.ext_method("research/capture_artifact", capture)
        return artifact["id"]


async def _read_skill(bound, session_id, values):
    return bound.skills[values["name"]].body()


async def _read_resource(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide project resources")
    result = await bound.client.read_text_file(
        session_id=session_id, path=f"@{values['node_id'].lstrip('@')}"
    )
    return result.content


async def _graph_query(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide a research graph")
    result = await bound.client.ext_method("research/graph_query", values)
    return json.dumps(result, ensure_ascii=False)


async def _report_validate(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide report validation")
    if set(values) != {"facts"}:
        raise ValueError("unexpected report validation fields")
    result = await bound.client.ext_method("research/report_validate", values)
    return json.dumps(result, ensure_ascii=False)


async def _export_bibtex(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide BibTeX export")
    if set(values) != {"artifact_id"}:
        raise ValueError("unexpected BibTeX export fields")
    result = await bound.client.ext_method("research/export_bibtex", values)
    return json.dumps(result, ensure_ascii=False)


async def _report_projection(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide report projection")
    result = await bound.client.ext_method("research/report_projection", values)
    return json.dumps(result, ensure_ascii=False)


async def _submit_observation(bound, session_id, values):
    if bound.client is None:
        raise RuntimeError("client does not provide observation submission")
    result = await bound.client.ext_method("research/submit_observation", values)
    return json.dumps(result, ensure_ascii=False)


async def _read_file(bound, session_id, values):
    return _path(bound, values["path"]).read_text(encoding="utf-8")


async def _write_file(bound, session_id, values):
    path = _path(bound, values["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(values["content"], encoding="utf-8")
    return str(path.relative_to(bound.workspace))


async def _crossref(bound, session_id, values):
    return await literature.crossref(values)


async def _openalex(bound, session_id, values):
    return await literature.openalex(values)


async def _arxiv(bound, session_id, values):
    return await literature.arxiv(values)


async def _pubmed(bound, session_id, values):
    return await literature.pubmed(values)


async def _project_files(bound, session_id, values):
    return await literature.project_files(bound, values)


_HANDLERS = {
    "read_skill": _read_skill,
    "read_resource": _read_resource,
    "graph_query": _graph_query,
    "report_validate": _report_validate,
    "export_bibtex": _export_bibtex,
    "report_projection": _report_projection,
    "submit_observation": _submit_observation,
    "read_file": _read_file,
    "write_file": _write_file,
    "crossref": _crossref,
    "openalex": _openalex,
    "arxiv": _arxiv,
    "pubmed": _pubmed,
    "project_files": _project_files,
}


def _with_skill_reader(selected, skills) -> list[str]:
    values = list(selected)
    if skills and "read_skill" not in values:
        values.append("read_skill")
    return values


def _path(bound, value: str) -> Path:
    path = (bound.workspace / value).resolve()
    if not path.is_relative_to(bound.workspace):
        raise ValueError("path escapes workspace")
    return path


def _media_type(content: str) -> str:
    try:
        json.loads(content)
    except json.JSONDecodeError:
        return "text/plain"
    return "application/json"


def _tool_outcome(value) -> ToolOutcome:
    if isinstance(value, ToolOutcome):
        return value
    content, failed = value
    return ToolOutcome(content, failed)


def _captured_result(artifact_ids: list[str], content: str) -> str:
    original = json.loads(content) if _media_type(content) == "application/json" else content
    value = {"artifact_ids": artifact_ids, "content": original}
    if len(artifact_ids) == 1:
        value["artifact_id"] = artifact_ids[0]
    return json.dumps(value, ensure_ascii=False)
