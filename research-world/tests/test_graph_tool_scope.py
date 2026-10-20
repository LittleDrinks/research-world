import httpx
import pytest
from fastapi import FastAPI

from runtime.adapter import TurnRequest
from runtime.bridge import ToolBridge
from server.kernel_http import kernel_graph_router
from server.kernel_interface import create_kernel


@pytest.fixture
def graph_bridge(tmp_path, monkeypatch):
    kernel = create_kernel(tmp_path / 'kernel.db', tmp_path / 'artifacts')
    project = kernel.create_project('Orbit', 'Why?')
    for text in ['radiation', 'integration', 'initial conditions']:
        kernel.record(project.id, 'direction', {'text': text})
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))
    client = httpx.AsyncClient
    monkeypatch.setenv('CONTROL_URL', 'http://control')
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: client(transport=httpx.ASGITransport(app=app), **kw))
    bridge = ToolBridge()
    request = TurnRequest('run', 'turn', 'message', 'summarize', (),
                          {'tools': ['graph'], 'project_id': project.id, 'adapter': 'pi'}, None)
    return bridge, bridge.bind(request), project.id


@pytest.mark.asyncio
async def test_actual_tool_query_keeps_project_totals_and_literal_empty_result(graph_bridge):
    bridge, token, project = graph_bridge
    result = await bridge.invoke(token, 'graph', {'query': '当前研究项目所有对象与关系'})
    assert result['records'] == []
    assert result['project_summary']['project_id'] == project
    assert result['project_summary']['records'] == 3
    assert result['selection']['matched_records'] == 0


@pytest.mark.asyncio
async def test_tool_overview_obeys_limit_and_session_project(graph_bridge):
    bridge, token, project = graph_bridge
    result = await bridge.invoke(token, 'graph', {'limit': 1, 'project_id': 'foreign'})
    assert len(result['records']) == 1
    assert result['project_summary']['project_id'] == project
    assert result['project_summary']['records'] == 3
    assert result['selection']['truncated'] is True
