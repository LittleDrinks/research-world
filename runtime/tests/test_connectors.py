import json

import pytest

from runtime.connectors import ConnectorStore, parse_connector
from runtime.service import Runtime
from tests.helpers import FakeProvider, endpoint


def private_connector():
    return {
        "id": "lab-db",
        "name": "Lab database",
        "description": "Private experiment records",
        "transport": "http",
        "url": "https://lab.test/mcp",
        "headers": {"Authorization": "Bearer ${LAB_DB_TOKEN}"},
    }


def agent_spec():
    return {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use evidence.",
        "connectors": ["lab-db"],
    }


def test_registers_connector_with_environment_reference(tmp_path, monkeypatch):
    monkeypatch.setenv("LAB_DB_TOKEN", "top-secret")
    store = ConnectorStore(tmp_path / "connectors.json")

    public = store.register(private_connector())

    stored = (tmp_path / "connectors.json").read_text()
    assert set(public) == {
        "id",
        "name",
        "description",
        "transport",
        "source",
        "available",
    }
    assert public["available"] is True
    assert "top-secret" not in json.dumps(public)
    assert "https://lab.test" not in json.dumps(public)
    assert "LAB_DB_TOKEN" not in json.dumps(public)
    assert "top-secret" not in stored
    assert "${LAB_DB_TOKEN}" in stored


def test_stdio_connector_public_projection_hides_command(tmp_path):
    store = ConnectorStore(tmp_path / "connectors.json")

    public = store.register(
        {"id": "lean4", "transport": "stdio", "command": "/usr/bin/lean"}
    )

    assert "command" not in public
    assert "/usr/bin/lean" not in json.dumps(public)


async def test_connector_config_and_credentials_do_not_enter_trace(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("LAB_DB_TOKEN", "top-secret")
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    runtime.register_connector(private_connector())

    launched = await runtime.launch(
        {"workspace": str(tmp_path), "agent_spec": agent_spec()}
    )
    trace = json.dumps(runtime.inspect(launched["session_id"])["session"])

    assert "top-secret" not in trace
    assert "LAB_DB_TOKEN" not in trace
    assert "https://lab.test" not in trace


@pytest.mark.parametrize(
    "credential",
    [
        {"headers": {"Authorization": "Bearer top-secret"}},
        {"api_key": "top-secret"},
    ],
)
def test_rejects_literal_connector_credentials(credential):
    value = {
        "id": "lab-db",
        "transport": "http",
        "url": "https://lab.test/mcp",
        **credential,
    }
    with pytest.raises(ValueError, match="environment variable"):
        parse_connector(value, "test")


@pytest.mark.parametrize(
    ("suffix", "message"),
    [("?key=top-secret", "query parameters"), ("#credentials", "a fragment")],
)
def test_rejects_remote_connector_location_suffix(suffix, message):
    with pytest.raises(ValueError, match=f"must not include {message}"):
        parse_connector(
            {
                "id": "lab-db",
                "transport": "http",
                "url": f"https://lab.test/mcp{suffix}",
            },
            "test",
        )


@pytest.mark.parametrize("connector_id", ["../lean", "lean 4", "_lean"])
def test_rejects_invalid_connector_names(connector_id):
    with pytest.raises(ValueError, match="invalid connector"):
        parse_connector(
            {
                "id": connector_id,
                "transport": "stdio",
                "command": "lean-mcp",
            },
            "test",
        )


def test_resolves_connector_credentials_only_at_execution(monkeypatch):
    connector = parse_connector(
        {
            "id": "literature",
            "transport": "http",
            "url": "https://literature.test/mcp",
            "headers": {"Authorization": "Bearer ${LITERATURE_TOKEN}"},
        },
        "test",
    )
    assert connector.available() is False

    monkeypatch.setenv("LITERATURE_TOKEN", "runtime-secret")

    assert connector.available() is True
    assert (
        connector.resolved_config()["headers"]["Authorization"]
        == "Bearer runtime-secret"
    )
