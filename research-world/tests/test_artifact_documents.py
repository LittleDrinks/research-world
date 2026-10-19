import copy
import io
import json
import zipfile
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from server.artifact_documents import DOCUMENT_TYPE, DocumentError, encode
from server.kernel_interface import create_kernel
from server.project_export import export_project
from test_pi_product import setup


@pytest.fixture
def case(tmp_path):
    app, kernel, runtime = setup(tmp_path)
    project = kernel.create_project('document', 'bounded audit')
    original = kernel.capture_artifact(project.id, b'# Original evidence', 'text/markdown')
    record = kernel.record(project.id, 'experiment', {'title': 'calculation'}, (original.id,))
    client = TestClient(app)
    root = f'/api/v1/projects/{project.id}'
    template = client.get(root + '/artifact-templates').json()[0]
    data = template['example'] | {'target_artifact_id': original.id}
    body = {'content': json.dumps(data), 'record_id': record.id, 'schema_id': template['id']}
    return kernel, runtime, client, root, record, data, body


def post(case, data=None, **patch):
    _, _, client, root, _, original, body = case
    return client.post(root + '/artifacts', json=body | {'content': json.dumps(data or original)} | patch)


def test_publication_is_immutable_idempotent_and_does_not_replace_attachments(case):
    kernel, _, client, root, record, data, _ = case
    value = post(case).json()
    assert post(case).json()['id'] == value['id']
    assert kernel.get_record(record.project_id, record.id).artifact_ids == (*record.artifact_ids, value['id'])
    reopened = create_kernel(kernel._database, kernel._artifacts)
    document = json.loads(reopened.read_artifact(record.project_id, value['id']))
    assert document['data'] == data
    assert client.get(root + f"/artifacts/{value['id']}/reading").json()['data'] == data
    assert client.get(root + f"/artifacts/{value['id']}/markdown").text.startswith('# 待填写的审计报告')
    assert value['view_url'].startswith('/projects/')


@pytest.mark.parametrize('mutation', ['extra', 'missing_section', 'too_long', 'blank_reason', 'bad_skip', 'false_pass', 'missing_evidence', 'many_checks', 'wrong_heading', 'budget'])
def test_schema_errors_have_paths_and_never_publish(case, mutation):
    kernel, _, _, _, record, original, _ = case
    data = copy.deepcopy(original)
    mutate(data, mutation)
    before = len(kernel.list_artifacts(record.project_id))
    response = post(case, data)
    assert response.status_code == 422, response.text
    assert response.json()['detail']['errors'][0]['path']
    assert kernel.get_record(record.project_id, record.id).artifact_ids == record.artifact_ids
    assert len(kernel.list_artifacts(record.project_id)) == before


def mutate(data, mutation):
    check = data['sections'][1]['checks'][0]
    if mutation == 'extra': data['score'] = 100
    if mutation == 'missing_section': data['sections'].pop()
    if mutation == 'too_long': data['summary'] = 'x' * 401
    if mutation == 'blank_reason': check['reason'] = ' \n '
    if mutation == 'bad_skip': check['action'] = 'skip'
    if mutation == 'false_pass': data['conclusion']['verdict'] = 'pass'
    if mutation == 'missing_evidence': check['result'] = 'pass'
    if mutation == 'many_checks': data['sections'][1]['checks'] *= 13
    if mutation == 'wrong_heading': data['sections'][0]['title'] = 'invented'
    if mutation == 'budget':
        for section in data['sections']: section['markdown'] = '长' * 1200
        check['reason'] = '长' * 240
        data['sections'][1]['checks'] = [check] * 10


def test_validate_only_unknown_schema_and_bad_json(case):
    kernel, _, _, _, record, _, _ = case
    before = len(kernel.list_artifacts(record.project_id))
    assert post(case, operation='validate').json() == {'valid': True}
    assert post(case, schema_id='artifact:' + 'a' * 64).status_code == 422
    assert post(case, content='{oops').status_code == 422
    assert kernel.get_record(record.project_id, record.id).artifact_ids == record.artifact_ids
    assert len(kernel.list_artifacts(record.project_id)) == before


