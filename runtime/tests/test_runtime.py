import json

import pytest

from runtime.service import Runtime
from runtime.types import CapabilityNotFound
from tests.helpers import FakeProvider


def spec(**values):
    data = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Answer from evidence.",
    }
    data.update(values)
    return data


async def test_launch_rejects_unrecognized_capability(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", {"openai-compatible": FakeProvider([])})

    with pytest.raises(CapabilityNotFound, match="skill is not available"):
        await runtime.launch(
            {"workspace": str(tmp_path), "agent_spec": spec(skills=["missing"])}
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
    runtime = Runtime(tmp_path / "data", {"openai-compatible": provider})
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


async def test_launch_with_same_session_id_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    runtime = Runtime(tmp_path / "data", {"openai-compatible": FakeProvider([])})
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
    runtime = Runtime(tmp_path / "data", {"openai-compatible": FakeProvider([])})
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
    runtime = Runtime(tmp_path / "data", {"openai-compatible": provider})
    launched = await runtime.launch(
        {"workspace": str(tmp_path), "agent_spec": spec(skills=["evidence-review"])}
    )

    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "review"}])

    first_request = provider.requests[0]["messages"]
    second_request = provider.requests[1]["messages"]
    assert "SECRET BODY" not in str(first_request)
    assert "SECRET BODY" in str(second_request)
