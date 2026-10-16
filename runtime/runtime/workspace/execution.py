import asyncio
import base64
from contextlib import closing
import json
from pathlib import Path
import secrets
import time

from docker.utils.socket import frames_iter
from docker.errors import DockerException
from .operations import settle

SUPERVISOR = Path(__file__).with_name('supervisor.py').read_text()
WORKER = Path(__file__).with_name('worker.py').read_text()
CANCEL = '''import psutil,sys
from pathlib import Path
p=Path('/tmp')/('rw-exec-'+sys.argv[1]); p.mkdir(mode=0o700,exist_ok=True)
(p/'cancel').touch()
try:
    process=psutil.Process(int((p/'pid').read_text()))
    if process.cmdline()[-1]==sys.argv[1]:
        process.terminate()
        process.wait(timeout=15)
except (FileNotFoundError,psutil.NoSuchProcess): pass
'''
CLEANUP = '''import shutil,sys
shutil.rmtree('/tmp/rw-exec-'+sys.argv[1],ignore_errors=True)
'''


class Execution:
    def __init__(self, container, values):
        self.container, self.values = container, values
        self.id = secrets.token_hex(16)
        self.execution_id = None
        self.queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self.task = asyncio.create_task(self.run())

    async def run(self):
        worker = asyncio.create_task(asyncio.to_thread(self._run))
        try:
            await asyncio.wait_for(asyncio.shield(worker), self.values.get('timeout') or 120)
        except (TimeoutError, asyncio.CancelledError) as error:
            await settle(self._cancel())
            await settle(worker)
            self.queue.put_nowait({'error': 'aborted' if isinstance(error, asyncio.CancelledError) else f"timeout:{self.values.get('timeout') or 120}"})
        except Exception:
            await settle(self._cancel())
            self.queue.put_nowait({'error': '工作区执行失败，请检查容器状态'})
        finally:
            await settle(self._finish())

    def _run(self):
        api = self.container.client.api
        execution = api.exec_create(self.container.id, ['python','-u','-c',SUPERVISOR,self.id],
                                    stdin=True, stdout=True, stderr=True, user='1000:1000', workdir='/workspace')
        self.execution_id = execution['Id']
        stream = api.exec_start(self.execution_id, socket=True)
        with closing(stream._response):
            stream._sock.sendall((json.dumps({**self.values, 'code':WORKER})+'\n').encode())
            for _, data in frames_iter(stream, tty=False):
                self.loop.call_soon_threadsafe(self.queue.put_nowait, {'data':base64.b64encode(data).decode()})
        state = api.exec_inspect(execution['Id'])
        if state['Running'] or state['ExitCode'] is None:
            raise ConnectionError('Workspace output ended before process exit')
        self.loop.call_soon_threadsafe(self.queue.put_nowait, {'exitCode':state['ExitCode']})

    def _control(self, code):
        result = self.container.exec_run(['python','-c',code,self.id], user='1000:1000')
        if result.exit_code != 0: raise RuntimeError('Workspace process cleanup failed')

    def _stop_remote(self):
        self._control(CANCEL)
        deadline = time.monotonic() + 15
        while self.execution_id and self.container.client.api.exec_inspect(self.execution_id)['Running']:
            if time.monotonic() >= deadline: raise TimeoutError('Workspace process did not stop')
            time.sleep(.05)

    async def _cancel(self):
        try: await asyncio.to_thread(self._stop_remote)
        except DockerException:
            await asyncio.to_thread(self.container.reload)
            if self.container.status == 'running': raise

    async def _finish(self):
        try: await asyncio.to_thread(self._control, CLEANUP)
        except DockerException: pass  # A stopped container cannot execute cleanup.
        finally: self.queue.put_nowait(None)

    async def stop(self):
        if not self.task.done() and not self.task.cancelling(): self.task.cancel()
        try: await settle(self.task)
        except asyncio.CancelledError:
            if not self.task.cancelled(): raise
        finally: self.queue.put_nowait(None)

    async def events(self):
        try:
            while (event := await self.queue.get()) is not None:
                yield json.dumps(event)+'\n'
        finally: await self.stop()
