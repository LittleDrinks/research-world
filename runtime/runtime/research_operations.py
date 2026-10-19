"""Project-bound research record operations shared with the product HTTP API."""
import re


def identifier(value, prefix):
    if not isinstance(value, str) or not re.fullmatch(prefix + r':[0-9a-f]{24}', value):
        raise ValueError('研究对象或标签标识无效')
    return value


def operation(values):
    action = values.get('operation')
    if not isinstance(action, str):
        raise ValueError('需要研究操作名称')
    if action == 'preflight':
        require_fields(values, {'operation', 'type', 'content'})
        return 'POST', '/records/preflight', {k:v for k,v in values.items() if k != 'operation'}
    if action == 'labels':
        require_fields(values, {'operation'})
        return 'GET', '/labels', None
    if action in {'read', 'history'}:
        return read_operation(values, action)
    if action.startswith('label_'):
        return label_operation(values, action)
    if action == 'submit':
        record = identifier(values['record_id'], 'record')
        return 'POST', f'/records/{record}/changes', {k: v for k, v in values.items() if k not in {'operation', 'record_id'}}
    raise ValueError('研究操作无效')


def require_fields(values, allowed):
    if set(values) - allowed:
        raise ValueError('操作包含未知字段')


def read_operation(values, action):
    require_fields(values, {'operation', 'record_id', 'revision'} if action == 'read' else {'operation', 'record_id'})
    record = identifier(values['record_id'], 'record') if 'record_id' in values else None
    if action == 'history':
        return 'GET', '/changes' + (f'?record_id={record}' if record else ''), None
    if record is None:
        raise ValueError('读取需要record_id')
    revision = values.get('revision')
    if revision is not None and (isinstance(revision, bool) or not isinstance(revision, int) or revision < 1):
        raise ValueError('版本必须是正整数')
    return 'GET', f'/records/{record}' + (f'/revisions/{revision}' if revision is not None else ''), None


def label_operation(values, action):
    if action == 'label_create':
        return 'POST', '/labels', {k: v for k, v in values.items() if k != 'operation'}
    label = identifier(values['label_id'], 'label')
    if action == 'label_delete':
        require_fields(values, {'operation', 'label_id'})
        return 'DELETE', f'/labels/{label}', None
    if action == 'label_update':
        return 'PUT', f'/labels/{label}', {k: v for k, v in values.items() if k not in {'operation', 'label_id'}}
    raise ValueError('标签操作无效')
