from __future__ import annotations

from fastapi.testclient import TestClient

from server.agents import AgentRegistry
from server.app import create_app


class FakeRuntime:
    def __init__(self):
        self.launches = []
        self.prompts = []
        self.sessions = {}

    async def launch(self, spec, workspace, **values):
        session_id = f"session-{len(self.sessions) + 1}"
        self.launches.append((spec, workspace, values))
        self.sessions[session_id] = _trace(spec, workspace)
        return session_id

    async def inspect(self, session_id):
        return self.sessions[session_id]

    async def recognize(self, workspace):
        return {"workspace": workspace, "skills": [], "mcp_servers": []}

    async def prompt_stream(self, session_id, message, project_id, node_ids):
        self.prompts.append((session_id, message, project_id, node_ids))
        self.sessions[session_id]["messages"].extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "答复"},
            ]
        )
        yield {"type": "delta", "text": "答复"}
        yield {"type": "done", "stop_reason": "end_turn"}


def _trace(spec, workspace):
    return {
        "session": {"agent_spec": spec, "workspace": workspace},
        "status": "active",
        "messages": [],
        "turns": [],
        "events": [],
    }


def _agents(tmp_path):
    root = tmp_path / "agents"
    root.mkdir()
    (root / "research-assistant.yaml").write_text(
        "id: research-assistant\nname: 研究助手\nruntime: codex\n"
        "model: test\ninstructions: test\n",
        encoding="utf-8",
    )
    return AgentRegistry(root)


def test_thread_points_to_runtime_session_and_pins_nodes(world, project, tmp_path):
    runtime = FakeRuntime()
    client = TestClient(create_app(world, runtime, _agents(tmp_path)))
    question = world.nodes(project["id"])[0]
    response = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"title": "轨道稳定性", "node_ids": [question["id"]]},
    )
    thread = response.json()
    assert response.status_code == 201
    assert thread["session_id"] == "session-1"
    assert [node["id"] for node in thread["nodes"]] == [question["id"]]
    assert thread["runtime"]["messages"] == []


def test_prompt_stream_passes_pinned_node_ids(world, project, tmp_path):
    runtime = FakeRuntime()
    client = TestClient(create_app(world, runtime, _agents(tmp_path)))
    question = world.nodes(project["id"])[0]
    thread = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"node_ids": [question["id"]]},
    ).json()
    response = client.post(
        f"/api/v1/threads/{thread['id']}/prompts", json={"message": "分析它"}
    )
    assert 'event: delta\ndata: {"text": "答复"}' in response.text
    assert runtime.prompts[0][3] == [question["id"]]


def test_restart_replaces_pointer_and_keeps_old_trace(world, project, tmp_path):
    runtime = FakeRuntime()
    client = TestClient(create_app(world, runtime, _agents(tmp_path)))
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()
    restarted = client.post(f"/api/v1/threads/{thread['id']}/restart").json()
    assert restarted["session_id"] == "session-2"
    assert "session-1" in runtime.sessions


def test_cross_project_node_cannot_be_pinned(world, project, tmp_path):
    runtime = FakeRuntime()
    client = TestClient(create_app(world, runtime, _agents(tmp_path)))
    other = world.create_project("other", tmp_path / "other", "Other?")
    foreign = world.nodes(other["id"])[0]
    response = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"node_ids": [foreign["id"]]},
    )
    assert response.status_code == 400


def test_agent_registry_reads_and_updates_yaml(tmp_path):
    registry = _agents(tmp_path)
    agent = registry.get("research-assistant")
    agent["instructions"] = "只陈述可验证结论"
    assert registry.save(agent["id"], agent)["instructions"] == "只陈述可验证结论"
