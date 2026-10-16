import asyncio
import hashlib
import os
import re
import secrets
import time
from collections import defaultdict
from pathlib import Path

import docker
from .operations import settle
from .config import pi_configuration,configuration_archive
from ..errors import RuntimeConflictError


class Workspaces:
    def __init__(self):
        self.locks=defaultdict(asyncio.Lock)
        self.prefix=os.environ.get('RW_WORKSPACE_PREFIX','research-world')
        self.image=os.environ.get('RW_WORKSPACE_IMAGE','research-world-workspace:local')
        self.root=Path(os.environ.get('RUNTIME_DATA','/runtime-data'))/'workspaces'
        self._client=None

    @property
    def client(self):
        if self._client is None:self._client=docker.from_env(timeout=60)
        return self._client

    def name(self,project_id):
        if not re.fullmatch(r'project:[0-9a-f]{24}',project_id):raise ValueError('Invalid Project id')
        digest=hashlib.sha256(project_id.encode()).hexdigest()[:24]
        return f'{self.prefix}-lab-{digest}'

    def container(self,project_id):
        try:container=self.client.containers.get(self.name(project_id))
        except docker.errors.NotFound:return None
        if container.labels.get('rw.project')!=project_id or container.labels.get('rw.owner')!=self.prefix:
            raise RuntimeConflictError('工作区标识冲突')
        return container

    def token(self,project_id):
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        path=self.root/(self.name(project_id)+'.token')
        if not path.exists():
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as target:target.write(secrets.token_urlsafe(32))
        return path.read_text()

    def status(self,project_id):
        container=self.container(project_id)
        if container is None:return {'status':'not_started'}
        health=container.attrs['State'].get('Health',{}).get('Status')
        status='ready' if container.status=='running' and health=='healthy' else container.status
        if container.status=='running' and health=='unhealthy':status='unhealthy'
        value={'status':status,'model':container.labels.get('rw.model','')}
        ports=container.attrs['NetworkSettings']['Ports'].get('8888/tcp')
        if status=='ready' and ports:value['url']=f'http://127.0.0.1:{ports[0]["HostPort"]}/lab?token={self.token(project_id)}'
        return value

    async def start(self,project_id,model):
        return await settle(self._start_locked(project_id,model))

    async def _start_locked(self,project_id,model):
        async with self.locks[project_id]:
            await asyncio.to_thread(self._start,project_id,model)
            return await asyncio.to_thread(self.status,project_id)

    def _start(self,project_id,model):
        container=self.container(project_id)
        if not container or container.status!='running':
            files=pi_configuration(Path(os.environ['PI_CODING_AGENT_DIR']),model)
            if container:container.remove()
            container=self._launch(project_id,model,files)
        self._ready(container)

    def _launch(self,project_id,model,files):
        container=self._create(project_id,model)
        try:
            if not container.put_archive('/home/runtime/.pi/agent',configuration_archive(files)):
                raise RuntimeConflictError('工作区配置写入失败')
            container.start()
        except Exception:
            container.remove(force=True)
            raise
        return container

    def _create(self,project_id,model):
        name=self.name(project_id);labels={'rw.owner':self.prefix,'rw.project':project_id,'rw.model':model}
        for suffix in ('files','home'):self._volume(name+'-'+suffix,labels)
        return self.client.containers.create(self.image,name=name,labels=labels,
            volumes={name+'-files':{'bind':'/workspace','mode':'rw'},name+'-home':{'bind':'/home/runtime','mode':'rw'}},
            environment={'JUPYTER_TOKEN':self.token(project_id)},ports={'8888/tcp':('127.0.0.1',None)},
            user='1000:1000',working_dir='/workspace',init=True,cap_drop=['ALL'],security_opt=['no-new-privileges:true'],
            mem_limit='2g',nano_cpus=2_000_000_000,pids_limit=256)

    def _volume(self,name,labels):
        try:volume=self.client.volumes.get(name)
        except docker.errors.NotFound:return self.client.volumes.create(name=name,labels=labels)
        current=volume.attrs.get('Labels') or {}
        if any(current.get(k)!=labels[k] for k in ['rw.owner','rw.project']):raise RuntimeConflictError('工作区存储标识冲突')
        return volume

    def _ready(self,container):
        deadline=time.monotonic()+50
        while time.monotonic()<deadline:
            container.reload();state=container.attrs['State']
            if state.get('Health',{}).get('Status')=='healthy':return
            if container.status in {'exited','dead'}:raise RuntimeConflictError('工作区启动失败，请停止后重试')
            time.sleep(.5)
        return False

    async def stop(self,project_id):
        return await settle(self._stop_locked(project_id))

    async def _stop_locked(self,project_id):
        async with self.locks[project_id]:
            container=await asyncio.to_thread(self.container,project_id)
            if container:await asyncio.to_thread(container.stop,timeout=10)
            return await asyncio.to_thread(self.status,project_id)

    def require_stopped(self,project_id):
        container=self.container(project_id)
        if container and container.status in {'running','restarting','paused'}:
            raise RuntimeConflictError('项目实验工作区正在运行，请先停止工作区再删除项目')

    def remove(self,project_id):
        self.require_stopped(project_id)
        container=self.container(project_id);volumes=self._owned_volumes(project_id)
        if container:container.remove()
        for volume in volumes:volume.remove()
        (self.root/(self.name(project_id)+'.token')).unlink(missing_ok=True)

    def _owned_volumes(self,project_id):
        volumes=[]
        for suffix in ('files','home'):
            try:volume=self.client.volumes.get(self.name(project_id)+'-'+suffix)
            except docker.errors.NotFound:continue
            labels=volume.attrs.get('Labels') or {}
            if labels.get('rw.project')!=project_id or labels.get('rw.owner')!=self.prefix:
                raise RuntimeConflictError('工作区存储标识冲突')
            volumes.append(volume)
        return volumes
