import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    database: Path
    artifacts: Path
    projects_root: Path
    runtime_url: str


def load_settings():
    data = Path(os.getenv('RW_DATA_ROOT', ROOT / 'data'))
    return Settings(data / 'research-world.db', data / 'artifacts',
                    Path(os.getenv('RW_PROJECTS_ROOT', ROOT / 'projects')),
                    os.getenv('RUNTIME_URL', 'http://runtime:8098'))
