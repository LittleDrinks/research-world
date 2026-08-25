from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

Emit = Callable[[str], Awaitable[None]]


class EndpointUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelResult:
    message: dict[str, Any]
    usage: dict[str, int]
    provider_session_id: str | None = None
    provider_items: list[dict[str, Any]] = field(default_factory=list)


class Provider(Protocol):
    id: str

    async def generate(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
        emit: Emit,
        context: dict[str, Any],
    ) -> ModelResult: ...

    async def embed(self, model: str, texts: list[str]) -> list[list[float]]: ...
