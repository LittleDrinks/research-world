import argparse
import importlib.metadata
import json
import subprocess
import uuid
from pathlib import Path

from .client import Product
from .report import report
from .protocol import prepare, save, score, write_jsonl


def arguments():
    parser=argparse.ArgumentParser(description='SciFact through the running Pi product; official retrieval and scoring')
    for name in ('data','archive','source','evaluator','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--url',default='http://127.0.0.1:18095')
    parser.add_argument('--runtime-url',default='http://127.0.0.1:18098')
    parser.add_argument('--split',choices=['train','dev'],default='train')
    parser.add_argument('--limit',type=int,default=3)
    parser.add_argument('--ids',type=int,nargs='+')
    parser.add_argument('--model')
    parser.add_argument('--thinking',default='low')
    parser.add_argument('--timeout',type=float,default=180)
    return parser.parse_args()


def main():
    args=arguments()
    if args.limit<1 or args.timeout<=0:
        raise ValueError('Positive limit and timeout required')
    args.output.mkdir(parents=True,exist_ok=False)
    gold,tasks,verified=prepare(args,args.output)
    product=Product(args.url,args.runtime_url,args.model,args.thinking,args.timeout)
    product.model=args.model or product.request('GET','/runtime/catalog')['default_model']
    run_id=uuid.uuid4().hex[:8]
    manifest=_manifest(args,verified,product.model)
    save(args.output/'manifest.json',manifest)
    results={arm:_arm(args,product,arm,run_id,gold,tasks) for arm in ('baseline','research')}
    save(args.output/'summary.json',{'split':args.split,'n':len(tasks),'arms':results,
         'claim':'smoke only; no equal-token-budget causal comparison','cost':None})
    report(args.output)
    print(json.dumps(results,ensure_ascii=False),flush=True)


def _manifest(args,verified,model):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    return {'runner_revision':revision,'product_source_trees':_source_trees(),'protocol':verified,'model':model,
            'thinking':args.thinking,'timeout_seconds':args.timeout,'split':args.split,
            'retrieval':'official TF-IDF top-3 (unigram+bigram); no gold fields',
            'dependencies':{name:importlib.metadata.version(name) for name in ['numpy','scikit-learn','jsonlines','httpx']},
            'token_budget_enforced':False,'token_usage_available':False}


def _source_trees():
    return {name:subprocess.check_output(['git','rev-parse','HEAD:'+name],text=True).strip()
            for name in ['runtime','research-world']}


def _arm(args,product,arm,run_id,gold,tasks):
    root=args.output/arm
    root.mkdir()
    profile=product.profile(arm,run_id)
    save(root/'agent.json',profile)
    results=[]
    for task in tasks:
        print(f'{arm}: claim {task["id"]}',flush=True)
        results.append(product.run_case(task,profile['id'],root/str(task['id'])))
    predictions=[r['prediction'] for r in results]
    write_jsonl(root/'predictions.jsonl',predictions)
    metrics=score(args.evaluator,args.output/'gold.jsonl',root/'predictions.jsonl',root/'metrics.json')
    save(root/'cases.json',[_case_score(args,root,g,t,r) for g,t,r in zip(gold,tasks,results)])
    return {'metrics':metrics,'completed':sum(r['status']=='completed' for r in results),
            'total':len(results),'seconds':round(sum(r['seconds'] for r in results),3)}


def _diagnose(gold,task,result):
    expected=set(gold['evidence'])
    candidates={str(d['doc_id']) for d in task['documents']}
    return {**result,'gold_documents':sorted(expected),'candidate_documents':sorted(candidates),
            'retrieval_missed_documents':sorted(expected-candidates),
            'prediction_matches_gold_labels':_labels_match(gold,result['prediction']),
            'note':'retrieval gap and label mismatch are observations, not causal attribution'}


def _labels_match(gold,prediction):
    actual={d:e['label'] for d,e in prediction['evidence'].items()}
    expected={d:values[0]['label'] for d,values in gold['evidence'].items()}
    return actual==expected



def _case_score(args,root,gold,task,result):
    folder=root/str(task['id'])
    write_jsonl(folder/'gold.jsonl',[gold])
    write_jsonl(folder/'prediction.jsonl',[result['prediction']])
    metrics=score(args.evaluator,folder/'gold.jsonl',folder/'prediction.jsonl',folder/'metrics.json')
    return {**_diagnose(gold,task,result),'official_metrics':metrics}

if __name__=='__main__':
    main()
