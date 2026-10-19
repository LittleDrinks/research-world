import copy
import json

import httpx
import pytest

from server.review_worker import ReviewWorker
from test_pi_product import setup


@pytest.fixture
def case(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Review', 'Why energy drifts?').id
    original = kernel.capture_artifact(project, b'# Results', 'text/markdown')
    record = kernel.record(project, 'experiment', {'title':'Energy','text':'Check error'}, (original.id,))
    label = kernel.save_label(project, {'name':'need-review','color':'#8050c0'})
    return app, kernel, runtime, project, record, label


def client_for(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://test')


async def bind(client, project, label, **patch):
    root = f'/api/v1/projects/{project}'
    template = (await client.get(root+'/artifact-templates')).json()[0]
    response = await client.put(root+'/review-rules/'+label['id'], json={
        'enabled':True,'agent_id':'research-assistant','schema_id':template['id'],**patch})
    assert response.status_code == 200, response.text
    return template


def tag(case, labels, author='user'):
    _, kernel, _, project, record, _ = case
    revision = kernel.get_record(project, record.id).revision
    return kernel.change_record(project, record.id, {'kind':'labels','base_revision':revision,
        'label_ids':[label['id'] for label in labels],'reason':'请复核'}, author)


def task(case):
    app, _, _, project, record, _ = case
    return app.state.reviews.store.list_tasks(project, record.id)[0]


async def report(client, value, template, **patch):
    data = copy.deepcopy(template['example'])
    data.update(title='能量漂移复核',summary='现有数值不足以判定误差来源。',target_artifact_id=value['target_id'])
    body = {'schema_id':template['id'],'record_id':value['record_id'],'content':json.dumps(data),**patch}
    return await client.post(f'/api/v1/projects/{value["project_id"]}/artifacts',json=body,
                             headers={'x-research-author':'agent:'+value['run_id']})


async def launch(case, client):
    app, _, _, project, _, label = case
    template = await bind(client, project, label)
    tag(case, [label], 'agent:author-run')
    await app.state.reviews.tick()
    return template, task(case)


@pytest.mark.asyncio
async def test_roundtrip(case):
    app, kernel, runtime, project, record, _ = case
    async with client_for(app) as client:
        template, value = await launch(case, client)
        prompt = kernel.get_session(project, value['session_id']).messages[0].content
        assert '原研究对话未注入' in prompt and template['id'] in prompt and value['target_id'] in prompt
        response = await report(client, value, template)
        assert response.status_code == 201, response.text
        await app.state.reviews.tick()
        assert task(case)['status'] == 'completed' and not kernel.get_record(project,record.id).labels
        comments = [c for c in kernel.list_changes(project,record.id) if c['kind']=='comment']
        assert len(comments)==1 and comments[0]['reference_revision']==2
        assert comments[0]['author']=='agent:'+value['run_id'] and '完整报告' in comments[0]['comment']
        await ReviewWorker(app.state.reviews.control).tick()
        assert runtime.calls==1 and len([c for c in kernel.list_changes(project,record.id) if c['kind']=='comment'])==1
        view = (await client.get(f'/api/v1/projects/{project}/records/{record.id}/reviews')).json()[0]
        assert view['input_changed'] is False


def mutate(case, mutation):
    _, kernel, _, project, record, label = case
    common = {'base_revision':kernel.get_record(project,record.id).revision,'reason':'研究更新'}
    if mutation=='body':
        kernel.change_record(project,record.id,common|{'kind':'revise','title':'New','text':'Different experiment'})
    if mutation=='attachment':
        artifact = kernel.capture_artifact(project,b'New input','text/plain')
        kernel.attach_artifact(project,record.id,artifact.id)
    if mutation=='retag':
        tag(case,[])
        tag(case,[label])
    if mutation=='comment':
        kernel.change_record(project,record.id,common|{'kind':'comment','comment':'关注误差','reference_revision':2})
    if mutation=='rename':
        kernel.save_label(project,{'name':'请复核','color':'#123456'},label['id'])


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation',['body','attachment','retag','comment','rename'])
async def test_scope_and_request_ownership(case,mutation):
    app,kernel,_,project,record,_=case
    async with client_for(app) as client:
        template,value=await launch(case,client)
        mutate(case,mutation)
        assert (await report(client,value,template)).status_code==201
        await app.state.reviews.tick()
    assert bool(kernel.get_record(project,record.id).labels)==(mutation in {'body','attachment','retag'})
    assert len(app.state.reviews.store.list_tasks(project,record.id))==1
    text=next(c['comment'] for c in kernel.list_changes(project,record.id) if c['kind']=='comment' and c['author'].startswith('agent:'))
    assert ('尚未覆盖' in text)==(mutation in {'body','attachment'})


@pytest.mark.asyncio
async def test_new_events_only_and_frozen_agent(case):
    app,_,runtime,project,record,label=case
    async with client_for(app) as client:
        tag(case,[label])
        await bind(client,project,label)
        assert not app.state.reviews.store.pending()
        tag(case,[]);tag(case,[label])
        config=app.state.reviews.store.rules(project)[0]['config']['agent']
        app.state.reviews.control.profiles.save(config|{'instructions':'Changed after binding'})
        await app.state.reviews.tick()
        assert 'Changed after binding' not in runtime.runs[task(case)['session_id']]['agent_snapshot']['instructions']
        tag(case,[]);tag(case,[label])
        assert runtime.calls==1 and len(app.state.reviews.store.pending())==1
        await bind(client,project,label,enabled=False)
        mutate(case,'body');tag(case,[]);tag(case,[label])
        assert len(app.state.reviews.store.list_tasks(project,record.id))==1


@pytest.mark.asyncio
async def test_restart_after_accepted_turn_never_duplicates_model_calls(case):
    app,_,runtime,_,_,_=case
    async with client_for(app) as client:
        template,value=await launch(case,client)
        app.state.reviews.store.update(value['id'],turn_id=None)
        await ReviewWorker(app.state.reviews.control).tick()
        assert runtime.calls==1
        assert (await report(client,task(case),template)).status_code==201
        await ReviewWorker(app.state.reviews.control).tick()
        assert task(case)['status']=='completed'


@pytest.mark.asyncio
async def test_plain_reply_is_not_report_explicit_retry_uses_same_session(case):
    app,kernel,runtime,project,record,_=case
    async with client_for(app) as client:
        await launch(case,client)
        await app.state.reviews.tick()
        value=task(case)
        assert value['status']=='failed' and '结构化报告' in value['error']
        assert kernel.get_record(project,record.id).labels
        assert (await client.post(f'/api/v1/projects/{project}/reviews/{value["id"]}/retry')).status_code==200
        await app.state.reviews.tick()
        assert runtime.calls==2 and task(case)['session_id']==value['session_id']
        assert task(case)['payload']['attempt']==1
        assert (await client.post(f'/api/v1/projects/{project}/reviews/{value["id"]}/retry')).status_code==400


@pytest.mark.asyncio
async def test_report_provenance_targets_and_schema(case):
    app,kernel,_,project,record,_=case
    async with client_for(app) as client:
        template,value=await launch(case,client)
        data=template['example']|{'target_artifact_id':value['target_id']}
        body={'schema_id':template['id'],'record_id':record.id,'content':json.dumps(data)}
        assert (await client.post(f'/api/v1/projects/{project}/artifacts',json=body)).status_code==400
        assert (await report(client,value,template,content=json.dumps(data|{'target_artifact_id':record.artifact_ids[0]}))).status_code==400
        assert (await report(client,value,template,content=json.dumps(data|{'summary':'x'*401}))).status_code==422
        other=kernel.record(project,'direction',{'title':'Other'},(value['target_id'],))
        assert (await report(client,value,template,record_id=other.id)).status_code==400
        assert task(case)['report_id'] is None
        first=await report(client,value,template)
        assert first.status_code==201
        assert (await report(client,value,template)).json()['id']==first.json()['id']
        assert (await report(client,value,template,content=json.dumps(data|{'summary':'Replacement'}))).status_code==400


@pytest.mark.asyncio
async def test_project_isolation(case):
    app,kernel,_,project,record,label=case
    other=kernel.create_project('Other','Other')
    async with client_for(app) as client:
        template=await bind(client,project,label)
        tag(case,[label])
        value=task(case)
        root=f'/api/v1/projects/{other.id}'
        body={'enabled':True,'agent_id':'research-assistant','schema_id':template['id']}
        assert (await client.put(root+'/review-rules/'+label['id'],json=body)).status_code==404
        assert (await client.get(root+f'/records/{record.id}/reviews')).status_code==404
        assert (await client.post(root+f'/reviews/{value["id"]}/retry')).status_code==404
        assert (await client.post(root+'/artifacts',json={'operation':'read','artifact_id':record.artifact_ids[0]})).status_code==404


@pytest.mark.asyncio
async def test_cancel_and_revocation_prevent_launch(case):
    app,kernel,runtime,project,record,label=case
    async with client_for(app) as client:
        await bind(client,project,label)
        tag(case,[label])
        value=task(case)
        assert (await client.post(f'/api/v1/projects/{project}/reviews/{value["id"]}/cancel')).status_code==200
        await app.state.reviews.tick()
        assert runtime.calls==0 and task(case)['status']=='cancelled'
        mutate(case,'body');tag(case,[]);tag(case,[label])
        kernel.remove_record(project,record.id)
        await app.state.reviews.tick()
        assert runtime.calls==0 and not app.state.reviews.store.pending()


def wait_task(client, root, record_id, status):
    import time
    for _ in range(60):
        values=client.get(root+f'/records/{record_id}/reviews').json()
        if values and values[0]['status']==status:
            return values[0]
        time.sleep(.1)
    raise AssertionError(f'Expected {status}, got {values}')


def configure_sync(client,project,label):
    root=f'/api/v1/projects/{project}'
    template=client.get(root+'/artifact-templates').json()[0]
    assert client.put(root+'/review-rules/'+label['id'],json={
        'enabled':True,'agent_id':'research-assistant','schema_id':template['id']}).status_code==200
    return root,template


def submit_report_sync(client,root,template,value):
    data=template['example']|{'target_artifact_id':value['target_id'],'summary':'缺少独立结果，暂不能确认。'}
    response=client.post(root+'/artifacts',json={'schema_id':template['id'],'record_id':value['record_id'],
        'content':json.dumps(data)},headers={'x-research-author':'agent:'+value['run_id']})
    assert response.status_code==201,response.text


def test_lifespan_dispatches_public_agent_change_and_writes_back(case):
    from fastapi.testclient import TestClient
    app,kernel,runtime,project,record,label=case
    with TestClient(app) as client:
        root,template=configure_sync(client,project,label)
        response=client.post(root+f'/records/{record.id}/changes',json={'kind':'labels','base_revision':1,
            'label_ids':[label['id']],'reason':'独立核查'},headers={'x-research-author':'agent:source'})
        assert response.status_code==201
        value=wait_task(client,root,record.id,'running')
        submit_report_sync(client,root,template,value)
        wait_task(client,root,record.id,'completed')
        assert runtime.calls==1 and not kernel.get_record(project,record.id).labels


def test_change_and_enqueued_task_roll_back_together(case,monkeypatch):
    import server.change_store as module
    _,kernel,_,project,record,label=case
    original=module.enqueue
    def fail(connection,change):
        original(connection,change)
        raise ValueError('storage failure')
    monkeypatch.setattr(module,'enqueue',fail)
    with pytest.raises(ValueError,match='storage failure'):
        tag(case,[label])
    assert kernel.get_record(project,record.id).revision==1
    assert not kernel.list_changes(project,record.id)
    assert not case[0].state.reviews.store.pending()


@pytest.mark.asyncio
async def test_binding_can_be_disabled_after_agent_config_is_deleted(case):
    from server.agent_profiles import default_profile
    app,_,_,project,_,label=case
    profiles=app.state.reviews.control.profiles
    profiles.save(default_profile('test/model')|{'id':'reviewer','name':'Reviewer'})
    async with client_for(app) as client:
        await bind(client,project,label,agent_id='reviewer')
        profiles.delete('reviewer')
        await bind(client,project,label,agent_id='reviewer',enabled=False)
        assert not app.state.reviews.store.rules(project)[0]['enabled']
