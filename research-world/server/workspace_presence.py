from collections import defaultdict
import logging

from anyio import CancelScope
from fastapi import WebSocket, WebSocketDisconnect
from httpx import HTTPError

from .runtime_http import RuntimeHttpError


async def start_workspace(control, project_id):
    async with control.project_locks[project_id]:
        control.kernel.get_project(project_id)
        catalog = await control.runtime.catalog()
        agent = control.profiles.get('research-assistant', catalog['default_model'])
        return await control.runtime.workspace(project_id, 'POST', agent['model'])


class WorkspacePresence:
    def __init__(self, control):
        self.control = control
        self.connections = defaultdict(set)

    async def visit(self, socket, project_id):
        self.connections[project_id].add(socket)
        try:
            await socket.send_json({'status': 'starting'})
            await self.prepare(socket, project_id)
            async for _ in socket.iter_text():
                pass
        except WebSocketDisconnect:
            pass
        finally:
            with CancelScope(shield=True):
                await self.leave(socket, project_id)

    async def prepare(self, socket, project_id):
        try:
            state = await start_workspace(self.control, project_id)
            if state['status'] != 'ready':
                raise ValueError('工作区启动未就绪，请重试')
            await socket.send_json(state)
        except (RuntimeHttpError, HTTPError, ValueError, KeyError):
            await socket.send_json({'status': 'error', 'detail': '工作区启动失败，请重试或返回项目列表'})

    async def leave(self, socket, project_id):
        async with self.control.project_locks[project_id]:
            self.connections[project_id].discard(socket)
            if self.connections[project_id]:
                return
            del self.connections[project_id]
            try:
                await self.control.runtime.workspace(project_id, 'POST', stop=True)
            except (RuntimeHttpError, HTTPError):
                logging.getLogger(__name__).error('工作区停止失败: %s', project_id)


def presence_route(router, control):
    presence = WorkspacePresence(control)

    @router.websocket('/presence')
    async def connect(socket: WebSocket, project_id: str):
        try:
            control.kernel.get_project(project_id)
        except KeyError:
            await socket.close(code=1008)
            return
        await socket.accept()
        await presence.visit(socket, project_id)
