from runtime.adapter import AdapterResult
import pytest

from runtime.adapter import TurnRequest
from runtime.bridge import ToolBridge


def request(tools):
    return TurnRequest('run','turn','message','prompt',(),
                       {'tools':tools,'project_id':'project-a','adapter':'pi'},None)


@pytest.mark.asyncio
async def test_bridge_rejects_unselected_tools_and_expired_bindings():
    bridge=ToolBridge()
    token=bridge.bind(request(['graph']))
    with pytest.raises(PermissionError):
        await bridge.invoke(token,'record',{'type':'direction'})
    bridge.release(token)
    with pytest.raises(PermissionError):
        await bridge.invoke(token,'graph',{})


@pytest.mark.asyncio
async def test_bridge_binds_project_server_side(monkeypatch):
    import runtime.bridge as module
    captured=[]
    async def graph(project,tool,values):
        captured.append(project)
        return {}
    monkeypatch.setattr(module,'_graph',graph)
    bridge=ToolBridge()
    token=bridge.bind(request(['graph']))
    await bridge.invoke(token,'graph',{'project_id':'foreign'})
    assert captured==['project-a']


@pytest.mark.asyncio
async def test_delegate_child_cannot_write_or_delegate():
    bridge=ToolBridge()
    class Runtime:
        async def delegate(self,parent,spec,**kwargs):
            self.spec=spec
            return {'id':'child'}
        async def submit_child(self,*args):
            return {'id':'child-turn'}
        async def subscribe(self,*args):
            yield {'type':'turn_end','data':{'status':'completed','result_text':'review'}}
    bridge.runtime=Runtime()
    token=bridge.bind(request(['graph','record','artifact','delegate','literature']))
    result=await bridge.invoke(token,'delegate',{'instructions':'review','task':'inspect'})
    assert bridge.runtime.spec['tools']==['graph','literature']
    assert result['result_text']=='review'


@pytest.mark.asyncio
async def test_runtime_tool_results_are_redacted_before_trace(tmp_path):
    from runtime.adapter import AdapterResult
    from runtime.runtime import Runtime
    runtime=Runtime(tmp_path,{'fake':SecretToolAdapter()})
    await runtime.launch({'adapter':'fake'},session_id='session')
    turn=await runtime.submit('session',{'id':'message','content':'inspect'})
    events=[e async for e in runtime.subscribe(turn['id'])]
    assert any(event['type']=='tool' for event in events)
    assert events[-1]['data']['status']=='completed'
    assert all(secret not in str(events) for secret in ['synthetic-value','synthetic-token','synthetic-final'])
    assert 'synthetic-final' not in str(runtime.inspect_session('session'))
    assert 'synthetic-token' not in str(runtime.export_session('session'))


class SecretToolAdapter:
    adapter_id='fake'
    supports_multiple_writers=True
    async def start(self,request): return object()
    async def submit(self,handle,request,emit):
        await emit({'type':'tool','data':{'result':{'api_key':'synthetic-value','token':'synthetic-token'}}})
        return AdapterResult(result_text='token=synthetic-final')
    async def cancel(self,*args): pass
    async def close(self): pass
