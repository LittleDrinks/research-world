from fastapi import APIRouter, HTTPException, Request, Response

from .change_store import ChangeConflict
from .research_changes import ChangeRequest
from .research_labels import LabelRequest
from .record_document import render_document


def research_router(kernel):
    router = APIRouter(prefix='/api/v1/projects/{project_id}')
    label_routes(router, kernel)
    change_routes(router, kernel)
    return router


def call(operation, *args):
    try:
        return operation(*args)
    except ChangeConflict as error:
        raise HTTPException(409, str(error)) from None
    except (KeyError, PermissionError):
        raise HTTPException(404, '记录或标签不存在') from None
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


def label_routes(router, kernel):
    @router.get('/labels')
    def list_all(project_id: str):
        return call(kernel.list_labels, project_id)

    @router.post('/labels', status_code=201)
    def create(project_id: str, body: LabelRequest, request: Request):
        return call(kernel.save_label, project_id, body.model_dump(), None, author(request))

    @router.put('/labels/{label_id}')
    def edit(project_id: str, label_id: str, body: LabelRequest, request: Request):
        return call(kernel.save_label, project_id, body.model_dump(), label_id, author(request))

    @router.delete('/labels/{label_id}', status_code=204)
    def remove(project_id: str, label_id: str, request: Request):
        call(kernel.delete_label, project_id, label_id, author(request))
        return Response(status_code=204)


def change_routes(router, kernel):
    @router.get('/records/{record_id}/document')
    def document(project_id: str, record_id: str):
        record = call(kernel.get_record, project_id, record_id)
        return Response(render_document(record), media_type='text/markdown; charset=utf-8')

    @router.get('/records/{record_id}')
    def current(project_id: str, record_id: str):
        return call(kernel.get_record, project_id, record_id)

    @router.get('/changes')
    def list_all(project_id: str, record_id: str | None = None):
        return call(kernel.list_changes, project_id, record_id)

    @router.get('/records/{record_id}/revisions/{revision}')
    def revision(project_id: str, record_id: str, revision: int):
        return call(kernel.record_revision, project_id, record_id, revision)

    @router.post('/records/{record_id}/changes', status_code=201)
    def change(project_id: str, record_id: str, body: ChangeRequest, request: Request):
        return call(kernel.change_record, project_id, record_id, body.model_dump(exclude_none=True), author(request))


def author(request):
    value = request.headers.get('x-research-author', 'user')
    if len(value) > 120 or not value.strip():
        raise HTTPException(422, '变更作者标识无效')
    return value
