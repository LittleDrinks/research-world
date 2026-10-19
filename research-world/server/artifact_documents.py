"""Versioned document templates and bounded, project-scoped publication."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .artifacts import ArtifactStore

DOCUMENT_TYPE = 'application/vnd.research-world.document+json'
SCHEMA_TYPE = 'application/schema+json'
MAX_BYTES = 4 * 1024 * 1024


class DocumentError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('；'.join(f"{e['path']}: {e['message']}" for e in errors))


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def published_schemas():
    values = [json.loads(path.read_text()) for path in sorted(Path(__file__).with_name('artifact_schemas').glob('*.json'))]
    return {ArtifactStore.identifier(encode(value)): value for value in values}


def templates(kernel, project_id):
    result = []
    for schema_id, schema in published_schemas().items():
        kernel.capture_artifact(project_id, encode(schema), SCHEMA_TYPE)
        result.append({'id': schema_id, 'title': schema['title'], 'schema': schema,
                       'example': schema['examples'][0], 'max_reading_chars': schema['x-max-reading-chars']})
    return result


def parse(content):
    try:
        return json.loads(content, parse_constant=lambda _: invalid('$', 'JSON 不允许非有限数值'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid('$', '文件必须是有效的 UTF-8 JSON')


def invalid(path, message):
    raise DocumentError([{'path': path, 'message': message}])


def validate_capture(kernel, project_id, content, media_type):
    if media_type == SCHEMA_TYPE and ArtifactStore.identifier(content) not in published_schemas():
        invalid('schema_id', '只接受平台发布的模板，不允许通过产物改写模板约束')
    if media_type != DOCUMENT_TYPE:
        return None
    document = parse(content)
    if not isinstance(document, dict) or set(document) != {'schema_id', 'record_id', 'data'}:
        invalid('$', '结构化产物必须且只能包含 schema_id、record_id、data')
    schema = published_schemas().get(document['schema_id']) if isinstance(document['schema_id'], str) else None
    if schema is None:
        invalid('schema_id', '请选择平台已发布的模板版本')
    kernel.read_artifact(project_id, document['schema_id'])
    validate_data(document['data'], schema)
    validate_references(kernel, project_id, document)
    return document


def validate_data(data, schema):
    errors = list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise DocumentError([{'path': '.'.join(map(str, error.absolute_path)) or '$',
                              'message': error.message[:240]} for error in errors[:12]])
    actual, maximum = reading_chars(data), schema['x-max-reading-chars']
    if actual > maximum:
        invalid('$', f'阅读正文 {actual} 字符，超过总预算 {maximum}；请精简或将细节移入附件')


def reading_chars(value):
    if isinstance(value, dict):
        return sum(reading_chars(item) for key, item in value.items() if key not in {'id', 'target_artifact_id', 'evidence', 'action', 'result', 'verdict'})
    if isinstance(value, list):
        return sum(map(reading_chars, value))
    return len(value) if isinstance(value, str) else 0


def references(data):
    for section in data['sections']:
        yield from section['evidence']
        for check in section.get('checks', []):
            yield from check['evidence']


def validate_references(kernel, project_id, document):
    record_id, data = document['record_id'], document['data']
    if not isinstance(record_id, str):
        invalid('record_id', '请选择被审研究对象')
    record = kernel.get_record(project_id, record_id)
    if data['target_artifact_id'] not in record.artifact_ids:
        invalid('target_artifact_id', '被审产物必须已关联到所选研究对象')
    for identifier in {data['target_artifact_id'], *(ref['artifact_id'] for ref in references(data))}:
        kernel.read_artifact(project_id, identifier)


def prepare(kernel, project_id, content, schema_id, record_id):
    document = {'schema_id': schema_id, 'record_id': record_id, 'data': parse(content)}
    raw = encode(document)
    schema = published_schemas().get(schema_id)
    if schema is None:
        invalid('schema_id', '请选择平台已发布的模板版本')
    kernel.capture_artifact(project_id, encode(schema), SCHEMA_TYPE)
    validate_capture(kernel, project_id, raw, DOCUMENT_TYPE)
    return raw
