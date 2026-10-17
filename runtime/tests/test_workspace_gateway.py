import hashlib
import os
import time

import docker
import httpx
import pytest

pytestmark=pytest.mark.skipif(os.getenv('RW_GATEWAY_TEST')!='1',reason='Requires server Compose gateway')


@pytest.fixture
def failed_workspace():
    prefix=os.getenv('RW_GATEWAY_PREFIX','research-world')
    client=docker.from_env();http=httpx.Client(base_url=os.getenv('RW_GATEWAY_URL','http://127.0.0.1'),timeout=20)
    project=http.post('/api/v1/projects',json={'name':'网关故障验收','question':'验证失败日志与路由边界'}).json()['id']
    name=prefix+'-lab-'+hashlib.sha256(project.encode()).hexdigest()[:24]
    container=client.containers.run(prefix+'-workspace:local',['python','-c','import time;time.sleep(60)'],detach=True,
        name=name,labels={'rw.owner':prefix,'rw.project':project},ports={'8888/tcp':('127.0.0.1',None)},
        healthcheck={'test':['CMD','true'],'interval':1000000000,'timeout':1000000000,'retries':1,'start_period':1000000})
    try:
        wait_healthy(container)
        yield http,project,client.containers.get(prefix+'-gateway-1'),client.containers.get(prefix+'-runtime-1')
    finally:
        container.remove(force=True);http.delete('/api/v1/projects/'+project);http.close();client.close()


def wait_healthy(container):
    for _ in range(50):
        container.reload()
        if container.attrs['State'].get('Health',{}).get('Status')=='healthy':return
        time.sleep(.1)
    pytest.fail('fault fixture did not start')


def test_gateway_replaces_untrusted_upstream_and_redacts_error_credentials(failed_workspace):
    client,project,gateway,runtime=failed_workspace
    marker='gateway-log-must-not-contain-this-token'
    path='/labs/'+project.split(':')[1]+'/api?token='+marker
    response=client.get(path,headers={'X-Workspace-Upstream':'127.0.0.1:8095','Referer':'http://example.test/?token='+marker})
    assert response.status_code==502
    logs=gateway.logs().decode()
    if project.split(':')[1] not in logs:pytest.fail('Expected error was not logged')
    if marker in logs or marker in runtime.logs().decode():pytest.fail('Workspace token leaked into logs')