def test_evidence_locators_count_toward_total_reading_budget(case):
    kernel, _, _, _, record, data, _ = case
    reference = {'artifact_id': record.artifact_ids[0], 'locator': '定位' * 80}
    for section in data['sections']:
        section['evidence'] = [reference] * 8
    checks = data['sections'][1]['checks']
    checks[0]['evidence'] = [reference] * 4
    data['sections'][1]['checks'] = checks * 12
    response = post(case)
    assert response.status_code == 422
    assert '5000' in response.json()['detail']['errors'][0]['message']
    assert kernel.get_record(record.project_id, record.id).artifact_ids == record.artifact_ids


def test_field_limit_errors_report_actual_limit_and_keyword_without_echoing_input(case):
    _, _, _, _, _, data, _ = case
    response = post(case, data | {'summary': '超' * 401})
    error = response.json()['detail']['errors'][0]
    assert error == {'path': 'summary', 'code': 'maxLength', 'actual': 401, 'limit': 400,
                     'message': '当前 401 字符，要求最多 400 字符'}
    response = post(case, data | {'sections': data['sections'] * 2})
    errors = response.json()['detail']['errors']
    assert any(e.get('code') == 'maxItems' and e.get('limit') == 3 for e in errors)


def test_cross_project_unattached_and_revoked_targets_are_rejected(case):
    kernel, _, _, _, record, data, _ = case
    other = kernel.create_project('foreign', 'other')
    foreign = kernel.capture_artifact(other.id, b'foreign evidence', 'text/plain')
    data['sections'][0]['evidence'] = [{'artifact_id': foreign.id, 'locator': 'page 1'}]
    assert post(case).status_code == 404
    data['sections'][0]['evidence'] = []
    data['target_artifact_id'] = foreign.id
    assert post(case).status_code == 422
    data['target_artifact_id'] = record.artifact_ids[0]
    kernel.remove_record(record.project_id, record.id)
    assert post(case).status_code == 404


def test_revocation_keeps_saved_document_readable_and_marks_target_unavailable(case):
    kernel, _, client, root, record, _, _ = case
    artifact = post(case).json()
    kernel.remove_record(record.project_id, record.id)
    view = client.get(root + f"/artifacts/{artifact['id']}/reading").json()
    assert view['target'] is None
    assert view['data']['target_artifact_id'] == record.artifact_ids[0]


def test_raw_capture_cannot_bypass_schema_and_plain_markdown_can_be_read(case):
    kernel, _, client, root, record, data, body = case
    raw = {'schema_id': body['schema_id'], 'record_id': record.id, 'data': data | {'summary': 'x' * 401}}
    with pytest.raises(DocumentError):
        kernel.capture_artifact(record.project_id, encode(raw), DOCUMENT_TYPE)
    response = client.post(root + '/artifacts', json={'content': '## 数学\n\\[x^2\\]', 'record_id': record.id})
    assert response.status_code == 201
    view = client.get(root + f"/artifacts/{response.json()['id']}/reading").json()
    assert view['kind'] == 'markdown' and '\\[x^2\\]' in view['text']


def test_workspace_publication_uses_same_contract(case):
    _, runtime, client, root, record, data, body = case
    runtime.workspace_file = AsyncMock(return_value=json.dumps(data))
    response = client.post(root + '/artifacts', json={k: v for k, v in body.items() if k != 'content'} | {'path': 'report.json'})
    assert response.status_code == 201, response.text
    runtime.workspace_file.assert_awaited_once_with(record.project_id, 'report.json')


@pytest.mark.asyncio
async def test_export_contains_document_fixed_schema_and_evidence(case):
    kernel, runtime, _, _, record, _, body = case
    artifact = post(case).json()
    archive = zipfile.ZipFile(io.BytesIO(await export_project(kernel, runtime, record.project_id)))
    for identifier in [artifact['id'], body['schema_id'], *record.artifact_ids]:
        assert 'artifacts/' + identifier.split(':')[1] in archive.namelist()


