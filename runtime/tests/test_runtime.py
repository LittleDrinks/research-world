import json

import pytest
from runtime.acp_agent import _default_spec
from runtime.service import Runtime
from runtime.endpoints import Endpoint
from runtime.runtimes import CodexRuntimeAdapter, REALM, RuntimeAdapter, RuntimeDescriptor
from runtime.types import AgentSpec, CapabilityNotFound
from runtime.types import RuntimeError as SpecError
from tests.helpers import FakeProvider, endpoint
from tests.test_codex import ready_provider


def spec(**values):
    data = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "openai-compatible", "realm": "container:runtime"},
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


@pytest.mark.parametrize("value", [
    spec(endpoint="codex"),
    spec(runtime={"id": "codex", "realm": REALM}),
])
def test_agent_spec_keeps_runtime_and_endpoint_independent(value):
    assert AgentSpec.parse(value).snapshot()["runtime"]["id"] == value["runtime"]["id"]


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
@pytest.mark.asyncio
async def test_runtime_validates_agent_spec_with_the_canonical_schema(tmp_path, invalid):
    runtime = generic_runtime(tmp_path, [endpoint(FakeProvider([]))])

    assert await runtime.validate_agent(spec(), str(tmp_path)) == {"valid": True}
    with pytest.raises(SpecError):
        await runtime.validate_agent({**spec(), **invalid}, str(tmp_path))


async def test_launch_rejects_unrecognized_capability(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = generic_runtime(tmp_path, [endpoint(FakeProvider([]))])

    with pytest.raises(CapabilityNotFound, match="skill is not available"):
        await runtime.launch(
            {"workspace": str(tmp_path), "agent_spec": spec(skills=["missing"])}
        )


def test_non_codex_adapter_cannot_register_codex_runtime(tmp_path):
    with pytest.raises(ValueError, match="requires CodexRuntimeAdapter"):
        Runtime(
            tmp_path / "data", [endpoint(FakeProvider([]))],
            runtimes=[RuntimeAdapter(RuntimeDescriptor("codex", REALM), ("openai-compatible",))],
        )


def test_duplicate_runtime_identity_is_rejected(tmp_path):
    adapter = RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))
    with pytest.raises(ValueError, match="runtime id and realm must be unique"):
        Runtime(tmp_path / "data", [endpoint(FakeProvider([]))], [adapter, adapter])


def test_default_spec_does_not_select_a_synthetic_runtime(tmp_path):
    provider = FakeProvider([])
    runtime = Runtime(
        tmp_path / "data", [endpoint(provider)],
        runtimes=[RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))],
    )
    with pytest.raises(CapabilityNotFound, match="no model endpoint"):
        _default_spec(runtime)


def test_default_spec_uses_declared_chat_endpoint_for_codex(tmp_path):
    endpoints = [Endpoint("embed", "Embed", "openai-compatible", (), ("embed",), 1, None, available=True), Endpoint("down", "Down", "openai-compatible", ("down",), (), 2, None), Endpoint("chat", "Chat", "openai-compatible", ("gpt",), (), 3, None, available=True)]
    runtime = Runtime(tmp_path / "data", endpoints, [CodexRuntimeAdapter(ready_provider())])

    assert _default_spec(runtime)["endpoint"] == "chat"


def test_default_spec_rejects_unavailable_endpoint_for_non_codex(tmp_path):
    endpoints = [Endpoint("down", "Down", "openai-compatible", ("gpt",), (), 1, None)]
    adapter = RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))
    runtime = Runtime(tmp_path / "data", endpoints, [adapter])

    with pytest.raises(CapabilityNotFound, match="no model endpoint"):
        _default_spec(runtime)


async def test_codex_rejects_incompatible_declared_endpoint_adapter(tmp_path):
    endpoint = Endpoint("foreign", "Foreign", "foreign", ("gpt",), (), 1, None, available=True)
    runtime = Runtime(tmp_path / "data", [endpoint], [CodexRuntimeAdapter(ready_provider())])

    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec(runtime={"id": "codex", "realm": REALM}, endpoint="foreign", model="gpt")})


async def test_generic_rejects_foreign_declared_endpoint_adapter(tmp_path):
    foreign = Endpoint("foreign", "Foreign", "foreign", ("gpt",), (), 1, None, available=True)
    runtime = generic_runtime(tmp_path, [foreign])

    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec(endpoint="foreign", model="gpt")})


async def test_generic_empty_adapter_declaration_rejects_endpoint(tmp_path):
    endpoint = Endpoint("primary", "Primary", "openai-compatible", ("gpt",), (), 1, FakeProvider([]))
    runtime = Runtime(tmp_path / "data", [endpoint], [RuntimeAdapter(RuntimeDescriptor("generic", REALM), ())])

    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec(runtime={"id": "generic", "realm": REALM}, endpoint="primary", model="gpt")})


async def test_generic_explicit_adapter_declaration_accepts_endpoint(tmp_path):
    endpoint = Endpoint("primary", "Primary", "openai-compatible", ("gpt",), (), 1, FakeProvider([]))
    adapter = RuntimeAdapter(RuntimeDescriptor("generic", REALM), ("openai-compatible",))
    runtime = Runtime(tmp_path / "data", [endpoint], [adapter])

    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec(runtime={"id": "generic", "realm": REALM}, endpoint="primary", model="gpt")})

    assert launched["session_id"].startswith("s-")


