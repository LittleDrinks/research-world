import json

import pytest
from runtime.endpoints import EndpointPool, load_endpoints
from runtime.providers.base import EndpointUnavailable
from runtime.service import Runtime
from runtime.types import CapabilityNotFound
from tests.helpers import FakeProvider, endpoint


def spec(endpoint_id="primary", model="shared-model"):
    return {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "openai-compatible", "realm": "container:runtime"},
        "endpoint": endpoint_id,
        "model": model,
        "instructions": "Answer from evidence.",
    }


def runtime_with(tmp_path, *endpoints):
    return Runtime(tmp_path / "data", list(endpoints))


def failover_runtime(tmp_path, primary, backup, model="shared-model"):
    return runtime_with(
        tmp_path,
        endpoint(primary, "primary", (model,), 10),
        endpoint(backup, "backup", (model,), 20),
    )


async def prompt(runtime, tmp_path):
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})
    result = await runtime.prompt(
        launched["session_id"], [{"type": "text", "text": "answer"}]
    )
    return result, runtime.inspect(launched["session_id"])


def response_endpoint(view):
    response = next(item for item in view["events"] if item["type"] == "model_response")
    return response["data"]["endpoint"]


def configured_row(**values):
    row = {
        "id": "primary",
        "name": "Primary",
        "adapter": "openai-compatible",
        "models": ["shared-model"],
        "embedding_models": ["embed-model"],
        "base_url_env": "PRIMARY_BASE_URL",
        "api_key_env": "PRIMARY_API_KEY",
        "priority": 10,
    }
    row.update(values)
    return row


async def test_fails_over_to_prioritized_endpoint_for_same_model(tmp_path):
    primary = FakeProvider([EndpointUnavailable("primary unavailable")])
    backup = FakeProvider([{"role": "assistant", "content": "recovered"}])
    runtime = failover_runtime(tmp_path, primary, backup)

    result, view = await prompt(runtime, tmp_path)

    assert result["result_text"] == "recovered"
    assert response_endpoint(view) == "backup"
    assert len(primary.requests) == len(backup.requests) == 1


async def test_orders_fallback_endpoints_by_priority(tmp_path):
    primary = FakeProvider([EndpointUnavailable("primary unavailable")])
    early = FakeProvider([{"role": "assistant", "content": "early"}])
    late = FakeProvider([{"role": "assistant", "content": "late"}])
    runtime = runtime_with(
        tmp_path,
        endpoint(primary, "primary", ("shared-model",), 10),
        endpoint(late, "late", ("shared-model",), 30),
        endpoint(early, "early", ("shared-model",), 20),
    )

    result, view = await prompt(runtime, tmp_path)

    assert result["result_text"] == "early"
    assert response_endpoint(view) == "early"
    assert not late.requests


async def test_does_not_fail_over_to_endpoint_for_another_model(tmp_path):
    primary = FakeProvider([EndpointUnavailable("primary unavailable")])
    other = FakeProvider([{"role": "assistant", "content": "wrong"}])
    runtime = runtime_with(
        tmp_path,
        endpoint(primary, "primary", ("shared-model",), 10),
        endpoint(other, "other", ("other-model",), 20),
    )
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    with pytest.raises(EndpointUnavailable, match="primary unavailable"):
        await runtime.prompt(
            launched["session_id"], [{"type": "text", "text": "answer"}]
        )

    assert not other.requests


async def test_does_not_fail_over_after_streaming_starts(tmp_path):
    primary = PartialFailureProvider([])
    backup = FakeProvider([{"role": "assistant", "content": "duplicate"}])
    runtime = failover_runtime(tmp_path, primary, backup)
    emitted = Collector()
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    with pytest.raises(EndpointUnavailable, match="stream interrupted"):
        await runtime.prompt(
            launched["session_id"],
            [{"type": "text", "text": "answer"}],
            emit=emitted,
        )

    assert emitted == ["partial"]
    assert not backup.requests


async def test_does_not_fail_over_non_transient_endpoint_error(tmp_path):
    primary = FakeProvider([RuntimeError("bad request")])
    backup = FakeProvider([{"role": "assistant", "content": "wrong"}])
    runtime = failover_runtime(tmp_path, primary, backup)

    with pytest.raises(RuntimeError, match="bad request"):
        await prompt(runtime, tmp_path)

    assert not backup.requests


