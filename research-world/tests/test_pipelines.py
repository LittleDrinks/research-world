from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.kernel import ResearchKernel
from server.pipelines import PipelineRegistry

SCHEMA = Path(__file__).parents[1] / "schemas" / "pipeline.schema.json"


def registry(tmp_path):
    root = tmp_path / "pipelines"
    root.mkdir()
    return PipelineRegistry(root, SCHEMA)


def spec(pipeline_id="custom"):
    return {
        "id": pipeline_id,
        "name": "Custom",
        "stages": [
            {
                "id": "generate",
                "type": "prompt",
                "prompt": "generate-directions",
                "agent": "research-assistant",
            }
        ],
    }


def direction_stages():
    return [
        {
            "id": "deduplicate",
            "type": "tool",
            "tool": "deduplicate-directions",
            "policy": "cosine-threshold",
        },
        {
            "id": "select",
            "type": "tool",
            "tool": "select-directions",
            "policy": "mmr",
        },
    ]


def direction_review(approve="admit"):
    return {
        "id": "review",
        "type": "prompt",
        "prompt": "review-directions",
        "agent": "reviewer",
        "repeat": 2,
        "policy": "unanimous-review",
        "on": {
            "approve": {"action": approve},
            "reject": {"action": "ghost"},
            "conflict": {"action": "wait_human"},
        },
    }


def test_registry_accepts_arbitrary_pipeline_ids(tmp_path):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    assert pipelines.get("custom")["stages"][0]["prompt"] == "generate-directions"


