from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.agents import AgentRegistry
from server.app import create_app
from server.kernel import ResearchKernel
from server.runtime_client import RuntimeRequestError


class FakeRuntime:
    def __init__(self):
        self.launches = []
        self.prompts = []
        self.sessions = {}
        self.validated = []
        self.kernel = None

    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def launch(self, spec, workspace, **values):
        session_id = f"session-{len(self.sessions) + 1}"
        self.launches.append((spec, workspace, values))
        self.sessions[session_id] = _trace(spec, workspace)
        return session_id

    async def inspect(self, session_id):
        return self.sessions[session_id]

    async def recognize(self, workspace):
        tools = ["read_resource", "graph_query", "report_projection", "publish_report",
                 "export_bibtex", "submit_observation"]
        return {
            "workspace": workspace,
            "endpoints": [],
            "skills": [],
            "tools": [{"id": tool, "status": "ready"} for tool in tools],
        }

    async def validate_agent(self, value):
        self.validated.append(value)
        if not value.get("name", "").strip():
            raise ValueError("agent name is required")
        return {"valid": True}

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
        "id: research-assistant\nname: 研究助手\nendpoint: codex\n"
        "model: test\ninstructions: test\n",
        encoding="utf-8",
    )
    (root / "pi-chat.yaml").write_text(
        "id: pi-chat\nname: Pi\nruntime:\n  id: pi\n  realm: container:runtime\n"
        "endpoint: pi\nmodel: default\ninstructions: chat\nskills: []\ntools: []\n",
        encoding="utf-8",
    )
    return AgentRegistry(root)


class PromptCommandKernel:
    def __init__(self):
        self.tags = []

    async def command(self, command):
        self.tags.append(command.tag)
        return prompt_events()

    async def query(self, _query):
        raise AssertionError("prompt must not query")


async def prompt_events():
    yield {"type": "delta", "text": "answer"}


def test_thread_points_to_runtime_session_and_pins_nodes(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    question = world.nodes(project["id"])[0]
    response = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"title": "轨道稳定性", "node_ids": [question["id"]]},
    )
    thread = response.json()
    assert response.status_code == 201
    assert thread["session_id"] == "session-1"
    assert thread["agent_id"] == "pi-chat"
    assert [node["id"] for node in thread["nodes"]] == [question["id"]]
    assert thread["runtime"]["messages"] == []
    assert runtime.launches[0][2]["session_name"] == "轨道稳定性"


def test_thread_detail_projects_persisted_publications_without_storage_fields(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=runtime, agents=_agents(tmp_path))
    client = TestClient(create_app(kernel))
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()
    publication = world.publish_report(project["id"], thread["id"], "Orbit", "artifact:private")
    report = world.save_report(project["id"], thread["id"], "V1", publication["id"])
    detail = client.get(f"/api/v1/threads/{thread['id']}").json()
    assert detail["report_publications"] == [{key: publication[key] for key in ("id", "thread_id", "title", "created_at")}]
    assert detail["reports"] == [{key: report[key] for key in ("id", "publication_id", "title", "created_at")}]
    assert "artifact_id" not in str(detail["report_publications"])
    assert "project_id" not in str(detail["report_publications"])


