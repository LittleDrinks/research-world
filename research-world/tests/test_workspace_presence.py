import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from server.session_control import SessionControl
from server.workspace_presence import WorkspacePresence
from test_pi_product import setup


class Socket:
    def __init__(self):
        self.messages = []
        self.closed = asyncio.Event()

    async def send_json(self, value):
        if self.closed.is_set():
            raise WebSocketDisconnect()
        self.messages.append(value)

    async def iter_text(self):
        await self.closed.wait()
        if False:
            yield ''


def presence(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Workspace', 'Question')
    runtime.workspace = AsyncMock(return_value={'status': 'ready'})
    control = SessionControl(kernel, runtime, AsyncMock(), tmp_path)
    control.profiles.get = lambda *_: {'model': 'test/model'}
    return WorkspacePresence(control), runtime, project.id


async def until(predicate):
    async with asyncio.timeout(3):
        while not predicate():
            await asyncio.sleep(.001)


@pytest.mark.asyncio
async def test_last_connection_stops_only_its_project(tmp_path):
    owner, runtime, project = presence(tmp_path)
    other = owner.control.kernel.create_project('Other', 'Question').id
    sockets = [Socket(), Socket(), Socket()]
    tasks = [asyncio.create_task(owner.visit(s, p)) for s, p in zip(sockets, [project, project, other])]
    await until(lambda: all(len(s.messages) == 2 for s in sockets))
    sockets[0].closed.set()
    await tasks[0]
    assert not any(c.kwargs.get('stop') for c in runtime.workspace.await_args_list)
    sockets[1].closed.set()
    await tasks[1]
    assert runtime.workspace.await_args.args == (project, 'POST')
    assert runtime.workspace.await_args.kwargs == {'stop': True}
    assert not tasks[2].done()
    sockets[2].closed.set()
    await tasks[2]
    assert not owner.connections


@pytest.mark.asyncio
async def test_exit_during_start_waits_then_stops(tmp_path):
    owner, runtime, project = presence(tmp_path)
    release = asyncio.Event()
    async def work(*_, **kwargs):
        if not kwargs.get('stop'):
            await release.wait()
        return {'status': 'ready'}
    runtime.workspace.side_effect = work
    socket = Socket()
    task = asyncio.create_task(owner.visit(socket, project))
    await until(lambda: runtime.workspace.await_count == 1)
    socket.closed.set()
    release.set()
    await task
    assert runtime.workspace.await_args.kwargs == {'stop': True}
    assert not owner.connections


@pytest.mark.asyncio
async def test_reenter_while_starting_does_not_stop_new_connection(tmp_path):
    owner, runtime, project = presence(tmp_path)
    release = asyncio.Event()
    async def work(*_, **kwargs):
        if not kwargs.get('stop'):
            await release.wait()
        return {'status': 'ready'}
    runtime.workspace.side_effect = work
    old, new = Socket(), Socket()
    first = asyncio.create_task(owner.visit(old, project))
    await until(lambda: runtime.workspace.await_count == 1)
    old.closed.set(); second = asyncio.create_task(owner.visit(new, project))
    await until(lambda: len(owner.connections[project]) == 2)
    release.set()
    await first
    await until(lambda: len(new.messages) == 2)
    assert not any(c.kwargs.get('stop') for c in runtime.workspace.await_args_list)
    new.closed.set()
    await second


@pytest.mark.asyncio
async def test_failed_start_is_visible_and_can_be_retried(tmp_path):
    owner, runtime, project = presence(tmp_path)
    runtime.workspace.side_effect = [ValueError('private detail'), {'status': 'exited'}, {'status': 'ready'}, {'status': 'exited'}]
    first, second = Socket(), Socket()
    task = asyncio.create_task(owner.visit(first, project))
    await until(lambda: len(first.messages) == 2)
    assert first.messages[1]['status'] == 'error'
    assert 'private detail' not in str(first.messages)
    first.closed.set()
    await task
    task = asyncio.create_task(owner.visit(second, project))
    await until(lambda: len(second.messages) == 2)
    assert second.messages[1]['status'] == 'ready'
    second.closed.set()
    await task


def test_websocket_route_starts_and_releases_workspace(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Workspace', 'Question')
    runtime.workspace = AsyncMock(return_value={'status': 'ready'})
    with TestClient(app) as client:
        with client.websocket_connect(f'/api/v1/projects/{project.id}/workspace/presence') as socket:
            assert socket.receive_json() == {'status': 'starting'}
            assert socket.receive_json() == {'status': 'ready'}
    assert runtime.workspace.await_args.kwargs == {'stop': True}


def test_missing_project_never_starts_workspace(tmp_path):
    app, _, runtime = setup(tmp_path)
    runtime.workspace = AsyncMock()
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect('/api/v1/projects/missing/workspace/presence'):
                pass
    runtime.workspace.assert_not_awaited()
