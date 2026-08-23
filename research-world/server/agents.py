from __future__ import annotations

from pathlib import Path

import yaml


class AgentRegistry:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[dict]:
        return [self._read(path) for path in sorted(self.root.glob("*.yaml"))]

    def get(self, agent_id: str) -> dict:
        path = self._path(agent_id)
        if not path.is_file():
            raise KeyError(agent_id)
        return self._read(path)

    def create(self, value: dict) -> dict:
        self.validate_new(value)
        self._path(value["id"]).write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return self.get(value["id"])

    def save(self, agent_id: str, value: dict) -> dict:
        if value.get("id") != agent_id:
            raise ValueError("agent id cannot change")
        if not self._path(agent_id).is_file():
            raise KeyError(agent_id)
        self._path(agent_id).write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return self.get(agent_id)

    def validate_new(self, value: dict) -> None:
        agent_id = value.get("id")
        if not isinstance(agent_id, str):
            raise ValueError("invalid agent id")
        if self._path(agent_id).exists():
            raise ValueError(f"agent already exists: {agent_id}")
        for key in ("name", "instructions"):
            if not str(value.get(key) or "").strip():
                raise ValueError(f"agent {key} is required")

    def _path(self, agent_id: str) -> Path:
        if not agent_id or any(
            char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in agent_id
        ):
            raise ValueError("invalid agent id")
        return self.root / f"{agent_id}.yaml"

    def _read(self, path: Path) -> dict:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError(f"invalid agent file: {path.name}")
        return value
