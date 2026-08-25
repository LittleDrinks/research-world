from __future__ import annotations

from pathlib import Path

from .adapters import McpAdapter
from .endpoints import Endpoint
from .runtimes import RuntimePool
from .skills import discover_skills
from .tools import BUILTINS, BuiltinAdapter

PRESETS = (
    {
        "id": "math-proof",
        "name": "数学证明",
        "description": "数学/理论方向的形式化证明 Agent：将命题形式化为 Lean4 定理并调用 Lean4 Tool 验证。",
        "spec": {
            "id": "math-proof",
            "name": "数学证明助手",
            "instructions": "把研究中的数学命题形式化为 Lean4 定理，调用 Lean4 Tool 验证证明，只汇报通过验证的结果。",
            "skills": [],
            "tools": ["lean4"],
        },
    },
)


async def discover(
    workspace: Path,
    endpoints: list[Endpoint],
    runtimes: RuntimePool,
    adapters: dict[str, McpAdapter],
    skill_paths: tuple[Path, ...] = (),
) -> dict:
    skills = discover_skills(workspace, skill_paths)
    values = [item.public() for item in endpoints]
    return {
        "runtimes": runtimes.public(),
        "endpoints": values,
        "models": _models(values),
        "skills": [item.public() for item in skills.values()],
        "tools": _tools(adapters),
        "presets": _presets(adapters),
    }


def _presets(adapters: dict[str, McpAdapter]) -> list[dict]:
    return [_preset(preset, adapters) for preset in PRESETS]


def _preset(preset: dict, adapters: dict[str, McpAdapter]) -> dict:
    tools = [_preset_tool(tool_id, adapters) for tool_id in preset["spec"]["tools"]]
    return {
        "id": preset["id"],
        "name": preset["name"],
        "description": preset["description"],
        "spec": dict(preset["spec"]),
        "tools": tools,
    }


def _preset_tool(tool_id: str, adapters: dict[str, McpAdapter]) -> dict:
    if tool_id in BUILTINS:
        return {"id": tool_id, "status": "ready"}
    if tool_id not in adapters:
        return {"id": tool_id, "status": "unavailable", "reason": "not_installed"}
    status = adapters[tool_id].inspect()["status"]
    if status == "unavailable":
        return {"id": tool_id, "status": status, "reason": "not_installed"}
    return {"id": tool_id, "status": status}


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
