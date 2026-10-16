import asyncio
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from .execution import Execution


class Operation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation: Literal['read','write','access','mkdir','mime','bash']
    path: str = ''
    content: str = ''
    command: str = ''
    timeout: float = Field(default=120, gt=0, le=600)


class WorkspaceTools:
    def __init__(self, bridge, workspaces):
        self.bridge, self.workspaces = bridge, workspaces
        self.containers, self.jobs = {}, defaultdict(set)
        self.locks = defaultdict(asyncio.Lock)

    async def prepare(self, token):
        request = self.bridge.authorize(token, 'workspace')
        async with self.locks[token]:
            if token not in self.containers:
                spec = request.agent_snapshot
                await self.workspaces.start(spec['project_id'], spec['model'])
                self.bridge.authorize(token, 'workspace')
                self.containers[token] = await asyncio.to_thread(self.workspaces.container, spec['project_id'])
        return self.containers[token]

    async def execute(self, token, values):
        container = await self.prepare(token)
        self.bridge.authorize(token, 'workspace')
        job = Execution(container, values)
        self.jobs[token].add(job)
        try:
            async for event in job.events(): yield event
        finally: self.jobs.get(token, set()).discard(job)

    async def close(self, token):
        await asyncio.gather(*(job.stop() for job in tuple(self.jobs.pop(token, ()))))
        self.containers.pop(token, None)
        self.locks.pop(token, None)


def workspace_tools_router(bridge):
    router = APIRouter()

    @router.post('/internal/workspace')
    async def execute(request: Request, body: Operation):
        token = request.headers.get('x-tool-token')
        try: bridge.authorize(token, 'workspace')
        except PermissionError: raise HTTPException(403, 'Workspace tool is not selected') from None
        return StreamingResponse(_events(bridge.workspace_tools, token, body.model_dump()), media_type='application/x-ndjson')

    return router


async def _events(tools, token, values):
    import json
    try:
        async for event in tools.execute(token, values): yield event
    except Exception:
        yield json.dumps({'error':'工作区不可用；请检查工作区状态后重试'})+'\n'
