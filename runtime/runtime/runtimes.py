from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .endpoints import Endpoint
from .providers.codex import CodexProvider
from .types import CapabilityNotFound

REALM = "container:runtime"


@dataclass(frozen=True)
class RuntimeDescriptor:
    id: str
    realm: str
    executable: str | None = None
    version: str | None = None
    status: str = "ready"
    capabilities: tuple[str, ...] = ()

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "realm": self.realm,
            "executable": self.executable,
            "version": self.version,
            "status": self.status,
            "capabilities": list(self.capabilities),
        }


class RuntimeAdapter:
    def __init__(self, descriptor: RuntimeDescriptor):
        self.descriptor = descriptor

    def accepts(self, endpoint) -> bool:
        return endpoint.adapter == self.descriptor.id

    async def generate(
        self, session_id, endpoint, model, messages, tools, emit, context
    ):
        if not self.accepts(endpoint) or endpoint.provider is None:
            raise CapabilityNotFound("endpoint is not available for runtime")
        result = await endpoint.provider.generate(model, messages, tools, emit, context)
        return endpoint.id, result

    def cancel(self, session_id: str) -> None:
        return None


class CodexRuntimeAdapter(RuntimeAdapter):
    def __init__(self, provider: CodexProvider):
        super().__init__(_codex_descriptor(provider))
        self.provider = provider
        self._processes: dict[str, object] = {}
        self._cancelled: set[str] = set()

    async def generate(
        self, session_id, endpoint, model, messages, tools, emit, context
    ):
        if not self.accepts(endpoint):
            raise CapabilityNotFound("endpoint is not available for runtime")
        process = await self.provider.start(model, context)
        self._processes[session_id] = process
        if session_id in self._cancelled:
            self.provider.cancel(process)
        try:
            result = await self.provider.collect(process, messages, emit)
            return endpoint.id, result
        finally:
            self._processes.pop(session_id, None)
            self._cancelled.discard(session_id)

    def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
        if process := self._processes.get(session_id):
            self.provider.cancel(process)


class RuntimePool:
    def __init__(self, adapters: list[RuntimeAdapter]):
        self._values = {
            (item.descriptor.id, item.descriptor.realm): item for item in adapters
        }

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
    values = [RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM))]
    if provider := CodexProvider.detected():
        values.append(CodexRuntimeAdapter(provider))
    return values


def _codex_descriptor(provider: CodexProvider) -> RuntimeDescriptor:
    return RuntimeDescriptor(
        "codex",
        REALM,
        provider.executable,
        provider.version,
        capabilities=("non-interactive", "resume"),
    )


def codex_endpoint(model: str) -> Endpoint:
    return Endpoint("codex", "Codex CLI", "codex", (model,), (), 200, None)
