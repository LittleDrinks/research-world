"""Durable label bindings and review requests committed with research changes."""
import hashlib
import json

from .artifacts import now

SCHEMA = '''
CREATE TABLE IF NOT EXISTS review_rules(
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
 label_id TEXT NOT NULL REFERENCES research_labels(id) ON DELETE CASCADE,
 enabled INTEGER NOT NULL, config TEXT NOT NULL, UNIQUE(project_id,label_id)
);
CREATE TABLE IF NOT EXISTS review_tasks(
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
 record_id TEXT NOT NULL REFERENCES kernel_records(id) ON DELETE CASCADE,
 rule_id TEXT NOT NULL, input_hash TEXT NOT NULL, payload TEXT NOT NULL,
 status TEXT NOT NULL, session_id TEXT NOT NULL, run_id TEXT, turn_id TEXT,
 target_id TEXT, report_id TEXT, error TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(rule_id,record_id,input_hash)
);
'''


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def inputs(connection, record):
    outputs = connection.execute('SELECT target_id,report_id FROM review_tasks').fetchall()
    excluded = {identifier for row in outputs for identifier in row if identifier}
    return {'content': record['content'], 'artifact_ids': sorted(set(record['artifact_ids']) - excluded)}


def fingerprint(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def enqueue(connection, change):
    if change['kind'] != 'labels':
        return
    before = {label['id'] for label in change['before']['labels']}
    for label in change['after']['labels']:
        if label['id'] in before:
            continue
        rule = connection.execute('SELECT * FROM review_rules WHERE project_id=? AND label_id=? AND enabled=1',
                                  (change['project_id'], label['id'])).fetchone()
        if rule:
            insert_task(connection, rule, label, change)


def insert_task(connection, rule, label, change):
    material = inputs(connection, change['after'])
    digest = fingerprint(material)
    identifier = 'review-' + fingerprint([rule['id'], change['record_id'], digest])[:32]
    payload = {'config': json.loads(rule['config']), 'label': label, 'change_id': change['id'],
               'revision': change['revision'], 'inputs': material, 'request_author': change['author']}
    connection.execute('INSERT OR IGNORE INTO review_tasks '
                       '(id,project_id,record_id,rule_id,input_hash,payload,status,session_id,created_at,updated_at) '
                       'VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (identifier, change['project_id'], change['record_id'], rule['id'], digest,
                        encode(payload), 'queued', 's-' + identifier, now(), now()))


def task_view(row):
    value = dict(row)
    value['payload'] = json.loads(value['payload'])
    return value


class ReviewStore:
    def __init__(self, kernel):
        self.kernel = kernel

    def rules(self, project_id):
        self.kernel.get_project(project_id)
        with self.kernel._connect() as connection:
            rows = connection.execute('SELECT * FROM review_rules WHERE project_id=? ORDER BY id', (project_id,)).fetchall()
        return [dict(row) | {'config': json.loads(row['config']), 'enabled': bool(row['enabled'])} for row in rows]

    def save_rule(self, project_id, label_id, config, enabled):
        self.kernel.get_project(project_id)
        with self.kernel._connect() as connection:
            from .research_labels import require_label
            require_label(connection, project_id, label_id)
            identifier = 'rule-' + fingerprint([project_id, label_id])[:24]
            connection.execute('INSERT INTO review_rules VALUES(?,?,?,?,?) ON CONFLICT(id) '
                               'DO UPDATE SET enabled=excluded.enabled,config=excluded.config',
                               (identifier, project_id, label_id, enabled, encode(config)))
        return next(rule for rule in self.rules(project_id) if rule['id'] == identifier)

    def list_tasks(self, project_id, record_id):
        self.kernel.get_record(project_id, record_id)
        with self.kernel._connect() as connection:
            rows = connection.execute('SELECT * FROM review_tasks WHERE project_id=? AND record_id=? ORDER BY created_at',
                                      (project_id, record_id)).fetchall()
        return [task_view(row) for row in rows]

    def get(self, project_id, task_id):
        self.kernel.get_project(project_id)
        with self.kernel._connect() as connection:
            row = connection.execute('SELECT * FROM review_tasks WHERE id=? AND project_id=?', (task_id, project_id)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return task_view(row)

    def pending(self):
        with self.kernel._connect() as connection:
            rows = connection.execute("SELECT * FROM review_tasks WHERE status IN ('queued','running','cancelling') ORDER BY created_at").fetchall()
        return [task_view(row) for row in rows]

    def update(self, task_id, **values):
        allowed = {'status', 'run_id', 'turn_id', 'target_id', 'report_id', 'error', 'payload'}
        if not values or set(values) - allowed:
            raise ValueError('Invalid task update')
        values['updated_at'] = now()
        if 'payload' in values:
            values['payload'] = encode(values['payload'])
        with self.kernel._connect() as connection:
            connection.execute(f'UPDATE review_tasks SET {",".join(key + "=?" for key in values)} WHERE id=?',
                               (*values.values(), task_id))

    def report_task(self, project_id, target_id):
        with self.kernel._connect() as connection:
            row = connection.execute('SELECT * FROM review_tasks WHERE project_id=? AND target_id=?', (project_id, target_id)).fetchone()
        return task_view(row) if row else None

    def run_task(self, project_id, run_id):
        with self.kernel._connect() as connection:
            row = connection.execute('SELECT * FROM review_tasks WHERE project_id=? AND run_id=?', (project_id, run_id)).fetchone()
        return task_view(row) if row else None
