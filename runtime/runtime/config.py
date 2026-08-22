from __future__ import annotations

import os
import shutil
from pathlib import Path


def codex_config_path() -> Path:
    explicit = os.getenv("CODEX_CONFIG")
    if explicit:
        return Path(explicit)
    home = Path(os.getenv("CODEX_HOME", Path.home() / ".codex"))
    return home / "config.toml"


def prepare_codex_home() -> None:
    source_value = os.getenv("CODEX_SOURCE")
    target_value = os.getenv("CODEX_HOME")
    if not source_value or not target_value:
        return
    source, target = Path(source_value), Path(target_value)
    if not source.is_dir():
        return
    target.mkdir(parents=True, exist_ok=True)
    for name in ("config.toml", "auth.json"):
        _copy_private(source / name, target / name)


def _copy_private(source: Path, target: Path) -> None:
    if not source.is_file():
        return
    shutil.copyfile(source, target)
    target.chmod(0o600)
