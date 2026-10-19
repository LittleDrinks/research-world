import copy

import httpx
import pytest
from fastapi.testclient import TestClient

from server.agent_profiles import AgentProfiles, default_profile
from test_pi_product import setup


def test_deleted_profile_stays_deleted_after_reload_and_default_is_protected(tmp_path):
    app, _, _ = setup(tmp_path)
    client = TestClient(app)
    value = default_profile('test/model') | {'id': 'custom', 'name': 'Custom'}
    assert client.put('/api/v1/agents/custom', json=value).status_code == 200
    assert client.delete('/api/v1/agents/custom').status_code == 204
    assert [a['id'] for a in client.get('/api/v1/agents').json()] == ['research-assistant']
    assert AgentProfiles(tmp_path/'profiles').list('test/model')[0]['id'] == 'research-assistant'
    assert client.delete('/api/v1/agents/custom').status_code == 404
    assert client.delete('/api/v1/agents/research-assistant').status_code == 400


@pytest.mark.parametrize('identifier', ['../other', '/tmp/other', '..', 'bad.name', 'a'*65])
def test_delete_rejects_invalid_identifiers_without_touching_files(tmp_path, identifier):
    profiles = AgentProfiles(tmp_path/'profiles')
    sentinel = tmp_path/'other.json'
    sentinel.write_text('keep')
    with pytest.raises(ValueError):
        profiles.delete(identifier)
    assert sentinel.read_text() == 'keep'


@pytest.mark.asyncio
async def test_deleting_profile_keeps_existing_session_snapshot_and_messages(tmp_path, monkeypatch):
    monkeypatch.setattr("server.session_control.schedule_title", lambda *args: None)
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Deletion', 'Preserve existing research')
    root = f'/api/v1/projects/{project.id}/sessions'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://test') as client:
        profile = default_profile('test/model') | {'id': 'custom', 'name': 'Custom'}
        await client.put('/api/v1/agents/custom', json=profile)
        first = await client.post(root, json={'agent_id': 'custom', 'content': 'first', 'message_id': 'm1'})
        sid = first.json()['session']['id'];snapshot = copy.deepcopy(runtime.runs[sid]['agent_snapshot'])
        assert (await client.delete('/api/v1/agents/custom')).status_code == 204
        detail = (await client.get(root+'/'+sid)).json()
        assert detail['run']['agent_snapshot']['instructions'] == snapshot['instructions']
        assert (await client.post(root+'/'+sid+'/messages', json={'content': 'continue', 'message_id': 'm2'})).status_code == 202
        assert runtime.runs[sid]['agent_snapshot'] == snapshot
        assert (await client.post(root, json={'agent_id': 'custom', 'content': 'new', 'message_id': 'm3'})).status_code == 404
