import hashlib
import json
from pathlib import Path

import pytest

from server.kernel_interface import create_kernel
from server.importing.writer import Writer,import_project
from server.importing.corpus import document
from server.importing.redact import trajectory


def fixture(tmp_path):
    source=tmp_path/'source';evidence=source/'research-world/evidence/contest-2026'
    all_dir=evidence/'all';all_dir.mkdir(parents=True)
    candidate=all_dir/'q001.md';candidate.write_text('---\nsources:\n  - title: Source\n    doi: example\n---\nCandidate, not a proven result.')
    (all_dir/'audit.md').write_text('Audit: partial')
    (all_dir/'run.md').write_text('Ledger: partial')
    item={'qid':'q001','question':'Why?','candidate':candidate,'files':[candidate,all_dir/'audit.md',all_dir/'run.md'],
          'author':'session-id','raw_sha256':'unused','model':'historical-model','corpus_status':'partial','audit':'audit.md','evidence':evidence,'deep':{}}
    kernel=create_kernel(tmp_path/'database',tmp_path/'artifacts')
    return source,item,kernel


def test_import_is_idempotent_and_preserves_status_and_attachments(tmp_path):
    source,item,kernel=fixture(tmp_path)
    writer=Writer(kernel,source)
    result=import_project(writer,item,{})
    count=writer.created
    import_project(writer,item,{})
    records=kernel.list_records(result['project_id'])
    assert writer.created==count and len(kernel.list_projects())==1
    candidate=next(r for r in records if r.content['origin']['key']=='all/q001')
    assert candidate.content['historical_status']=='partial' and candidate.content['verified'] is False
    assert len(candidate.artifact_ids)==4 and result['raw_missing']==['session-id']
    assert all(r.type=='depends_on' for r in kernel.list_relations(result['project_id']))


def test_changed_imported_content_is_rejected(tmp_path):
    source,item,kernel=fixture(tmp_path);writer=Writer(kernel,source)
    import_project(writer,item,{})
    item['candidate'].write_text('Changed content')
    with pytest.raises(ValueError,match='Imported content changed'):
        import_project(writer,item,{})


def test_malformed_metadata_does_not_invent_sources(tmp_path):
    path=tmp_path/'document.md';path.write_text('---\nsources: [broken\n---\nOriginal report')
    metadata,body=document(path)
    assert metadata=={'metadata_parse_error':True} and body=='Original report'


def test_historical_trajectory_redacts_credentials(tmp_path):
    path=tmp_path/'raw.jsonl'
    rows=[{'type':'session','id':'s','cwd':'/private/location'},
          {'type':'message','message':{'content':'Authorization: Bearer test-secret','api_key':'hidden-value'}}]
    path.write_text('\n'.join(json.dumps(r) for r in rows))
    cleaned=trajectory(path).decode()
    assert 'test-secret' not in cleaned and 'hidden-value' not in cleaned and '/private/location' not in cleaned
    assert 'message' in cleaned


def test_revoked_import_is_not_resurrected(tmp_path):
    source,item,kernel=fixture(tmp_path);writer=Writer(kernel,source)
    result=import_project(writer,item,{})
    question=next(r for r in kernel.list_records(result['project_id']) if r.type=='question')
    kernel.remove_record(result['project_id'],question.id)
    with pytest.raises(ValueError,match='was revoked'):
        import_project(writer,item,{})


def test_trajectory_inventory_rejects_changed_bytes(tmp_path):
    from server.importing.corpus import raw_sessions
    raw=tmp_path/'log.jsonl';raw.write_text('{}\n')
    inventory=tmp_path/'inventory.json'
    inventory.write_text(json.dumps({'raw_sessions':[{'session_id':'s','path':str(raw),'sha256':'incorrect'}]}))
    with pytest.raises(ValueError,match='Trajectory changed'):
        raw_sessions(inventory)


def test_codex_metadata_and_inline_credentials_are_sanitized(tmp_path):
    path=tmp_path/'log.jsonl'
    path.write_text(json.dumps({'type':'session_meta','payload':{'id':'abc','cwd':'private-path'}})+'\n'+json.dumps({'type':'response_item','payload':{'text':'API_KEY=example-secret https://me:private-password@host sk-123456789abcdefghijklmnop'}}))
    cleaned=trajectory(path).decode()
    assert all(value not in cleaned for value in ['private-path','example-secret','private-password','sk-123456789abcdefghijklmnop'])
    assert 'response_item' in cleaned and 'abc' in cleaned
