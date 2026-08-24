import json

from runtime.adapters import discover_adapters
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


def test_discovers_workspace_tool_without_exposing_secrets(tmp_path, monkeypatch):
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

    adapter = discover_adapters(tmp_path)["search"]

    public = adapter.inspect()
    assert set(public) == {"id", "name", "description", "source", "status"}
    assert public["source"] == "workspace"
    assert public["status"] == "ready"
    assert "https://mcp.test" not in json.dumps(public)
    assert "SEARCH_TOKEN" not in json.dumps(public)
    assert str(tmp_path) not in json.dumps(public)


async def test_catalog_contains_only_detected_workspace_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")

    value = await Runtime(tmp_path / "data").recognize(str(tmp_path))

    assert set(value) == {"endpoints", "models", "skills", "tools", "presets"}
    assert {item["id"] for item in value["endpoints"]} >= {"openai-compatible"}
    assert {item["id"] for item in value["models"]} >= {"qwen-test"}
    assert all(set(item) == {"id", "endpoint"} for item in value["models"])
    tools = {item["id"]: item for item in value["tools"]}
    for tool_id in (
        "report_projection",
        "report_validate",
        "export_bibtex",
        "submit_observation",
    ):
        assert tool_id in tools
    assert all(item["status"] == "ready" for key, item in tools.items() if key != "lean4")
    assert all(
        set(item) == {"id", "name", "description", "source", "status"}
        for item in tools.values()
    )


async def test_catalog_lists_unavailable_lean4_in_math_preset(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")

    value = await Runtime(tmp_path / "data").recognize(str(tmp_path))

    presets = {item["id"]: item for item in value["presets"]}
    preset = presets["math-proof"]
    assert preset["spec"]["tools"] == ["lean4"]
    assert preset["tools"] == [
        {"id": "lean4", "status": "unavailable", "reason": "not_installed"}
    ]
    assert set(preset) == {"id", "name", "description", "spec", "tools"}


async def test_preset_tool_status_follows_adapter_readiness(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    monkeypatch.setattr("runtime.lean4._doctor", lambda _url: True)
    runtime = Runtime(tmp_path / "data")

    value = await runtime.recognize(str(tmp_path))

    preset = {item["id"]: item for item in value["presets"]}["math-proof"]
    assert preset["tools"] == [{"id": "lean4", "status": "ready"}]
    assert "command" not in json.dumps(preset)
