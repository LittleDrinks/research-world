import io
import json
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kernel_contract import LocalMapQuery

from server.kernel_http import kernel_graph_router
from server.kernel_interface import create_kernel
from server.project_export import export_project


@pytest.fixture
def setup(graph_kernel):
    kernel = graph_kernel
    project = kernel.create_project('joint', 'orbit')
    records = [kernel.record(project.id, 'direction', {'title': name}) for name in ['A', 'B', 'Target']]
    artifact = kernel.capture_artifact(project.id, b'Evidence section 2', 'text/plain')
    request = {'title': 'joint explanation', 'rule': 'AND', 'target_id': records[2].id,
               'members': [{'record_id': r.id, 'role': r.content['title']} for r in records[:2]],
               'statement': 'bounded statement', 'rationale': 'Both conditions are required',
               'evidence': [{'artifact_id': artifact.id, 'locator': 'section 2'}]}
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))
    return kernel, project, records, request, TestClient(app)


@pytest.mark.parametrize(('rule', 'k'), [('AND', None), ('OR', None), ('k-of-N', 1), ('k-of-N', 2)])
def test_http_roundtrip_and_local_map_closure(setup, rule, k):
    kernel, project, records, request, client = setup
    request.update(rule=rule, k=k)
    path = f'/api/v1/projects/{project.id}/joint-conditions'
    response = client.post(path, json=request)
    assert response.status_code == 201, response.text
    value = response.json()
    assert client.post(path, json=request).json()['id'] == value['id']
    reopened = create_kernel(kernel._database, kernel._artifacts)
    assert reopened.list_joint_conditions(project.id) == [value]
    result = reopened.local_map(project.id, LocalMapQuery(record_id=records[0].id, limit=1))
    assert {r.id for r in result.records} == {r.id for r in records}
    assert result.joint_conditions == (value,)
    assert result.artifacts[0].id == request['evidence'][0]['artifact_id']


@pytest.mark.parametrize('patch', [
    {'rule': 'causal'}, {'k': 1}, {'rule': 'k-of-N'}, {'rule': 'k-of-N', 'k': 0},
    {'rule': 'k-of-N', 'k': 3}, {'rule': 'k-of-N', 'k': True}, {'rule': 'k-of-N', 'k': 1.5},
    {'rationale': '  '}, {'statement': ''}, {'title': 'x' * 161}, {'evidence': []}, {'extra': 'value'},
])
def test_invalid_conditions_rejected(setup, patch):
    kernel, project, _, request, client = setup
    response = client.post(f'/api/v1/projects/{project.id}/joint-conditions', json=request | patch)
    assert response.status_code == 422
    assert kernel.list_joint_conditions(project.id) == []


def test_duplicate_members_self_reference_and_blank_locator(setup):
    _, project, records, request, client = setup
    path = f'/api/v1/projects/{project.id}/joint-conditions'
    assert client.post(path, json=request | {'members': [request['members'][0]] * 2}).status_code == 422
    assert client.post(path, json=request | {'target_id': records[0].id}).status_code == 422
    request['evidence'][0]['locator'] = ' '
    assert client.post(path, json=request).status_code == 422


def test_project_isolation_and_revoked_references(setup):
    kernel, project, records, request, client = setup
    other = kernel.create_project('other', 'other')
    foreign = kernel.record(other.id, 'source', {'title': 'foreign'})
    path = f'/api/v1/projects/{project.id}/joint-conditions'
    assert client.post(path, json=request | {'target_id': foreign.id}).status_code == 403
    foreign_artifact = kernel.capture_artifact(other.id, b'foreign', 'text/plain')
    assert client.post(path, json=request | {'evidence': [{'artifact_id': foreign_artifact.id, 'locator': '1'}]}).status_code == 404
    condition = client.post(path, json=request).json()
    kernel.remove_record(project.id, records[0].id)
    assert client.post(path, json=request).status_code == 404
    assert kernel.get_record(project.id, records[2].id).id == records[2].id
    result = client.get(path).json()[0]
    assert result['unavailable_ids'] == [records[0].id]
    assert result['id'] == condition['id']


@pytest.mark.asyncio
async def test_export_and_project_deletion(setup):
    kernel, project, _, request, _ = setup
    condition = kernel.create_joint_condition(project.id, request)
    payload = await export_project(kernel, object(), project.id)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        snapshot = json.loads(archive.read('project.json'))
        assert snapshot['joint_conditions'] == [condition]
    kernel.delete_project(project.id)
    with kernel._connect() as connection:
        assert connection.execute('SELECT COUNT(*) FROM kernel_joint_conditions').fetchone()[0] == 0


@pytest.mark.asyncio
async def test_agent_tool_reaches_real_http_validation(setup, monkeypatch):
    import httpx
    import runtime.bridge as bridge_module
    from runtime.adapter import TurnRequest
    kernel, project, _, request, client = setup
    original = httpx.AsyncClient
    monkeypatch.setenv('CONTROL_URL', 'http://control')
    monkeypatch.setattr(bridge_module.httpx, 'AsyncClient', lambda **kw: original(transport=httpx.ASGITransport(app=client.app), **kw))
    bridge = bridge_module.ToolBridge()
    turn = TurnRequest('run', 'turn', 'message', 'prompt', (), {'tools': ['joint_condition'], 'project_id': project.id}, None)
    token = bridge.bind(turn)
    value = await bridge.invoke(token, 'joint_condition', request)
    assert kernel.list_joint_conditions(project.id)[0]['id'] == value['id']
    with pytest.raises(httpx.HTTPStatusError):
        await bridge.invoke(token, 'joint_condition', request | {'rule': 'unbounded-meaning'})
    with pytest.raises(PermissionError):
        await bridge.invoke(token, 'record', {})


def test_all_conditions_remain_discoverable_after_all_members_are_revoked(setup):
    kernel, project, records, request, client = setup
    for number in range(21):
        kernel.create_joint_condition(project.id, request | {'title': f'condition {number}'})
    path = f'/api/v1/projects/{project.id}/local-map'
    selected = client.post(path, json={'record_id': records[2].id, 'limit': 50}).json()
    assert len(selected['joint_conditions']) == 21
    for record in records:
        kernel.remove_record(project.id, record.id)
    result = client.post(path, json={'limit': 50}).json()
    assert result['records'] == []
    assert len(result['joint_conditions']) == 21
    assert all(len(c['unavailable_ids']) == 3 for c in result['joint_conditions'])
    assert result['artifacts'][0]['id'] == request['evidence'][0]['artifact_id']
    searched = client.post(path, json={'text': 'condition 20', 'limit': 1}).json()
    assert len(searched['joint_conditions']) == 1


def test_withdrawal_preserves_members_and_history(setup):
    kernel, project, records, request, client = setup
    condition = kernel.create_joint_condition(project.id, request)
    path = f'/api/v1/projects/{project.id}/joint-conditions/{condition["id"]}'
    assert client.delete(path).status_code == 204
    assert client.delete(path).status_code == 204
    assert kernel.list_joint_conditions(project.id) == []
    assert {r.id for r in kernel.list_records(project.id)} == {r.id for r in records}
    history = kernel.history(project.id)[0]
    assert history['object_id'] == condition['id']
    assert history['object']['content']['title'] == request['title']
    assert client.post(path.rsplit('/', 1)[0], json=request).status_code == 422
    other = kernel.create_project('foreign withdrawal', 'isolation')
    assert client.delete(f'/api/v1/projects/{other.id}/joint-conditions/{condition["id"]}').status_code == 403
