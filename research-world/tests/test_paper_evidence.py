import json
from fastapi.testclient import TestClient
from server.agent_profiles import AgentProfiles
from server.app import create_product


def test_page_evidence_artifact_round_trips_through_source_and_graph(graph_kernel, tmp_path):
    app = create_product(graph_kernel, object(), AgentProfiles(tmp_path / 'agents'), tmp_path / 'projects')
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'Paper review', 'question': 'When does A hold?'}).json()
    root = f"/api/v1/projects/{project['id']}"
    evidence = {'source_sha256': 'a' * 64, 'page': 2, 'quote': 'A holds only if B.', 'limitations': 'B required'}
    artifact = client.post(root + '/artifacts', json={'content': json.dumps(evidence), 'media_type': 'application/json'})
    assert artifact.status_code == 201
    source = client.post(root + '/records', json={'type': 'source', 'content': {'canonical_url': 'https://example.org/paper', 'title': 'Paper', 'text': 'Conditional A'},
                                                'artifact_ids': [artifact.json()['id']]}).json()
    direction = client.post(root + '/records', json={'type': 'direction', 'content': {'title': 'Conditional A', 'text': 'Requires B'}}).json()
    relation = client.post(root + '/relations', json={'source_id': source['id'], 'target_id': direction['id'], 'type': 'supports'})
    assert relation.status_code == 201
    assert client.get(root + '/artifacts/' + source['artifact_ids'][0]).json() == evidence
    graph = client.post(root + '/local-map', json={'record_id': source['id']}).json()
    assert relation.json() in graph['relations']
    assert artifact.json()['id'] in [item['id'] for item in graph['artifacts']]
