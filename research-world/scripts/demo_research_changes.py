"""Create a q049 example with real OpenAlex metadata and explicitly illustrative changes."""
import argparse
import json
from pathlib import Path

import httpx

EVIDENCE = Path(__file__).resolve().parents[2] / 'benchmarks/research-changes-385'
SELECTED = ['W2071681224','W2171324723','W2137743288','W2113887078','W2144176564','W2023498002',
            'W2064816908','W2076480618','W1864108573','W2126701677','W2107852741','W2967227764']
LABELS = [('warning','#c58b20','需要关注的具体疑点；标签本身不代表结论失败'),
          ('need-info','#3b82b6','需要补充资料或澄清缺失条件'),('need-grill','#9560b5','需要追问假设、可比性或推理边界'),
          ('metadata-only','#697b8c','本项目仅取得文献元数据，未核验全文'),('示例','#70766c','界面与变更演示文字，不是新实验结果')]


def post(client, path, body):
    response = client.post(path, json=body)
    response.raise_for_status()
    return response.json()


def metadata():
    found = {}
    for path in [EVIDENCE/'openalex-search.json', EVIDENCE/'openalex-search-more.json']:
        for query in json.loads(path.read_text()):
            for work in query.get('results', []):
                found.setdefault(work['id'].rsplit('/', 1)[-1], (work, query['query'], query['retrieved_at']))
    return [found[identifier] for identifier in SELECTED]


def record(client, root, kind, title, text, artifacts=(), **extra):
    return post(client, root+'/records', {'type':kind,'content':{'title':title,'text':text,**extra},'artifact_ids':list(artifacts)})


def change(client, root, item, kind, reason, **fields):
    value = post(client, root+f"/records/{item['id']}/changes", {'kind':kind,'base_revision':item['revision'],'reason':reason,**fields})
    item.update(value['after'])
    return value


def apply_labels(client, root, item, labels, *names):
    return change(client, root, item, 'labels', '示例标注：由用户管理的行动标签，可并存', label_ids=[labels[name]['id'] for name in names])


def add_sources(client, root, labels):
    result = []
    for work, query, retrieved in metadata():
        artifact = post(client, root+'/artifacts', {'content':json.dumps(work,ensure_ascii=False,indent=2),'media_type':'application/json'})
        authors = ', '.join(a['author']['display_name'] for a in work['authorships'])
        text = f"**OpenAlex 元数据** · {work['publication_year']}\n\n作者：{authors}\n\n[OpenAlex]({work['id']})"
        if work.get('doi'): text += f" · [DOI]({work['doi']})"
        text += '\n\n**访问范围：**本项目仅检索书目元数据，尚未下载或阅读全文。检索结果不是支持或反驳研究方向的证据。'
        item = record(client,root,'source',work['title'],text,[artifact['id']],openalex_id=work['id'],doi=work.get('doi'),
                      discovery={'query':query,'retrieved_at':retrieved},attachments=[{'id':artifact['id'],'name':'OpenAlex 元数据.json'}])
        apply_labels(client,root,item,labels,'metadata-only','need-info')
        result.append(item)
    return result


def add_questions(client, root, labels):
    questions = [('理想模型里的守恒意味着什么？','需要区分能量守恒、轨道有界和真实多体系统的长期稳定。'),
                 ('引力波耗散与轨道变化如何比较？','明确模型、输入、单位、观察量与时间尺度。'),
                 ('一条失稳轨迹能说明概率吗？','需要采样方法、样本数、初值分布和终点事件定义。'),
                 ('太阳演化与多体混沌如何共同讨论？','不同机制的时间尺度可能对应不同事件，先核对比较条件。')]
    result = [record(client,root,'question',title,'**示例问题**\n\n'+text,note='示例文字；未调用模型开展研究') for title,text in questions]
    for item in result: apply_labels(client,root,item,labels,'示例','need-info')
    return result


def add_directions(client, root, labels, questions):
    drafts = [('按机制区分轨道稳定性的解释','示例初稿：尝试并列比较守恒、引力波耗散、混沌和太阳演化。'),
              ('概率主张需要怎样的证据？','示例候选：核查构造轨迹与统计概率之间的证据缺口。')]
    items = [record(client,root,'direction',title,text,note='示例文字，不是新科研结论') for title,text in drafts]
    for item, question in zip(items,[questions[1],questions[2]]):
        post(client,root+'/relations',{'source_id':item['id'],'target_id':question['id'],'type':'depends_on'})
        apply_labels(client,root,item,labels,'示例','warning','need-grill')
    change(client,root,items[0],'comment','示例讨论：指出比较条件缺口',reference_revision=1,comment='**示例讨论：**守恒模型与耗散模型的前提不同，不能直接标成科学矛盾。请明确对象、假设和可比指标。')
    change(client,root,items[0],'revise','示例修订：把比较前提写进正文，保留待核查标签',title=items[0]['content']['title'],
           text='**示例修订稿**\n\n先分别说明理想无耗散、引力波耗散和真实多体模型的适用范围。\n\n- 预期与实际证据分别是什么？\n- 对象、单位和条件是否可比？\n- 转录、实现和统计差异是否已排除？\n\n本项目尚未复算或核验文献全文；这里只演示可修订的研究记录。')
    return items


def add_joint(client, root, sources, direction):
    selected = [s for s in sources if s['content']['openalex_id'].endswith(('W2064816908','W2076480618'))]
    return post(client,root+'/joint-conditions',{'title':'示例：功率与轨道演化的联合核查条件','rule':'AND','target_id':direction['id'],
        'members':[{'record_id':s['id'],'role':'候选公式来源，全文与适用范围待核查'} for s in selected],
        'statement':'只有原文公式、适用条件与输入定义分别核对后，才讨论联合支撑的尺度比较。',
        'rationale':'此处是所需条件的示例，尚不代表文献已核验或目标成立。',
        'evidence':[{'artifact_id':s['artifact_ids'][0],'locator':'OpenAlex title/doi 元数据；全文未读'} for s in selected]})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://localhost:8095');args=parser.parse_args()
    with httpx.Client(base_url=args.url,timeout=60) as client:
        project=post(client,'/api/v1/projects',{'name':'q049 · 标签与变更','question':'轨道稳定性：多个相关问题、可修订研究记录与文献核查。示例内容，不调用模型。'})
        root=f"/api/v1/projects/{project['id']}"
        labels={name:post(client,root+'/labels',{'name':name,'color':color,'description':description}) for name,color,description in LABELS}
        questions=add_questions(client,root,labels);sources=add_sources(client,root,labels);directions=add_directions(client,root,labels,questions)
        experiment=record(client,root,'experiment','公式复算计划 · 示例未执行','**未执行计划**\n\n明确输入和单位，复查限定模型的公式与输出。\n\n这段是交互示例，未生成新的数值结果。')
        apply_labels(client,root,experiment,labels,'示例','need-info')
        post(client,root+'/relations',{'source_id':experiment['id'],'target_id':directions[0]['id'],'type':'depends_on'})
        add_joint(client,root,sources,directions[0])
        manifest={'project_id':project['id'],'name':project['name'],'selected_record':directions[0]['id'],'sources':len(sources),
                  'questions':len(questions),'records':len(client.get(root+'/records').json()),'model_calls':0,'metadata_scope':'OpenAlex only; full texts not downloaded or verified'}
        (EVIDENCE/'demo.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__': main()