def test_registry_rejects_invalid_prompt_stage(tmp_path):
    value = spec()
    value["stages"] = [
        {"id": "draft", "type": "prompt", "prompt": "generate-directions"}
    ]
    with pytest.raises(ValueError, match="agent"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_unknown_primitive(tmp_path):
    value = spec()
    value["stages"][0]["prompt"] = "unknown"
    with pytest.raises(ValueError, match="unknown stage primitive"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_unimplemented_spawn(tmp_path):
    value = spec()
    value["stages"] = [
        {
            "id": "child",
            "type": "spawn",
            "pipeline": "research",
        }
    ]
    with pytest.raises(ValueError, match="unsupported stage type"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_invalid_on_target(tmp_path):
    value = spec()
    value["stages"][0]["on"] = {"next": {"next": "missing"}}
    with pytest.raises(ValueError, match="unknown next stage"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_exit_with_action_and_next(tmp_path):
    value = spec()
    value["stages"][0]["on"] = {"next": {"action": "admit", "next": "generate"}}
    with pytest.raises(ValueError, match="exactly one action or next"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_unimplemented_exit_action(tmp_path):
    value = spec()
    value["stages"][0]["on"] = {"next": {"action": "admit"}}
    with pytest.raises(ValueError, match="requires action None"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_review_with_wrong_action(tmp_path):
    value = spec()
    value["stages"].extend([*direction_stages(), direction_review("ghost")])
    with pytest.raises(ValueError, match="requires action admit"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_route_that_skips_required_value(tmp_path):
    value = spec()
    value["stages"][0]["on"] = {"next": {"next": "select"}}
    value["stages"].extend(direction_stages())
    with pytest.raises(ValueError, match="route to select misses stage values: pool"):
        registry(tmp_path).save("custom", value)


def test_registry_rejects_missing_stage_input(tmp_path):
    value = spec()
    value["stages"] = [
        {
            "id": "select",
            "type": "tool",
            "tool": "select-directions",
            "policy": {"name": "mmr", "params": {"weight": 0.2}},
        }
    ]
    with pytest.raises(ValueError, match="requires stage values: pool"):
        registry(tmp_path).save("custom", value)


def test_run_keeps_definition_snapshot(world, project):
    value = spec()
    run = world.create_run(project["id"], world.nodes(project["id"])[0]["id"], value)
    value["name"] = "Changed"
    assert world.run(run["id"])["definition_snapshot"]["name"] == "Custom"


def test_pipeline_api_starts_run_by_id(world, project, tmp_path, graph_kernel):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", pipelines=pipelines
    )
    client = TestClient(create_app(kernel, graph_kernel=graph_kernel))
    response = client.post(
        f"/api/v1/projects/{project['id']}/runs",
        json={"node_id": world.nodes(project["id"])[0]["id"], "pipeline_id": "custom"},
    )
    assert response.status_code == 201
    assert response.json()["pipeline_id"] == "custom"


@pytest.mark.parametrize("life_state", ["pending", "ghost"])
def test_pipeline_api_rejects_unadmitted_nodes(
    world, project, tmp_path, life_state, graph_kernel
):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    node = world.create_node(project["id"], "direction", {"text": "unreviewed"})
    if life_state == "ghost":
        world.ghost_node(node["id"], "rejected")
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", pipelines=pipelines
    )

    response = TestClient(create_app(kernel, graph_kernel=graph_kernel)).post(
        f"/api/v1/projects/{project['id']}/runs",
        json={"node_id": node["id"], "pipeline_id": "custom"},
    )

    assert response.status_code == 404
    assert world.runs(project["id"]) == []


@pytest.mark.parametrize(
    "payload",
    [
        {"_pipeline": {"cursor": 99}},
        {"_signal": {"kind": "confirm_step"}},
        {"experiment_id": "node:forged"},
        {"unknown": True},
    ],
)
def test_pipeline_api_rejects_internal_run_payload(
    world, project, tmp_path, payload, graph_kernel
):
    client = pipeline_client(world, tmp_path, graph_kernel)
    response = client.post(
        f"/api/v1/projects/{project['id']}/runs",
        json={
            "node_id": world.nodes(project["id"])[0]["id"],
            "pipeline_id": "custom",
            "payload": payload,
        },
    )
    assert response.status_code == 400
    assert world.runs(project["id"]) == []


@pytest.mark.parametrize("life_state", ["pending", "ghost"])
def test_pipeline_api_rejects_unadmitted_pins(
    world, project, tmp_path, life_state, graph_kernel
):
    pin = world.create_node(project["id"], "source", {"title": "private"})
    if life_state == "ghost":
        world.ghost_node(pin["id"], "rejected")
    response = start_with_payload(
        world, project, tmp_path, {"pins": [pin["id"]]}, graph_kernel
    )
    assert response.status_code == 404
    assert world.runs(project["id"]) == []


def test_pipeline_api_rejects_cross_project_pin(world, project, tmp_path, graph_kernel):
    other = world.create_project("other", tmp_path / "other", "Other?")
    pin = world.nodes(other["id"])[0]
    response = start_with_payload(
        world, project, tmp_path, {"pins": [pin["id"]]}, graph_kernel
    )
    assert response.status_code == 404
    assert world.runs(project["id"]) == []


def test_pipeline_api_accepts_admitted_pin(world, project, tmp_path, graph_kernel):
    pin = world.create_node(project["id"], "source", {"title": "public"})
    world.admit_node(pin["id"])
    response = start_with_payload(
        world, project, tmp_path, {"pins": [pin["id"]]}, graph_kernel
    )
    assert response.status_code == 201
    assert response.json()["payload"]["pins"] == [pin["id"]]


def test_pipeline_api_rejects_cross_project_thread(
    world, project, tmp_path, graph_kernel
):
    other = world.create_project("thread-owner", tmp_path / "thread-owner", "Other?")
    thread = world.create_thread(other["id"], "private", "session:x", "assistant")
    response = start_with_payload(
        world, project, tmp_path, {"thread_id": thread["id"]}, graph_kernel
    )
    assert response.status_code == 404
    assert world.runs(project["id"]) == []


def pipeline_client(world, tmp_path, graph_kernel):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", pipelines=pipelines
    )
    return TestClient(create_app(kernel, graph_kernel=graph_kernel))


def start_with_payload(world, project, tmp_path, payload, graph_kernel):
    return pipeline_client(world, tmp_path, graph_kernel).post(
        f"/api/v1/projects/{project['id']}/runs",
        json={
            "node_id": world.nodes(project["id"])[0]["id"],
            "pipeline_id": "custom",
            "payload": payload,
        },
    )


def test_pipeline_api_rejects_unknown_primitive_before_run(
    world, project, tmp_path, graph_kernel
):
    pipelines = registry(tmp_path)
    kernel = ResearchKernel(
        world, projects_root=tmp_path / "projects", pipelines=pipelines
    )
    client = TestClient(create_app(kernel, graph_kernel=graph_kernel))
    value = spec()
    value["stages"][0]["prompt"] = "unknown"
    response = client.put("/api/v1/pipelines/custom", json=value)
    assert response.status_code == 400
    assert world.runs(project["id"]) == []


class SignalCommandKernel:
    def __init__(self):
        self.tags = []

    async def command(self, command):
        self.tags.append(command.tag)
        return {"tag": command.tag}

    async def query(self, _query):
        raise AssertionError("run control must not query")


def test_run_control_routes_use_semantic_commands_without_query(graph_kernel):
    kernel = SignalCommandKernel()
    client = TestClient(create_app(kernel, graph_kernel=graph_kernel))

    confirmed = client.post("/api/v1/runs/run:test/confirm")
    resolved = client.post(
        "/api/v1/runs/run:test/resolve",
        json={"decision": "approve", "reason": "reviewed"},
    )

    assert confirmed.json() == {"tag": "confirm_run"}
    assert resolved.json() == {"tag": "resolve_run"}
    assert kernel.tags == ["confirm_run", "resolve_run"]


def test_research_pipeline_reviews_reflected_direction():
    root = Path(__file__).parents[1]
    pipelines = PipelineRegistry(root / "pipelines", SCHEMA)
    stages = pipelines.get("research")["stages"]
    assert [stage["id"] for stage in stages[-2:]] == ["reflect", "review-reflection"]
    assert stages[-1]["prompt"] == "review-directions"
