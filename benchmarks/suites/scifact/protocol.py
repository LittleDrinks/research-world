import json
import subprocess
import sys
import tarfile
from pathlib import Path

from benchmarks.suites.scifact.scifact_integrity import read_jsonl, verify
from benchmarks.adapters.research_world import save

BASE_INSTRUCTIONS = ('Verify the scientific claim against ONLY the supplied retrieved abstracts. '
    'Return one JSON object, no markdown: {"id": CLAIM_ID, "evidence": {"DOC_ID": '
    '{"label": "SUPPORT" or "CONTRADICT", "sentences": [zero-based indices]}}}. '
    'Use evidence={} for insufficient evidence. Select only necessary sentences, but include a complete rationale even if it needs more than three. '
    'A valid evidence set must cover the complete claim, not just shared terms. '
    'Never invent documents or sentence indices. Do not access external information.')
RESEARCH_INSTRUCTIONS = (' First use record once to save a concise provisional direction with the proposed verification and evidence indices, without copying full abstracts into the graph. '
    'Then delegate exactly one independent review, passing the claim and ALL supplied abstracts '
    'verbatim to that fresh Agent, plus your proposed answer. The reviewer must not access '
    'external sources. Use its feedback to finalize the requested JSON; do not return a report.')


def prepare(args, output):
    verified = verify(args.data, args.archive, args.source, args.evaluator)
    _verify_files(args)
    _verify_scorer(args.evaluator, output)
    rows = read_jsonl(args.data / f'claims_{args.split}.jsonl')
    selected = [r for r in rows if r['id'] in args.ids] if args.ids else rows[:args.limit]
    if not selected or (args.ids and {r['id'] for r in selected} != set(args.ids)):
        raise ValueError('Requested claim ids are missing')
    write_jsonl(output / 'gold.jsonl', selected)
    public = [{'id':r['id'], 'claim':r['claim']} for r in selected]
    write_jsonl(output / 'retrieval-test.jsonl', public)
    retrieval = _retrieve(args, output)
    corpus = {r['doc_id']:r for r in read_jsonl(args.data / 'corpus.jsonl')}
    tasks = [_task(r, retrieval[r['id']], corpus) for r in public]
    write_jsonl(output / 'tasks.jsonl', tasks)
    return selected, tasks, verified


def _retrieve(args, output):
    script = args.source / 'verisci/inference/abstract_retrieval/tfidf.py'
    command = [sys.executable, str(script), '--corpus', str(args.data / 'corpus.jsonl'),
               '--dataset', str(output / 'retrieval-test.jsonl'), '--k', '3',
               '--min-gram', '1', '--max-gram', '2', '--output', str(output / 'retrieval.jsonl')]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return {r['claim_id']:r['doc_ids'] for r in read_jsonl(output / 'retrieval.jsonl')}


def _task(claim, ids, corpus):
    documents = [{'doc_id':doc_id,'title':corpus[doc_id]['title'],
                  'sentences':dict(enumerate(corpus[doc_id]['abstract']))} for doc_id in ids]
    return {'id':claim['id'],'claim':claim['claim'],'documents':documents}


def prediction(text, task):
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {'id','evidence'} or type(value['id']) is not int or value['id'] != task['id']:
        raise ValueError('Invalid prediction identity or fields')
    if not isinstance(value['evidence'], dict):
        raise ValueError('Evidence must be an object')
    documents = {str(d['doc_id']):d for d in task['documents']}
    for doc_id, evidence in value['evidence'].items():
        _validate_evidence(doc_id, evidence, documents)
    return value


def _validate_evidence(doc_id, value, documents):
    if doc_id not in documents or not isinstance(value,dict) or set(value) != {'label','sentences'}:
        raise ValueError('Evidence document or fields invalid')
    sentences = value['sentences']
    if value['label'] not in {'SUPPORT','CONTRADICT'} or not isinstance(sentences,list):
        raise ValueError('Evidence label or sentences invalid')
    if not sentences or len(set(sentences)) != len(sentences):
        raise ValueError('Need distinct rationale sentences')
    if any(type(i) is not int or not 0 <= i < len(documents[doc_id]['sentences']) for i in sentences):
        raise ValueError('Sentence index outside candidate abstract')


def score(evaluator, gold, predictions, target):
    subprocess.run([sys.executable,str(evaluator / 'evaluator/eval.py'), '--labels_file',str(gold),
                    '--preds_file',str(predictions), '--metrics_output_file',str(target), '--verbose'],
                   check=True, capture_output=True, text=True)
    return json.loads(target.read_text())


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))


def _verify_files(args):
    with tarfile.open(args.archive) as archive:
        for name in ['corpus.jsonl','claims_train.jsonl','claims_dev.jsonl','claims_test.jsonl']:
            original=archive.extractfile('data/'+name).read()
            if original != (args.data/name).read_bytes():
                raise ValueError('Extracted data differs from pinned archive: '+name)
    for root in [args.source,args.evaluator]:
        if subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True).strip():
            raise ValueError('Official source must be clean')


def _verify_scorer(evaluator, output):
    fixture=evaluator/'fixture'
    actual=score(evaluator,fixture/'gold_small.jsonl',fixture/'predictions_small.jsonl',output/'scorer-check.json')
    expected=json.loads((fixture/'expected_metrics_small.json').read_text())
    if actual!=expected:
        raise ValueError('Official scorer fixture mismatch')


def agent_profile(arm, run_id, model, thinking):
    agent_id=f'scifact-{run_id}-{arm}'
    return {'id':agent_id,'name':agent_id,'model':model,'thinking':thinking,
            'instructions':BASE_INSTRUCTIONS+(RESEARCH_INSTRUCTIONS if arm=='research' else ''),
            'tools':[] if arm=='baseline' else ['graph','record','connect','delegate'],'skills':[]}


def interpret(execution, task):
    result={**execution,'id':task['id'],'prediction':{'id':task['id'],'evidence':{}}}
    if execution['status']!='completed':
        return result
    try:
        result['prediction']=prediction(execution['answer'],task)
    except (ValueError,TypeError,KeyError):
        result['status']='invalid_output'
    return result
