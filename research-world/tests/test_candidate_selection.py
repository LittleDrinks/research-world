import pytest
from fastapi.testclient import TestClient

from test_pi_product import setup


@pytest.fixture
def case(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('Selection', 'Sources')
    record = kernel.record(project.id, 'source', {'title': 'Paper'}, ())
    calls = []
    async def select(values):
        calls.append(values)
        return {'selected': values['candidates']}
    runtime.select_candidates = select
    return kernel, TestClient(app), project.id, record.id, calls


def test_selection_passes_only_project_owned_candidates_to_runtime(case):
    kernel, client, project, record, calls = case
    url = f'/api/v1/projects/{project}/candidate-selection'
    values = {'candidates': [{'id': record, 'relevance': 1.0}], 'count': 1}
    assert client.post(url, json=values).status_code == 200
    assert calls == [values]
    other = kernel.create_project('Other', 'Sources')
    foreign = kernel.record(other.id, 'source', {'title': 'Other paper'}, ())
    assert client.post(url, json={'candidates': [{'id': foreign.id}]}).status_code in {403, 404}
    assert len(calls) == 1


@pytest.mark.parametrize('values', [[], {}, {'candidates': [None]}, {'candidates': [{}]}, {'candidates': [{'id': []}]}])
def test_invalid_selection_never_calls_runtime(case, values):
    _, client, project, _, calls = case
    assert client.post(f'/api/v1/projects/{project}/candidate-selection', json=values).status_code == 400
    assert calls == []
