from __future__ import annotations

import asyncio
import json
import os
import secrets

import httpx
from fastapi import APIRouter, HTTPException, Request

from . import literature


class ToolBridge:
    def __init__(self):
        self.bindings = {}
        self.runtime = None
        self.workspace_tools = None

    def bind(self, request):
        token = secrets.token_urlsafe(32)
        self.bindings[token] = request
        return token

    def release(self, token):
        self.bindings.pop(token, None)

    def authorize(self, token, tool):
        request = self.bindings.get(token)
        if request is None or tool not in request.agent_snapshot.get('tools', []):
            raise PermissionError('Tool is not selected for this Agent')
        return request

    async def close(self, token):
        self.release(token)
        if self.workspace_tools: await self.workspace_tools.close(token)

    async def invoke(self, token, tool, values):
        request = self.authorize(token, tool)
        if tool == 'delegate':
            return await self.delegate(request, values)
        if tool == 'literature':
            return await _literature(values)
        return await _graph(request.agent_snapshot['project_id'], tool, values)

    async def delegate(self, request, values):
        spec = dict(request.agent_snapshot)
        spec['instructions'] = values['instructions']
        spec['tools'] = [t for t in spec.get('tools', []) if t in {'graph', 'literature'}]
        child = await self.runtime.delegate(request.run_id, spec, parent_turn_id=request.turn_id)
        turn = await self.runtime.submit_child(child['id'], {'id': secrets.token_hex(16), 'content': values['task']})
        async for event in self.runtime.subscribe(turn['id']):
            if event['type'] == 'turn_end':
                return {'run_id': child['id'], **event['data']}


def bridge_router(bridge):
    router = APIRouter()

    @router.post('/internal/tools')
    async def invoke(request: Request):
        body = await request.json()
        try:
            return await bridge.invoke(request.headers.get('x-tool-token'), body['tool'], body['arguments'])
        except PermissionError as error:
            raise HTTPException(403, str(error)) from None
        except (ValueError, KeyError, httpx.HTTPError):
            raise HTTPException(422, 'Tool operation failed; verify arguments or source availability') from None

    return router


async def _graph(project_id, tool, values):
    root = f'/api/v1/projects/{project_id}'
    operations = {'graph': ('local-map', {'text': values.get('query'), 'limit': 30}),
                  'artifact': ('artifacts', values), 'record': ('records', values), 'connect': ('relations', values)}
    path, payload = operations[tool]
    async with httpx.AsyncClient(base_url=os.environ['CONTROL_URL'], timeout=30) as client:
        response = await client.post(f'{root}/{path}', json=payload)
        response.raise_for_status()
        return response.json()


async def _literature(values):
    sources = {'crossref': literature.crossref, 'openalex': literature.openalex,
               'arxiv': literature.arxiv, 'pubmed': literature.pubmed}
    result = await sources[values.get('source', 'crossref')]({
        'action': 'search', 'query': values['query'], 'limit': 5})
    return json.loads(result)
