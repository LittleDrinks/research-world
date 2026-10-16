from dataclasses import asdict
from pathlib import Path
import json

from .corpus import checksum,document,sessions_for
from .redact import trajectory
from .directions import import_directions


class Writer:
    def __init__(self,kernel,source):
        self.kernel,self.source=kernel,source
        self.projects={p.name:p for p in kernel.list_projects()}
        self.created=0

    def project(self,name,question):
        if name not in self.projects:self.projects[name]=self.kernel.create_project(name,question)
        project=self.projects[name]
        if project.question!=question:raise ValueError(f'{name}: existing project question differs')
        return project

    def record(self,project,key,kind,content,artifacts=()):
        value={**content,'origin':{'collection':'contest-2026','key':key}}
        records=self.kernel.list_records(project.id)
        matches=[r for r in records if r.content.get('origin')==value['origin']]
        if len(matches)>1:raise ValueError('Duplicate import identity')
        if matches:
            current=matches[0]
            if current.type!=kind or current.content!=value or current.artifact_ids!=tuple(artifacts):raise ValueError(f'Imported content changed: {key}')
            return current
        revoked=self.kernel.history(project.id)
        if any((r.get('object') or {}).get('content',{}).get('origin')==value['origin'] for r in revoked):
            raise ValueError(f'Imported object was revoked: {key}')
        self.created+=1
        return self.kernel.record(project.id,kind,value,tuple(artifacts))

    def link(self,project,source,target):
        existing=self.kernel.list_relations(project.id)
        if not any(r.source_id==source.id and r.target_id==target.id and r.type=='depends_on' for r in existing):
            self.kernel.connect(project.id,source.id,target.id,'depends_on')

    def file(self,project,path):
        content=path.read_bytes()
        return self.kernel.capture_artifact(project.id,content,'text/markdown')


def import_project(writer,item,raw_index):
    project=writer.project(item['qid'],item['question'])
    question=writer.record(project,'question','question',{'title':item['question'].splitlines()[0],'text':item['question']})
    attachments=_artifacts(writer,project,item,raw_index)
    archive=_archive(writer,project,question,item,attachments)
    main=_candidate(writer,project,question,item,attachments)
    writer.link(project,main,archive)
    _versions(writer,project,question,item,attachments)
    _sources(writer,project,main,item)
    import_directions(writer,project,question,item)
    return {'qid':item['qid'],'project_id':project.id,'artifacts':len(attachments['files']),
            'raw_imported':attachments['raw_count'],'raw_missing':attachments['missing'],'corpus_status':item['corpus_status']}


def _artifacts(writer,project,item,index):
    files={str(path.relative_to(writer.source)):writer.file(project,path) for path in item['files']}
    logs,missing=sessions_for(item,index)
    raw=[]
    for session_id,info in logs:
        path=Path(info['path']);content=trajectory(path)
        artifact=writer.kernel.capture_artifact(project.id,content,'application/x-ndjson')
        raw.append({**{k:v for k,v in info.items() if k not in {'path','bytes'}},'original_sha256':info['sha256'],'sanitized_sha256':checksum(content),'artifact_id':artifact.id})
    manifest={'files':{key:asdict(value) for key,value in files.items()},'trajectories':raw,'missing_session_ids':missing}
    capture=writer.kernel.capture_artifact(project.id,json.dumps(manifest,ensure_ascii=False,indent=2).encode(),'application/json')
    return {'files':files,'manifest':capture.id,'raw':[r['artifact_id'] for r in raw],'raw_names':{r['artifact_id']:f'轨迹 {r["session_id"]}.jsonl' for r in raw},'raw_count':len(raw),'missing':missing}


def _candidate(writer,project,question,item,attachments):
    path=item['candidate'];meta,body=document(path)
    artifact=attachments['files'][str(path.relative_to(writer.source))]
    audit=attachments['files'][str((item['evidence']/'all'/item['audit']).relative_to(writer.source))]
    ledger=attachments['files'][str((item['evidence']/'all/run.md').relative_to(writer.source))]
    ids=[artifact.id,audit.id,ledger.id,attachments['manifest']]
    content={'title':'历史候选报告 · '+item['qid'],'text':body,'historical_status':item['corpus_status'],
             'verified':False,'author_session':item['author'],'model':item['model'],
             'attachments':_names(attachments,ids),'source_sha256':artifact.sha256,'note':'历史研究材料；交付状态不代表科学问题已解决。'}
    node=writer.record(project,'all/'+item['qid'],'source',content,ids)
    writer.link(project,node,question)
    return node


def _versions(writer,project,question,item,attachments):
    deep=item['deep']
    for path in item['files']:
        if path.parent.name!=item['qid'] or not path.stem.startswith('v') or not path.stem[1:].isdigit():continue
        meta,body=document(path);artifact=attachments['files'][str(path.relative_to(writer.source))]
        final=path.name==deep.get('final')
        related=[artifact.id,*_review_artifacts(writer,item,attachments,path,final)]
        content={'title':f'深度案例 {path.stem}'+(' · 最终交付版' if final else ''),'text':body,'verified':False,
                 'historical_status':deep.get('status') if final else 'historical_version','declared_metadata':json.loads(json.dumps(meta,default=str)),'source_sha256':artifact.sha256,'attachments':_names(attachments,related)}
        node=writer.record(project,f'{item["qid"]}/{path.name}','source',content,related)
        writer.link(project,node,question)


def _review_artifacts(writer,item,attachments,path,final):
    names=[f'review-{path.stem}.md','run.md']
    if final:names.extend(item['deep'].get(key,'') for key in ['final_review','final_receipt'])
    values=[]
    for name in dict.fromkeys(names):
        key=str((path.parent/name).relative_to(writer.source))
        if name and key in attachments['files']:values.append(attachments['files'][key].id)
    return list(dict.fromkeys(values))


def _sources(writer,project,report,item):
    metadata,_=document(item['candidate'])
    sources=metadata.get('sources',[])
    if not isinstance(sources,list):return
    for index,source in enumerate(sources):
        if not isinstance(source,dict):continue
        title=source.get('title') or source.get('doi') or source.get('url')
        if not isinstance(title,str):continue
        text='\n'.join(f'{key}: {value}' for key,value in source.items())
        node=writer.record(project,f'all/{item["qid"]}/source/{index}','source',{'title':title,'text':text,'verified':False,'note':'历史报告列出的来源，未重新核验其支持范围。'})
        writer.link(project,report,node)


def _names(attachments,ids):
    names={value.id:'/'.join(path.split('/')[-2:]) for path,value in attachments['files'].items()}
    names.update(attachments['raw_names'])
    names[attachments['manifest']]='导入清单.json'
    return [{'id':value,'name':names[value]} for value in ids]


def _archive(writer,project,question,item,attachments):
    ids=list(dict.fromkeys([v.id for v in attachments['files'].values()]+attachments['raw']+[attachments['manifest']]))
    content={'title':'历史资料与轨迹','text':'保留原始报告、版本、审计、运行账本及脱敏轨迹。历史日志不等于当前可恢复会话。',
             'attachments':_names(attachments,ids),'missing_sessions':attachments['missing'],'verified':False}
    node=writer.record(project,'archive','source',content,ids)
    writer.link(project,question,node)
    return node
