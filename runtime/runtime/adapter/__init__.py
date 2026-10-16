from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol


class RuntimeAdapter(Protocol):
    adapter_id: str
    supports_multiple_writers: bool

    async def start(self, request: TurnRequest) -> Any: ...

    async def submit(
        self,
        handle: Any,
        request: TurnRequest,
        emit: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> AdapterResult: ...

    async def cancel(self, handle: Any, request: TurnRequest) -> Any: ...

    async def close(self) -> None: ...


@dataclass(frozen=True)
class TurnRequest:
    run_id: str
    turn_id: str
    message_id: str
    input: Any
    context: tuple[dict[str, Any], ...]
    agent_snapshot: dict[str, Any]
    tools: Any


@dataclass(frozen=True)
class AdapterResult:
    status: str = "completed"
    result_text: str | None = None


__all__ = ["AdapterResult", "RuntimeAdapter", "TurnRequest"]
