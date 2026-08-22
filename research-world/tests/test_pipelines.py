from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
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


def test_pipeline_api_starts_run_by_id(world, project, tmp_path):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    client = TestClient(create_app(world, pipelines=pipelines))
    response = client.post(
        f"/api/v1/projects/{project['id']}/runs",
        json={"node_id": world.nodes(project["id"])[0]["id"], "pipeline_id": "custom"},
    )
    assert response.status_code == 201
    assert response.json()["pipeline_id"] == "custom"


def test_pipeline_api_rejects_unknown_primitive_before_run(world, project, tmp_path):
    pipelines = registry(tmp_path)
    client = TestClient(create_app(world, pipelines=pipelines))
    value = spec()
    value["stages"][0]["prompt"] = "unknown"
    response = client.put("/api/v1/pipelines/custom", json=value)
    assert response.status_code == 400
    assert world.runs(project["id"]) == []


def test_research_pipeline_reviews_reflected_direction():
    root = Path(__file__).parents[1]
    pipelines = PipelineRegistry(root / "pipelines", SCHEMA)
    stages = pipelines.get("research")["stages"]
    assert [stage["id"] for stage in stages[-2:]] == ["reflect", "review-reflection"]
    assert stages[-1]["prompt"] == "review-directions"
