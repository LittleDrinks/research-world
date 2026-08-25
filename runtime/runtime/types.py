from __future__ import annotations

import builtins
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).parents[1] / "schemas" / "agent.schema.json"


class RuntimeError(builtins.RuntimeError):
    pass


class SessionNotFound(RuntimeError):
    pass


class SessionSpecInvalid(RuntimeError):
    pass


class CapabilityNotFound(RuntimeError):
    pass


class TraceError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ToolPlanDrift(SessionSpecInvalid):
    pass


@dataclass(frozen=True)
class AgentOptions:
    reasoning_effort: str = "medium"
    sandbox: str = "read-only"
    max_rounds: int = 12
    token_budget: int = 200_000


@dataclass(frozen=True)
class RuntimeRef:
    id: str
    realm: str


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    runtime: RuntimeRef
    endpoint: str
    model: str
    instructions: str
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    options: AgentOptions = field(default_factory=AgentOptions)

    @classmethod
    def parse(cls, value: dict[str, Any]) -> AgentSpec:
        errors = sorted(
            _validator().iter_errors(value), key=lambda item: list(item.path)
        )
        if errors:
            raise RuntimeError(errors[0].message)
        options = AgentOptions(**value.get("options", {}))
        arrays = {key: tuple(value.get(key, [])) for key in ("skills", "tools")}
        runtime = RuntimeRef(**value["runtime"])
        return cls(
            **{key: value[key] for key in _required()}, runtime=runtime, **arrays, options=options
        )

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


def _required() -> tuple[str, ...]:
    return "id", "name", "endpoint", "model", "instructions"


def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
