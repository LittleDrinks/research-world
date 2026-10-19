import json

from .artifact_documents import DOCUMENT_TYPE, validate_capture
from .artifact_reading import view_url
from .artifacts import now
from .change_store import append, root_record, snapshot
from .review_store import fingerprint, inputs


def check_report(store, project_id, raw, author):
    document = json.loads(raw)
    task = store.run_task(project_id, author.removeprefix('agent:')) if author.startswith('agent:') else None
    task = task or store.report_task(project_id, document['data']['target_artifact_id'])
    if task is None:
        return None
    if task['status'] != 'running' or not task['run_id'] or author != 'agent:' + task['run_id']:
        raise ValueError('此复核报告只能由任务绑定的运行提交')
    if (document['record_id'] != task['record_id'] or document['schema_id'] != task['payload']['config']['schema_id']
            or document['data']['target_artifact_id'] != task['target_id']):
        raise ValueError('报告的对象或模板与复核任务不符')
    return task


def completed_report(kernel, task):
    if not task['report_id']:
        raise ValueError('Agent 已结束，但没有提交匹配本次输入的结构化报告；请求标签保留')
    raw = kernel.read_artifact(task['project_id'], task['report_id'])
    document = validate_capture(kernel, task['project_id'], raw, DOCUMENT_TYPE)
    if document['data']['target_artifact_id'] != task['target_id']:
        raise ValueError('报告与固定输入不匹配')
    return document['data']


def finish_review(kernel, task):
    data = completed_report(kernel, task)
    with kernel._connect() as connection:
        connection.execute('BEGIN IMMEDIATE')
        status = connection.execute('SELECT status FROM review_tasks WHERE id=?', (task['id'],)).fetchone()
        if status is None or status['status'] != 'running':
            return
        row = root_record(connection, task['project_id'], task['record_id'])
        current = snapshot(connection, row)
        unchanged = fingerprint(inputs(connection, current)) == task['input_hash']
        clear = unchanged and label_untouched(connection, task)
        publish_result(connection, row, current, task, data, unchanged, clear)
        connection.execute("UPDATE review_tasks SET status='completed',error='',updated_at=? WHERE id=?", (now(), task['id']))


def label_untouched(connection, task):
    rows = connection.execute("SELECT before_json,after_json FROM research_changes WHERE record_id=? AND revision>? AND kind='labels'",
                              (task['record_id'], task['payload']['revision'])).fetchall()
    label_id = task['payload']['label']['id']
    return all((label_id in {v['id'] for v in json.loads(row[0])['labels']}) ==
               (label_id in {v['id'] for v in json.loads(row[1])['labels']}) for row in rows)


def publish_result(connection, row, current, task, data, unchanged, clear):
    verdicts = {'pass': '通过', 'revise': '需要修订', 'inconclusive': '尚无定论'}
    revision, author = task['payload']['revision'], 'agent:' + task['run_id']
    scope = '当前正文及输入附件与被审版本一致。' if unchanged else '正文或输入附件已变化，本次结果尚未覆盖当前修改。'
    text = f"**复核 r{revision}：{verdicts[data['conclusion']['verdict']]}**\n\n{data['summary']}\n\n{data['conclusion']['markdown']}"
    text += f"\n\n{scope}\n\n[完整报告]({view_url(task['project_id'], task['report_id'])}) · [执行过程](/chat/{task['session_id']})"
    result = append(connection, row, current, current, 'comment', author, '独立复核完成', text, revision)
    if clear and any(label['id'] == task['payload']['label']['id'] for label in current['labels']):
        before = result['after']
        after = {**before, 'labels': [label for label in before['labels'] if label['id'] != task['payload']['label']['id']]}
        append(connection, row, before, after, 'labels', 'system', f'复核 r{revision} 已完成，移除本次请求标签')
