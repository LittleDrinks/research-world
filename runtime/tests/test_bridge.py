from runtime.adapter import AdapterResult
import asyncio
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
    token=bridge.bind(request(['graph','record','artifact','delegate','literature','workspace']))
    result=await bridge.invoke(token,'delegate',{'tasks':[{'instructions':'review','task':'inspect','thinking':'medium'}]})
    assert bridge.runtime.spec['tools']==['graph','literature']
    assert result['results'][0]['result_text']=='review'
    assert bridge.runtime.spec['thinking']=='medium'


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


class DelegatingAdapter:
    adapter_id='pi'
    supports_multiple_writers=True
    def __init__(self):
        import asyncio
        self.bridge=ToolBridge()
        self.child_started=asyncio.Event()
        self.children=0
        self.release={}
    async def start(self,request):
        return self.bridge.bind(request)
    async def submit(self,handle,request,emit):
        try:
            if 'delegate' in request.agent_snapshot['tools']:
                await self.bridge.invoke(handle,'delegate',{'tasks':[{'instructions':'review','task':'wait','thinking':'low'} for _ in range(2)]})
            else:
                self.release[request.turn_id]=asyncio.Event()
                self.children += 1
                if self.children == 2: self.child_started.set()
                await self.release[request.turn_id].wait()
            return AdapterResult(result_text='finished')
        finally:
            self.bridge.release(handle)
    async def cancel(self,handle,request):
        if request.turn_id in self.release: self.release[request.turn_id].set()
    async def close(self):
        pass


@pytest.mark.asyncio
async def test_parent_cancellation_stops_delegated_tools_and_turns(tmp_path):
    import asyncio
    from runtime.runtime import Runtime
    adapter=DelegatingAdapter()
    runtime=Runtime(tmp_path,{'pi':adapter})
    adapter.bridge.runtime=runtime
    await runtime.launch({'adapter':'pi','tools':['delegate','graph']},session_id='session')
    turn=await runtime.submit('session',{'id':'message','content':'research'})
    await asyncio.wait_for(adapter.child_started.wait(),1)
    await asyncio.wait_for(runtime.cancel(turn['id']),1)
    runs=runtime.export_session('session')
    assert len(runs)==3
    assert all(t['status']=='cancelled' for run in runs for t in run['turns'])
    assert adapter.bridge.bindings=={}


class ParallelRuntime:
    def __init__(self):
        import asyncio
        self.specs, self.started = [], asyncio.Event()

    async def delegate(self, parent, spec, **kwargs):
        self.specs.append(spec)
        return {'id': str(len(self.specs))}

    async def submit_child(self, child, message):
        if len(self.specs) == 2:
            self.started.set()
        await self.started.wait()
        return {'id': child}

    async def subscribe(self, turn):
        yield {'type': 'turn_end', 'data': {'status': 'completed', 'result_text': turn}}


@pytest.mark.asyncio
async def test_batch_delegation_starts_independent_children_concurrently():
    import asyncio
    bridge = ToolBridge()
    bridge.runtime = ParallelRuntime()
    token = bridge.bind(request(['delegate', 'graph', 'record', 'connect', 'artifact']))
    tasks = [{'instructions': name, 'task': name, 'thinking': depth}
             for name, depth in [('intro', 'low'), ('proof', 'high')]]
    result = await asyncio.wait_for(bridge.invoke(token, 'delegate', {'tasks': tasks}), 1)
    assert [r['run_id'] for r in result['results']] == ['1', '2']
    assert [s['thinking'] for s in bridge.runtime.specs] == ['low', 'high']
    assert [s['instructions'] for s in bridge.runtime.specs] == ['intro', 'proof']
    assert all(s['tools'] == ['graph'] for s in bridge.runtime.specs)


@pytest.mark.asyncio
@pytest.mark.parametrize('tasks', [[], [{}], [{'instructions':'x','task':'x','thinking':'max'}]])
async def test_invalid_batch_never_starts_children(tasks):
    bridge = ToolBridge()
    bridge.runtime = ParallelRuntime()
    token = bridge.bind(request(['delegate']))
    with pytest.raises(ValueError):
        await bridge.invoke(token, 'delegate', {'tasks': tasks})
    assert bridge.runtime.specs == []


@pytest.mark.asyncio
async def test_one_failed_child_does_not_discard_other_results():
    bridge = ToolBridge()
    async def child(request, task):
        if task['task'] == 'fail':
            raise RuntimeError('private provider details')
        return {'status': 'completed', 'result_text': 'evidence'}
    bridge._delegate_one = child
    token = bridge.bind(request(['delegate']))
    tasks = [{'instructions': 'review', 'task': task, 'thinking': 'low'} for task in ['fail', 'ok']]
    result = await bridge.invoke(token, 'delegate', {'tasks': tasks})
    assert result['results'][0]['status'] == 'error'
    assert result['results'][1]['result_text'] == 'evidence'
    assert 'private provider details' not in str(result)
