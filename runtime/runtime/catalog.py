from __future__ import annotations

from pathlib import Path

from .connectors import Connector, discover_connectors
from .endpoints import Endpoint
from .skills import discover_skills

TOOLS = (
    {"id": "read_skill", "name": "读取 Skill"},
    {"id": "read_resource", "name": "读取引用节点"},
    {"id": "graph_query", "name": "查询研究图谱"},
    {"id": "report_projection", "name": "读取报告投影"},
    {"id": "report_validate", "name": "校验科研报告"},
    {"id": "export_bibtex", "name": "导出 BibTeX"},
    {"id": "submit_observation", "name": "提交人工观测"},
    {"id": "read_file", "name": "读取工作区文件"},
    {"id": "write_file", "name": "写入工作区文件"},
)


async def discover(
    workspace: Path,
    endpoints: list[Endpoint],
    registered: list[Connector],
    skill_paths: tuple[Path, ...] = (),
) -> dict:
    skills = discover_skills(workspace, skill_paths)
    connectors = discover_connectors(workspace, registered)
    values = [item.public() for item in endpoints]
    return {
        "endpoints": values,
        "models": _models(values),
        "skills": [item.public() for item in skills.values()],
        "tools": list(TOOLS),
        "connectors": [item.public() for item in connectors.values()],
    }


def _models(endpoints: list[dict]) -> list[dict]:
    return [
        {"id": model, "endpoint": endpoint["id"]}
        for endpoint in endpoints
        if endpoint["available"]
        for model in endpoint["models"]
    ]
