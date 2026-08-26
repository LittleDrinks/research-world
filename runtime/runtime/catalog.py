from __future__ import annotations

from pathlib import Path

from .adapters import McpAdapter
from .endpoints import Endpoint
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
    {
        "id": "source-researcher",
        "name": "文献研究员",
        "description": "检索一手来源、核验元数据、保存完整正文，并生成等待 Admission 的 Source 候选。",
        "spec": {
            "id": "source-researcher",
            "name": "文献研究员",
            "instructions": "检索并交叉核验一手来源；完整正文可得时保存 Project File/Artifact 并精确定位证据。全文不可得时显式披露，只作背景且不输出关键 claim。只返回 SourceCandidate，不提交节点或裁决 Admission。",
            "skills": ["source-research"],
            "tools": ["crossref", "openalex", "arxiv", "pubmed", "project_files"],
        },
        "reasons": {
            "crossref": "核验 DOI、作者、年份、venue 与许可元数据",
            "openalex": "交叉核验书目记录与开放获取位置",
            "arxiv": "检索并核验 arXiv 一手记录",
            "pubmed": "检索 PubMed 并读取可得的 PMC 全文",
            "project_files": "保存完整正文并登记不可变 Artifact",
            "anysearch": "补充实时网页检索",
            "tavily": "补充网页检索与正文提取",
            "opencli-browser": "查阅需要浏览器交互的一手页面",
            "zotero": "复用已维护的本地文献库",
        },
    },
)


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
        "presets": _presets(adapters, skills),
    }


def _presets(adapters: dict[str, McpAdapter], skills: dict) -> list[dict]:
    return [_preset(preset, adapters, skills) for preset in PRESETS]


def _preset(preset: dict, adapters: dict[str, McpAdapter], skills: dict) -> dict:
    spec = _preset_spec(preset, adapters)
    tools = [_preset_tool(tool_id, adapters, preset) for tool_id in spec["tools"]]
    return {
        "id": preset["id"],
        "name": preset["name"],
        "description": preset["description"],
        "spec": spec,
        "tools": tools,
        "skills": [_preset_skill(skill_id, skills) for skill_id in spec["skills"]],
    }


def _preset_tool(tool_id: str, adapters: dict[str, McpAdapter], preset: dict) -> dict:
    reason = preset.get("reasons", {}).get(tool_id, "补充已识别的检索能力")
    if tool_id in BUILTINS:
        return {**BuiltinAdapter(tool_id).inspect(), "recommendation": reason}
    if tool_id not in adapters:
        return _unavailable(tool_id, reason, "not_installed")
    value = {**adapters[tool_id].inspect(), "recommendation": reason}
    if value["status"] == "unavailable":
        value["reason"] = "not_installed"
    return value


def _preset_spec(preset: dict, adapters: dict[str, McpAdapter]) -> dict:
    spec = {
        **preset["spec"],
        "skills": list(preset["spec"]["skills"]),
        "tools": list(preset["spec"]["tools"]),
    }
    if preset["id"] != "source-researcher":
        return spec
    optional = [tool_id for tool_id in ("anysearch", "tavily", "opencli-browser", "zotero") if tool_id in adapters]
    return {**spec, "tools": [*spec["tools"], *optional]}


def _preset_skill(skill_id: str, skills: dict) -> dict:
    if skill_id not in skills:
        return _unavailable(skill_id, "执行全文、元数据与证据边界检查")
    return {**skills[skill_id].public(), "status": "ready", "recommendation": "执行全文、元数据与证据边界检查"}


def _unavailable(
    capability_id: str, recommendation: str, reason: str = "not_recognized"
) -> dict:
    return {
        "id": capability_id,
        "status": "unavailable",
        "reason": reason,
        "recommendation": recommendation,
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
