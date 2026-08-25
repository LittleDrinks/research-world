from __future__ import annotations

import json
import os
import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import codex_config_path
from .providers import CodexProvider, OpenAIProvider
from .providers.base import Emit, EndpointUnavailable, ModelResult, Provider
from .types import CapabilityNotFound

ENDPOINT_ID = re.compile(r"^[a-z][a-z0-9-]*$")
ENV_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
ENDPOINT_FIELDS = {
    "id",
    "name",
    "adapter",
    "models",
    "embedding_models",
    "base_url_env",
    "api_key_env",
    "priority",
}


@dataclass(frozen=True)
class Endpoint:
    id: str
    name: str
    adapter: str
    models: tuple[str, ...]
    embedding_models: tuple[str, ...]
    priority: int
    provider: Provider | None
    base_url_env: str | None = None
    api_key_env: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "adapter": self.adapter,
            "models": list(self.models),
            "embedding_models": list(self.embedding_models),
            "priority": self.priority,
            "available": self.provider is not None,
        }


class EndpointPool:
    def __init__(self, endpoints: Iterable[Endpoint]):
        values = list(endpoints)
        if len({item.id for item in values}) != len(values):
            raise ValueError("endpoint ids must be unique")
        self._values = {item.id: item for item in values}

    def public(self) -> list[dict[str, Any]]:
        return [item.public() for item in self._ordered()]

    def values(self) -> list[Endpoint]:
        return self._ordered()

    def require(self, endpoint_id: str, model: str) -> Endpoint:
        return self._require(endpoint_id, model, "models", "model")

    def require_embedding(self, endpoint_id: str, model: str) -> Endpoint:
        return self._require(
            endpoint_id, model, "embedding_models", "embedding model"
        )

    def candidates(self, endpoint_id: str, model: str) -> list[Endpoint]:
        endpoint = self.require(endpoint_id, model)
        return self._candidates(endpoint, model, "models")

    def _require(self, endpoint_id, model, field, capability) -> Endpoint:
        endpoint = self._values.get(endpoint_id)
        if endpoint is None:
            raise CapabilityNotFound(f"endpoint is not available: {endpoint_id}")
        if model not in getattr(endpoint, field):
            raise CapabilityNotFound(
                f"{capability} is not available on endpoint: {model}"
            )
        if not self._candidates(endpoint, model, field):
            raise CapabilityNotFound(f"endpoint is not available: {endpoint_id}")
        return endpoint

    def default(self) -> Endpoint:
        endpoint = next(
            (item for item in self._ordered() if item.provider and item.models), None
        )
        if endpoint is None:
            raise CapabilityNotFound("no model endpoint is available")
        return endpoint

    def default_for(self, adapter: str) -> Endpoint:
        endpoint = next(
            (item for item in self._ordered() if item.adapter == adapter and item.provider and item.models),
            None,
        )
        if endpoint is None:
            raise CapabilityNotFound("no model endpoint is available for runtime")
        return endpoint

    async def generate(
        self, endpoint_id, model, messages, tools, emit: Emit, context
    ) -> tuple[str, ModelResult]:
        endpoint = self.require(endpoint_id, model)
        last_error = None
        for candidate in self._candidates(endpoint, model, "models"):
            relay = _Emission(emit)
            try:
                result = await candidate.provider.generate(
                    model, messages, tools, relay, context
                )
                return candidate.id, result
            except EndpointUnavailable as error:
                if relay.sent:
                    raise
                last_error = error
        raise last_error or CapabilityNotFound(
            f"endpoint is not available: {endpoint_id}"
        )

    async def embed(self, endpoint_id: str, model: str, texts: list[str]):
        endpoint = self.require_embedding(endpoint_id, model)
        last_error = None
        for candidate in self._candidates(endpoint, model, "embedding_models"):
            try:
                return await candidate.provider.embed(model, texts)
            except EndpointUnavailable as error:
                last_error = error
        raise last_error or CapabilityNotFound(
            f"endpoint is not available: {endpoint_id}"
        )

    def _ordered(self) -> list[Endpoint]:
        return sorted(self._values.values(), key=lambda item: (item.priority, item.id))

    def _candidates(self, endpoint: Endpoint, model: str, field: str) -> list[Endpoint]:
        values = [
            item
            for item in self._ordered()
            if item.adapter == endpoint.adapter
            and model in getattr(item, field)
            and item.provider
        ]
        return sorted(values, key=lambda item: item.id != endpoint.id)


