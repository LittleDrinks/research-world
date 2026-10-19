import hashlib
import io
import json
import zipfile
from dataclasses import asdict
from .review_store import ReviewStore


async def export_project(kernel, runtime, project_id):
    sessions = kernel.list_sessions(project_id, include_archived=True)
    snapshot = {'project':asdict(kernel.get_project(project_id)),
                'records':[asdict(v) for v in kernel.list_records(project_id)],
                'relations':[asdict(v) for v in kernel.list_relations(project_id)],
                'joint_conditions':kernel.list_joint_conditions(project_id),
                'sessions':[asdict(v) for v in sessions], 'revocations':kernel.history(project_id),
                'labels':kernel.list_labels(project_id), 'changes':kernel.list_changes(project_id),
                'review_rules':ReviewStore(kernel).rules(project_id)}
    with kernel._connect() as connection:
        from .review_store import task_view
        snapshot['review_tasks'] = [task_view(row) for row in connection.execute('SELECT * FROM review_tasks WHERE project_id=?', (project_id,))]
    files = {'project.json':_json(snapshot)}
    for artifact in kernel.list_artifacts(project_id):
        files[f'artifacts/{artifact.sha256}'] = kernel.read_artifact(project_id, artifact.id)
    for session in sessions:
        files[f'trajectories/{session.id}.json'] = _json(await runtime.export(session.id))
    return _package(project_id, files)


def _package(project_id, files):
    manifest = {name:{'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)} for name,content in files.items()}
    files['manifest.json'] = _json({'project_id':project_id,'files':manifest})
    files['checksums.sha256'] = ''.join(f'{hashlib.sha256(value).hexdigest()}  {name}\n' for name,value in sorted(files.items())).encode()
    result = io.BytesIO()
    with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in sorted(files.items()):
            archive.writestr(name,content)
    return result.getvalue()


def _json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).encode()
