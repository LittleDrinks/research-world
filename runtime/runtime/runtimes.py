from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from .providers.codex import CodexProvider
from .providers.pi import PiProvider
from .types import CapabilityNotFound, TraceError

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
    def __init__(
        self, descriptor: RuntimeDescriptor, endpoint_adapters: tuple[str, ...] = ()
    ):
        self.descriptor = descriptor
        self.endpoint_adapters = endpoint_adapters

    def accepts(self, endpoint) -> bool:
        adapter = endpoint["adapter"] if isinstance(endpoint, dict) else endpoint.adapter
        return adapter in self.endpoint_adapters

    @property
    def owns_process(self) -> bool:
        return False

    def cancel(self, session_id: str) -> None:
        return None

    async def close(self) -> None:
        return None

    def release(self) -> None:
        return None


class ProcessRuntimeAdapter(RuntimeAdapter):
    def __init__(self, descriptor, endpoint_adapters, provider):
        super().__init__(descriptor, endpoint_adapters)
        self.provider = provider
        self._processes: dict[str, object] = {}
        self._starts: dict[str, asyncio.Task] = {}
        self._cancelled: set[str] = set()
        self._stops: dict[str, asyncio.Task] = {}
        self._stopped: dict[str, object] = {}
        self._closing = False
        self._close_task: asyncio.Task | None = None

    @property
    def owns_process(self) -> bool:
        return True

    async def generate(
        self, session_id, endpoint, model, messages, tools, emit, context
    ):
        process = None
        try:
            process = await self._start(session_id, model, context, messages)
            collected = await self.provider.collect(
                process, messages, emit, (context.get("provider_session_id"),)
            )
            return endpoint.id, collected.result, collected.continuation_id
        except BaseException:
            if process is not None and not self._closing:
                await self._stop(session_id, process)
            raise
        finally:
            self._unregister(session_id, process)

    async def _start(self, session_id, model, context, messages):
        if self._closing:
            raise self._closed_error()
        task = asyncio.create_task(self._provider_start(model, context, messages))
        self._starts[session_id] = task
        try:
            process = await task
            if self._closing:
                await self._stop(session_id, process)
                raise self._closed_error()
            self._processes[session_id] = process
            if session_id in self._cancelled:
                self._schedule_stop(session_id, process)
            return process
        finally:
            if self._starts.get(session_id) is task:
                self._starts.pop(session_id)

    def _closed_error(self) -> TraceError:
        name = self.descriptor.id
        return TraceError("runtime_closed", f"{name} runtime is closed")

    async def _provider_start(self, model, context, messages):
        return await self.provider.start(model, context)

    def _unregister(self, session_id, process) -> None:
        if self._processes.get(session_id) is process:
            self._processes.pop(session_id, None)
        self._stopped.pop(session_id, None)
        self._cancelled.discard(session_id)

    def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
        if process := self._processes.get(session_id):
            self._schedule_stop(session_id, process)

    def _schedule_stop(self, session_id, process) -> None:
        if self._stopped.get(session_id) is process:
            return
        if session_id not in self._stops:
            self._stops[session_id] = asyncio.create_task(
                self._stop_registered(session_id, process)
            )

    async def close(self) -> None:
        if self._close_task is None:
            self._closing = True
            self._close_task = asyncio.create_task(self._close())
        await asyncio.shield(self._close_task)

    async def _close(self) -> None:
        try:
            self._stop_active()
            await self._stop_pending()
            await self._wait_stops()
        finally:
            self._starts.clear()
            self._processes.clear()
            self._stops.clear()
            self._stopped.clear()
            self.release()

    def _stop_active(self) -> None:
        self._cancelled.update(self._processes)
        for session_id, process in tuple(self._processes.items()):
            self._schedule_stop(session_id, process)

    async def _stop_pending(self) -> None:
        starts = tuple(self._starts.items())
        results = await asyncio.gather(
            *(task for _, task in starts), return_exceptions=True
        )
        for (session_id, _), process in zip(starts, results):
            if not isinstance(process, BaseException):
                self._schedule_stop(session_id, process)

    async def _wait_stops(self) -> None:
        errors = []
        while stops := tuple(self._stops.values()):
            results = await asyncio.gather(*stops, return_exceptions=True)
            errors.extend(value for value in results if isinstance(value, BaseException))
        if errors:
            raise errors[0]

    async def _stop(self, session_id, process) -> None:
        self._schedule_stop(session_id, process)
        if task := self._stops.get(session_id):
            await _wait_task(task)

    def release(self) -> None:
        self.provider.close()

    def __del__(self):
        self.release()

    async def _stop_registered(self, session_id, process) -> None:
        try:
            await _cleanup(self.provider, process)
            self._stopped[session_id] = process
        finally:
            if self._processes.get(session_id) is process:
                self._processes.pop(session_id, None)
            self._stops.pop(session_id, None)


class CodexRuntimeAdapter(ProcessRuntimeAdapter):
    def __init__(self, provider: CodexProvider):
        super().__init__(
            _codex_descriptor(provider), ("openai-compatible",), provider
        )


class PiRuntimeAdapter(ProcessRuntimeAdapter):
    def __init__(self, provider: PiProvider):
        super().__init__(_pi_descriptor(provider), ("pi",), provider)

    async def _provider_start(self, model, context, messages):
        return await self.provider.start(model, context, messages)


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

    def values(self) -> list[RuntimeAdapter]:
        return list(self._values.values())

    async def close(self) -> None:
        for adapter in self._values.values():
            await adapter.close()

    def release(self) -> None:
        for adapter in self._values.values():
            adapter.release()


def load_runtimes() -> list[RuntimeAdapter]:
    values = [RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))]
    values.append(CodexRuntimeAdapter(CodexProvider.detected()))
    values.append(PiRuntimeAdapter(PiProvider.detected()))
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


def _pi_descriptor(provider: PiProvider) -> RuntimeDescriptor:
    return RuntimeDescriptor(
        "pi", REALM, "Pi CLI", "pi", provider.version, "path", provider.path,
        provider.resolved_path, provider.last_checked_at, provider.status,
        ("rpc", "streaming", "resume", "model-select", "reasoning-select",
         "workspace", "native-tools"), provider.reason,
    )


async def _cleanup(provider, process) -> None:
    task = asyncio.create_task(provider.stop(process))
    await _wait_task(task)


async def _wait_task(task) -> None:
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
    required = {"codex": CodexRuntimeAdapter, "pi": PiRuntimeAdapter}
    for item in adapters:
        expected = required.get(item.descriptor.id)
        if expected is not None and not isinstance(item, expected):
            raise ValueError(f"{item.descriptor.id} runtime requires {expected.__name__}")
