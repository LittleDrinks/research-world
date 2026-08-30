from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

from server.app import create_app
from server.kernel import ResearchKernel
from server.kernel_interface import create_kernel
from server.world import World


class ImmediateAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    async def start(self, _request):
        return object()

    async def submit(self, _handle, request, emit):
        await emit({"type": "delta", "data": {"text": request.input}})
        return AdapterResult(result_text=request.input)

    async def cancel(self, _handle, _request):
        return None


class DeferredAdapter(ImmediateAdapter):
    def __init__(self):
        self.release = asyncio.Event()

    async def submit(self, handle, request, emit):
        await self.release.wait()
        return await super().submit(handle, request, emit)


class FailingAdapter(ImmediateAdapter):
    async def submit(self, _handle, _request, _emit):
        raise RuntimeError("adapter failed")


class CancellableAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.gates = {}
        self.cancelled = set()

    async def start(self, request):
        self.gates[request.turn_id] = asyncio.Event()
        return request.turn_id

    async def submit(self, handle, request, emit):
        await self.gates[handle].wait()
        if handle in self.cancelled:
            return AdapterResult(status="cancelled")
        await emit({"type": "delta", "data": {"text": request.input}})
        return AdapterResult(result_text=request.input)

    async def cancel(self, handle, _request):
        self.cancelled.add(handle)
        self.gates[handle].set()

    async def wait_for_turns(self, count):
        await asyncio.wait_for(self._wait_for_turns(count), timeout=1)

    async def _wait_for_turns(self, count):
        while len(self.gates) < count:
            await asyncio.sleep(0)

    def complete(self, turn_id):
        self.gates[turn_id].set()


def _sse_events(text):
    return [
        json.loads(line.removeprefix("data: "))
        for line in text.splitlines()
        if line.startswith("data: ")
    ]


def _app(tmp_path, adapter=None):
    graph_kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    legacy = ResearchKernel(
        World(tmp_path / "world.db", tmp_path / "world-artifacts"),
        projects_root=tmp_path / "projects",
    )
    runtime = Runtime(
        data_root=tmp_path / "runtime",
        adapters={"fake": adapter or ImmediateAdapter()},
    )
    return create_app(legacy, graph_kernel=graph_kernel, transport_runtime=runtime), graph_kernel, runtime


@pytest.mark.asyncio
async def test_session_http_creates_reads_and_lists_kernel_sessions(tmp_path):
    app, kernel, _runtime = _app(tmp_path)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
        )
        session = created.json()
        read = await client.get(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}"
        )
        listed = await client.get(f"/api/v1/projects/{project.id}/sessions")

    assert created.status_code == 201
    assert read.status_code == listed.status_code == 200
    assert session["project_id"] == project.id
    assert session["messages"] == []
    assert read.json() == session
    assert listed.json() == [session]


@pytest.mark.asyncio
async def test_message_submission_persists_before_returning_json_turn(tmp_path):
    adapter = DeferredAdapter()
    app, kernel, runtime = _app(tmp_path, adapter)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")
    run = await runtime.launch({"id": "main", "adapter": "fake"})

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(
                f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
            )
        ).json()
        response = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:one", "content": "Hello"},
        )

    assert response.status_code == 202
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"message", "turn"}
    assert body["message"]["id"] == "message:one"
    assert body["turn"]["run_id"] == run["id"]
    assert body["turn"]["status"] == "running"
    persisted = kernel.get_session(project.id, session["id"]).messages
    assert [(item.id, item.content, item.assistant_response) for item in persisted] == [
        ("message:one", "Hello", None)
    ]
    await runtime.cancel(body["turn"]["id"])


@pytest.mark.asyncio
async def test_completed_main_turn_projects_answer_to_its_session_message(tmp_path):
    adapter = DeferredAdapter()
    app, kernel, runtime = _app(tmp_path, adapter)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(
                f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
            )
        ).json()
        run = await runtime.launch(
            {"id": "main", "adapter": "fake"}, session_id=session["id"]
        )
        submitted = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:one", "content": "Hello"},
        )
        turn_id = submitted.json()["turn"]["id"]
        adapter.release.set()
        events = await client.get(f"/api/v1/turns/{turn_id}/events")

    assert events.status_code == 200
    assert '"type": "turn_end"' in events.text
    message = kernel.get_session(project.id, session["id"]).messages[0]
    assert message.assistant_response == "Hello"


