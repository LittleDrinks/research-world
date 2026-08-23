from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).parents[1] / "schemas" / "agent.schema.json"


class RuntimeError(Exception):
    pass


class SessionNotFound(RuntimeError):
    pass


class SessionSpecInvalid(RuntimeError):
    pass


class CapabilityNotFound(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentOptions:
    reasoning_effort: str = "medium"
    sandbox: str = "read-only"
    max_rounds: int = 12
    token_budget: int = 200_000


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    endpoint: str
    model: str
    instructions: str
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    connectors: tuple[str, ...] = ()
    options: AgentOptions = field(default_factory=AgentOptions)

    @classmethod
    def parse(cls, value: dict[str, Any]) -> AgentSpec:
        errors = sorted(
            _validator().iter_errors(value), key=lambda item: list(item.path)
        )
        if errors:
            raise RuntimeError(errors[0].message)
        options = AgentOptions(**value.get("options", {}))
        arrays = {
            key: tuple(value.get(key, [])) for key in ("skills", "tools", "connectors")
        }
        return cls(
            **{key: value[key] for key in _required()}, **arrays, options=options
        )

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


def _required() -> tuple[str, ...]:
    return "id", "name", "endpoint", "model", "instructions"


def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
