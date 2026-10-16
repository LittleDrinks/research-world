import asyncio
import pytest
from runtime.runtime import Runtime
from runtime.errors import RuntimeConflictError
from test_run_turn_trace import FakeAdapter


async def completed(runtime,adapter,session,message):
    turn=await runtime.submit(session,{'id':message,'content':'test'})
    await adapter.wait_for_handles(len(runtime._turns))
    adapter.complete(turn['id'],'done')
    async for _ in runtime.subscribe(turn['id']):pass
    await runtime._turns[turn['id']].task
    return turn


@pytest.mark.asyncio
async def test_project_delete_removes_owned_state_and_survives_restart(tmp_path):
    adapter=FakeAdapter();runtime=Runtime(tmp_path,{'fake':adapter})
    for pid in ['one','two']:await runtime.launch({'adapter':'fake','project_id':pid},session_id=pid)
    await completed(runtime,adapter,'one','message-one')
    kept=await completed(runtime,adapter,'two','message-two')
    events=runtime._store.read_events(kept['id'])
    assert (await runtime.delete_project('one'))['deleted_runs']==1
    assert runtime._store.read_events(kept['id'])==events
    assert (await runtime.delete_project('one'))['deleted_runs']==0
    with pytest.raises(KeyError):runtime.inspect_session('one')
    assert runtime.inspect_session('two')['session_id']=='two'
    assert set(runtime._store.snapshot()['turns'])=={kept['id']}
    await runtime.close();again=Runtime(tmp_path,{'fake':FakeAdapter()})
    assert again.inspect_session('two')['session_id']=='two'
    with pytest.raises(KeyError):again.inspect_session('one')
    await again.close()


@pytest.mark.asyncio
async def test_running_child_prevents_delete_then_entire_family_is_removed(tmp_path):
    adapter=FakeAdapter();runtime=Runtime(tmp_path,{'fake':adapter})
    root=await runtime.launch({'adapter':'fake','project_id':'one'},session_id='one')
    turn=await runtime.submit('one',{'id':'parent','content':'work'})
    child=await runtime.delegate(root['id'],{'adapter':'fake'},parent_turn_id=turn['id'])
    await runtime.submit_child(child['id'],{'id':'child','content':'work'})
    with pytest.raises(RuntimeConflictError):await runtime.delete_project('one')
    assert len(runtime.export_session('one'))==2
    await runtime.cancel(turn['id'])
    await asyncio.gather(*(t.task for t in runtime._turns.values()),return_exceptions=True)
    assert (await runtime.delete_project('one'))['deleted_runs']==2
    snapshot=runtime._store.snapshot()
    assert not any(snapshot[key] for key in ['runs','turns','events','delegations'])
    await runtime.close()
