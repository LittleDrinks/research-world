from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from .providers.codex import CodexProvider
from .types import CapabilityNotFound

REALM = "container:runtime"


@dataclass(frozen=True)
class RuntimeDescriptor:
    id: str
    realm: str
    display_name: str = ""
    executable: str | None = None
    version: str | None = None
    source: str = "path"
    path: str | None = None
    resolved_path: str | None = None
    last_checked_at: str | None = None
    status: str = "ready"
    capabilities: tuple[str, ...] = ()
    reason: dict[str, str] | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "realm": self.realm,
            "display_name": self.display_name,
            "executable": self.executable,
            "version": self.version,
            "source": self.source,
            "last_checked_at": self.last_checked_at,
            "status": self.status,
            "capabilities": list(self.capabilities),
            "reason": self.reason,
        }


class RuntimeAdapter:
    def __init__(self, descriptor: RuntimeDescriptor, endpoint_ids: tuple[str, ...] = ()):
        self.descriptor = descriptor
        self.endpoint_ids = endpoint_ids

    def accepts(self, endpoint) -> bool:
        endpoint_id = endpoint["id"] if isinstance(endpoint, dict) else endpoint.id
        return endpoint_id in self.endpoint_ids

    @property
    def owns_process(self) -> bool:
        return False

    def cancel(self, session_id: str) -> None:
        return None


class CodexRuntimeAdapter(RuntimeAdapter):
    def __init__(self, provider: CodexProvider):
        super().__init__(_codex_descriptor(provider))
        self.provider = provider
        self._processes: dict[str, object] = {}
        self._cancelled: set[str] = set()
        self._stops: dict[str, asyncio.Task] = {}

    @property
    def owns_process(self) -> bool:
        return True

    def accepts(self, endpoint) -> bool:
        adapter = endpoint["adapter"] if isinstance(endpoint, dict) else endpoint.adapter
        return adapter == "openai-compatible"

    async def generate(
        self, session_id, endpoint, model, messages, tools, emit, context
    ):
        process = None
        try:
            process = await self._start(session_id, model, context)
            result = await self.provider.collect(process, messages, emit)
            return endpoint.id, result
        except BaseException:
            if process is not None:
                await _cleanup(self.provider, process)
            raise
        finally:
            self._unregister(session_id, process)

    async def _start(self, session_id, model, context):
        process = await self.provider.start(model, context)
        self._processes[session_id] = process
        if session_id in self._cancelled:
            self._schedule_stop(session_id, process)
        return process

    def _unregister(self, session_id, process) -> None:
        if process is not None:
            self._processes.pop(session_id, None)
        self._cancelled.discard(session_id)

    def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
        if process := self._processes.get(session_id):
            self._schedule_stop(session_id, process)

    def _schedule_stop(self, session_id, process) -> None:
        if session_id not in self._stops:
            self._stops[session_id] = asyncio.create_task(
                self._stop_registered(session_id, process)
            )

    async def _stop_registered(self, session_id, process) -> None:
        try:
            await _cleanup(self.provider, process)
        finally:
            if self._processes.get(session_id) is process:
                self._processes.pop(session_id, None)
            self._stops.pop(session_id, None)


class RuntimePool:
    def __init__(self, adapters: list[RuntimeAdapter]):
        _validate_adapters(adapters)
        self._values = {(item.descriptor.id, item.descriptor.realm): item for item in adapters}

    def public(self) -> list[dict[str, Any]]:
        return [item.descriptor.public() for item in self._values.values()]

    def require(self, value) -> RuntimeAdapter:
        adapter = self._values.get((value.id, value.realm))
        if adapter is None or adapter.descriptor.status != "ready":
            raise CapabilityNotFound(f"runtime is not available: {value.id}")
        return adapter

    def default(self) -> RuntimeAdapter:
        adapter = next(iter(self._values.values()), None)
        if adapter is None:
            raise CapabilityNotFound("no runtime is available")
        return adapter


def load_runtimes() -> list[RuntimeAdapter]:
    values = [RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ())]
    values.append(CodexRuntimeAdapter(CodexProvider.detected()))
    return values


def _codex_descriptor(provider: CodexProvider) -> RuntimeDescriptor:
    return RuntimeDescriptor(
        "codex",
        REALM,
        "Codex CLI", "codex", provider.version, "path", provider.path,
        provider.resolved_path, provider.last_checked_at, provider.status,
        ("non-interactive", "resume", "model-select",
         "reasoning-select", "workspace", "auth-probe"), provider.reason,
    )


async def _cleanup(provider, process) -> None:
    task = asyncio.create_task(provider.stop(process))
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            continue
    task.result()


def _validate_adapters(adapters: list[RuntimeAdapter]) -> None:
    keys = [(item.descriptor.id, item.descriptor.realm) for item in adapters]
    if len(keys) != len(set(keys)):
        raise ValueError("runtime id and realm must be unique")
    if any(item.descriptor.id == "codex" and not isinstance(item, CodexRuntimeAdapter) for item in adapters):
        raise ValueError("codex runtime requires CodexRuntimeAdapter")