@pytest.mark.asyncio
async def test_agent_workspace_capture_reaches_real_product_validation(case, monkeypatch):
    from runtime.bridge import ToolBridge
    import runtime.bridge as module
    _, _, client, _, record, data, body = case
    request_type = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kw: request_type(transport=httpx.ASGITransport(app=client.app), **kw))
    monkeypatch.setenv('CONTROL_URL', 'http://test')
    bridge = ToolBridge(); binding = SimpleNamespace(run_id='artifact-test-run', agent_snapshot={'tools': ['artifact'], 'project_id': record.project_id})
    token = bridge.bind(binding); bridge.workspace_tools = FileWorkspace(json.dumps(data).encode())
    values = {k: v for k, v in body.items() if k != 'content'} | {'path': 'paper.json'}
    assert (await bridge.invoke(token, 'artifact', values))['view_url'].startswith('/projects/')
    bridge.workspace_tools = FileWorkspace(json.dumps(data | {'summary': 'x' * 401}).encode())
    with pytest.raises(httpx.HTTPStatusError) as caught:
        await bridge.invoke(token, 'artifact', values)
    assert caught.value.response.json()['detail']['errors'][0]['limit'] == 400


class FileWorkspace:
    def __init__(self, content):
        self.content = content

    async def execute(self, token, values):
        assert values['path'] == 'paper.json'
        yield json.dumps({'data': base64.b64encode(self.content).decode()})
        yield json.dumps({'exitCode': 0})


@pytest.mark.parametrize(('media_type', 'name', 'linked', 'expected'), [
    ('text/plain', 'v3.md', True, 'markdown'), ('text/plain; charset=utf-8', 'V3.MD', True, 'markdown'),
    ('text/plain', 'log.txt', True, 'text'), ('text/plain', 'v3.md', False, 'text'),
    ('application/json', 'v3.md', True, 'text'), ('text/markdown', 'log.txt', True, 'markdown'),
])
def test_text_reading_uses_linked_filename_without_changing_original(case, media_type, name, linked, expected):
    kernel, _, client, root, record, _, _ = case
    raw = b'# Research title\n\n**Evidence**'
    artifact = kernel.capture_artifact(record.project_id, raw, media_type)
    content = {'title': 'named evidence', 'attachments': [{'id': artifact.id, 'name': name}]}
    kernel.record(record.project_id, 'source', content, (artifact.id,) if linked else ())
    view = client.get(root + f'/artifacts/{artifact.id}/reading').json()
    assert view['kind'] == expected
    assert view['text'].encode() == raw and view['artifact']['media_type'] == media_type
    assert client.get(root + f'/artifacts/{artifact.id}?download=true').content == raw


def test_unrelated_project_filename_cannot_change_reading_mode(case):
    kernel, _, client, root, record, _, _ = case
    raw = b'# Literal text'
    artifact = kernel.capture_artifact(record.project_id, raw, 'text/plain')
    other = kernel.create_project('other-names', 'other')
    other_artifact = kernel.capture_artifact(other.id, raw, 'text/plain')
    kernel.record(other.id, 'source', {'attachments': [{'id': other_artifact.id, 'name': 'paper.md'}]}, (other_artifact.id,))
    assert client.get(root + f'/artifacts/{artifact.id}/reading').json()['kind'] == 'text'


def test_conflicting_attachment_formats_keep_plain_text_and_ignore_malformed_metadata(case):
    kernel, _, client, root, record, _, _ = case
    artifact = kernel.capture_artifact(record.project_id, b'# Ambiguous content', 'text/plain')
    for name in ['report.md', 'report.py']:
        kernel.record(record.project_id, 'source', {'attachments': [{'id': artifact.id, 'name': name}]}, (artifact.id,))
    kernel.record(record.project_id, 'source', {'attachments': [None, {'id': artifact.id, 'name': 4}]}, (artifact.id,))
    view = client.get(root + f'/artifacts/{artifact.id}/reading').json()
    assert view['kind'] == 'text'


def test_image_and_code_results_are_readable_without_a_manual_upload_ui(case):
    import io
    from PIL import Image
    _, _, client, root, _, _, _ = case
    buffer=io.BytesIO();Image.new('RGB',(4,4),'blue').save(buffer,format='PNG')
    result=client.post(root+'/artifacts',json={'content_base64':base64.b64encode(buffer.getvalue()).decode(),'media_type':'image/png'})
    assert result.status_code==201
    assert client.get(root+'/artifacts/'+result.json()['id']+'/reading').json()['kind']=='image'
    assert client.get(root+'/artifacts/'+result.json()['id']).content==buffer.getvalue()
    code=client.post(root+'/artifacts',json={'content':'print(42)','media_type':'text/x-python'}).json()
    assert client.get(root+'/artifacts/'+code['id']+'/reading').json()['text']=='print(42)'
