import json

from runtime.catalog import discover
from runtime.mcp_servers import discover_mcp
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


def test_discovers_mcp_without_exposing_secrets(tmp_path):
    tmp_path.joinpath(".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "search": {
                        "type": "http",
                        "url": "https://mcp.test",
                        "headers": {"Authorization": "secret"},
                    }
                }
            }
        )
    )

    server = discover_mcp(tmp_path)["search"]

    assert server.public()["url"] == "https://mcp.test"
    assert server.public()["header_names"] == ["Authorization"]
    assert "headers" not in server.public()


async def test_catalog_contains_only_detected_workspace_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")

    value = await discover(tmp_path)

    assert {item["id"] for item in value["runtimes"]} >= {"openai-compatible"}
    assert {item["id"] for item in value["models"]} >= {"qwen-test"}
