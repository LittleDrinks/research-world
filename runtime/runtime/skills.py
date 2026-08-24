from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import codex_config_path


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str
    path: Path
    source: str

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
        }

    def body(self) -> str:
        return _split(self.path.read_text(encoding="utf-8"))[1].strip()


def discover_skills(
    workspace: Path, extra_paths: tuple[Path, ...] = ()
) -> dict[str, Skill]:
    found: dict[str, Skill] = {}
    for source, path in _candidates(workspace, extra_paths):
        for skill_file in _skill_files(path):
            skill = _load(skill_file, source)
            if skill and skill.id not in found:
                found[skill.id] = skill
    return found


def skill_index(skills: list[Skill]) -> str:
    rows = [f"- {skill.id}: {skill.description}" for skill in skills]
    return (
        "Available skills (read with read_skill when needed):\n" + "\n".join(rows)
        if rows
        else ""
    )


def _candidates(workspace: Path, extra_paths: tuple[Path, ...]):
    configured = [
        Path(item)
        for item in os.getenv("RUNTIME_SKILLS_PATHS", "").split(os.pathsep)
        if item
    ]
    local = [
        workspace / ".agents" / "skills",
        Path("/app/skills"),
        Path.home() / ".agents" / "skills",
    ]
    direct = [("workspace", path) for path in [*extra_paths, *configured, *local]]
    return [*direct, *(("codex", path) for path in _codex_skill_files())]


def _skill_files(path: Path):
    if path.name == "SKILL.md" and path.is_file():
        return [path]
    if not path.is_dir():
        return []
    return sorted(path.glob("*/SKILL.md"))


def _load(path: Path, source: str) -> Skill | None:
    frontmatter, _ = _split(path.read_text(encoding="utf-8"))
    data = yaml.safe_load(frontmatter) or {}
    name = str(data.get("name") or path.parent.name)
    description = str(data.get("description") or "").strip()
    if not description:
        return None
    return Skill(name, name, description, path.resolve(), source)


def _split(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    parts = text.split("---", 2)
    return parts[1], parts[2] if len(parts) > 2 else ""


def _codex_skill_files() -> list[Path]:
    config = codex_config_path()
    if not config.is_file():
        return []
    data = tomllib.loads(config.read_text(encoding="utf-8"))
    rows = (data.get("skills") or {}).get("config") or []
    return [Path(row["path"]) for row in rows if row.get("path")]
