from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

PRIMITIVES = {
    "collect-sources": ("prompt", (), ("source_candidates",), None, 1),
    "submit-sources": ("tool", ("source_candidates",), ("sources",), None, 1),
    "generate-directions": ("prompt", (), ("origin", "candidates"), None, 1),
    "deduplicate-directions": (
        "tool",
        ("origin", "candidates"),
        ("pool",),
        "cosine-threshold",
        1,
    ),
    "select-directions": ("tool", ("pool",), ("directions",), "mmr", 1),
    "review-directions": (
        "prompt",
        ("directions",),
        (),
        "unanimous-review",
        2,
    ),
    "plan-experiment": ("prompt", (), ("experiment", "steps"), None, 1),
    "execute-experiment": (
        "tool",
        ("experiment", "steps"),
        ("outputs",),
        "mechanical-audit",
        1,
    ),
    "review-experiment": (
        "prompt",
        ("experiment", "outputs"),
        (),
        "unanimous-review",
        2,
    ),
    "reflect-direction": (
        "prompt",
        ("experiment", "outputs"),
        ("directions",),
        None,
        1,
    ),
}

REVIEW_ACTIONS = {
    "approve": "admit",
    "reject": "ghost",
    "conflict": "wait_human",
}


class StagePrimitiveRegistry:
    def __init__(self, handlers: dict | None = None):
        self.handlers = handlers or {}

    def validate(self, pipeline: dict) -> None:
        available: set[str] = set()
        for stage in pipeline["stages"]:
            contract = self._contract(stage)
            self._validate_stage(stage, contract, available)
            available.update(contract[2])
        self._validate_exits(pipeline)

    def execute(self, stage: dict, context: dict):
        primitive = _stage_primitive(stage)
        if primitive not in self.handlers:
            raise ValueError(f"stage primitive has no executor: {primitive}")
        return self.handlers[primitive](stage, context)

    def _contract(self, stage: dict) -> tuple:
        if stage["type"] == "spawn":
            raise ValueError("unsupported stage type: spawn")
        primitive = _stage_primitive(stage)
        if primitive not in PRIMITIVES:
            raise ValueError(f"unknown stage primitive: {primitive}")
        return PRIMITIVES[primitive]

    def _validate_stage(self, stage, contract, available) -> None:
        stage_type, requires, _, policy, repeat = contract
        primitive = _stage_primitive(stage)
        if stage["type"] != stage_type:
            raise ValueError(f"primitive {primitive} requires type {stage_type}")
        missing = set(requires) - available
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"primitive {primitive} requires stage values: {names}")
        self._validate_options(stage, policy, repeat)

    def _validate_options(self, stage, expected_policy, expected_repeat) -> None:
        primitive = _stage_primitive(stage)
        policy = _policy_name(stage.get("policy"))
        if policy != expected_policy:
            raise ValueError(f"primitive {primitive} requires policy {expected_policy}")
        if stage.get("repeat", 1) != expected_repeat:
            raise ValueError(f"primitive {primitive} requires repeat {expected_repeat}")

    def _validate_exits(self, pipeline: dict) -> None:
        stages = pipeline["stages"]
        stage_ids = {stage["id"] for stage in stages}
        for stage in pipeline["stages"]:
            primitive = _stage_primitive(stage)
            exits = stage.get("on", {})
            self._validate_outcomes(primitive, exits)
            for outcome, exit_value in exits.items():
                self._validate_exit(outcome, exit_value, stage_ids, primitive)
                self._validate_route(stage, exit_value, stages)

    def _validate_outcomes(self, primitive, exits) -> None:
        expected = set(REVIEW_ACTIONS) if primitive.startswith("review-") else {"next"}
        if exits and set(exits) != expected:
            raise ValueError(
                f"primitive {primitive} requires on outcomes: {', '.join(sorted(expected))}"
            )
        if primitive.startswith("review-") and not exits:
            raise ValueError(f"primitive {primitive} requires on outcomes")

    def _validate_exit(self, outcome, value, stage_ids, primitive) -> None:
        if isinstance(value, str):
            target = value
        else:
            if ("action" in value) == ("next" in value):
                raise ValueError("pipeline exit requires exactly one action or next")
            target = value.get("next")
        if target and target not in stage_ids:
            raise ValueError(f"unknown next stage: {target}")
        self._validate_action(outcome, value, primitive)

    def _validate_action(self, outcome, value, primitive) -> None:
        action = value.get("action") if isinstance(value, dict) else None
        expected = (
            REVIEW_ACTIONS.get(outcome) if primitive.startswith("review-") else None
        )
        if action != expected:
            raise ValueError(f"primitive {primitive} requires action {expected}")

    def _validate_route(self, source, value, stages) -> None:
        target = value if isinstance(value, str) else value.get("next")
        if not target:
            return
        source_index = _stage_index(stages, source["id"])
        target_index = _stage_index(stages, target)
        if target_index <= source_index:
            raise ValueError("pipeline stage routes must move forward")
        available = _available_after(stages, source_index)
        required = set(self._contract(stages[target_index])[1])
        if missing := required - available:
            raise ValueError(
                f"route to {target} misses stage values: {', '.join(sorted(missing))}"
            )


class PipelineRegistry:
    def __init__(self, root: Path, schema: Path, primitives=None):
        self.root = Path(root)
        self.validator = Draft202012Validator(_json(schema))
        self.primitives = primitives or StagePrimitiveRegistry()

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
        self.primitives.validate(value)


def _json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _policy_name(value) -> str | None:
    if isinstance(value, str) or value is None:
        return value
    return value["name"]


def _stage_primitive(stage: dict) -> str:
    return stage["prompt"] if stage["type"] == "prompt" else stage["tool"]


def _stage_index(stages: list[dict], stage_id: str) -> int:
    return next(index for index, stage in enumerate(stages) if stage["id"] == stage_id)


def _available_after(stages: list[dict], index: int) -> set[str]:
    available = set()
    for stage in stages[: index + 1]:
        available.update(PRIMITIVES[_stage_primitive(stage)][2])
    return available
