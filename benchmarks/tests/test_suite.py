import json

import pytest

from benchmarks.suites.scifact import SciFact
from benchmarks.suites.scifact.protocol import write_jsonl


def suite(tmp_path):
    return SciFact(tmp_path,tmp_path/'archive',tmp_path/'source',tmp_path/'evaluator')


@pytest.mark.parametrize('ids',[[1],[1,1],[2,1]])
def test_aggregate_rejects_missing_duplicate_or_reordered_claims(tmp_path,ids):
    write_jsonl(tmp_path/'gold.jsonl',[{'id':1},{'id':2}])
    with pytest.raises(ValueError,match='Every selected claim'):
        suite(tmp_path)._aggregate(tmp_path,'baseline',[{'id':i} for i in ids])


def test_failed_case_is_preserved_in_official_predictions(tmp_path,monkeypatch):
    import benchmarks.suites.scifact.suite as module
    from benchmarks.suites.scifact.protocol import read_jsonl
    (tmp_path/'baseline').mkdir()
    write_jsonl(tmp_path/'gold.jsonl',[{'id':1},{'id':2}])
    cases=[{'id':i,'status':'runtime_failed','prediction':{'id':i,'evidence':{}},'seconds':1} for i in [1,2]]
    captured=[]
    def score(evaluator,gold,predictions,target):
        captured.extend(read_jsonl(predictions));return {'score':0}
    monkeypatch.setattr(module,'score',score)
    result=suite(tmp_path)._aggregate(tmp_path,'baseline',cases)
    assert result['total']==2 and result['completed']==0
    assert [row['id'] for row in captured]==[1,2]


def test_reference_is_only_consumed_by_scoring(tmp_path,monkeypatch):
    import benchmarks.suites.scifact.suite as module
    monkeypatch.setattr(module,'score',lambda *args:{'sentence_label_f1':0})
    task={'id':1,'documents':[]}
    execution={'status':'completed','answer':'{}','seconds':1}
    result=suite(tmp_path).evaluate(execution,task,{'id':1,'evidence':{}},tmp_path)
    assert result['status']=='invalid_output'
    assert result['prediction']=={'id':1,'evidence':{}}
