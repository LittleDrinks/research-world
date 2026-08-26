import json

import pytest
from runtime.service import Runtime
from runtime.types import AgentSpec, CapabilityNotFound
from runtime.types import RuntimeError as SpecError
from tests.helpers import FakeProvider, endpoint


def spec(**values):
    data = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Answer from evidence.",
    }
    data.update(values)
    return data


@pytest.mark.parametrize("legacy", [{"runtime": "old"}, {"mcp_servers": []}, {"connectors": ["lean4"]}])
def test_agent_spec_rejects_legacy_fields(legacy):
    with pytest.raises(SpecError):
        AgentSpec.parse({**spec(), **legacy})


@pytest.mark.parametrize(
    "invalid",
    [
        {"name": ""},
        {"name": "   "},
        {"instructions": "\n\t"},
        {"runtime": "legacy"},
        {"options": {"max_rounds": 0}},
        {"tools": ["graph_query", "graph_query"]},
    ],
)
def test_runtime_validates_agent_spec_with_the_canonical_schema(tmp_path, invalid):
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])

    assert runtime.validate_agent(spec()) == {"valid": True}
    with pytest.raises(SpecError):
        runtime.validate_agent({**spec(), **invalid})


async def test_launch_rejects_unrecognized_capability(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])

    with pytest.raises(CapabilityNotFound, match="skill is not available"):
        await runtime.launch(
            {"workspace": str(tmp_path), "agent_spec": spec(skills=["missing"])}
        )


async def test_launch_reports_missing_capability_status_and_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])

    with pytest.raises(
        CapabilityNotFound,
        match=r"tool is not available: absent \(missing / not_recognized\)",
    ):
        await runtime.launch(
            {"workspace": str(tmp_path), "agent_spec": spec(tools=["absent"])}
        )


async def test_prompt_and_resume_are_derived_from_trace(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    provider = FakeProvider(
        [
            {"role": "assistant", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
    )
    runtime = Runtime(tmp_path / "data", [endpoint(provider)])
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "two"}])

    view = runtime.inspect(launched["session_id"])
    assert [item["content"] for item in view["messages"]] == [
        "one",
        "first",
        "two",
        "second",
    ]
    assert [
        item["content"]
        for item in provider.requests[1]["messages"]
        if item["role"] != "system"
    ] == ["one", "first", "two"]


async def test_prompt_rejects_an_empty_final_response(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(
        tmp_path / "data",
        [endpoint(FakeProvider([{"role": "assistant", "content": ""}]))],
    )
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    with pytest.raises(RuntimeError, match="empty assistant response"):
        await runtime.prompt(
            launched["session_id"], [{"type": "text", "text": "answer"}]
        )

    turn = runtime.inspect(launched["session_id"])["turns"][0]
    assert turn["status"] == "error"
    assert turn["output"] is None


async def test_agent_spec_exposes_only_selected_builtin_tools(tmp_path, monkeypatch):
    runtime, provider = configured_runtime(tmp_path, monkeypatch)
    selected_tools = ["report_projection", "report_validate"]
    selected = await launch(runtime, tmp_path, spec(tools=selected_tools))
    omitted = await launch(runtime, tmp_path, spec(id="without-report"))

    await runtime.prompt(selected["session_id"], [{"type": "text", "text": "one"}])
    await runtime.prompt(omitted["session_id"], [{"type": "text", "text": "two"}])

    assert request_tool_names(provider.requests[0]) == set(selected_tools)
    assert request_tool_names(provider.requests[1]) == set()


async def test_launch_with_same_session_id_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    value = {
        "workspace": str(tmp_path),
        "agent_spec": spec(),
        "session_id": "s-operation_1",
    }

    assert await runtime.launch(value) == {"session_id": "s-operation_1"}
    assert await runtime.launch(value) == {"session_id": "s-operation_1"}
    assert len(runtime.inspect("s-operation_1")["events"]) == 1


async def test_launch_rejects_reusing_session_for_other_spec(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    value = {"workspace": str(tmp_path), "agent_spec": spec(), "session_id": "s-op"}
    await runtime.launch(value)

    with pytest.raises(ValueError, match="different launch"):
        await runtime.launch({**value, "agent_spec": spec(instructions="changed")})


async def test_skill_body_is_disclosed_only_after_tool_call(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    folder = tmp_path / ".agents" / "skills" / "evidence-review"
    folder.mkdir(parents=True)
    folder.joinpath("SKILL.md").write_text(
        "---\nname: evidence-review\ndescription: Review evidence.\n---\nSECRET BODY\n"
    )
    call = {
        "id": "c1",
        "type": "function",
        "function": {
            "name": "read_skill",
            "arguments": json.dumps({"name": "evidence-review"}),
        },
    }
    provider = FakeProvider(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            {"role": "assistant", "content": "done"},
        ]
    )
    runtime = Runtime(tmp_path / "data", [endpoint(provider)])
    launched = await runtime.launch(
        {"workspace": str(tmp_path), "agent_spec": spec(skills=["evidence-review"])}
    )

    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "review"}])

    first_request = provider.requests[0]["messages"]
    second_request = provider.requests[1]["messages"]
    assert "SECRET BODY" not in str(first_request)
    assert "SECRET BODY" in str(second_request)


def request_tool_names(request):
    return {value["function"]["name"] for value in request["tools"]}


async def launch(runtime, workspace, agent_spec):
    return await runtime.launch({"workspace": str(workspace), "agent_spec": agent_spec})


def configured_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    outputs = [
        {"role": "assistant", "content": "selected"},
        {"role": "assistant", "content": "omitted"},
    ]
    provider = FakeProvider(outputs)
    return Runtime(tmp_path / "data", [endpoint(provider)]), provider
