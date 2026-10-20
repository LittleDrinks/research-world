from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.kernel_http import kernel_graph_router


def scoped_project(kernel):
    project = kernel.create_project('Orbit research', 'What changes an orbit?')
    artifact = kernel.capture_artifact(project.id, b'calculation', 'text/plain')
    a = kernel.record(project.id, 'direction', {'text': 'radiation'}, (artifact.id,))
    b = kernel.record(project.id, 'experiment', {'text': 'integration'})
    kernel.connect(project.id, b.id, a.id, 'supports')
    other = kernel.create_project('Other research', 'Other question')
    kernel.record(other.id, 'question', {'text': 'unrelated'})
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))
    return project.id, TestClient(app)


def test_no_keyword_matches_does_not_report_empty_project(graph_kernel):
    project, client = scoped_project(graph_kernel)
    result = client.post(f'/api/v1/projects/{project}/local-map', json={
        'text': '当前研究项目所有对象与关系', 'limit': 30}).json()
    assert result['records'] == []
    assert result['project_summary'] == {'project_id': project, 'records': 2,
        'records_by_type': {'direction': 1, 'experiment': 1},
        'relations': 1, 'joint_conditions': 0, 'artifacts': 1}
    assert result['selection']['matched_records'] == 0
    assert result['selection']['mode'] == 'search'
    assert result['selection']['truncated'] is False


def test_overview_discloses_truncation_and_reads_all_matches(graph_kernel):
    project, client = scoped_project(graph_kernel)
    route = f'/api/v1/projects/{project}/local-map'
    first = client.post(route, json={'limit': 1}).json()
    assert first['selection']['matched_records'] == 2
    assert first['selection']['returned_records'] == 1
    assert first['selection']['truncated'] is True
    complete = client.post(route, json={'limit': first['selection']['matched_records']}).json()
    assert len(complete['records']) == 2
    assert complete['selection']['mode'] == 'overview'
    assert complete['selection']['truncated'] is False


def test_actual_empty_project_has_zero_totals(graph_kernel):
    project, client = scoped_project(graph_kernel)
    empty = graph_kernel.create_project('Empty', 'What next?')
    result = client.post(f'/api/v1/projects/{empty.id}/local-map', json={}).json()
    assert result['project_summary']['records'] == 0
    assert result['project_summary']['artifacts'] == 0
    assert result['selection']['mode'] == 'overview'
    assert result['selection']['truncated'] is False
