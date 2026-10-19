from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, StrictBool

from .artifact_documents import published_schemas
from .review_store import fingerprint, inputs


class ReviewBinding(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: StrictBool
    agent_id: str
    schema_id: str


def review_router(worker):
    router = APIRouter(prefix='/api/v1/projects/{project_id}')
    rule_routes(router, worker)
    task_routes(router, worker)
    return router


def rule_routes(router, worker):
    @router.get('/review-rules')
    def rules(project_id: str):
        return worker.store.rules(project_id)

    @router.put('/review-rules/{label_id}')
    async def save(project_id: str, label_id: str, body: ReviewBinding):
        worker.kernel.get_project(project_id)
        if label_id not in {label['id'] for label in worker.kernel.list_labels(project_id)}:
            raise KeyError(label_id)
        existing = next((rule for rule in worker.store.rules(project_id) if rule['label_id'] == label_id), None)
        if existing and not body.enabled:
            return worker.store.save_rule(project_id, label_id, existing['config'], False)
        if body.schema_id not in published_schemas():
            raise ValueError('请选择已发布的报告模板')
        config = await prepare_agent(worker, body)
        return worker.store.save_rule(project_id, label_id, config, body.enabled)


async def prepare_agent(worker, body):
    catalog = await worker.runtime.catalog()
    agent = worker.control.profiles.get(body.agent_id, catalog['default_model'])
    if not {'artifact', 'change'} <= set(agent['tools']):
        raise ValueError('复核 Agent 需要启用 artifact 和 change 工具')
    prepared = await worker.runtime.validate(agent)
    return {'agent': agent | {'instructions': prepared['instructions']}, 'schema_id': body.schema_id}


def task_routes(router, worker):
    @router.get('/records/{record_id}/reviews')
    def tasks(project_id: str, record_id: str):
        return [public_task(worker, task) for task in worker.store.list_tasks(project_id, record_id)]

    @router.post('/reviews/{task_id}/retry')
    async def retry(project_id: str, task_id: str):
        await worker.retry(project_id, task_id)
        return public_task(worker, worker.store.get(project_id, task_id))

    @router.post('/reviews/{task_id}/cancel')
    async def cancel(project_id: str, task_id: str):
        await worker.cancel(project_id, task_id)
        return public_task(worker, worker.store.get(project_id, task_id))


def public_task(worker, task):
    record = worker.kernel.get_record(task['project_id'], task['record_id'])
    with worker.kernel._connect() as connection:
        current = inputs(connection, {'content': record.content, 'artifact_ids': record.artifact_ids})
    payload = task['payload']
    return {key: value for key, value in task.items() if key != 'payload'} | {
        'revision': payload['revision'], 'label': payload['label'], 'agent_name': payload['config']['agent']['name'],
        'model': payload['config']['agent']['model'], 'schema_id': payload['config']['schema_id'],
        'input_changed': fingerprint(current) != task['input_hash'],
    }
