import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from server.kernel_interface import create_kernel
from server.project_export import export_project
from test_pi_product import setup


@pytest.fixture
def case(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Changes', 'Several research questions')
    artifact = kernel.capture_artifact(project.id, b'Original source', 'text/plain')
    record = kernel.record(project.id, 'direction', {'title': 'v1', 'text': 'Initial', 'doi': 'preserved'}, (artifact.id,))
    return kernel, runtime, TestClient(app), project.id, record


def root(case):
    return f'/api/v1/projects/{case[3]}'


def change(case, body):
    return case[2].post(root(case) + f'/records/{case[4].id}/changes', json=body)


def revise(revision=1, text='Revised'):
    return {'kind': 'revise', 'base_revision': revision, 'reason': 'Scope corrected', 'title': 'v2', 'text': text}


def label(case, name='warning'):
    response = case[2].post(root(case) + '/labels', json={'name': name, 'color': '#aa6600', 'description': 'A user-defined concern'})
    assert response.status_code == 201, response.text
    return response.json()


def test_revision_comment_snapshots_and_reopen(case):
    kernel, _, client, project, record = case
    assert change(case, revise()).status_code == 201
    body = {'kind': 'comment', 'base_revision': 2, 'reference_revision': 1, 'reason': 'Question', 'comment': 'Why was v1 too broad?'}
    assert change(case, body).status_code == 201
    current = kernel.get_record(project, record.id)
    assert current.revision == 3 and current.content == {'title': 'v2', 'text': 'Revised', 'doi': 'preserved'}
    assert current.artifact_ids == record.artifact_ids
    initial = client.get(root(case) + f'/records/{record.id}/revisions/1').json()
    assert initial['content']['text'] == 'Initial'
    reopened = create_kernel(kernel._database, kernel._artifacts)
    assert reopened.get_record(project, record.id) == current
    history = reopened.list_changes(project, record.id)
    assert history[1]['reference_revision'] == 1 and history[1]['after']['content']['text'] == 'Revised'


def test_labels_can_coexist_rename_and_delete_without_rewriting_history(case):
    kernel, _, client, project, record = case
    first, second = label(case), label(case, 'need-grill')
    body = {'kind': 'labels', 'base_revision': 1, 'reason': 'Independent concerns', 'label_ids': [first['id'], second['id']]}
    assert change(case, body).status_code == 201
    assert client.put(root(case) + '/labels/' + first['id'], json={'name': '需核查', 'color': '#0055AA', 'description': 'clarified'}).status_code == 200
    assert kernel.get_record(project, record.id).labels[0]['name'] == '需核查'
    assert kernel.record_revision(project, record.id, 2).labels[0]['name'] == 'warning'
    assert client.delete(root(case) + '/labels/' + first['id']).status_code == 204
    assert [l['name'] for l in kernel.get_record(project, record.id).labels] == ['need-grill']
    assert kernel.record_revision(project, record.id, 3).labels[0]['name'] == '需核查'
    assert len(kernel.list_changes(project, record.id)) == 3


@pytest.mark.parametrize('body', [
    {'name': ' ', 'color': '#111111'}, {'name': 'x', 'color': 'red'},
    {'name': 'x', 'color': '#112233', 'description': 'x' * 301}, {'name': 'x' * 41, 'color': '#112233'},
    {'name': 'x', 'color': '#112233', 'state': 'passed'},
])
def test_invalid_label_contract(case, body):
    assert case[2].post(root(case) + '/labels', json=body).status_code == 422
    assert case[0].list_labels(case[3]) == []


def test_duplicate_labels_and_cross_project_isolation(case):
    kernel, _, client, _, record = case
    first = label(case)
    assert client.post(root(case) + '/labels', json={'name': 'WARNING', 'color': '#112233'}).status_code == 409
    other = kernel.create_project('other', 'other')
    other_label = kernel.save_label(other.id, {'name': 'warning', 'color': '#112233'})
    assert client.put(root(case) + '/labels/' + other_label['id'], json={'name': 'changed', 'color': '#112233'}).status_code == 404
    assert client.delete(root(case) + '/labels/' + other_label['id']).status_code == 404
    assert change(case, {'kind': 'labels', 'base_revision': 1, 'reason': 'invalid', 'label_ids': [first['id'], other_label['id']]}).status_code == 422
    assert kernel.list_changes(case[3]) == []
    assert client.get(f'/api/v1/projects/{other.id}/records/{record.id}/revisions/1').status_code == 404


def test_conflicting_updates_are_atomic_and_drafts_not_silently_overwritten(case):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda text: change(case, revise(text=text)), ['first', 'second']))
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert len(case[0].list_changes(case[3])) == 1
    assert case[0].get_record(case[3], case[4].id).revision == 2


