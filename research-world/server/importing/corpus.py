import hashlib
import json
import re
from pathlib import Path

import yaml

QID=re.compile(r'q\d{3}')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def table_rows(path):
    rows=[]
    for line in path.read_text().splitlines():
        if line.startswith('|'):
            rows.append([part.strip().strip('`') for part in line.strip('|').split('|')])
    return rows


def document(path):
    text=path.read_text()
    if not text.startswith('---\n'):
        return {},text
    _,header,body=text.split('---',2)
    try:
        metadata=yaml.safe_load(header)
    except yaml.YAMLError:
        return {'metadata_parse_error':True},body.strip()
    return metadata if isinstance(metadata,dict) else {},body.strip()


def corpus(source):
    evidence=source/'research-world/evidence/contest-2026'
    rows={r[0]:r for r in table_rows(evidence/'all/run.md') if r and QID.fullmatch(r[0])}
    expected={f'q{i:03d}' for i in range(1,126)}
    if set(rows)!=expected:
        raise ValueError('Corpus ledger must contain q001 through q125 exactly')
    result=[]
    for qid in sorted(rows):
        result.append(_project(source,evidence,qid,rows[qid]))
    return result


def _project(source,evidence,qid,row):
    candidate=evidence/'all'/f'{qid}.md'
    if checksum(candidate.read_bytes())!=row[7]:
        raise ValueError(f'{qid}: candidate hash differs from ledger')
    canonical=json.loads((source/'research-world/projects'/qid/'project.json').read_text(encoding='utf-8-sig'))
    deep=evidence/qid
    meta,_=document(deep/'run.md') if deep.is_dir() else ({},'')
    paths=[candidate,evidence/'all'/row[10],evidence/'all/run.md',evidence/'all/index.md',*sorted(evidence.glob('*.md'))]
    if deep.is_dir():paths.extend(sorted(deep.glob('*.md')))
    return {'qid':qid,'question':canonical['question'],'corpus_status':row[9],
            'author':row[1],'raw_sha256':row[8],'model':row[2],'audit':row[10],
            'deep':meta,'files':paths,'candidate':candidate,'evidence':evidence}


def raw_sessions(inventory,source=None):
    data=json.loads(inventory.read_text())
    if source is not None:_validate_files(data,source)
    result={}
    for value in data['raw_sessions']:
        path=Path(value['path'])
        if checksum(path.read_bytes())!=value['sha256']:
            raise ValueError(f"Trajectory changed: {value['session_id']}")
        result[value['session_id']]=value
    return result


def _belongs(project,reference):
    if reference['scope']==project['qid']:return True
    if reference['scope']=='cross_case':return bool(project['deep'])
    if reference['scope']!='all':return False
    if reference.get('project')==project['qid']:return True
    if reference.get('role')=='auditor':return reference.get('artifact_path','').endswith('/'+project['audit'])
    return reference.get('role')=='stopped' and project['qid'] in {'q041','q042','q043','q044','q045'}


def sessions_for(project,index):
    ids={project['author']}
    for path in project['files']:
        if path.parent.name==project['qid'] and path.name=='run.md' or project['deep'] and path.name=='scale-up-review-run.md':
            ids.update(row[1] for row in table_rows(path) if len(row)>1 and UUID.search(row[1]))
    if project['author'] in index and index[project['author']]['sha256']!=project['raw_sha256']:
        raise ValueError(f'{project["qid"]}: author trajectory differs from ledger')
    for session_id,value in index.items():
        if any(_belongs(project,r) for r in value['ledger_references']):ids.add(session_id)
    return [(sid,index[sid]) for sid in sorted(ids) if sid in index],sorted(ids-set(index))


def _validate_files(data,source):
    for row in data['session_ledger_records']:
        name=row.get('artifact_path');expected=row.get('artifact_sha256_actual')
        if name and expected and checksum((source/name).read_bytes())!=expected:
            raise ValueError(f'Historical file changed: {name}')
