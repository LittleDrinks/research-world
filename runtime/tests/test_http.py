import asyncio

import httpx
import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime
from runtime.run_store import RunStoreError
from runtime.server import create_app
from server.runtime_http import RuntimeHttpClient, RuntimeHttpError


SPEC = {"id": "main", "adapter": "fake"}


class ControlledAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.calls = []
        self.finished = asyncio.Event()

    async def start(self, request):
        self.calls.append(("start", request.message_id))
        return object()

    async def submit(self, handle, request, emit):
        self.calls.append(("submit", request.message_id))
        self.finished.set()
        return AdapterResult(result_text=request.input)

    async def cancel(self, handle, request):
        self.calls.append(("cancel", request.message_id))


class TrackingTransport(httpx.AsyncBaseTransport):
    def __init__(self, app):
        self.delegate = httpx.ASGITransport(app=app)
        self.calls = 0
        self.closed = False

    async def handle_async_request(self, request):
        self.calls += 1
        return await self.delegate.handle_async_request(request)

    async def aclose(self):
        self.closed = True
        await self.delegate.aclose()


class ErroringRuntime:
    def __init__(self, error):
        self.error = error

    async def launch(self, *_, **__):
        raise self.error


def make_app(tmp_path):
    adapter = ControlledAdapter()
    return create_app(Runtime(tmp_path, {"fake": adapter})), adapter


async def post(app, path, payload):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://runtime"
    ) as client:
        return await client.post(path, json=payload)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "status_code", "code", "detail"),
    [
        (RunStoreError("storage secret"), 500, "internal_error", "internal server error"),
        (ValueError("bad input"), 422, "invalid_request", "bad input"),
    ],
)
async def test_http_error_boundary(error, status_code, code, detail):
    response = await post(
        create_app(ErroringRuntime(error)),
        "/api/v1/runtime/launch",
        {"agent_spec": SPEC},
    )
    assert response.status_code == status_code
    assert response.json() == {"code": code, "detail": detail}


@pytest.mark.asyncio
async def test_transport_app_exposes_health_launch_submit_without_acp(tmp_path):
    app, adapter = make_app(tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://runtime"
    ) as client:
        health = await client.get("/health")
        launch = await client.post(
            "/api/v1/runtime/launch",
            json={"agent_spec": SPEC, "session_id": "s"},
        )
        submit = await client.post("/api/v1/runtime/submit", json=_message("one"))
        acp = await client.get("/acp")
    await adapter.finished.wait()
    assert health.json() == {"ok": True}
    assert launch.status_code == 200
    assert submit.status_code == 202
    assert acp.status_code == 404


@pytest.mark.asyncio
async def test_launch_over_http_returns_runtime_run_view(tmp_path):
    app, _ = make_app(tmp_path)
    response = await post(
        app,
        "/api/v1/runtime/launch",
        {"agent_spec": SPEC, "session_id": "session-235"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "run_id", "parent_run_id", "session_id", "agent_snapshot"}
    assert body["id"] == body["run_id"]
    assert body["session_id"] == "session-235"


@pytest.mark.asyncio
async def test_submit_over_http_is_idempotent_and_runs_once(tmp_path):
    app, adapter = make_app(tmp_path)
    await post(app, "/api/v1/runtime/launch", {"agent_spec": SPEC, "session_id": "s"})
    first = await post(app, "/api/v1/runtime/submit", _message("one"))
    duplicate = await post(app, "/api/v1/runtime/submit", _message("changed"))
    await adapter.finished.wait()
    assert first.status_code == duplicate.status_code == 202
    assert first.json() == duplicate.json()
    assert set(first.json()) == {"id", "turn_id", "run_id", "message_id", "status", "result_text"}
    assert adapter.calls == [("start", "m"), ("submit", "m")]


@pytest.mark.asyncio
async def test_submit_maps_unknown_session_without_adapter_call(tmp_path):
    app, adapter = make_app(tmp_path)
    response = await post(app, "/api/v1/runtime/submit", _message("one", "missing"))
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_submit_maps_cross_session_message_conflict(tmp_path):
    app, adapter = make_app(tmp_path)
    await post(app, "/api/v1/runtime/launch", {"agent_spec": SPEC, "session_id": "s"})
    await post(app, "/api/v1/runtime/launch", {"agent_spec": SPEC, "session_id": "t"})
    await post(app, "/api/v1/runtime/submit", _message("one"))
    await adapter.finished.wait()
    response = await post(app, "/api/v1/runtime/submit", _message("one", "t"))
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert adapter.calls == [("start", "m"), ("submit", "m")]


@pytest.mark.asyncio
async def test_launch_maps_snapshot_conflict(tmp_path):
    app, adapter = make_app(tmp_path)
    await post(app, "/api/v1/runtime/launch", {"agent_spec": SPEC, "session_id": "s"})
    response = await post(
        app,
        "/api/v1/runtime/launch",
        {"agent_spec": {**SPEC, "id": "other"}, "session_id": "s"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_invalid_request_has_stable_error_body(tmp_path):
    app, _ = make_app(tmp_path)
    response = await post(
        app,
        "/api/v1/runtime/launch",
        {"agent_spec": SPEC, "session_id": "s", "extra": True},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"


@pytest.mark.asyncio
async def test_typed_client_reuses_transport_and_closes(tmp_path):
    app, adapter = make_app(tmp_path)
    transport = TrackingTransport(app)
    client = RuntimeHttpClient("http://runtime", transport=transport)
    run = await client.launch(SPEC, session_id="s")
    turn = await client.submit("s", {"id": "m", "content": "one"})
    await adapter.finished.wait()
    assert run.id == run.run_id == turn.run_id
    assert transport.calls == 2
    await client.close()
    assert client.is_closed and transport.closed


@pytest.mark.asyncio
async def test_typed_client_maps_not_found_error(tmp_path):
    app, _ = make_app(tmp_path)
    client = RuntimeHttpClient("http://runtime", transport=httpx.ASGITransport(app=app))
    with pytest.raises(RuntimeHttpError) as raised:
        await client.submit("missing", {"id": "m", "content": "one"})
    assert raised.value.status_code == 404
    assert raised.value.code == "not_found"
    await client.close()


async def _launch_submit(app, adapter):
    client = RuntimeHttpClient("http://runtime", transport=httpx.ASGITransport(app=app))
    await client.launch(SPEC, session_id="s")
    turn = await client.submit("s", {"id": "m", "content": "one"})
    await adapter.finished.wait()
    await client.close()
    return turn


async def _submit_with_client(app, content):
    client = RuntimeHttpClient("http://runtime", transport=httpx.ASGITransport(app=app))
    turn = await client.submit("s", {"id": "m", "content": content})
    await client.close()
    return turn


@pytest.mark.asyncio
async def test_fresh_typed_client_reuses_persisted_turn(tmp_path):
    app, first_adapter = make_app(tmp_path)
    original = await _launch_submit(app, first_adapter)

    second_app, second_adapter = make_app(tmp_path)
    recovered = await _submit_with_client(second_app, "changed")
    assert recovered.id == original.id
    assert recovered.status == "completed"
    assert recovered.result_text == "one"
    assert second_adapter.calls == []


def _message(content, session_id="s"):
    return {"session_id": session_id, "message": {"id": "m", "content": content}}
