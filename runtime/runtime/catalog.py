from __future__ import annotations

from pathlib import Path

from .adapters import McpAdapter
from .endpoints import Endpoint
from .skills import discover_skills
from .tools import BUILTINS, BuiltinAdapter


async def discover(
    workspace: Path,
    endpoints: list[Endpoint],
    adapters: dict[str, McpAdapter],
    skill_paths: tuple[Path, ...] = (),
) -> dict:
    skills = discover_skills(workspace, skill_paths)
    values = [item.public() for item in endpoints]
    return {
        "endpoints": values,
        "models": _models(values),
        "skills": [item.public() for item in skills.values()],
        "tools": _tools(adapters),
    }


def _tools(adapters: dict[str, McpAdapter]) -> list[dict]:
    builtins = [BuiltinAdapter(tool_id).inspect() for tool_id in BUILTINS]
    external = [adapter.inspect() for adapter in adapters.values()]
    return [*builtins, *external]


def _models(endpoints: list[dict]) -> list[dict]:
    return [
        {"id": model, "endpoint": endpoint["id"]}
        for endpoint in endpoints
        if endpoint["available"]
        for model in endpoint["models"]
    ]
