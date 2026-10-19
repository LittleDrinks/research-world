"""Publish executed q049 results and research semantics through public APIs."""
import base64
import json
import re
from pathlib import Path

import httpx

from q049_reports import ROOT, coverage, reports


def post(client, path, body):
    response=client.post(path,json=body);response.raise_for_status();return response.json()


def artifact(client, root, content, mime, binary=False, record_id=None):
    body={'media_type':mime, 'content_base64' if binary else 'content':base64.b64encode(content).decode() if binary else content}
    if record_id:body['record_id']=record_id
    return post(client,root+'/artifacts',body)


def publish_record(client, root, kind, title, text, attachments=(), origin=''):
    existing=next((r for r in client.get(root+'/records').json() if r['content'].get('origin')==origin),None)
    if existing:return existing
    return post(client,root+'/records',{'type':kind,'content':{'title':title,'text':text,'origin':origin,
        'attachments':[{'id':a['id'],'name':name} for name,a in attachments]},'artifact_ids':[a['id'] for _,a in attachments]})


def connect(client,root,source,target,kind):
    return post(client,root+'/relations',{'source_id':source['id'],'target_id':target['id'],'type':kind})


def selected_metadata():
    found={}
    for path in ROOT.glob('openalex-search*.json'):
        for query in json.loads(path.read_text()):
            for item in query.get('results',[]):found.setdefault(item['id'],item)
    ids=['W2071681224','W2171324723','W2137743288','W2113887078','W2144176564','W2023498002',
         'W2064816908','W2076480618','W1864108573','W2126701677','W2107852741','W2967227764']
    return [found['https://openalex.org/'+identifier] for identifier in ids]


def sources(client,root,method_report):
    records=[]
    for work in selected_metadata():
        raw=artifact(client,root,json.dumps(work,ensure_ascii=False,indent=2),'application/json')
        title=work['title'];read=work['id'].endswith(('W1864108573','W2126701677'))
        text=f"{', '.join(a['author']['display_name'] for a in work['authorships'])} · {work['publication_year']}\n\n[DOI]({work['doi']}) · [OpenAlex]({work['id']})"
        text+='\n\n已取得原文，核对摘要与方法段。' if read else '\n\n待办：取得全文，核对适用条件与关键结果。'
        attachments=[('文献元数据.json',raw)]+([('方法依据核查.md',method_report)] if read else [])
        records.append(publish_record(client,root,'source',title,text,attachments,origin=work['id']))
    return records


def selection(client,root,records):
    stop={'a','an','the','of','and','for','in','to','with','on','from','by','over','as'}
    tokens={r['id']:set(re.findall(r'[a-z]+',r['content']['title'].lower()))-stop for r in records}
    query={'solar','system','orbit','orbits','gravitational','dynamics','integrator','symplectic','energy'}
    candidates=[{'id':r['id'],'title':r['content']['title'],'relevance':len(tokens[r['id']]&query)/len(query)} for r in records]
    sims={a:{b:len(x&y)/len(x|y) if x|y else 0 for b,y in tokens.items() if b!=a} for a,x in tokens.items()}
    payload={'candidates':candidates,'similarities':sims,'count':4,'diversity_weight':.65}
    value=post(client,root+'/candidate-selection',payload)
    (ROOT/'mmr-result.json').write_text(json.dumps({'input':payload,'output':value},ensure_ascii=False,indent=2)+'\n')
    titles={r['id']:r['content']['title'] for r in records}
    rows='\n'.join(f"| {i+1} | {titles[s['id']]} | {s['relevance']:.3f} | {s['redundancy']:.3f} | {s['score']:.3f} |" for i,s in enumerate(value['steps']))
    text='# MMR 文献选择\n相关性：标题关键词命中比例。相似度：标题词集合Jaccard。重复性权重0.65，选4篇。\n\n| 顺序 | 文献 | 相关性 | 最大相似度 | MMR分数 |\n| --- | --- | ---: | ---: | ---: |\n'+rows+'\n\n分数用于安排阅读顺序，科学证据强度另行核查。'
    return artifact(client,root,text,'text/markdown'),artifact(client,root,json.dumps({'input':payload,'output':value},ensure_ascii=False),'application/json')


def joint(client,root,rule,title,members,target,statement,evidence,k=None):
    body={'rule':rule,'title':title,'target_id':target['id'],'members':[{'record_id':r['id'],'role':role} for r,role in members],
          'statement':statement,'rationale':statement,'evidence':[{'artifact_id':a['id'],'locator':loc} for a,loc in evidence]}
    if k is not None:body['k']=k
    return post(client,root+'/joint-conditions',body)


def run(client,project):
    root=f"/api/v1/projects/{project['id']}";documents={key:artifact(client,root,text,'text/markdown') for key,text in reports().items()}
    files={name:artifact(client,root,(ROOT/'experiments'/name).read_bytes() if name.endswith('.png') else (ROOT/'experiments'/name).read_text(),mime,name.endswith('.png'))
           for name,mime in [('q049_cpu.py','text/x-python'),('results.json','application/json'),('integration.csv','text/csv'),('stdout.txt','application/json'),('energy-drift.png','image/png')]}
    refs=sources(client,root,documents['papers']);mmr=selection(client,root,refs)
    q=publish_record(client,root,'question','如何区分轨道变化的物理来源与数值来源？','比较对象、模型条件和观测量先对齐，再解释能量变化。',origin='q049:question')
    records=research_records(client,root,q,refs,documents,files,mmr)
    semantics=relations(client,root,records,refs,documents)
    manifest={'project_id':project['id'],'records':{k:v['id'] for k,v in records.items()},'conditions':{k:v['id'] for k,v in semantics.items()},'documents':documents,'files':files,'mmr':mmr}
    return publish_overview(client,root,manifest)


