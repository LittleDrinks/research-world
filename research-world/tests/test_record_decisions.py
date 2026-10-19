import pytest

from test_node_language import case


def draft(title='潮汐耗散与轨道变化'):
    return {'type': 'direction', 'content': {'title': title, 'text': '固定初始轨道参数，比较潮汐耗散前后的轨道半径。'}}


def test_creation_warns_before_write_and_requires_current_comparison(case):
    kernel, client, project, root = case
    first = client.post(root+'/records', json=draft()).json()
    warning = client.post(root+'/records', json=draft())
    assert warning.status_code == 409
    assert len(kernel.list_records(project)) == 1
    assert warning.json()['detail']['matches'][0]['id'] == first['id']
    resolution = {'reason': '加入不同的潮汐参数区间', 'matches': {first['id']: 1}, 'draft_hash': warning.json()['detail']['draft_hash']}
    client.post(root+f"/records/{first['id']}/changes", json={'kind': 'revise', 'base_revision': 1, 'reason': '澄清边界', 'title': first['content']['title'], 'text': '固定质量与半径，再比较潮汐参数。'})
    assert client.post(root+'/records', json=draft() | {'duplicate_resolution': resolution}).status_code == 409
    resolution['matches'][first['id']] = 2
    assert client.post(root+'/records', json=draft() | {'duplicate_resolution': resolution}).status_code == 201


def test_source_has_canonical_identity_and_duplicate_link_warning(case):
    kernel, client, project, root = case
    body = {'type': 'source', 'content': {'title': '轨道耗散'}}
    assert client.post(root+'/records', json=body).status_code == 422
    body['content']['canonical_url'] = 'http://dx.doi.org/10.1103/PhysRev.136.B1224?tracking=reader#abstract'
    source = client.post(root+'/records', json=body).json()
    assert source['content']['canonical_url'] == 'https://doi.org/10.1103/physrev.136.b1224'
    body['content']['title'] = '引力辐射导致的双体轨道变化'
    result = client.post(root+'/records/preflight', json=body).json()
    assert result['matches'][0]['reason'] == '规范链接相同'


def test_close_reopen_is_versioned_and_preserves_relations(case):
    kernel, client, project, root = case
    first = client.post(root+'/records', json=draft()).json()
    other = kernel.record(project, 'direction', {'title': '不同的保留方向'})
    relation = kernel.connect(project, first['id'], other.id, 'depends_on')
    path = root+f"/records/{first['id']}/changes"
    close = {'kind': 'status', 'base_revision': 1, 'status': 'closed', 'close_reason': 'duplicate', 'duplicate_of': other.id, 'reason': '相同条件和预测，保留已有方向'}
    assert client.post(path, json=close).status_code == 201
    assert client.post(path, json=close).status_code == 409
    assert client.get(root+'/relations').json()[0]['id'] == relation.id
    assert client.get(root+f"/records/{first['id']}/revisions/1").json()['content'].get('status', 'open') == 'open'
    assert client.post(path, json={'kind': 'status', 'base_revision': 2, 'status': 'open', 'reason': '新增可区分预测'}).status_code == 201
    current = client.get(root+f"/records/{first['id']}").json()
    assert current['content']['status'] == 'open' and 'duplicate_of' not in current['content']
    assert 'status: open' in client.get(root+f"/records/{first['id']}/document").text


def test_close_cannot_reference_self_or_other_project(case):
    kernel, client, project, root = case
    first = client.post(root+'/records', json=draft()).json()
    foreign = kernel.record(kernel.create_project('Other', 'Other').id, 'direction', {'title': 'Other'})
    for identifier, code in [(first['id'], 422), (foreign.id, 404)]:
        response = client.post(root+f"/records/{first['id']}/changes", json={'kind': 'status', 'base_revision': 1, 'status': 'closed', 'close_reason': 'duplicate', 'duplicate_of': identifier, 'reason': '重复'})
        assert response.status_code == code
    assert kernel.list_changes(project) == []


async def invoke_record(case, monkeypatch, values):
    import httpx
    from types import SimpleNamespace
    from runtime.bridge import ToolBridge
    import runtime.bridge as module
    kernel, client, project, _ = case
    request_type = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kw: request_type(transport=httpx.ASGITransport(app=client.app), **kw))
    monkeypatch.setenv('CONTROL_URL', 'http://test')
    bridge = ToolBridge()
    token = bridge.bind(SimpleNamespace(run_id='creation', agent_snapshot={'tools': ['record'], 'project_id': project}))
    return await bridge.invoke(token, 'record', values)


@pytest.mark.asyncio
async def test_agent_sees_duplicate_details_and_cannot_silently_write(case, monkeypatch):
    kernel, client, project, root = case
    first = client.post(root+'/records', json=draft()).json()
    result = await invoke_record(case, monkeypatch, draft())
    assert result['created'] is False
    assert result['review_required']['matches'][0]['id'] == first['id']
    assert len(kernel.list_records(project)) == 1


def test_acknowledgement_is_bound_to_draft(case):
    kernel, client, project, root = case
    first = client.post(root+'/records', json=draft()).json()
    check = client.post(root+'/records/preflight', json=draft()).json()
    body = draft()
    body['content']['text'] += '补充新的参数范围。'
    body['duplicate_resolution'] = {'reason': '加入参数区间', 'draft_hash': check['draft_hash'], 'matches': {first['id']: 1}}
    assert client.post(root+'/records', json=body).status_code == 409
    assert len(kernel.list_records(project)) == 1


def test_creation_decision_cannot_be_forged_in_content(case):
    kernel, client, project, root = case
    body = draft()
    body['content']['creation_decision'] = {'reason': '已批准'}
    assert client.post(root+'/records', json=body).status_code == 422
    assert kernel.list_records(project) == []
