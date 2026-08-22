from __future__ import annotations

import asyncio
import os
import shutil
import tomllib
from pathlib import Path

from .config import codex_config_path
from .mcp_servers import discover_mcp
from .skills import discover_skills

TOOLS = (
    {"id": "read_skill", "name": "读取 Skill"},
    {"id": "read_resource", "name": "读取引用节点"},
    {"id": "read_file", "name": "读取工作区文件"},
    {"id": "write_file", "name": "写入工作区文件"},
)


async def discover(workspace: Path, skill_paths: tuple[Path, ...] = ()) -> dict:
    skills = discover_skills(workspace, skill_paths)
    mcp = discover_mcp(workspace)
    runtimes = await _runtimes()
    return {
        "runtimes": runtimes,
        "models": _models(runtimes),
        "skills": [item.public() for item in skills.values()],
        "tools": list(TOOLS),
        "mcp_servers": [item.public() for item in mcp.values()],
    }


async def _runtimes() -> list[dict]:
    values = [_openai_runtime()]
    codex = await _codex_runtime()
    if codex:
        values.append(codex)
    return values


def _openai_runtime() -> dict:
    available = bool(os.getenv("RUNTIME_API_BASE") and os.getenv("RUNTIME_API_KEY"))
    return {
        "id": "openai-compatible",
        "name": "OpenAI 兼容端点",
        "available": available,
    }


async def _codex_runtime() -> dict | None:
    executable = shutil.which("codex")
    if not executable:
        return None
    process = await asyncio.create_subprocess_exec(
        executable, "--version", stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    return {
        "id": "codex",
        "name": "Codex CLI",
        "available": process.returncode == 0,
        "version": stdout.decode().strip(),
    }


def _models(runtimes: list[dict]) -> list[dict]:
    models = []
    if any(
        item["id"] == "openai-compatible" and item["available"] for item in runtimes
    ):
        models.append(
            {
                "id": os.getenv("RUNTIME_MODEL", "qwen3.7-flash"),
                "runtime": "openai-compatible",
            }
        )
    codex_model = _codex_model()
    if codex_model and any(item["id"] == "codex" for item in runtimes):
        models.append({"id": codex_model, "runtime": "codex"})
    return models


def _codex_model() -> str | None:
    path = codex_config_path()
    if not path.is_file():
        return None
    return tomllib.loads(path.read_text(encoding="utf-8")).get("model")
