"""Joint conditions are relations over existing records, never scientific verdicts."""
import json
import secrets
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator

from .artifacts import now
from .node_language import validate_node_language

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

SCHEMA = """
CREATE TABLE IF NOT EXISTS kernel_joint_conditions(
 id TEXT PRIMARY KEY,
 project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
 content TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(project_id, content)
);
"""


class Member(BaseModel):
    model_config = ConfigDict(extra='forbid')
    record_id: Label
    role: Label


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    artifact_id: Label
    locator: Text


class JointConditionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: Label
    rule: Literal['AND', 'OR', 'k-of-N']
    k: StrictInt | None = None
    members: list[Member] = Field(min_length=2, max_length=12)
    target_id: Label
    statement: Text
    rationale: Text
    evidence: list[Evidence] = Field(min_length=1, max_length=12)

    @model_validator(mode='after')
    def check_members(self):
        validate_node_language({'title': self.title, 'text': self.statement, 'note': self.rationale})
        for member in self.members:
            validate_node_language({'text': member.role})
        ids = [member.record_id for member in self.members]
        if len(set(ids)) != len(ids) or self.target_id in ids:
            raise ValueError('members must be distinct and cannot include the target')
        if self.rule == 'k-of-N':
            if self.k is None or not 1 <= self.k <= len(ids):
                raise ValueError('k must be between 1 and the member count')
        elif self.k is not None:
            raise ValueError('k is only permitted for k-of-N')
        return self


def create_condition(kernel, project_id, values):
    request = JointConditionRequest.model_validate(values)
    kernel.get_project(project_id)
    for record_id in [request.target_id, *(m.record_id for m in request.members)]:
        kernel.get_record(project_id, record_id)
    for evidence in request.evidence:
        kernel.get_artifact(project_id, evidence.artifact_id)
    return save_condition(kernel, project_id, request)


def save_condition(kernel, project_id, request):
    content = json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True)
    with kernel._connect() as connection:
        connection.execute('INSERT OR IGNORE INTO kernel_joint_conditions VALUES(?,?,?,?)',
                           (f'joint:{secrets.token_hex(12)}', project_id, content, now()))
        row = connection.execute('SELECT * FROM kernel_joint_conditions WHERE project_id=? AND content=?',
                                 (project_id, content)).fetchone()
        if connection.execute('SELECT 1 FROM kernel_revocations WHERE object_id=?', (row['id'],)).fetchone():
            raise ValueError('joint condition has been withdrawn')
    return condition_view(row, {r.id for r in kernel.list_records(project_id)})


def list_conditions(kernel, project_id):
    kernel.get_project(project_id)
    active = {r.id for r in kernel.list_records(project_id)}
    with kernel._connect() as connection:
        rows = connection.execute('SELECT * FROM kernel_joint_conditions WHERE project_id=? '
                                  'AND id NOT IN (SELECT object_id FROM kernel_revocations) ORDER BY created_at,id',
                                  (project_id,)).fetchall()
    return [condition_view(row, active) for row in rows]


def condition_view(row, active):
    content = json.loads(row['content'])
    ids = referenced_ids(content)
    return {'id': row['id'], 'project_id': row['project_id'], **content,
            'created_at': row['created_at'], 'unavailable_ids': [i for i in ids if i not in active]}


def referenced_ids(condition):
    return [condition['target_id'], *(m['record_id'] for m in condition['members'])]


def matches_condition(condition, ids, query):
    if query.text is None and query.record_id is None:
        return True
    return bool(ids.intersection(referenced_ids(condition)) or
                (query.text and query.text.casefold() in json.dumps(condition, ensure_ascii=False).casefold()))


def local_conditions(kernel, project_id, records, query):
    ids = {r.id for r in records}
    conditions = [c for c in list_conditions(kernel, project_id) if matches_condition(c, ids, query)]
    related = {i for c in conditions for i in referenced_ids(c)}
    records = (*records, *(r for r in kernel.list_records(project_id) if r.id in related - ids))
    return records, tuple(conditions)


def condition_artifacts(kernel, project_id, conditions, artifacts):
    existing = {a.id for a in artifacts}
    ids = {e['artifact_id'] for c in conditions for e in c['evidence']}
    return (*artifacts, *(kernel.get_artifact(project_id, i) for i in sorted(ids - existing)))


def remove_condition(kernel, project_id, condition_id):
    kernel.get_project(project_id)
    with kernel._connect() as connection:
        row = connection.execute('SELECT project_id FROM kernel_joint_conditions WHERE id=?', (condition_id,)).fetchone()
    if row is None:
        raise KeyError(condition_id)
    if row['project_id'] != project_id:
        raise PermissionError('joint condition belongs to another project')
    kernel._revoke(project_id, [condition_id], 'joint condition withdrawn')