async def test_runtime_accepts_independent_compatible_endpoint_id(tmp_path):
    runtime = _independent_runtime(tmp_path)

    launched = await runtime.launch(
        {"workspace": str(tmp_path), "agent_spec": _independent_spec()}
    )

    assert launched["session_id"].startswith("s-")


@pytest.mark.parametrize(
    "runtime_value, endpoint_id, model, message",
    [
        ({"id": "generic", "realm": "other"}, "logical", "gpt", "runtime is not available"),
        ({"id": "generic", "realm": REALM}, "foreign", "gpt", "endpoint is not available"),
        ({"id": "generic", "realm": REALM}, "logical", "other", "model is not available"),
    ],
)
async def test_runtime_rejects_independent_invalid_bindings(
    tmp_path, runtime_value, endpoint_id, model, message
):
    runtime = _independent_runtime(tmp_path)
    agent = _independent_spec(runtime=runtime_value, endpoint=endpoint_id, model=model)

    with pytest.raises(CapabilityNotFound, match=message):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})


async def test_public_usage_has_only_official_counters(tmp_path, monkeypatch):
    runtime, _ = configured_runtime(tmp_path, monkeypatch)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()}))["session_id"]

    result = await runtime.prompt(session, [{"type": "text", "text": "one"}])
    assert set(result["usage"]) == _usage_keys()
    assert set(runtime.inspect(session)["turns"][0]["events"][-1]["data"]["usage"]) == _usage_keys()


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
    runtime = generic_runtime(tmp_path, [endpoint(provider)])
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
    runtime = generic_runtime(
        tmp_path, [endpoint(FakeProvider([{"role": "assistant", "content": ""}]))]
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
    selected_tools = ["report_projection", "publish_report"]
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
    runtime = generic_runtime(tmp_path, [endpoint(FakeProvider([]))])
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
    runtime = generic_runtime(tmp_path, [endpoint(FakeProvider([]))])
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
    runtime = generic_runtime(tmp_path, [endpoint(provider)])
    launched = await runtime.launch(
        {"workspace": str(tmp_path), "agent_spec": spec(skills=["evidence-review"])}
    )

    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "review"}])

    first_request = provider.requests[0]["messages"]
    second_request = provider.requests[1]["messages"]
    assert "SECRET BODY" not in str(first_request)
    assert "SECRET BODY" in str(second_request)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"runtime": {"id": "codex", "realm": "legacy:runtime"}}, "runtime is not available"),
        ({"endpoint": "missing"}, "endpoint is not available"),
        ({"model": "missing"}, "model is not available"),
    ],
)
async def test_codex_validation_rejects_invalid_bindings(tmp_path, change, message):
    runtime = codex_runtime_for_test(tmp_path)
    with pytest.raises(CapabilityNotFound, match=message):
        await runtime.validate_agent({**codex_spec(), **change}, str(tmp_path))


async def test_codex_validation_rejects_incompatible_endpoint_and_tools(tmp_path):
    foreign = Endpoint("foreign", "Foreign", "foreign", ("gpt",), (), 1, FakeProvider([]), available=True)
    runtime = Runtime(tmp_path / "data", [foreign], [CodexRuntimeAdapter(ready_provider())])
    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.validate_agent({**codex_spec(), "endpoint": "foreign", "model": "gpt"}, str(tmp_path))

    runtime = codex_runtime_for_test(tmp_path)
    with pytest.raises(CapabilityNotFound, match="cannot expose selected Tool"):
        await runtime.validate_agent({**codex_spec(), "tools": ["publish_report"]}, str(tmp_path))


async def test_launch_revalidates_existing_session_binding(tmp_path):
    runtime = codex_runtime_for_test(tmp_path)
    value = {"workspace": str(tmp_path), "agent_spec": codex_spec(), "session_id": "s-revalidate"}
    await runtime.launch(value)
    current = runtime.endpoints._values["openai-compatible"]
    runtime.endpoints._values["openai-compatible"] = Endpoint(
        current.id, current.name, current.adapter, current.models, current.embedding_models,
        current.priority, None, current.base_url_env, current.api_key_env, False,
    )
    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.launch(value)


def codex_spec(**values):
    return {**spec(runtime={"id": "codex", "realm": REALM}, tools=[]), **values}


def codex_runtime_for_test(path):
    return Runtime(path / "data", [endpoint(FakeProvider([]))], [CodexRuntimeAdapter(ready_provider())])


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
    return generic_runtime(tmp_path, [endpoint(provider)]), provider


def _usage_keys():
    return {"input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens"}


def generic_runtime(path, endpoints):
    adapter = RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))
    return Runtime(path / "data", endpoints, [adapter])


def _independent_runtime(path):
    endpoint = Endpoint("logical", "Logical", "openai-compatible", ("gpt",), (), 1, FakeProvider([]), available=True)
    adapter = RuntimeAdapter(RuntimeDescriptor("generic", REALM), ("openai-compatible",))
    return Runtime(path / "data", [endpoint], [adapter])


def _independent_spec(**values):
    return spec(**{
        "runtime": {"id": "generic", "realm": REALM},
        "endpoint": "logical",
        "model": "gpt",
        **values,
    })
