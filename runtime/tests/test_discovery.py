import json

from runtime.connectors import discover_connectors
from runtime.service import Runtime
from runtime.skills import discover_skills


def test_discovers_skill_frontmatter(tmp_path):
    folder = tmp_path / ".agents" / "skills" / "evidence-review"
    folder.mkdir(parents=True)
    folder.joinpath("SKILL.md").write_text(
        "---\nname: evidence-review\ndescription: Review evidence.\n---\n\nRead claims.\n"
    )

    skills = discover_skills(tmp_path)

    assert skills["evidence-review"].description == "Review evidence."
    assert skills["evidence-review"].body() == "Read claims."


def test_discovers_mcp_without_exposing_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("SEARCH_TOKEN", "secret")
    tmp_path.joinpath(".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "search": {
                        "type": "http",
                        "url": "https://mcp.test",
                        "headers": {"Authorization": "Bearer ${SEARCH_TOKEN}"},
                    }
                }
            }
        )
    )

    connector = discover_connectors(tmp_path)["search"]

    assert connector.public()["url"] == "https://mcp.test"
    assert connector.public()["header_names"] == ["Authorization"]
    assert "headers" not in connector.public()


async def test_catalog_contains_only_detected_workspace_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")

    value = await Runtime(tmp_path / "data").recognize(str(tmp_path))

    assert set(value) == {"endpoints", "models", "skills", "tools", "connectors"}
    assert {item["id"] for item in value["endpoints"]} >= {"openai-compatible"}
    assert {item["id"] for item in value["models"]} >= {"qwen-test"}
    assert all(set(item) == {"id", "endpoint"} for item in value["models"])
    assert "report_validate" in {item["id"] for item in value["tools"]}
    assert "submit_observation" in {item["id"] for item in value["tools"]}
