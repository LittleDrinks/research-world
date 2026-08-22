from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


class PipelineRegistry:
    def __init__(self, root: Path, schema: Path):
        self.root = Path(root)
        self.validator = Draft202012Validator(_json(schema))

    def all(self) -> list[dict]:
        return [self._read(path) for path in sorted(self.root.glob("*.yaml"))]

    def get(self, pipeline_id: str) -> dict:
        path = self._path(pipeline_id)
        if not path.is_file():
            raise KeyError(pipeline_id)
        return self._read(path)

    def save(self, pipeline_id: str, value: dict) -> dict:
        if value.get("id") != pipeline_id:
            raise ValueError("pipeline id cannot change")
        self._validate(value)
        text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False)
        self._path(pipeline_id).write_text(text, encoding="utf-8")
        return self.get(pipeline_id)

    def _path(self, pipeline_id: str) -> Path:
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
        if not pipeline_id or any(char not in allowed for char in pipeline_id):
            raise ValueError("invalid pipeline id")
        return self.root / f"{pipeline_id}.yaml"

    def _read(self, path: Path) -> dict:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError(f"invalid pipeline file: {path.name}")
        self._validate(value)
        return value

    def _validate(self, value: dict) -> None:
        errors = sorted(
            self.validator.iter_errors(value), key=lambda item: list(item.path)
        )
        if errors:
            raise ValueError(errors[0].message)
        ids = [stage["id"] for stage in value["stages"]]
        if len(ids) != len(set(ids)):
            raise ValueError("pipeline stage ids must be unique")


def _json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
