"""Read immutable documents and derive Markdown without a second stored copy."""
from dataclasses import asdict
from pathlib import PurePosixPath
from urllib.parse import quote

from .artifact_documents import DOCUMENT_TYPE, MAX_BYTES, parse, reading_chars

RESULTS = {'pass': '通过', 'partial': '部分满足', 'fail': '失败', 'unverified': '未能验证', 'not_applicable': '不适用'}
VERDICTS = {'pass': '通过', 'revise': '需修订', 'inconclusive': '待补证'}


def view_url(project_id, artifact_id):
    return f'/projects/{quote(project_id, safe="")}/artifacts/{quote(artifact_id, safe="")}'


def reading(kernel, project_id, artifact_id):
    artifact = kernel.get_artifact(project_id, artifact_id)
    value = {'artifact': asdict(artifact), 'kind': 'download'}
    if artifact.size > MAX_BYTES:
        return value
    content = kernel.read_artifact(project_id, artifact_id)
    if artifact.media_type == DOCUMENT_TYPE:
        document = parse(content)
        schema = parse(kernel.read_artifact(project_id, document['schema_id']))
        return value | document | {'kind': 'document', 'schema': schema, 'reading_chars': reading_chars(document['data']),
                                    'target': target_record(kernel, project_id, document['record_id'])}
    return text_reading(kernel, project_id, artifact, content, value)


def text_reading(kernel, project_id, artifact, content, value):
    media_type = artifact.media_type.split(';')[0].strip().lower()
    if media_type not in {'text/markdown', 'text/plain', 'application/json', 'application/schema+json'}:
        return value
    names = attachment_names(kernel, project_id, artifact.id)
    markdown_file = bool(names) and all(PurePosixPath(name).suffix.lower() in {'.md', '.markdown'} for name in names)
    kind = 'markdown' if media_type == 'text/markdown' or media_type == 'text/plain' and markdown_file else 'text'
    return value | {'kind': kind, 'name': names[0] if names else None, 'text': content.decode('utf-8')}


def attachment_names(kernel, project_id, artifact_id):
    names = set()
    for record in kernel.list_records(project_id):
        attachments = record.content.get('attachments')
        if artifact_id not in record.artifact_ids or not isinstance(attachments, list):
            continue
        for item in attachments:
            if not isinstance(item, dict) or item.get('id') != artifact_id:
                continue
            name = item.get('name')
            if isinstance(name, str) and name.strip():
                names.add(PurePosixPath(name).name)
    return sorted(names)


def target_record(kernel, project_id, record_id):
    try:
        return asdict(kernel.get_record(project_id, record_id))
    except KeyError:
        return None


def markdown(document, project_id):
    data = document['data']
    lines = [f"# {data['title']}", data['summary']]
    for section in data['sections']:
        lines.extend([f"## {section['title']}", section['markdown'], evidence_markdown(section['evidence'], project_id)])
        for check in section.get('checks', []):
            lines.extend([f"### {check['label']} · {check['action']} · {RESULTS[check['result']]}", check['reason'],
                          evidence_markdown(check['evidence'], project_id)])
    lines.extend([f"## 结论 · {VERDICTS[data['conclusion']['verdict']]}", data['conclusion']['markdown'],
                  f"模板版本：{document['schema_id']}", f"被审产物：{data['target_artifact_id']}"])
    return '\n\n'.join(filter(None, lines)) + '\n'


def evidence_markdown(evidence, project_id):
    return '\n'.join(f"- [{ref['artifact_id']}]({view_url(project_id, ref['artifact_id'])}) — {ref['locator']}" for ref in evidence)