@pytest.mark.asyncio
async def test_subagent_turn_does_not_project_a_session_answer(tmp_path):
    adapter = DeferredAdapter()
    app, kernel, runtime = _app(tmp_path, adapter)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(
                f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
            )
        ).json()
        parent = await runtime.launch(
            {"id": "main", "adapter": "fake"}, session_id=session["id"]
        )
        parent_turn = await runtime.submit(
            parent["id"], {"id": "parent-message", "content": "delegate"}
        )
        child = await runtime.delegate(
            parent["id"], {"id": "child", "adapter": "fake"}, parent_turn_id=parent_turn["id"]
        )
        child_turn = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": child["id"], "message_id": "child-message", "content": "child work"},
        )
        child_turn_id = child_turn.json()["turn"]["id"]
        adapter.release.set()
        await client.get(f"/api/v1/turns/{child_turn_id}/events")

    message = kernel.get_session(project.id, session["id"]).messages[0]
    assert message.id == "child-message"
    assert message.assistant_response is None


@pytest.mark.asyncio
async def test_adapter_failure_is_visible_on_the_turn_trace(tmp_path):
    app, kernel, runtime = _app(tmp_path, FailingAdapter())
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(f"/api/v1/projects/{project.id}/sessions", json={})
        ).json()
        run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id=session["id"])
        submitted = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:error", "content": "Hello"},
        )
        trace = await client.get(f"/api/v1/turns/{submitted.json()['turn']['id']}/events")

    terminal = _sse_events(trace.text)[-1]
    assert submitted.status_code == 202
    assert terminal["type"] == "turn_end"
    assert terminal["data"] == {
        "status": "error",
        "result_text": None,
        "error": "adapter failed",
    }
    assert kernel.get_session(project.id, session["id"]).messages[0].assistant_response is None


@pytest.mark.asyncio
async def test_turn_subscription_replays_after_sequence_without_resubmitting(tmp_path):
    app, kernel, runtime = _app(tmp_path)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(
                f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
            )
        ).json()
        run = await runtime.launch(
            {"id": "main", "adapter": "fake"}, session_id=session["id"]
        )
        submitted = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:one", "content": "Hello"},
        )
        turn_id = submitted.json()["turn"]["id"]
        first = await client.get(f"/api/v1/turns/{turn_id}/events")
        initial = _sse_events(first.text)
        resumed = await client.get(
            f"/api/v1/turns/{turn_id}/events",
            params={"after_seq": initial[0]["seq"]},
        )

    remaining = _sse_events(resumed.text)
    assert first.headers["content-type"].startswith("text/event-stream")
    assert [event["type"] for event in initial] == [
        "turn_start",
        "delta",
        "turn_end",
    ]
    assert [event["type"] for event in remaining] == ["delta", "turn_end"]
    assert all(event["turn_id"] == turn_id for event in initial + remaining)
    assert all(event["seq"] > initial[0]["seq"] for event in remaining)


@pytest.mark.asyncio
async def test_turn_cancellation_is_independent_per_turn(tmp_path):
    adapter = CancellableAdapter()
    app, kernel, runtime = _app(tmp_path, adapter)
    project = kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        session = (
            await client.post(
                f"/api/v1/projects/{project.id}/sessions", json={"title": "Orbit notes"}
            )
        ).json()
        run = await runtime.launch(
            {"id": "main", "adapter": "fake"}, session_id=session["id"]
        )
        first = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:first", "content": "Stop"},
        )
        second = await client.post(
            f"/api/v1/projects/{project.id}/sessions/{session['id']}/messages",
            json={"run_id": run["id"], "message_id": "message:second", "content": "Continue"},
        )
        assert first.status_code == second.status_code == 202
        await adapter.wait_for_turns(2)
        first_id = first.json()["turn"]["id"]
        second_id = second.json()["turn"]["id"]
        cancelled = await client.post(f"/api/v1/turns/{first_id}/cancel")
        assert cancelled.status_code == 200
        adapter.complete(second_id)
        first_events = await client.get(f"/api/v1/turns/{first_id}/events")
        second_events = await client.get(f"/api/v1/turns/{second_id}/events")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert _sse_events(first_events.text)[-1]["data"]["status"] == "cancelled"
    assert _sse_events(second_events.text)[-1]["data"] == {
        "status": "completed",
        "result_text": "Continue",
    }
    messages = kernel.get_session(project.id, session["id"]).messages
    assert [(item.id, item.assistant_response) for item in messages] == [
        ("message:first", None),
        ("message:second", "Continue"),
    ]
