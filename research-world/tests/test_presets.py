import pytest
from fastapi.testclient import TestClient

from server.agents import AgentRegistry
from server.app import create_app
from server.kernel import ResearchKernel


class FakeRuntime:
    def __init__(self, catalog):
        self.catalog = catalog
        self.recognized = []
        self.validated = []
        self.validated_workspaces = []

    def bind_kernel(self, kernel):
        self.kernel = kernel

    async def recognize(self, workspace):
        self.recognized.append(workspace)
        return self.catalog

    async def validate_agent(self, value, workspace):
        self.validated.append(value)
        self.validated_workspaces.append(workspace)
        runtime = value.get("runtime")
        endpoint = next((item for item in self.catalog["endpoints"] if item["id"] == value.get("endpoint")), None)
        if runtime != {"id": "codex", "realm": "container:runtime"}:
            raise ValueError("runtime is not available")
        if not endpoint or not endpoint["available"] or runtime not in endpoint["runtime_refs"]:
            raise ValueError("endpoint is not available")
        if not any(item["endpoint"] == value.get("endpoint") and item["id"] == value.get("model") for item in self.catalog["models"]):
            raise ValueError("model is not available")
        tool = next((item for item in self.catalog["tools"] if item["id"] in value.get("tools", [])), None)
        if tool and tool["status"] != "ready":
            raise ValueError(f"tool unavailable: {tool['id']} ({tool['status']} / {tool.get('reason', '')})")
        if value.get("tools"):
            raise ValueError("codex cannot expose selected Tool schemas")
        return {"valid": True}


def catalog(lean4_status="ready", lean4_reason=None):
    tool = _tool(lean4_status, lean4_reason)
    codex = {"id": "codex", "realm": "container:runtime"}
    return {
        "runtimes": [{**codex, "status": "ready"}],
        "endpoints": [{"id": "openai-compatible", "name": "OpenAI", "available": True, "runtime_refs": [codex]}],
        "models": [{"id": "qwen-test", "endpoint": "openai-compatible"}],
        "skills": [],
        "tools": [{"name": "Lean 4", **tool}],
        "presets": [_preset(tool)],
    }


def _tool(status, reason=None):
    return {"id": "lean4", "status": status, **({"reason": reason} if reason else {})}


def _preset(tool):
    return {
        "id": "math-proof",
        "name": "数学证明",
        "description": "形式化证明 Agent 推荐配置",
        "spec": {**_agent(["lean4"]), "skills": []},
        "tools": [tool],
    }


def _agent(tools):
    return {
        "id": "math-proof", "name": "数学证明助手",
        "runtime": {"id": "codex", "realm": "container:runtime"},
        "endpoint": "openai-compatible", "model": "qwen-test",
        "instructions": "用 Lean4 验证证明。", "tools": tools,
    }


def make_client(world, project, tmp_path, lean4_status="ready", lean4_reason=None):
    runtime = FakeRuntime(catalog(lean4_status, lean4_reason))
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=AgentRegistry(tmp_path / "agents"),
    )
    return TestClient(create_app(kernel)), runtime


def draft_url(project):
    return f"/api/v1/projects/{project['id']}/agent-drafts"


def test_draft_builds_spec_from_preset_and_catalog_defaults(world, project, tmp_path):
    client, _runtime = make_client(world, project, tmp_path)

    response = client.post(draft_url(project), json={"preset_id": "math-proof"})

    assert response.status_code == 201
    draft = response.json()
    assert draft["preset_id"] == "math-proof"
    assert draft["reason"] == "形式化证明 Agent 推荐配置"
    assert draft["spec"]["endpoint"] == "openai-compatible"
    assert draft["spec"]["model"] == "qwen-test"
    assert draft["spec"]["runtime"] == {"id": "codex", "realm": "container:runtime"}
    assert draft["spec"]["tools"] == ["lean4"]
    assert draft["spec"]["options"]["sandbox"] == "read-only"
    assert draft["confirmable"] is True
    assert draft["issues"] == []


def test_draft_marks_unavailable_tool_as_blocking(world, project, tmp_path):
    client, _runtime = make_client(
        world, project, tmp_path, "unavailable", "not_installed"
    )

    response = client.post(draft_url(project), json={"preset_id": "math-proof"})

    draft = response.json()
    assert draft["confirmable"] is False
    assert draft["issues"] == ["tool unavailable: lean4 (unavailable / not_installed)"]


def test_draft_rejects_unknown_preset(world, project, tmp_path):
    client, _runtime = make_client(world, project, tmp_path)

    response = client.post(draft_url(project), json={"preset_id": "ghost"})

    assert response.status_code == 400
    assert "unknown preset: ghost" in response.json()["detail"]