def test_endpoint_settings_reference_environment_without_exposing_key(monkeypatch):
    monkeypatch.setenv("RUNTIME_ENDPOINTS", json.dumps([configured_row()]))
    monkeypatch.setenv("PRIMARY_BASE_URL", "https://model.test/v1")
    monkeypatch.setenv("PRIMARY_API_KEY", "top-secret")

    configured = load_endpoints()[0]
    public = configured.public()

    assert public["id"] == "primary"
    assert public["models"] == ["shared-model"]
    assert public["embedding_models"] == ["embed-model"]
    assert configured.api_key_env == "PRIMARY_API_KEY"
    assert "top-secret" not in str(public)
    assert "PRIMARY_API_KEY" not in str(public)


def test_endpoint_settings_reject_inline_credentials(monkeypatch):
    row = configured_row(api_key="top-secret")
    monkeypatch.setenv("RUNTIME_ENDPOINTS", json.dumps([row]))

    with pytest.raises(ValueError, match="invalid endpoint definition"):
        load_endpoints()


async def test_embedding_requires_an_endpoint_id(tmp_path):
    provider = FakeProvider([])
    runtime = Runtime(
        tmp_path / "data",
        [endpoint(provider, "embedding", (), embedding_models=("embed-model",))],
    )

    vectors = await runtime.embed("embedding", "embed-model", ["one", "two"])

    assert vectors == [[0.0], [1.0]]


async def test_embedding_fails_over_for_same_model(tmp_path):
    primary = FailedEmbeddingProvider([])
    backup = FakeProvider([])
    runtime = runtime_with(
        tmp_path,
        endpoint(primary, "primary", ("primary-chat",), 10, ("embed-model",)),
        endpoint(backup, "backup", ("backup-chat",), 20, ("embed-model",)),
    )

    vectors = await runtime.embed("primary", "embed-model", ["proof"])

    assert vectors == [[0.0]]
    assert len(primary.embedding_requests) == len(backup.embedding_requests) == 1


async def test_generation_rejects_embedding_only_model():
    provider = FakeProvider([{"role": "assistant", "content": "wrong"}])
    pool = EndpointPool(
        [endpoint(provider, "primary", ("chat-model",), 10, ("embed-model",))]
    )

    with pytest.raises(CapabilityNotFound, match="model is not available"):
        await pool.generate("primary", "embed-model", [], [], Collector(), {})

    assert not provider.requests


async def test_embedding_rejects_chat_only_model():
    provider = FakeProvider([])
    pool = EndpointPool(
        [endpoint(provider, "primary", ("chat-model",), 10, ("embed-model",))]
    )

    with pytest.raises(CapabilityNotFound, match="embedding model is not available"):
        await pool.embed("primary", "chat-model", ["proof"])

    assert not provider.embedding_requests


async def test_embedding_does_not_fail_over_to_chat_model_match():
    primary = FailedEmbeddingProvider([])
    backup = FakeProvider([])
    pool = EndpointPool(
        [
            endpoint(primary, "primary", (), 10, ("embed-model",)),
            endpoint(backup, "backup", ("embed-model",), 20),
        ]
    )

    with pytest.raises(EndpointUnavailable, match="embedding unavailable"):
        await pool.embed("primary", "embed-model", ["proof"])

    assert not backup.embedding_requests


def test_default_endpoint_has_independent_embedding_model(monkeypatch):
    monkeypatch.delenv("RUNTIME_ENDPOINTS", raising=False)
    monkeypatch.setenv("RUNTIME_MODEL", "chat-model")
    monkeypatch.setenv("RUNTIME_EMBEDDING_MODEL", "embed-model")

    configured = load_endpoints()[0]

    assert configured.models == ("chat-model",)
    assert configured.embedding_models == ("embed-model",)


class PartialFailureProvider(FakeProvider):
    async def generate(self, model, messages, tools, emit, context):
        self.requests.append({"model": model, "messages": messages, "tools": tools})
        await emit("partial")
        raise EndpointUnavailable("stream interrupted")


class FailedEmbeddingProvider(FakeProvider):
    async def embed(self, model, texts):
        self.embedding_requests.append({"model": model, "texts": texts})
        raise EndpointUnavailable("embedding unavailable")


class Collector(list):
    async def __call__(self, text):
        self.append(text)
