import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from runtime.bridge import ToolBridge
from runtime.adapter import AdapterResult
from runtime.workspace.tools import WorkspaceTools, workspace_tools_router


def binding(bridge, project='one', tools=('workspace',)):
    return bridge.bind(SimpleNamespace(agent_snapshot={'tools':tools,'project_id':project,'model':'provider/model'}))


@pytest.mark.asyncio
async def test_workspace_rejects_foreign_project_and_unselected_or_expired_tokens():
    bridge=ToolBridge();app=FastAPI();app.include_router(workspace_tools_router(bridge))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        token=binding(bridge,tools=('graph',))
        assert (await client.post('/internal/workspace',headers={'x-tool-token':token},json={'operation':'read','path':'file'})).status_code==403
        token=binding(bridge)
        assert (await client.post('/internal/workspace',headers={'x-tool-token':token},json={'operation':'read','project_id':'other'})).status_code==422
        bridge.release(token)
        assert (await client.post('/internal/workspace',headers={'x-tool-token':token},json={'operation':'read'})).status_code==403


@pytest.mark.asyncio
async def test_containers_are_project_bound_and_started_only_once_per_turn():
    class Manager:
        def __init__(self): self.started=[]
        async def start(self,project,model): self.started.append(project)
        def container(self,project): return project+'-container'
    manager=Manager();bridge=ToolBridge();tools=WorkspaceTools(bridge,manager);bridge.workspace_tools=tools
    one,two=binding(bridge,'one'),binding(bridge,'two')
    assert await tools.prepare(one)=='one-container'
    assert await tools.prepare(one)=='one-container'
    assert await tools.prepare(two)=='two-container'
    assert manager.started==['one','two']
    await bridge.close(one)
    with pytest.raises(PermissionError): await tools.prepare(one)
    assert one not in tools.containers


@pytest.mark.asyncio
async def test_persisted_chat_replays_text_and_tools_in_execution_order(tmp_path):
    from runtime.runtime import Runtime
    runtime=Runtime(tmp_path,{'fake':TimelineAdapter()})
    await runtime.launch({'adapter':'fake'},session_id='s')
    turn=await runtime.submit('s',{'id':'m','content':'run'})
    _=[event async for event in runtime.subscribe(turn['id'])]
    original=runtime.inspect_session('s')['turns'][0]['events']
    await runtime.close()
    restarted=Runtime(tmp_path,{'fake':TimelineAdapter()})
    assert restarted.inspect_session('s')['turns'][0]['events']==original
    assert [e['type'] for e in original]==['delta','tool','tool','delta','turn_end']
    await restarted.close()


class TimelineAdapter:
    adapter_id='fake'
    supports_multiple_writers=True
    async def start(self,request): return object()
    async def submit(self,handle,request,emit):
        for kind,data in [('delta',{'text':'before'}),('tool',{'id':'call','phase':'started','name':'bash'}),
                          ('tool',{'id':'call','phase':'completed','name':'bash'}),('delta',{'text':'after'})]:
            await emit({'type':kind,'data':data})
        return AdapterResult(result_text='after')
    async def close(self): pass
    async def cancel(self,*args): pass
