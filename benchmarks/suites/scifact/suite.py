"""SciFact data and scoring; execution belongs to the caller."""
from pathlib import Path
from types import SimpleNamespace

from .protocol import prepare, interpret, save, score, write_jsonl
from .report import report


class SciFact:
    def __init__(self, data, archive, source, evaluator):
        self.paths = {name:Path(value) for name,value in
                      [('data',data),('archive',archive),('source',source),('evaluator',evaluator)]}

    def prepare(self, output, split='train', limit=3, ids=None):
        if limit<1 or split not in {'train','dev'}:
            raise ValueError('Use train/dev and a positive sample limit')
        output.mkdir(parents=True,exist_ok=False)
        args=SimpleNamespace(**self.paths,split=split,limit=limit,ids=ids)
        references,tasks,verified=prepare(args,output)
        save(output/'protocol.json',{'split':split,'integrity':verified,'claim_ids':[t['id'] for t in tasks]})
        return tasks,references

    def evaluate(self, execution, task, reference, folder):
        if reference['id']!=task['id']:
            raise ValueError('Task and reference identity mismatch')
        result=interpret(execution,task)
        write_jsonl(folder/'gold.jsonl',[reference])
        write_jsonl(folder/'prediction.jsonl',[result['prediction']])
        metrics=score(self.paths['evaluator'],folder/'gold.jsonl',folder/'prediction.jsonl',folder/'metrics.json')
        result.update(official_metrics=metrics,**_diagnose(reference,task,result))
        save(folder/'result.json',result)
        return result

    def summarize(self, output, arms):
        summaries={arm:self._aggregate(output,arm,cases) for arm,cases in arms.items()}
        save(output/'summary.json',{'arms':summaries,'cost':None,
             'claim':'pilot only; no equal-token-budget causal comparison'})
        report(output)
        return summaries

    def _aggregate(self, output, arm, cases):
        from .scifact_integrity import read_jsonl
        expected=[row['id'] for row in read_jsonl(output/'gold.jsonl')]
        if [row['id'] for row in cases]!=expected:
            raise ValueError('Every selected claim must appear once in original order')
        root=output/arm
        write_jsonl(root/'predictions.jsonl',[row['prediction'] for row in cases])
        metrics=score(self.paths['evaluator'],output/'gold.jsonl',root/'predictions.jsonl',root/'metrics.json')
        save(root/'cases.json',cases)
        return {'metrics':metrics,'completed':sum(r['status']=='completed' for r in cases),
                'total':len(cases),'seconds':round(sum(r['seconds'] for r in cases),3)}


def _diagnose(gold,task,result):
    expected={d:values[0]['label'] for d,values in gold['evidence'].items()}
    actual={d:e['label'] for d,e in result['prediction']['evidence'].items()}
    candidates={str(d['doc_id']) for d in task['documents']}
    return {'gold_documents':sorted(expected),'candidate_documents':sorted(candidates),
            'retrieval_missed_documents':sorted(set(expected)-candidates),
            'prediction_matches_gold_labels':actual==expected,
            'note':'retrieval and label differences are observations, not causal attribution'}
