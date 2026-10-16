import pytest
from .protocol import _task, prediction


def test_model_input_does_not_include_gold_or_citations():
    task=_task({'id':1,'claim':'Claim'},[42],{42:{'title':'Study','abstract':['Sentence']}})
    assert set(task)=={'id','claim','documents'}
    assert task['documents'][0]['sentences']=={0:'Sentence'}


def test_prediction_accepts_insufficient_evidence():
    assert prediction('{"id":1,"evidence":{}}',{'id':1,'documents':[]})['evidence']=={}


@pytest.mark.parametrize('evidence',[
    {'99':{'label':'SUPPORT','sentences':[0]}},
    {'42':{'label':'SUPPORT','sentences':[1]}},
    {'42':{'label':'SUPPORT','sentences':[True]}},
    {'42':{'label':'SUPPORT','sentences':[0,0]}},
    {'42':{'label':'REFUTES','sentences':[0]}},
])
def test_prediction_rejects_outside_evidence(evidence):
    import json
    task={'id':1,'documents':[{'doc_id':42,'sentences':{0:'Evidence'}}]}
    with pytest.raises(ValueError):prediction(json.dumps({'id':1,'evidence':evidence}),task)