def test_thread_detail_recovers_report_records_in_stable_order(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects", runtime=runtime, agents=_agents(tmp_path))
    client = TestClient(create_app(kernel))
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()
    publications = _report_records(world, project, thread)
    _same_record_timestamps(world, "report_publications", publications)
    _same_record_timestamps(world, "reports", world.reports(project["id"], thread["id"]))
    details = [client.get(f"/api/v1/threads/{thread['id']}").json() for _ in range(2)]
    assert details[0]["report_publications"] == details[1]["report_publications"]
    assert [item["id"] for item in details[0]["report_publications"]] == sorted([item["id"] for item in publications], reverse=True)
    assert [item["id"] for item in details[0]["reports"]] == sorted([item["id"] for item in world.reports(project["id"], thread["id"])], reverse=True)


def _report_records(world, project, thread):
    tokens = iter(["a" * 24, "b" * 24, "c" * 24, "d" * 24])
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("server.world.secrets.token_hex", lambda _size: next(tokens))
        publications = [world.publish_report(project["id"], thread["id"], title, "artifact:private") for title in ("A", "B")]
        for title, publication in zip(("A", "B"), publications, strict=True):
            world.save_report(project["id"], thread["id"], title, publication["id"])
    return publications


def _same_record_timestamps(world, table, records):
    with world.db.connect() as connection:
        connection.executemany(f"UPDATE {table} SET created_at=? WHERE id=?", [("2026-08-26T00:00:00+00:00", record["id"]) for record in records])


def test_research_assistant_exposes_the_report_publication_tool():
    agent = AgentRegistry(Path(__file__).parents[1] / "agents").get("research-assistant")
    assert "research-report" in agent["skills"]
    assert "publish_report" in agent["tools"]


def test_pi_chat_uses_native_runtime_without_runtime_tools():
    agent = AgentRegistry(Path(__file__).parents[1] / "agents").get("pi-chat")
    assert agent["runtime"] == {"id": "pi", "realm": "container:runtime"}
    assert (agent["endpoint"], agent["model"]) == ("pi", "default")
    assert agent["skills"] == agent["tools"] == []


def test_prompt_stream_passes_pinned_node_ids(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
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


def test_prompt_route_uses_kernel_command():
    kernel = PromptCommandKernel()
    response = TestClient(create_app(kernel)).post(
        "/api/v1/threads/thread:test/prompts", json={"message": "analyze"}
    )

    assert "event: delta" in response.text
    assert kernel.tags == ["thread_prompt"]


def test_prompt_error_frame_carries_code_and_user_text(world, project, tmp_path):
    class SpecInvalidRuntime(FakeRuntime):
        async def prompt_stream(self, session_id, message, project_id, node_ids):
            raise RuntimeRequestError(
                "Additional properties are not allowed", "session_spec_invalid"
            )
            yield  # pragma: no cover

    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=SpecInvalidRuntime(),
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()

    response = client.post(
        f"/api/v1/threads/{thread['id']}/prompts", json={"message": "分析它"}
    )

    assert '"code": "session_spec_invalid"' in response.text
    assert "此对话的 Agent 配置已变更，需要重启会话" in response.text
    assert "Additional properties" not in response.text


def test_restart_replaces_pointer_and_keeps_old_trace(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()
    restarted = client.post(f"/api/v1/threads/{thread['id']}/restart").json()
    assert restarted["session_id"] == "session-2"
    assert "session-1" in runtime.sessions
    assert runtime.launches[1][2]["session_name"] == thread["title"]


def test_cross_project_node_cannot_be_pinned(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    other = world.create_project("other", tmp_path / "other", "Other?")
    foreign = world.nodes(other["id"])[0]
    response = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"node_ids": [foreign["id"]]},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("life_state", ["pending", "ghost"])
def test_unadmitted_node_cannot_enter_thread_context(
    world, project, tmp_path, life_state
):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    pending = world.create_node(project["id"], "direction", {"text": "unreviewed"})
    if life_state == "ghost":
        world.ghost_node(pending["id"], "rejected")

    created = client.post(
        f"/api/v1/projects/{project['id']}/threads",
        json={"node_ids": [pending["id"]]},
    )
    thread = client.post(f"/api/v1/projects/{project['id']}/threads", json={}).json()
    pinned = client.post(
        f"/api/v1/threads/{thread['id']}/nodes", json={"node_id": pending["id"]}
    )

    assert created.status_code == 400
    assert pinned.status_code == 400


def test_agent_registry_reads_and_updates_yaml(tmp_path):
    registry = _agents(tmp_path)
    agent = registry.get("research-assistant")
    agent["instructions"] = "只陈述可验证结论"
    assert registry.save(agent["id"], agent)["instructions"] == "只陈述可验证结论"


def test_agent_api_validates_before_registry_write(world, project, tmp_path):
    runtime = FakeRuntime()
    agents = _agents(tmp_path)
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=agents,
    )
    value = {**agents.get("research-assistant"), "name": ""}
    response = TestClient(create_app(kernel)).put(
        "/api/v1/agents/research-assistant",
        params={"project_id": project["id"]},
        json=value,
    )
    assert response.status_code == 400
    assert runtime.validated == [value]
    assert agents.get("research-assistant")["name"] == "研究助手"


def test_agent_api_creates_without_upserting(world, project, tmp_path):
    runtime = FakeRuntime()
    agents = _agents(tmp_path)
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", runtime=runtime, agents=agents
    )
    client = TestClient(create_app(kernel))
    value = {**agents.get("research-assistant"), "id": "proof-reviewer"}

    params = {"project_id": project["id"]}
    created = client.post("/api/v1/agents", params=params, json=value)
    duplicate = client.post(
        "/api/v1/agents", params=params, json={**value, "name": "覆盖"}
    )

    assert created.status_code == 201
    assert created.json() == value
    assert duplicate.status_code == 400
    assert agents.get("proof-reviewer")["name"] == "研究助手"
    assert runtime.validated == [value]


def test_agent_update_requires_existing_id(world, project, tmp_path):
    runtime = FakeRuntime()
    agents = _agents(tmp_path)
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", runtime=runtime, agents=agents
    )
    value = {**agents.get("research-assistant"), "id": "missing"}

    response = TestClient(create_app(kernel)).put(
        "/api/v1/agents/missing",
        params={"project_id": project["id"]},
        json=value,
    )

    assert response.status_code == 404
    assert not (agents.root / "missing.yaml").exists()