@pytest.mark.parametrize('patch', [
    {'kind': 'pass'}, {'base_revision': True}, {'base_revision': 0}, {'reason': '  '},
    {'label_ids': []}, {'text': 'x' * 20001}, {'title': ''}, {'author': 'invented'},
])
def test_invalid_change_is_rejected_without_partial_write(case, patch):
    assert change(case, revise() | patch).status_code == 422
    assert case[0].list_changes(case[3]) == []
    assert case[0].get_record(case[3], case[4].id) == case[4]


def test_attachment_addition_is_versioned_idempotent_and_preserves_other_fields(case):
    kernel, _, _, project, record = case
    first = label(case)
    change(case, {'kind': 'labels', 'base_revision': 1, 'reason': 'flag', 'label_ids': [first['id']]})
    artifact = kernel.capture_artifact(project, b'new evidence', 'text/plain')
    for _ in range(2): kernel.attach_artifact(project, record.id, artifact.id)
    current = kernel.get_record(project, record.id)
    assert current.revision == 3 and current.artifact_ids == (*record.artifact_ids, artifact.id)
    assert current.labels[0]['id'] == first['id'] and current.content == record.content
    assert kernel.record_revision(project, record.id, 2).artifact_ids == record.artifact_ids


@pytest.mark.asyncio
async def test_export_and_revocation_preserve_history(case):
    kernel, runtime, client, project, record = case
    change(case, revise())
    kernel.remove_record(project, record.id)
    assert change(case, revise(2)).status_code == 404
    assert client.get(root(case) + f'/records/{record.id}/revisions/1').status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(await export_project(kernel, runtime, project)))
    snapshot = json.loads(archive.read('project.json'))
    assert snapshot['changes'][0]['before']['content']['text'] == 'Initial'
    assert snapshot['changes'][0]['after']['content']['text'] == 'Revised'
    kernel.delete_project(project)
    with kernel._connect() as connection:
        assert connection.execute('SELECT COUNT(*) FROM research_changes').fetchone()[0] == 0


@pytest.mark.asyncio
async def test_agent_change_uses_bound_project_and_real_validation(case, monkeypatch):
    from runtime.bridge import ToolBridge
    import runtime.bridge as module
    kernel, _, client, project, record = case
    first = label(case)
    original = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kw: original(transport=httpx.ASGITransport(app=client.app), **kw))
    monkeypatch.setenv('CONTROL_URL', 'http://test')
    bridge = ToolBridge();token = bridge.bind(SimpleNamespace(run_id='test-run', agent_snapshot={'project_id': project, 'tools': ['change']}))
    assert (await bridge.invoke(token, 'change', {'operation': 'labels'}))[0]['id'] == first['id']
    value = await bridge.invoke(token, 'change', {'operation': 'submit', 'record_id': record.id, **revise()})
    assert value['author'] == 'agent:test-run'
    with pytest.raises(httpx.HTTPStatusError):
        await bridge.invoke(token, 'change', {'operation': 'submit', 'record_id': record.id, **revise()})
    assert kernel.get_record(project, record.id).revision == 2
