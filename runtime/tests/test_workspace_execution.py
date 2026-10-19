import asyncio
import base64
import json
import os

import pytest
from runtime.workspace.execution import Execution

pytestmark=pytest.mark.skipif(os.getenv('RW_DOCKER_TEST')!='1',reason='Requires the workspace image and Docker')


@pytest.fixture
def container():
    import docker
    client=docker.from_env()
    value=client.containers.run('research-world-workspace:local',entrypoint=['python','-c','import time;time.sleep(600)'],
                                detach=True,network_mode='none',user='1000:1000',working_dir='/workspace')
    try: yield value
    finally: value.remove(force=True);client.close()


async def execute(container, **values):
    events=[json.loads(event) async for event in Execution(container,values).events()]
    output=b''.join(base64.b64decode(event['data']) for event in events if 'data' in event)
    return events,output


@pytest.mark.asyncio
async def test_artifact_file_read_is_bounded_and_rejects_escape(container):
    from runtime.artifact_files import read_text
    await execute(container, operation='write', path='report.json', content='{"summary":"范围"}')
    value = await read_text(Execution(container, {'operation':'read','path':'report.json','max_bytes':100}).events())
    assert value == '{"summary":"范围"}'
    for path, limit in [('report.json', 2), ('/etc/passwd', 100), ('../secret', 100)]:
        with pytest.raises(ValueError):
            await read_text(Execution(container, {'operation':'read','path':path,'max_bytes':limit}).events())
    await execute(container, operation='bash', command='ln -s /etc/passwd /workspace/escape')
    with pytest.raises(ValueError):
        await read_text(Execution(container, {'operation':'read','path':'escape','max_bytes':100}).events())


@pytest.mark.asyncio
async def test_files_commands_and_user_edits_share_one_directory(container):
    content='print("hello-world")\n'+'# 中文\n'*40000
    events,_=await execute(container,operation='write',path='/workspace/hello.py',content=content)
    assert events[-1]=={'exitCode':0}
    events,output=await execute(container,operation='read',path='hello.py')
    assert output.decode()==content
    events,output=await execute(container,operation='bash',command='python hello.py')
    assert output==b'hello-world\n' and events[-1]=={'exitCode':0}
    container.exec_run(['python','-c','from pathlib import Path;Path("/workspace/hello.py").write_text("print(42)")'])
    events,output=await execute(container,operation='bash',command='python hello.py')
    assert output==b'42\n'
    events,_=await execute(container,operation='read',path='/etc/passwd')
    assert events[-1]=={'exitCode':1}


@pytest.mark.asyncio
async def test_timeout_and_cancel_kill_descendants(container):
    events,_=await execute(container,operation='bash',command='(sleep 2; touch /workspace/leaked) & wait',timeout=.2)
    assert events[-1]=={'error':'timeout:0.2'}
    job=Execution(container,{'operation':'bash','command':'echo ready; (sleep 2; touch /workspace/leaked) & wait'})
    await asyncio.wait_for(job.queue.get(),5)
    await job.stop()
    await asyncio.sleep(2.1)
    assert container.exec_run(['test','-e','/workspace/leaked']).exit_code==1


@pytest.mark.asyncio
async def test_normal_completion_cleans_background_and_reports_failure(container):
    events,output=await execute(container,operation='bash',command='(sleep 2; touch /workspace/leaked) & echo done')
    assert events[-1]=={'exitCode':0} and output==b'done\n'
    await asyncio.sleep(2.1)
    assert container.exec_run(['test','-e','/workspace/leaked']).exit_code==1
    events,_=await execute(container,operation='bash',command='exit 7')
    assert events[-1]=={'exitCode':7}


@pytest.mark.asyncio
async def test_immediate_cancellation_and_stopped_container_terminate_stream(container):
    job=Execution(container,{'operation':'bash','command':'sleep 10'})
    await asyncio.wait_for(job.stop(),2)
    assert job.task.done()
    container.stop(timeout=1)
    events,_=await asyncio.wait_for(execute(container,operation='read',path='hello.py'),3)
    assert events[-1].get('error')


@pytest.mark.asyncio
@pytest.mark.parametrize('mode',['cancel','timeout','complete'])
async def test_detached_job_control_descendants_do_not_escape(container,mode):
    command='set -m; (sleep 2; touch /workspace/escaped) >/dev/null 2>&1 & echo READY'
    if mode!='complete': command+='; wait'
    job=Execution(container,{'operation':'bash','command':command,'timeout':.4 if mode=='timeout' else 30})
    if mode=='cancel':
        await asyncio.wait_for(job.queue.get(),5)
        await job.stop()
    else: _=[event async for event in job.events()]
    await asyncio.sleep(2.1)
    assert container.exec_run(['test','-e','/workspace/escaped']).exit_code==1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["before","reset","eof"])
async def test_broken_output_transport_still_stops_command(container,monkeypatch,failure):
    import runtime.workspace.execution as module
    original=module.frames_iter
    def disconnect(*args,**kwargs):
        if failure=="before": raise ConnectionResetError('disconnect before first output')
        for frame in original(*args,**kwargs):
            yield frame
            if failure=='reset': raise ConnectionResetError('simulated output disconnect')
            import socket
            args[0]._sock.shutdown(socket.SHUT_RD)
    monkeypatch.setattr(module,'frames_iter',disconnect)
    events,_=await execute(container,operation='bash',command='echo ready; sleep 2; touch /workspace/disconnect')
    assert events[-1].get('error')
    await asyncio.sleep(2.1)
    assert container.exec_run(['test','-e','/workspace/disconnect']).exit_code==1
