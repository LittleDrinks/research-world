import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from server.kernel import ResearchKernel
from server.titles import validate_title


@pytest.mark.parametrize(
    "title",
    ["one two three four five six seven eight nine ten eleven twelve", "一二三四五六七八九十一二", "a,b,c,d,e,f?"],
)
def test_title_accepts_exactly_twelve_tokens(title):
    assert validate_title(title) == title


@pytest.mark.parametrize(
    "title",
    ["one two three four five six seven eight nine ten eleven twelve thirteen", "一二三四五六七八九十一二十三", "a,b,c,d,e,f,g"],
)
def test_title_rejects_more_than_twelve_tokens(title):
    with pytest.raises(ValueError, match="12-token"):
        validate_title(title)


@pytest.mark.parametrize("title", [None, 7, {}, "", " \t\n "])
def test_title_rejects_non_text_and_whitespace(title):
    with pytest.raises((TypeError, ValueError), match="title"):
        validate_title(title)


@pytest.mark.parametrize("kind", ["question", "source", "direction", "experiment"])
def test_kernel_api_requires_title_for_each_node_kind(world, project, tmp_path, kind):
    client = TestClient(create_app(ResearchKernel(world, projects_root=tmp_path / "projects")))
    response = client.post(
        f"/api/v1/projects/{project['id']}/nodes",
        json={"kind": kind, "payload": {"text": "body cannot become a title"}},
    )

    assert response.status_code == 400
    assert "title" in response.json()["detail"]
    assert len(world.nodes(project["id"])) == 1


def test_project_title_is_validated_at_world_boundary(world, tmp_path):
    with pytest.raises(ValueError, match="12-token"):
        world.create_project(
            "study", tmp_path, "a b c d e f g h i j k l m", "Question text"
        )


def test_all_project_seeds_have_valid_explicit_titles():
    seeds = Path(__file__).parents[1].glob("projects/q*/project.json")
    titles = [json.loads(seed.read_text())["title"] for seed in seeds]

    assert len(titles) == 125
    assert [validate_title(title) for title in titles] == titles
