from __future__ import annotations

import asyncio
import json
import os
import secrets

import httpx
from fastapi import APIRouter, HTTPException, Request

from . import literature
from .agent_catalog import has_workspace
from .artifact_files import read_text
from .selection import select_candidates
from .research_operations import operation as research_operation


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
        if request is None:
            raise PermissionError('Tool binding has expired')
        allowed = has_workspace(request.agent_snapshot) if tool == 'workspace' else tool in request.agent_snapshot.get('tools', [])
        if not allowed:
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
        if tool == 'change':
            return await _change(request, values)
        if tool == 'mmr':
            return select_candidates(values)
        if tool == 'artifact':
            if values.get('operation') in {'templates', 'read'}:
                return await _graph(request.agent_snapshot['project_id'], tool, values, request.run_id)
            if ('path' in values) == ('content' in values):
                raise ValueError('artifact requires exactly one of content or path')
            if 'path' in values:
                values = await self._file_artifact(token, values)
        return await _graph(request.agent_snapshot['project_id'], tool, values, request.run_id)

    async def _file_artifact(self, token, values):
        path = values['path']
        if 'content' in values or not isinstance(path, str) or not path.strip():
            raise ValueError('artifact requires either content or a non-empty path')
        content = await self._workspace_text(token, path)
        return {key: value for key, value in values.items() if key != 'path'} | {'content': content, 'media_type': values.get('media_type', 'text/plain')}

    async def _workspace_text(self, token, path):
        return await read_text(self.workspace_tools.execute(token, {'operation': 'read', 'path': path, 'max_bytes': 4 * 1024 * 1024}))

    async def delegate(self, request, values):
        tasks = values.get('tasks')
        if not isinstance(tasks, list) or not 1 <= len(tasks) <= 8:
            raise ValueError('delegate requires 1 to 8 tasks')
        for task in tasks:
            if not isinstance(task, dict) or task.get('thinking') not in {'low', 'medium', 'high'}:
                raise ValueError('Each task requires low, medium or high thinking')
            if any(not isinstance(task.get(k), str) or not task[k].strip() for k in ('instructions', 'task')):
                raise ValueError('Each task requires instructions and task')
        results = await asyncio.gather(*(self._delegate_one(request, task) for task in tasks), return_exceptions=True)
        return {'results': [{'status': 'error', 'error': 'Child execution failed'}
                            if isinstance(result, Exception) else result for result in results]}

    async def _delegate_one(self, request, values):
        spec = dict(request.agent_snapshot)
        spec['instructions'] = values['instructions']
        spec['thinking'] = values['thinking']
        spec['tools'] = [t for t in spec.get('tools', []) if t in {'graph', 'literature'}]
        child = await self.runtime.delegate(request.run_id, spec, parent_turn_id=request.turn_id)
        turn = await self.runtime.submit_child(child['id'], {'id': secrets.token_hex(16), 'content': values['task']})
        async for event in self.runtime.subscribe(turn['id']):
            if event['type'] == 'turn_end':
                return {'run_id': child['id'], **event['data']}
        return {'run_id': child['id'], 'status': 'error', 'error': 'Child ended without a result'}


def bridge_router(bridge):
    router = APIRouter()

    @router.post('/internal/tools')
    async def invoke(request: Request):
        body = await request.json()
        try:
            return await bridge.invoke(request.headers.get('x-tool-token'), body['tool'], body['arguments'])
        except PermissionError as error:
            raise HTTPException(403, str(error)) from None
        except httpx.HTTPStatusError as error:
            if body['tool'] in {'artifact', 'change'} and error.response.status_code in {409, 422}:
                raise HTTPException(error.response.status_code, error.response.json().get('detail')) from None
            raise HTTPException(422, 'Tool operation failed; verify arguments or source availability') from None
        except (ValueError, KeyError, httpx.HTTPError):
            raise HTTPException(422, 'Tool operation failed; verify arguments or source availability') from None

    return router


async def _graph(project_id, tool, values, run_id=None):
    root = f'/api/v1/projects/{project_id}'
    operations = {'graph': ('local-map', {'text': values.get('query'), 'limit': values.get('limit', 30)}),
                  'joint_condition': ('joint-conditions', values),
                  'artifact': ('artifacts', values), 'record': ('records', values), 'connect': ('relations', values)}
    path, payload = operations[tool]
    async with httpx.AsyncClient(base_url=os.environ['CONTROL_URL'], timeout=30) as client:
        headers = {'x-research-author': 'agent:' + run_id} if run_id else {}
        response = await client.post(f'{root}/{path}', json=payload, headers=headers)
        if tool == 'record' and response.status_code == 409:
            return {'created': False, 'review_required': response.json()['detail']}
        response.raise_for_status()
        return response.json()


async def _literature(values):
    sources = {'crossref': literature.crossref, 'openalex': literature.openalex,
               'arxiv': literature.arxiv, 'pubmed': literature.pubmed}
    result = await sources[values.get('source', 'crossref')]({
        'action': 'search', 'query': values['query'], 'limit': 5})
    return json.loads(result)


async def _change(request, values):
    root = f"/api/v1/projects/{request.agent_snapshot['project_id']}"
    method, path, payload = research_operation(values)
    async with httpx.AsyncClient(base_url=os.environ['CONTROL_URL'], timeout=30) as client:
        response = await client.request(method, root + path, json=payload,
                                        headers={'x-research-author': 'agent:' + request.run_id})
        response.raise_for_status()
        return {'deleted': True} if response.status_code == 204 else response.json()