def test_create_blocks_unavailable_tool_without_writing(world, project, tmp_path):
    client, runtime = make_client(
        world, project, tmp_path, "unavailable", "not_installed"
    )
    value = _agent(["lean4"])

    response = client.post(
        "/api/v1/agents", params={"project_id": project["id"]}, json=value
    )

    assert response.status_code == 400
    assert "tool unavailable: lean4 (unavailable / not_installed)" in response.json()["detail"]
    assert runtime.validated == [value]
    assert runtime.validated_workspaces == [project["root"]]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_create_blocks_codex_tools_without_writing(world, project, tmp_path):
    client, _runtime = make_client(world, project, tmp_path)
    value = _agent(["lean4"])

    response = client.post(
        "/api/v1/agents", params={"project_id": project["id"]}, json=value
    )

    assert response.status_code == 400
    assert "codex cannot expose selected Tool schemas" in response.json()["detail"]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_create_blocks_missing_runtime_without_writing(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    value = _agent([])
    value.pop("runtime")

    response = client.post("/api/v1/agents", params={"project_id": project["id"]}, json=value)

    assert response.status_code == 400
    assert "runtime is not available" in response.json()["detail"]
    assert runtime.validated_workspaces == [project["root"]]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_create_blocks_unknown_runtime_without_writing(world, project, tmp_path):
    client, _runtime = make_client(world, project, tmp_path)
    value = {**_agent([]), "runtime": {"id": "codex", "realm": "legacy:runtime"}}

    response = client.post("/api/v1/agents", params={"project_id": project["id"]}, json=value)

    assert response.status_code == 400
    assert "runtime is not available" in response.json()["detail"]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [("endpoint", "missing", "endpoint is not available"), ("model", "missing", "model is not available")],
)
def test_create_blocks_invalid_endpoint_or_model_without_writing(world, project, tmp_path, field, value, message):
    client, _runtime = make_client(world, project, tmp_path)
    payload = {**_agent([]), field: value}

    response = client.post("/api/v1/agents", params={"project_id": project["id"]}, json=payload)

    assert response.status_code == 400
    assert message in response.json()["detail"]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_create_blocks_unavailable_or_incompatible_endpoint_without_writing(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    runtime.catalog["endpoints"][0]["available"] = False
    value = _agent([])

    response = client.post("/api/v1/agents", params={"project_id": project["id"]}, json=value)

    assert response.status_code == 400
    assert "endpoint is not available" in response.json()["detail"]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_create_blocks_incompatible_endpoint_without_writing(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    runtime.catalog["endpoints"][0]["runtime_refs"] = []
    value = _agent([])

    response = client.post("/api/v1/agents", params={"project_id": project["id"]}, json=value)

    assert response.status_code == 400
    assert "endpoint is not available" in response.json()["detail"]
    with pytest.raises(KeyError):
        AgentRegistry(tmp_path / "agents").get("math-proof")


def test_saved_profile_does_not_follow_preset_changes(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    params = {"project_id": project["id"]}

    response = client.post("/api/v1/agents", params=params, json=_agent([]))
    runtime.catalog["presets"][0]["spec"]["tools"].clear()

    assert response.status_code == 201
    saved = AgentRegistry(tmp_path / "agents").get("math-proof")
    assert saved["tools"] == []


def test_create_requires_project_context(world, tmp_path):
    runtime = FakeRuntime(catalog("unavailable"))
    kernel = ResearchKernel(
        world,
        projects_root=tmp_path / "projects",
        runtime=runtime,
        agents=AgentRegistry(tmp_path / "agents"),
    )
    client = TestClient(create_app(kernel))
    value = _agent(["lean4"])

    response = client.post("/api/v1/agents", json=value)

    assert response.status_code == 422


def test_update_blocks_unavailable_tool_without_writing(world, project, tmp_path):
    client, runtime = make_client(
        world, project, tmp_path, "unavailable", "not_installed"
    )
    registry = AgentRegistry(tmp_path / "agents")
    value = _agent([])
    registry.create(value)

    response = client.put(
        "/api/v1/agents/math-proof",
        params={"project_id": project["id"]},
        json={**value, "tools": ["lean4"]},
    )

    assert response.status_code == 400
    assert "tool unavailable: lean4 (unavailable / not_installed)" in response.json()["detail"]
    assert runtime.validated_workspaces == [project["root"]]
    assert registry.get("math-proof")["tools"] == []


def test_update_blocks_unknown_runtime_without_writing(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    registry = AgentRegistry(tmp_path / "agents")
    original = _agent([])
    registry.create(original)
    value = {**original, "runtime": {"id": "codex", "realm": "legacy:runtime"}}

    response = client.put(
        "/api/v1/agents/math-proof", params={"project_id": project["id"]}, json=value
    )

    assert response.status_code == 400
    assert "runtime is not available" in response.json()["detail"]
    assert runtime.validated_workspaces == [project["root"]]
    assert registry.get("math-proof") == original


def test_update_requires_project_context(world, project, tmp_path):
    client, runtime = make_client(world, project, tmp_path)
    value = _agent([])
    AgentRegistry(tmp_path / "agents").create(value)

    response = client.put("/api/v1/agents/math-proof", json=value)

    assert response.status_code == 422
    assert runtime.recognized == []
