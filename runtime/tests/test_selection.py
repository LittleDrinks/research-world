from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from runtime.bridge import ToolBridge
from runtime.selection import selection_router
from runtime.server import _input_errors

VALUES = {'candidates':[{'id':'a','relevance':.9},{'id':'b','relevance':.85},{'id':'c','relevance':.8}],
          'similarities':{'a':{'b':.95,'c':.1},'b':{'a':.95,'c':.1},'c':{'a':.1,'b':.1}},'count':2,'diversity_weight':.7}


def client():
    app=FastAPI();_input_errors(app);app.include_router(selection_router());return TestClient(app)


def test_runtime_http_selection_returns_relevance_redundancy_and_scores():
    response=client().post('/api/v1/runtime/mmr',json=VALUES)
    assert response.status_code==200
    assert [s['id'] for s in response.json()['selected']]==['a','c']
    assert response.json()['steps'][1]['redundancy']==.1
    assert response.json()['steps'][1]['score']==pytest.approx(.73)


@pytest.mark.parametrize('patch',[{'count':4},{'count':True},{'diversity_weight':2.0},{'similarities':{}},
                                  {'candidates':[{'id':'a','relevance':2.0}]},{'candidates':[{'id':'a'}]}])
def test_invalid_selection_inputs_rejected(patch):
    assert client().post('/api/v1/runtime/mmr',json=VALUES|patch).status_code==422


@pytest.mark.asyncio
async def test_selected_agent_tool_uses_same_algorithm_without_model_calls():
    bridge=ToolBridge();token=bridge.bind(SimpleNamespace(agent_snapshot={'tools':['mmr']}))
    assert (await bridge.invoke(token,'mmr',VALUES))['steps'][1]['id']=='c'
    other=bridge.bind(SimpleNamespace(agent_snapshot={'tools':[]}))
    with pytest.raises(PermissionError):await bridge.invoke(other,'mmr',VALUES)
