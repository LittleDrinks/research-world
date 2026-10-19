import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator

from .change_store import ChangeConflict, append, root_record, snapshot
from .node_language import validate_node_language

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ChangeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['revise', 'comment', 'labels', 'status']
    base_revision: Annotated[StrictInt, Field(ge=1)]
    reason: Text
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)] | None = None
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)] | None = None
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)] | None = None
    reference_revision: Annotated[StrictInt, Field(ge=1)] | None = None
    label_ids: Annotated[list[Identifier], Field(max_length=20)] | None = None

    status: Literal['open', 'closed'] | None = None
    close_reason: Literal['completed', 'not_planned', 'duplicate'] | None = None
    duplicate_of: Identifier | None = None

    @model_validator(mode='after')
    def shape(self):
        fields = {'title': self.title, 'text': self.text, 'comment': self.comment, 'label_ids': self.label_ids, 'reference_revision': self.reference_revision}
        if self.kind == 'status':
            return validate_status_request(self, fields)
        if any(value is not None for value in (self.status, self.close_reason, self.duplicate_of)):
            raise ValueError('状态字段只适用于状态变更')
        required = {'revise': {'title', 'text'}, 'comment': {'comment', 'reference_revision'}, 'labels': {'label_ids'}}[self.kind]
        if {key for key, value in fields.items() if value is not None} != required:
            raise ValueError('变更字段与类型不匹配')
        if self.label_ids is not None and len(set(self.label_ids)) != len(self.label_ids):
            raise ValueError('标签不能重复')
        if self.kind == 'revise':
            validate_node_language({'title': self.title, 'text': self.text})
        return self


def submit_change(connection, project_id, record_id, values, author):
    request = ChangeRequest.model_validate(values)
    row = root_record(connection, project_id, record_id)
    before = snapshot(connection, row)
    if before['revision'] != request.base_revision:
        raise ChangeConflict(f"记录已更新至 r{before['revision']}；请核对最新版本后提交，草稿已保留")
    after = json.loads(json.dumps(before))
    if request.kind == 'revise':
        after['content'].update(title=request.title, text=request.text)
    if request.kind == 'status':
        apply_status(connection, project_id, record_id, request, after)
    if request.kind == 'labels':
        after['labels'] = selected_labels(connection, project_id, request.label_ids)
    if request.reference_revision:
        snapshot(connection, row, request.reference_revision)
    if request.kind != 'comment' and before == after:
        raise ValueError('没有需要保存的变更')
    return append(connection, row, before, after, request.kind, author, request.reason, request.comment or '', request.reference_revision)


def selected_labels(connection, project_id, identifiers):
    values = []
    for identifier in identifiers:
        row = connection.execute('SELECT id,name,color,description FROM research_labels WHERE id=? AND project_id=?',
                                 (identifier, project_id)).fetchone()
        if row is None:
            raise ValueError('标签不存在或不属于当前项目')
        values.append(dict(row))
    return values


def attach(connection, project_id, record_id, artifact_id):
    row = root_record(connection, project_id, record_id)
    before = snapshot(connection, row)
    if artifact_id in before['artifact_ids']:
        return
    after = {**before, 'artifact_ids': [*before['artifact_ids'], artifact_id]}
    append(connection, row, before, after, 'attachment', 'system', '保存并关联不可变研究产物')


def validate_status_request(request, fields):
    if any(value is not None for value in fields.values()) or request.status is None:
        raise ValueError('状态变更字段无效')
    if (request.status == 'closed') != (request.close_reason is not None):
        raise ValueError('关闭需要原因；重新打开不能包含关闭原因')
    if (request.close_reason == 'duplicate') != (request.duplicate_of is not None):
        raise ValueError('重复关闭需要指定保留的研究对象')
    return request


def apply_status(connection, project_id, record_id, request, after):
    if request.duplicate_of:
        target = root_record(connection, project_id, request.duplicate_of)
        if target['id'] == record_id:
            raise ValueError('不能将自身标为重复对象')
    if after['content'].get('status', 'open') == request.status:
        raise ValueError('节点已经处于该状态')
    after['content']['status'] = request.status
    for key in ('close_reason', 'duplicate_of'):
        after['content'].pop(key, None)
        if getattr(request, key) is not None:
            after['content'][key] = getattr(request, key)
