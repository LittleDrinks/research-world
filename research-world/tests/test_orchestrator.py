from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from server.app import create_app
from server.orchestrator import OrchestratorAgent, WorkflowManager, validate_decision


class FakeAgent:
    def __init__(self, action=None, count=8, select=4, deltas=("可以按当前思路推进。",)):
        self.value = {"action": action, "count": count, "select": select}
        self.deltas = list(deltas)
        self.call = None

    def decide(self, node, messages, message, actions):
        self.call = (node, messages, message, actions)
        return self.value

    def reply(self, node, messages, message, decision):
        return iter(self.deltas)


class FakeHarness:
    def __init__(self, value):
        self.value = value
        self.call = None

    def json(self, role, instruction, payload):
        self.call = (role, instruction, payload)
        return self.value


class FailingAgent:
    def decide(self, node, messages, message, actions):
        raise RuntimeError("model unavailable")


def test_question_instruction_starts_brainstorm(world, project):
    question = world.nodes(project["id"])[0]
    agent = FakeAgent("brainstorm", count=5, select=2)
    events = list(WorkflowManager(world, agent).assist(project["id"], question["id"],
                                                       "生成五个方向，只保留两个"))
    assert [event["event"] for event in events] == ["user", "delta", "done"]
    reply = events[-1]["data"]
    assert reply["workflow"]["kind"] == "brainstorm"
    assert reply["workflow"]["payload"] == {"instruction": "生成五个方向，只保留两个",
                                            "mode": "brainstorm", "count": 5, "select": 2}
    assert agent.call[3] == ["brainstorm"]
    assert reply["content"].startswith("可以按当前思路推进。")
    assert "已按你的要求创建工作流" in reply["content"]
    assert len(world.messages(project["id"], question["id"])) == 2


def test_discussion_does_not_start_workflow(world, project):
    direction = world.create_node(project["id"], "direction", {"text": "Candidate"})
    events = list(WorkflowManager(world, FakeAgent()).assist(project["id"], direction["id"],
                                                             "解释一下这个方向"))
    reply = events[-1]["data"]
    assert reply["workflow"] is None
    assert reply["actions"] == ["research"]
    assert reply["content"] == "可以按当前思路推进。"
    assert world.workflows(project["id"]) == []


def test_failed_decide_does_not_persist_partial_message(world, project):
    question = world.nodes(project["id"])[0]
    with pytest.raises(RuntimeError, match="model unavailable"):
        list(WorkflowManager(world, FailingAgent()).assist(project["id"], question["id"], "开始研究"))
    assert world.messages(project["id"], question["id"]) == []


def test_orchestrator_decide_passes_conversation_and_validates_action():
    harness = FakeHarness({"action": "research", "count": 8, "select": 4})
    node = {"id": "node:d", "kind": "direction", "life_state": "admitted",
            "direction_status": "proposed", "payload": {"text": "轨道稳定"}, "rebuttal": None}
    result = OrchestratorAgent(harness).decide(node, [{"role": "user", "content": "先讨论"}],
                                               "开始实验", ["research"])
    assert result == {"action": "research", "count": 8, "select": 4}
    assert harness.call[2]["conversation"] == [{"role": "user", "content": "先讨论"}]


def test_decide_protocol_accepts_null_action_without_content():
    result = validate_decision({"action": None, "count": 8, "select": 4}, ["brainstorm"])
    assert result == {"action": None, "count": 8, "select": 4}


def test_decide_protocol_validates_action_and_numbers():
    with pytest.raises(ValueError, match="unavailable action"):
        validate_decision({"action": "launch", "count": 8, "select": 4}, ["brainstorm"])
    with pytest.raises(ValueError, match="integer count"):
        validate_decision({"action": None, "count": "8", "select": 4}, ["brainstorm"])
    with pytest.raises(ValueError, match="1 <= select"):
        validate_decision({"action": None, "count": 2, "select": 4}, ["brainstorm"])


def test_materializing_draft_clears_conversation(world, project):
    question = world.nodes(project["id"])[0]
    manager = WorkflowManager(world, FakeAgent())
    list(manager.assist(project["id"], question["id"], "记录这个方向"))
    node = manager.materialize(project["id"], question["id"], "direction", {"text": "Resonance"})
    assert node["parent_id"] == question["id"]
    assert world.messages(project["id"], question["id"]) == []


def test_new_conversation_clears_current_node_messages(world, project):
    question = world.nodes(project["id"])[0]
    world.add_message(project["id"], question["id"], "user", "旧草稿")
    response = TestClient(create_app(world)).delete(
        f"/api/v1/projects/{project['id']}/messages", params={"node_id": question["id"]})
    assert response.status_code == 204
    assert world.messages(project["id"], question["id"]) == []


HARNESS = "http://harness:8098"
DECIDE_TURN = {"id": "t1", "status": "completed",
               "result_text": '{"action": null, "count": 8, "select": 4}', "usage": {}}


def mock_decide_then_reply(stream_response):
    respx.post(f"{HARNESS}/sessions").mock(side_effect=[
        httpx.Response(200, json={"id": "s1"}), httpx.Response(200, json={"id": "s2"})])
    respx.post(f"{HARNESS}/sessions/s1/turns").mock(
        return_value=httpx.Response(200, json=DECIDE_TURN))
    respx.post(f"{HARNESS}/sessions/s2/turns/stream").mock(return_value=stream_response)


def parse_frames(body: str) -> list[tuple[str, dict]]:
    return [parse_frame(frame) for frame in body.split("\n\n") if frame]


def parse_frame(frame: str) -> tuple[str, dict]:
    event_line, data_line = frame.split("\n", 1)
    return event_line[len("event: "):], json.loads(data_line[len("data: "):])


def post_message(client, project_id, node_id, message="聊聊") -> str:
    with client.stream("POST", f"/api/v1/projects/{project_id}/messages",
                       json={"node_id": node_id, "message": message}) as response:
        assert response.status_code == 200
        return "".join(response.iter_text())


@respx.mock
def test_messages_endpoint_streams_reply_events(world, project):
    question = world.nodes(project["id"])[0]
    reply = ''.join('data: {"delta": "%s"}\n\n' % delta for delta in ("可以", "推进"))
    reply += 'data: {"done": true, "turn": {"status": "completed"}}\n\n'
    mock_decide_then_reply(httpx.Response(200, text=reply))
    body = post_message(TestClient(create_app(world)), project["id"], question["id"])
    events = parse_frames(body)
    assert [name for name, _ in events] == ["user", "delta", "delta", "done"]
    assert events[3][1]["content"] == "可以推进"
    saved = world.messages(project["id"], question["id"])
    assert [message["role"] for message in saved] == ["user", "assistant"]
    assert saved[1]["content"] == "可以推进"


@respx.mock
def test_messages_endpoint_relay_error_event(world, project):
    question = world.nodes(project["id"])[0]
    mock_decide_then_reply(httpx.Response(500, text="boom"))
    body = post_message(TestClient(create_app(world)), project["id"], question["id"])
    assert "event: error" in body
    saved = world.messages(project["id"], question["id"])
    assert [message["role"] for message in saved] == ["user"]
