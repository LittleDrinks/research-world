from dataclasses import asdict
import base64
import binascii
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict

from .artifact_documents import DOCUMENT_TYPE, MAX_BYTES, DocumentError, invalid, parse, prepare, templates
from .artifact_reading import markdown, reading, view_url
from .review_store import ReviewStore
from .review_results import check_report


class CaptureRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation: Literal['capture', 'validate', 'templates', 'read'] = 'capture'
    artifact_id: str | None = None
    content: str | None = None
    content_base64: str | None = None
    path: str | None = None
    media_type: str = 'text/plain'
    schema_id: str | None = None
    record_id: str | None = None
    target_artifact_id: str | None = None


def artifact_router(kernel, runtime):
    router = APIRouter(prefix='/api/v1/projects/{project_id}')

    @router.post('/artifacts', status_code=201)
    async def capture(project_id: str, body: CaptureRequest, request: Request):
        kernel.get_project(project_id)
        try:
            return await capture_request(kernel, runtime, project_id, body, request.headers.get('x-research-author', 'user'))
        except DocumentError as error:
            raise HTTPException(422, {'message': '报告校验未通过', 'errors': error.errors}) from None

    add_reading_routes(router, kernel)
    return router


async def capture_request(kernel, runtime, project_id, body, author='user'):
    if body.operation == 'templates':
        return templates(kernel, project_id)
    if body.operation == 'read':
        return reading(kernel, project_id, body.artifact_id)
    raw, media_type = await capture_bytes(runtime, project_id, body), body.media_type
    if len(raw) > MAX_BYTES:
        raise ValueError('Artifact 超过 4 MiB')
    if body.schema_id:
        check_selected_target(raw, body.target_artifact_id)
        raw, media_type = prepare(kernel, project_id, raw, body.schema_id, body.record_id), DOCUMENT_TYPE
    elif media_type.split(';')[0].strip().lower() == 'text/markdown':
        invalid('schema_id', '报告必须选择平台模板；原始文献和执行文件请按证据文件格式保存')
    elif body.operation == 'validate':
        raise ValueError('结构化校验需要选择模板')
    elif media_type.strip() == DOCUMENT_TYPE:
        raise ValueError('请通过 schema_id 和 record_id 发布结构化报告')
    return reviewed_capture(kernel, project_id, body, raw, media_type, author)


def reviewed_capture(kernel, project_id, body, raw, media_type, author):
    store = ReviewStore(kernel)
    task = check_report(store, project_id, raw, author) if media_type == DOCUMENT_TYPE else None
    if task and task['report_id']:
        from .artifacts import ArtifactStore
        if ArtifactStore.identifier(raw) != task['report_id']:
            raise ValueError('本次复核已经提交报告，不能替换原件')
    result = finish_capture(kernel, project_id, body, raw, media_type)
    if task and body.operation == 'capture':
        store.update(task['id'], report_id=result['id'])
    return result


async def capture_bytes(runtime, project_id, body):
    if sum(value is not None for value in (body.content, body.path, body.content_base64)) != 1:
        raise ValueError('必须且只能提供 content、content_base64 或工作区 path')
    if body.content_base64 is not None:
        if len(body.content_base64) > MAX_BYTES * 4 // 3 + 4:
            raise ValueError('Artifact 超过 4 MiB')
        try:
            return base64.b64decode(body.content_base64, validate=True)
        except binascii.Error:
            raise ValueError('产物编码无效') from None
    content = body.content if body.path is None else await runtime.workspace_file(project_id, body.path)
    return content.encode('utf-8')


def check_selected_target(raw, expected):
    if expected is None:
        return
    data = parse(raw)
    if not isinstance(data, dict) or data.get('target_artifact_id') != expected:
        invalid('target_artifact_id', '文件中的被审原件与所选原件不同，请核对版本')


def finish_capture(kernel, project_id, body, raw, media_type):
    if body.operation == 'validate':
        return {'valid': True}
    if body.record_id:
        kernel.get_record(project_id, body.record_id)
    artifact = kernel.capture_artifact(project_id, raw, media_type)
    if body.record_id:
        kernel.attach_artifact(project_id, body.record_id, artifact.id)
    base = f'/api/v1/projects/{project_id}/artifacts/{artifact.id}'
    return asdict(artifact) | {'download_url': base + '?download=true', 'view_url': view_url(project_id, artifact.id)}


def add_reading_routes(router, kernel):
    @router.get('/artifact-templates')
    def catalog(project_id: str):
        return templates(kernel, project_id)

    @router.get('/artifacts/{artifact_id}/reading')
    def read(project_id: str, artifact_id: str):
        return reading(kernel, project_id, artifact_id)

    @router.get('/artifacts/{artifact_id}/markdown')
    def export(project_id: str, artifact_id: str):
        document = reading(kernel, project_id, artifact_id)
        if document['kind'] != 'document':
            raise ValueError('该产物不是结构化报告')
        return Response(markdown(document, project_id), media_type='text/markdown',
                        headers={'Content-Disposition': 'attachment; filename="report.md"'})
