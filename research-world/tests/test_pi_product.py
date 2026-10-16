import asyncio
from pathlib import Path

import httpx
import pytest

@pytest.fixture(autouse=True)
def no_background_title(monkeypatch):
    monkeypatch.setattr("server.session_control.schedule_title", lambda *args: None)


from server.agent_profiles import AgentProfiles, default_profile
from server.kernel_interface import create_kernel
from server.app import create_product


class RuntimeStub:
    def __init__(self):
        self.runs = {}
        self.calls = 0

    async def catalog(self):
        return {'default_model':'test/model','models':['test/model'],'skills':[],
                'tools':{'graph':'read','record':'write'},'runtime':'pi'}

    async def validate(self, value):
        if value['model'] != 'test/model':
            raise ValueError('unknown model')
        return {'instructions':value['instructions']}

    async def launch(self, spec, session_id):
        self.runs[session_id] = {'id':'run-'+session_id,'agent_snapshot':spec,'turns':[]}

    async def inspect(self, session_id):
        return self.runs[session_id]

    async def submit(self, session_id, message):
        existing = next((t for t in self.runs[session_id]['turns'] if t['message_id']==message['id']),None)
        if existing:
            return existing
        self.calls += 1
        turn = {'id':'turn-'+message['id'],'message_id':message['id'],'status':'completed','result_text':'answer'}
        self.runs[session_id]['turns'].append(turn)
        return turn

    async def subscribe(self, turn_id, cursor=-1):
        yield {'seq':0,'type':'turn_end','data':{'status':'completed','result_text':'answer'}}

    async def close(self):
        pass


def setup(tmp_path):
    kernel=create_kernel(tmp_path/'graph.db',tmp_path/'artifacts')
    runtime=RuntimeStub()
    profiles=AgentProfiles(tmp_path/'profiles')
    app=create_product(kernel,runtime,profiles,tmp_path/'workspaces')
    return app,kernel,runtime


@pytest.mark.asyncio
async def test_product_message_refresh_idempotency_and_isolation(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        project=(await client.post('/api/v1/projects',json={'name':'Orbit','question':'Why stable?'})).json()
        root=f'/api/v1/projects/{project["id"]}/sessions'
        session=(await client.post(root,json={'content':'first message','message_id':'initial'})).json()['session']
        path=f'{root}/{session["id"]}'
        body={'message_id':'message-1','content':'Calculate a baseline'}
        first=await client.post(path+'/messages',json=body)
        second=await client.post(path+'/messages',json=body)
        detail=(await client.get(path)).json()
        other=kernel.create_project('Other','Question')
        foreign=await client.get(f'/api/v1/projects/{other.id}/sessions/{session["id"]}')
    assert first.status_code==second.status_code==202
    assert runtime.calls==2
    assert detail['session']['messages'][0]['assistant_response']=='answer'
    assert 'workspace' not in detail['run']['agent_snapshot']
    assert foreign.status_code==404


@pytest.mark.asyncio
async def test_agent_edits_only_affect_new_session(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        project=kernel.create_project('Orbit','Question')
        root=f'/api/v1/projects/{project.id}/sessions'
        old=(await client.post(root,json={'content':'first message','message_id':'initial'})).json()['session']
        profile=default_profile('test/model')|{'instructions':'Updated scientific instructions'}
        assert (await client.put('/api/v1/agents/research-assistant',json=profile)).status_code==200
        new=(await client.post(root,json={'content':'new first message','message_id':'initial-new'})).json()['session']
    assert runtime.runs[old['id']]['agent_snapshot']['instructions']!=runtime.runs[new['id']]['agent_snapshot']['instructions']


@pytest.mark.asyncio
async def test_research_record_roundtrip_and_export(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        project=kernel.create_project('Orbit','Question')
        root=f'/api/v1/projects/{project.id}'
        record=await client.post(root+'/records',json={'type':'direction','content':{'title':'Baseline','text':'Unverified hypothesis'}})
        graph=(await client.post(root+'/local-map',json={})).json()
        exported=await client.get(root+'/export')
    assert record.status_code==201
    assert record.json()['id'] in [r['id'] for r in graph['records']]
    assert exported.status_code==200 and exported.content.startswith(b'PK')


def test_custom_profile_keeps_default_available(tmp_path):
    profiles=AgentProfiles(tmp_path/'profiles')
    profiles.save(default_profile('test/model')|{'id':'reviewer','name':'Reviewer'})
    assert {p['id'] for p in profiles.list('test/model')}=={'research-assistant','reviewer'}


@pytest.mark.asyncio
async def test_export_includes_unlinked_report_and_checksums(tmp_path):
    import io, json, zipfile, hashlib
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Report','Question')
    artifact=kernel.capture_artifact(project.id,b'report body','text/markdown')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        response=await client.get(f'/api/v1/projects/{project.id}/export')
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        name=f'artifacts/{artifact.sha256}'
        assert archive.read(name)==b'report body'
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['files'][name]['sha256']==hashlib.sha256(b'report body').hexdigest()
        assert name.encode() in archive.read('checksums.sha256')


@pytest.mark.asyncio
async def test_sessions_require_first_message_and_can_be_archived(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Drafts','Question')
    root=f'/api/v1/projects/{project.id}/sessions'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        assert (await client.post(root,json={})).status_code==422
        assert (await client.get(root)).json()==[]
        created=(await client.post(root,json={'content':'A scientific question','message_id':'first'})).json()
        session=created['session']
        assert session['title']=='A scientific question'
        assert (await client.delete(root+'/'+session['id'])).status_code==204
        assert (await client.get(root)).json()==[]
        assert len(kernel.list_sessions(project.id,include_archived=True))==1


@pytest.mark.asyncio
async def test_first_message_retry_reuses_session_and_turn(tmp_path):
    app,kernel,runtime=setup(tmp_path)
    project=kernel.create_project('Retry','Question')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
        path=f'/api/v1/projects/{project.id}/sessions'
        body={'content':'Initial scientific question','message_id':'first'}
        first=(await client.post(path,json=body)).json()
        repeated=(await client.post(path,json=body)).json()
    assert first['session']['id']==repeated['session']['id']
    assert first['turn']==repeated['turn']
    assert runtime.calls==1
