from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database: Path
    artifacts: Path
    projects_root: Path
    agents_root: Path
    pipelines_root: Path
    pipeline_schema: Path
    runtime_url: str


def load_settings() -> Settings:
    data = Path(os.getenv("RW_DATA_ROOT", ROOT / "data"))
    return Settings(
        database=data / "research-world.db",
        artifacts=data / "artifacts",
        projects_root=Path(os.getenv("RW_PROJECTS_ROOT", ROOT / "projects")),
        agents_root=Path(os.getenv("RW_AGENTS_ROOT", ROOT / "agents")),
        pipelines_root=Path(os.getenv("RW_PIPELINES_ROOT", ROOT / "pipelines")),
        pipeline_schema=ROOT / "schemas" / "pipeline.schema.json",
        runtime_url=os.getenv("RUNTIME_URL", "http://runtime:8098"),
    )
