from __future__ import annotations

from fastapi.testclient import TestClient

from server.agents import AgentRegistry
from server.app import create_app
from server.kernel import ResearchKernel


class FakeRuntime:
    def __init__(self):
        self.launches = []
        self.prompts = []
        self.sessions = {}
        self.connectors = []
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
        return {
            "workspace": workspace,
            "endpoints": [],
            "skills": [],
            "connectors": self.connectors,
        }

    async def register_connector(self, value):
        self.connectors.append(value)
        return value

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
    assert [node["id"] for node in thread["nodes"]] == [question["id"]]
    assert thread["runtime"]["messages"] == []


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


def test_pending_node_cannot_enter_thread_context(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    pending = world.create_node(project["id"], "direction", {"text": "unreviewed"})

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


def test_agent_api_validates_before_registry_write(world, tmp_path):
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
        "/api/v1/agents/research-assistant", json=value
    )
    assert response.status_code == 400
    assert runtime.validated == [value]
    assert agents.get("research-assistant")["name"] == "研究助手"


def test_connector_registration_is_delegated_to_runtime(world, project, tmp_path):
    runtime = FakeRuntime()
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=_agents(tmp_path),
    )
    client = TestClient(create_app(kernel))
    connector = {"id": "lean4", "transport": "stdio", "command": "lean-mcp"}

    response = client.post("/api/v1/runtime/connectors", json=connector)

    assert response.status_code == 201
    assert runtime.connectors == [connector]
