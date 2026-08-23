import json

import pytest
from runtime.adapters import McpAdapter, discover_adapters, parse_definition


def private_tool():
    return {
        "id": "lab-db",
        "name": "Lab database",
        "description": "Private experiment records",
        "transport": "http",
        "url": "https://lab.test/mcp",
        "headers": {"Authorization": "Bearer ${LAB_DB_TOKEN}"},
    }


def test_tool_projection_hides_location_and_credentials(monkeypatch):
    monkeypatch.setenv("LAB_DB_TOKEN", "top-secret")
    adapter = McpAdapter(parse_definition(private_tool(), "runtime"))

    public = adapter.inspect()

    assert set(public) == {"id", "name", "description", "source", "status"}
    assert public["status"] == "ready"
    assert "top-secret" not in json.dumps(public)
    assert "https://lab.test" not in json.dumps(public)
    assert "LAB_DB_TOKEN" not in json.dumps(public)


def test_stdio_tool_projection_hides_command():
    adapter = McpAdapter(
        parse_definition(
            {"id": "lean4", "transport": "stdio", "command": "/usr/bin/lean"}, "test"
        )
    )

    public = adapter.inspect()

    assert "command" not in public
    assert "/usr/bin/lean" not in json.dumps(public)


def test_absolute_stdio_tool_must_be_executable(tmp_path):
    command = tmp_path / "lean4-mcp"
    command.write_text("#!/bin/sh\n", encoding="utf-8")
    definition = parse_definition(
        {"id": "lean4", "transport": "stdio", "command": str(command)}, "test"
    )

    command.chmod(0o600)
    assert definition.status() == "unavailable"
    command.chmod(0o700)
    assert definition.status() == "ready"


@pytest.mark.parametrize(
    "credential",
    [
        {"headers": {"Authorization": "Bearer top-secret"}},
        {"api_key": "top-secret"},
    ],
)
def test_rejects_literal_tool_credentials(credential):
    value = {
        "id": "lab-db",
        "transport": "http",
        "url": "https://lab.test/mcp",
        **credential,
    }
    with pytest.raises(ValueError, match="environment variable"):
        parse_definition(value, "test")


@pytest.mark.parametrize(
    ("suffix", "message"),
    [("?key=top-secret", "query parameters"), ("#credentials", "a fragment")],
)
def test_rejects_remote_tool_location_suffix(suffix, message):
    with pytest.raises(ValueError, match=f"must not include {message}"):
        parse_definition(
            {
                "id": "lab-db",
                "transport": "http",
                "url": f"https://lab.test/mcp{suffix}",
            },
            "test",
        )


@pytest.mark.parametrize("tool_id", ["../lean", "lean 4", "_lean"])
def test_rejects_invalid_tool_names(tool_id):
    with pytest.raises(ValueError, match="invalid tool"):
        parse_definition(
            {
                "id": tool_id,
                "transport": "stdio",
                "command": "lean-mcp",
            },
            "test",
        )


def test_resolves_tool_credentials_only_at_execution(monkeypatch):
    definition = parse_definition(
        {
            "id": "literature",
            "transport": "http",
            "url": "https://literature.test/mcp",
            "headers": {"Authorization": "Bearer ${LITERATURE_TOKEN}"},
        },
        "test",
    )
    assert definition.status() == "unavailable"

    monkeypatch.setenv("LITERATURE_TOKEN", "runtime-secret")

    assert definition.status() == "ready"
    assert (
        definition.resolved_config()["headers"]["Authorization"]
        == "Bearer runtime-secret"
    )


def test_duplicate_tool_id_across_sources_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_CONFIG", str(tmp_path / "missing.toml"))
    tmp_path.joinpath(".mcp.json").write_text(
        json.dumps(
            {"mcpServers": {"lab-dup": {"type": "http", "url": "https://mcp.test"}}}
        )
    )
    extra = [
        parse_definition(
            {"id": "lab-dup", "transport": "http", "url": "https://other.test"},
            "runtime",
        )
    ]

    with pytest.raises(ValueError, match="duplicate tool id: lab-dup"):
        discover_adapters(tmp_path, extra)


def test_tool_id_colliding_with_builtin_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_CONFIG", str(tmp_path / "missing.toml"))
    extra = [
        parse_definition(
            {"id": "graph_query", "transport": "http", "url": "https://x.test"},
            "runtime",
        )
    ]

    with pytest.raises(ValueError, match="duplicate tool id: graph_query"):
        discover_adapters(tmp_path, extra)
