from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .providers.base import Emit, EndpointUnavailable
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
        self._sessions: dict[str, object] = {}
        self._cancelled: set[str] = set()

    def accepts(self, endpoint) -> bool:
        return endpoint.adapter == self.descriptor.id

    async def generate(
        self, session_id, endpoints, model, messages, tools, emit, context
    ):
        if not all(self.accepts(endpoint) for endpoint in endpoints):
            raise CapabilityNotFound("endpoint is not available for runtime")
        return await self._generate(
            session_id, endpoints, model, messages, tools, emit, context
        )

    async def _generate(
        self, session_id, endpoints, model, messages, tools, emit, context
    ):
        last_error = None
        for endpoint in endpoints:
            self._sessions[session_id] = endpoint.provider
            relay = _Emission(emit)
            try:
                result = await endpoint.provider.generate(
                    model, messages, tools, relay, context
                )
                return endpoint.id, result
            except EndpointUnavailable as error:
                if relay.sent:
                    raise
                last_error = error
            finally:
                self._sessions.pop(session_id, None)
        self._cancelled.discard(session_id)
        raise last_error

    def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
        cancel = getattr(self._sessions.get(session_id), "cancel", None)
        if cancel:
            cancel(session_id)


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
        values.append(RuntimeAdapter(_codex_descriptor(provider)))
    return values


def _codex_descriptor(provider: CodexProvider) -> RuntimeDescriptor:
    return RuntimeDescriptor(
        "codex", REALM, provider.executable, provider.version,
        capabilities=("non-interactive", "streaming", "resume"),
    )


class _Emission:
    def __init__(self, emit: Emit):
        self.emit = emit
        self.sent = False

    async def __call__(self, text: str) -> None:
        self.sent = True
        await self.emit(text)
