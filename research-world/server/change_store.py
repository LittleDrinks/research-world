"""Append-only research changes and immutable record snapshots."""
import json
import secrets

from .artifacts import now
from .review_store import enqueue

SCHEMA = '''
CREATE TABLE IF NOT EXISTS research_labels(
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
 name TEXT NOT NULL, name_key TEXT NOT NULL, color TEXT NOT NULL, description TEXT NOT NULL,
 UNIQUE(project_id,name_key)
);
CREATE TABLE IF NOT EXISTS research_changes(
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
 record_id TEXT NOT NULL REFERENCES kernel_records(id) ON DELETE CASCADE,
 revision INTEGER NOT NULL, kind TEXT NOT NULL, author TEXT NOT NULL, reason TEXT NOT NULL,
 comment TEXT NOT NULL, reference_revision INTEGER, before_json TEXT NOT NULL, after_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(record_id,revision)
);
CREATE INDEX IF NOT EXISTS research_changes_project ON research_changes(project_id,created_at);
'''


class ChangeConflict(ValueError):
    pass


def root_record(connection, project_id, record_id, active=True):
    row = connection.execute('SELECT * FROM kernel_records WHERE id=?', (record_id,)).fetchone()
    if row is None:
        raise KeyError(record_id)
    if row['project_id'] != project_id:
        raise PermissionError('record belongs to another project')
    if active and connection.execute('SELECT 1 FROM kernel_revocations WHERE object_id=?', (record_id,)).fetchone():
        raise KeyError(record_id)
    return row


def snapshot(connection, row, revision=None):
    query = 'SELECT after_json FROM research_changes WHERE record_id=?'
    params = (row['id'],) if revision is None else (row['id'], revision)
    query += ' ORDER BY revision DESC LIMIT 1' if revision is None else ' AND revision=?'
    saved = connection.execute(query, params).fetchone()
    if saved:
        return json.loads(saved['after_json'])
    if revision not in (None, 1):
        raise KeyError(f'revision:{revision}')
    return {'content': json.loads(row['content']), 'artifact_ids': json.loads(row['artifact_ids']), 'labels': [], 'revision': 1}


def append(connection, row, before, after, kind, author, reason, comment='', reference_revision=None):
    value = {'id': 'change:' + secrets.token_hex(12), 'project_id': row['project_id'], 'record_id': row['id'],
             'revision': before['revision'] + 1, 'kind': kind, 'author': author, 'reason': reason,
             'comment': comment, 'reference_revision': reference_revision, 'before': before, 'after': {**after, 'revision': before['revision'] + 1}, 'created_at': now()}
    connection.execute('INSERT INTO research_changes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                       tuple(value[k] for k in ('id', 'project_id', 'record_id', 'revision', 'kind', 'author', 'reason', 'comment', 'reference_revision')) +
                       (json.dumps(value['before'], ensure_ascii=False), json.dumps(value['after'], ensure_ascii=False), value['created_at']))
    enqueue(connection, value)
    return value


def history(connection, project_id, record_id=None):
    query, params = 'SELECT * FROM research_changes WHERE project_id=?', (project_id,)
    if record_id:
        root_record(connection, project_id, record_id, active=False)
        query, params = query + ' AND record_id=?', (*params, record_id)
    rows = connection.execute(query + ' ORDER BY created_at,record_id,revision', params).fetchall()
    return [change_view(row) for row in rows]


def change_view(row):
    value = dict(row)
    value['before'] = json.loads(value.pop('before_json'))
    value['after'] = json.loads(value.pop('after_json'))
    return value
