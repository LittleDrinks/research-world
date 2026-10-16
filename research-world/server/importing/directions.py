import json
import re

from .corpus import checksum


def load_directions(evidence,qid):
    spec=json.loads((evidence/'direction-spans.json').read_text())[qid]
    raw=(evidence/spec['path']).read_bytes()
    if checksum(raw)!=spec['sha256']:raise ValueError(f'{qid}: direction source changed')
    text=raw.decode('utf-8')
    if len(spec['directions'])!=3:raise ValueError(f'{qid}: expected three reviewed directions')
    return {**spec,'directions':[_extract(text,value) for value in spec['directions']]}


def _extract(text,value):
    excerpts=[];locations=[]
    for start,end in value['spans']:
        if not 0<=start<end<=len(text):raise ValueError('Invalid direction span')
        excerpts.append(text[start:end].strip())
        locations.append({'start':start,'end':end,'start_line':text.count('\n',0,start)+1,'end_line':text.count('\n',0,end)+1})
    if not value['title'] or not excerpts or not all(excerpts):raise ValueError('Empty direction')
    return {'title':value['title'],'text':'\n\n'.join(excerpts),'source_spans':locations}


def import_directions(writer,project,question,item,sources):
    spec=item['directions']
    for index,value in enumerate(spec['directions'],1):
        content={**value,'verified':False,'source_path':spec['path'],'source_sha256':spec['sha256'],
                 'attachments':[{'id':f'artifact:{spec["sha256"]}','name':'研究报告 · '+spec['path']}],
                 'note':'历史报告中的研究方向；证据与结论尚未重新核验。'}
        node=writer.record(project,f'direction/{index}','direction',content,(f'artifact:{spec["sha256"]}',))
        writer.link(project,node,question)
        for citation,source in sources.items():
            if re.search(r'(?<![A-Za-z0-9_-])'+re.escape(citation)+r'(?![A-Za-z0-9_-])',value['text']):writer.link(project,node,source)