def publish_overview(client,root,manifest):
    text=coverage(manifest)
    report=artifact(client,root,text,'text/markdown',record_id=manifest['records']['question'])
    base='http://localhost:8095/projects/'+manifest['project_id']
    manifest['coverage_url']='http://localhost:8095'+report['view_url']
    manifest['map_url']=base+'/map?node='+manifest['records']['question']
    manifest['preview_links']={key:base+'/records/'+rid for key,rid in manifest['records'].items()}
    manifest['preview_links']['mmr']='http://localhost:8095'+manifest['mmr'][0]['view_url']
    (ROOT/'coverage.md').write_text(text)
    return manifest


def research_records(client,root,q,refs,docs,files,mmr):
    r={'question':q}
    r['methods']=publish_record(client,root,'direction','联合检查积分方法与误差控制','WHFast与IAS15分别提供算法实现和误差控制的研究依据。先测误差，再解释轨道演化。',[('方法依据.md',docs['papers']),('MMR选择结果.md',mmr[0]),('MMR选择输入输出.json',mmr[1])],origin='q049:methods')
    r['radiation']=publish_record(client,root,'experiment','引力波功率与时间尺度复算','已执行：孤立圆轨道模型。结果约196.29 W；局部能量时标是形式并合时间的四倍。',[('复算报告.md',docs['radiation']),('计算代码.py',files['q049_cpu.py']),('完整结果.json',files['results.json'])],origin='q049:radiation')
    r['drift']=publish_record(client,root,'experiment','无耗散方程下的能量漂移','已执行：30个轨道周期、100/200/400步每圈。Euler与Leapfrog出现不同的能量误差。',[('积分对照.md',docs['integration']),('能量误差.png',files['energy-drift.png']),('结果表.csv',files['integration.csv']),('计算代码.py',files['q049_cpu.py']),('运行输出.txt',files['stdout.txt'])],origin='q049:drift')
    r['numeric']=publish_record(client,root,'direction','算法误差造成数值能量漂移','同一无耗散方程更换积分器和步长后，误差改变。当前结果支持优先检查数值实现。',origin='q049:numeric')
    r['physical']=publish_record(client,root,'direction','物理耗散造成能量变化','需要方程中存在耗散项，并对齐观察量。当前无耗散对照不支持用物理耗散解释其数值漂移。',origin='q049:physical')
    r['budget']=publish_record(client,root,'direction','三个配额优先覆盖两项检查','规划预算3个计算配额，至少选2项：分辨率1、积分时长2、初值集合3。可行组合为分辨率与积分时长。',[('预算选择.md',docs['budget']),('预算数据.json',files['results.json'])],origin='q049:budget')
    for key,title,cost in [('resolution','加倍时间分辨率',1),('duration','延长积分时间',2),('ensemble','初值扰动集合',3)]:
        r[key]=publish_record(client,root,'experiment',title,f'下一轮计划。所需规划配额：{cost}。',[('预算选择.md',docs['budget'])],origin='q049:'+key)
    for key in ['methods','numeric','physical','budget']:connect(client,root,r[key],q,'depends_on')
    return r


def relations(client,root,r,sources,docs):
    pair=[s for s in sources if s['content']['origin'].endswith(('W1864108573','W2126701677'))]
    a=joint(client,root,'AND','算法实现与误差控制共同约束数值解释',[(s,'论文方法依据') for s in pair],r['methods'],'同时核查算法实现和误差控制，形成对数值解释的联合依据。',[(docs['papers'],'来源与方法段核查表')])
    o=joint(client,root,'OR','能量漂移的两个候选解释',[(r['numeric'],'数值算法误差'),(r['physical'],'模型中的物理耗散')],r['drift'],'对能量变化分别调查数值误差和物理耗散；由具体方程与对照结果区分。',[(docs['integration'],'积分器与步长对照')])
    k=joint(client,root,'k-of-N','配额3以内选择两项后续实验',[(r[key],f'规划配额 {cost}') for key,cost in [('resolution',1),('duration',2),('ensemble',3)]],r['budget'],'至少覆盖两项检查，并满足总配额不超过3；枚举结果选中分辨率与积分时长。',[(docs['budget'],'候选成本与可行组合')],2)
    connect(client,root,r['drift'],r['numeric'],'supports');connect(client,root,r['drift'],r['physical'],'refutes')
    connect(client,root,r['radiation'],r['methods'],'depends_on')
    return {'AND':a,'OR':o,'k-of-N':k}


def main():
    with httpx.Client(base_url='http://localhost:8095',timeout=60,headers={'x-research-author':'experiment'}) as client:
        existing=client.get('/api/v1/projects').raise_for_status().json()
        project=next((p for p in existing if p['name']=='q049 · 计算与证据'),None) or post(client,'/api/v1/projects',{'name':'q049 · 计算与证据','question':'如何区分轨道变化的物理来源与数值来源？'})
        manifest=run(client,project);(ROOT/'components.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'project_id':project['id'],'records':len(manifest['records']),'conditions':list(manifest['conditions'])},ensure_ascii=False))


if __name__=='__main__':main()