class _Emission:
    def __init__(self, emit: Emit):
        self.emit = emit
        self.sent = False

    async def __call__(self, text: str) -> None:
        self.sent = True
        await self.emit(text)


def provider_endpoint(
    provider: Provider,
    models: tuple[str, ...],
    endpoint_id: str | None = None,
    priority: int = 100,
    embedding_models: tuple[str, ...] = (),
) -> Endpoint:
    value = endpoint_id or provider.id
    return Endpoint(
        value, value, provider.id, models, embedding_models, priority, provider
    )


def load_endpoints() -> list[Endpoint]:
    values = [_openai_endpoint(row) for row in _endpoint_rows()]
    codex = _codex_endpoint()
    return [*values, *([codex] if codex else [])]


def _endpoint_rows() -> list[dict[str, Any]]:
    encoded = os.getenv("RUNTIME_ENDPOINTS")
    if encoded:
        rows = json.loads(encoded)
        if not isinstance(rows, list):
            raise ValueError("RUNTIME_ENDPOINTS must be a JSON array")
        return rows
    return [_default_openai_row()]


def _default_openai_row() -> dict[str, Any]:
    return {
        "id": "openai-compatible",
        "name": "OpenAI Compatible",
        "adapter": "openai-compatible",
        "models": [os.getenv("RUNTIME_MODEL", "qwen3.7-flash")],
        "embedding_models": [
            os.getenv("RUNTIME_EMBEDDING_MODEL", "qwen3.7-text-embedding")
        ],
        "base_url_env": "RUNTIME_API_BASE",
        "api_key_env": "RUNTIME_API_KEY",
        "priority": 100,
    }


def _openai_endpoint(row: dict[str, Any]) -> Endpoint:
    _validate_endpoint_row(row)
    adapter = row.get("adapter", "openai-compatible")
    if adapter != "openai-compatible":
        raise ValueError(f"unsupported endpoint adapter: {adapter}")
    provider = _openai_provider(row)
    return Endpoint(
        row["id"],
        row.get("name", row["id"]),
        adapter,
        tuple(row.get("models", [])),
        tuple(row.get("embedding_models", [])),
        row.get("priority", 100),
        provider,
        row["base_url_env"],
        row["api_key_env"],
    )


def _openai_provider(row: dict[str, Any]) -> OpenAIProvider | None:
    base_url = os.getenv(row["base_url_env"], "")
    api_key = os.getenv(row["api_key_env"], "")
    parsed = urlparse(base_url)
    if base_url and (parsed.scheme not in {"http", "https"} or not parsed.netloc):
        raise ValueError("endpoint base url must be absolute http(s)")
    return OpenAIProvider(base_url, api_key) if base_url and api_key else None


def _validate_endpoint_row(row: dict[str, Any]) -> None:
    if not isinstance(row, dict) or set(row) - ENDPOINT_FIELDS:
        raise ValueError("invalid endpoint definition")
    _validate_endpoint_id(row.get("id"))
    models = row.get("models", [])
    embedding_models = row.get("embedding_models", [])
    if not _models(models):
        raise ValueError("endpoint models must be unique non-empty strings")
    if not _models(embedding_models):
        raise ValueError("endpoint embedding models must be unique non-empty strings")
    if not models and not embedding_models:
        raise ValueError("endpoint must expose at least one model")
    _validate_endpoint_env(row)
    _validate_priority(row.get("priority", 100))


def _validate_endpoint_id(value) -> None:
    endpoint_id = str(value or "")
    if len(endpoint_id) > 64 or not ENDPOINT_ID.fullmatch(endpoint_id):
        raise ValueError("invalid endpoint id")


def _validate_endpoint_env(row: dict[str, Any]) -> None:
    for key in ("base_url_env", "api_key_env"):
        if not ENV_NAME.fullmatch(str(row.get(key, ""))):
            raise ValueError(f"invalid {key}")


def _validate_priority(priority) -> None:
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise TypeError("endpoint priority must be an integer")
    if priority < 0:
        raise ValueError("endpoint priority must be non-negative")


def _models(value) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and item for item in value)
        and len(set(value)) == len(value)
    )


def _codex_endpoint() -> Endpoint | None:
    provider = CodexProvider.detected()
    if provider is None:
        return None
    model = os.getenv("CODEX_MODEL") or _codex_model() or "gpt-5.6-sol"
    return Endpoint("codex", "Codex CLI", "codex", (model,), (), 200, provider)


def _codex_model() -> str | None:
    path = codex_config_path()
    if not Path(path).is_file():
        return None
    return tomllib.loads(Path(path).read_text(encoding="utf-8")).get("model")
