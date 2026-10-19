import secrets
import sqlite3
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from .change_store import ChangeConflict, append, snapshot


class LabelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    color: Annotated[str, StringConstraints(pattern=r'^#[0-9a-fA-F]{6}$')]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = ''


def labels(connection, project_id):
    rows = connection.execute('SELECT id,name,color,description FROM research_labels WHERE project_id=? ORDER BY name_key,id', (project_id,)).fetchall()
    return [dict(row) for row in rows]


def save_label(connection, project_id, values, identifier=None, author='user'):
    value = LabelRequest.model_validate(values).model_dump()
    value['color'] = value['color'].lower()
    if identifier:
        require_label(connection, project_id, identifier)
    result = {'id': identifier or 'label:' + secrets.token_hex(12), **value}
    params = (project_id, value['name'], value['name'].casefold(), value['color'].lower(), value['description'], result['id'])
    try:
        if identifier:
            connection.execute('UPDATE research_labels SET project_id=?,name=?,name_key=?,color=?,description=? WHERE id=?', params)
        else:
            connection.execute('INSERT INTO research_labels(project_id,name,name_key,color,description,id) VALUES(?,?,?,?,?,?)', params)
    except sqlite3.IntegrityError:
        raise ChangeConflict('当前项目已有同名标签') from None
    if identifier:
        update_assigned(connection, project_id, identifier, result, author)
    return result


def require_label(connection, project_id, identifier):
    row = connection.execute('SELECT id FROM research_labels WHERE id=? AND project_id=?', (identifier, project_id)).fetchone()
    if row is None:
        raise KeyError(identifier)


def delete_label(connection, project_id, identifier, author='user'):
    require_label(connection, project_id, identifier)
    update_assigned(connection, project_id, identifier, None, author)
    connection.execute('DELETE FROM research_labels WHERE id=? AND project_id=?', (identifier, project_id))


def update_assigned(connection, project_id, identifier, replacement, author):
    rows = connection.execute('SELECT * FROM kernel_records WHERE project_id=?', (project_id,)).fetchall()
    for row in rows:
        before = snapshot(connection, row)
        if not any(label['id'] == identifier for label in before['labels']):
            continue
        updated = [replacement if label['id'] == identifier else label for label in before['labels']]
        after = {**before, 'labels': [label for label in updated if label is not None]}
        if after != before:
            reason = '更新项目标签定义' if replacement else '删除项目标签并移除关联'
            append(connection, row, before, after, 'labels', author, reason)
