import pytest
from .protocol import _task, prediction


def test_model_input_does_not_include_gold_or_citations():
    task=_task({'id':1,'claim':'Claim','evidence':{'leak':'gold'},'cited_doc_ids':[99]},[42],{42:{'title':'Study','abstract':['Sentence']}})
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


def test_boolean_claim_id_is_invalid():
    with pytest.raises(ValueError):prediction('{"id":true,"evidence":{}}',{'id':1,'documents':[]})


def test_complete_rationale_can_exceed_three_sentences():
    task={'id':1,'documents':[{'doc_id':42,'sentences':dict(enumerate(['a','b','c','d']))}]}
    value=prediction('{"id":1,"evidence":{"42":{"label":"SUPPORT","sentences":[0,1,2,3]}}}',task)
    assert value['evidence']['42']['sentences']==[0,1,2,3]
