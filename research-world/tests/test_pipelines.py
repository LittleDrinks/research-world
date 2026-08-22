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
        "stages": [{"id": "search", "type": "tool", "tool": "literature-search"}],
    }


def test_registry_accepts_arbitrary_pipeline_ids(tmp_path):
    pipelines = registry(tmp_path)
    pipelines.save("custom", spec())
    assert pipelines.get("custom")["stages"][0]["tool"] == "literature-search"


def test_registry_rejects_invalid_prompt_stage(tmp_path):
    value = spec()
    value["stages"] = [{"id": "draft", "type": "prompt"}]
    with pytest.raises(ValueError, match="agent"):
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
