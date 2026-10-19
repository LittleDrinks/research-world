from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from test_pi_product import setup


@pytest.fixture
def case(tmp_path):
    app, kernel, _ = setup(tmp_path)
    project = kernel.create_project('Orbits', 'What causes orbital drift?')
    return kernel, TestClient(app), project.id, f'/api/v1/projects/{project.id}'


@pytest.mark.parametrize('word', ['演示②', '实例', '示例', 'DEMO', 'toy'])
@pytest.mark.parametrize('field', ['title', 'text', 'summary', 'note'])
def test_new_node_rejects_toy_copy_without_writing(case, word, field):
    kernel, client, project, root = case
    response = client.post(root + '/records', json={'type': 'experiment', 'content': {field: word}})
    assert response.status_code == 422
    assert f'content.{field}' in response.text
    assert kernel.list_records(project) == []


@pytest.mark.parametrize('field', ['title', 'text'])
def test_revise_rejects_toy_copy_without_new_version(case, field):
    kernel, client, project, root = case
    record = kernel.record(project, 'direction', {'title': '相对论进动', 'text': '配对比较偏心率。'})
    body = {'kind': 'revise', 'base_revision': 1, 'reason': '明确比较范围',
            'title': '相对论进动', 'text': '固定初值，比较偏心率。', field: '演示②'}
    response = client.post(root + f'/records/{record.id}/changes', json=body)
    assert response.status_code == 422
    assert kernel.get_record(project, record.id) == record
    assert kernel.list_changes(project) == []


def test_research_text_and_original_evidence_remain_readable(case):
    kernel, client, project, root = case
    content = {'title': 'Demographic model', 'text': '比较日地二体的轨道耗散时间。'}
    response = client.post(root + '/records', json={'type': 'direction', 'content': content})
    assert response.status_code == 201
    artifact = kernel.capture_artifact(project, '论文中的纠错演示'.encode(), 'text/plain')
    assert kernel.read_artifact(project, artifact.id).decode() == '论文中的纠错演示'


@pytest.mark.parametrize('field', ['title', 'statement', 'rationale', 'role'])
def test_joint_node_rejects_toy_copy(case, field):
    kernel, client, project, root = case
    records = [kernel.record(project, 'direction', {'title': f'检验条件{i}'}) for i in range(3)]
    artifact = kernel.capture_artifact(project, b'Conditions', 'text/plain')
    members = [{'record_id': r.id, 'role': '检验前提'} for r in records[:2]]
    body = {'title': '联合检验', 'rule': 'AND', 'members': members, 'target_id': records[2].id,
            'statement': '前提共同约束结论', 'rationale': '对齐输入条件',
            'evidence': [{'artifact_id': artifact.id, 'locator': 'L1'}]}
    if field == 'role': members[0]['role'] = '演示'
    else: body[field] = '演示'
    response = client.post(root + '/joint-conditions', json=body)
    assert response.status_code == 422
    assert client.get(root + '/joint-conditions').json() == []


@pytest.mark.asyncio
async def test_agent_record_uses_the_same_language_guard(case, monkeypatch):
    from runtime.bridge import ToolBridge
    import runtime.bridge as module
    kernel, client, project, _ = case
    request_type = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kw: request_type(transport=httpx.ASGITransport(app=client.app), **kw))
    monkeypatch.setenv('CONTROL_URL', 'http://test')
    bridge = ToolBridge()
    token = bridge.bind(SimpleNamespace(run_id='language', agent_snapshot={'tools': ['record'], 'project_id': project}))
    with pytest.raises(httpx.HTTPStatusError) as error:
        await bridge.invoke(token, 'record', {'type': 'experiment', 'content': {'title': '演示②'}})
    assert error.value.response.status_code == 422
    assert kernel.list_records(project) == []
