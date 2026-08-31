import asyncio
import json
import os
import time

import pytest
from runtime.adapter.pi import PiAdapter
from runtime.adapter.pi import PiAdapterError
from runtime.runtime import Runtime


FAKE_PI = r'''#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

log = Path.cwd() / "fake-pi-log.jsonl"

def record(value):
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value) + "\n")

if "--version" in sys.argv:
    print("0.84.3")
    raise SystemExit

record({
    "argv": sys.argv[1:],
    "api_key": os.environ.get("RUNTIME_API_KEY"),
    "forbidden": {
        name: os.environ.get(name)
        for name in ("RUNTIME_API_BASE", "OPENAI_API_KEY", "PI_OFFLINE")
    },
    "home": os.environ.get("HOME"),
    "pi_dir": os.environ.get("PI_CODING_AGENT_DIR"),
    "locale": {
        name: os.environ.get(name)
        for name in (
            "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "LC_COLLATE",
            "LC_MESSAGES", "LC_MONETARY", "LC_NUMERIC", "LC_TIME",
        )
        if os.environ.get(name) is not None
    },
    "unsafe_locale": os.environ.get("LC_UNSAFE"),
})
active_message = None
for line in sys.stdin:
    command = json.loads(line)
    record({"command": command})
    if command["type"] == "abort":
        if active_message == "cancel-protocol-error":
            print(json.dumps({"type": "unknown"}), flush=True)
            continue
        raise SystemExit
    if command["type"] != "prompt":
        continue
    active_message = command["message"]
    if command["message"] == "reject":
        print(json.dumps({
            "id": command["id"],
            "type": "response",
            "command": "prompt",
            "success": False,
        }), flush=True)
        continue
    if command["message"] == "foreign-response":
        print(json.dumps({
            "id": "foreign-prompt",
            "type": "response",
            "command": "foreign-command",
            "success": True,
        }), flush=True)
    print(json.dumps({
        "id": command["id"],
        "type": "response",
        "command": "prompt",
        "success": True,
    }), flush=True)
    if command["message"] == "invalid":
        print("not-json", flush=True)
        continue
    if command["message"] == "settled-crash":
        message = {"role": "assistant", "content": [{"type": "text", "text": "hello"}], "stopReason": "stop"}
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "hello"}}), flush=True)
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        record({"stage": "agent_end"})
        print(json.dumps({"type": "agent_settled"}), flush=True)
        record({"stage": "agent_settled"})
        os._exit(7)
    if command["message"] == "crash":
        os._exit(7)
    if command["message"] == "incomplete":
        raise SystemExit
    if command["message"] == "cancel":
        continue
    if command["message"] == "cancel-protocol-error":
        record({"stage": "cancel-ready"})
        continue
    if command["message"] == "rich":
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "thinking_start", "contentIndex": 0}}), flush=True)
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "thinking_delta", "contentIndex": 0, "delta": "plan"}}), flush=True)
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "thinking_end", "contentIndex": 0, "content": "plan"}}), flush=True)
        print(json.dumps({"type": "tool_execution_start", "toolCallId": "tool-1", "toolName": "read", "args": {"path": "README.md"}}), flush=True)
        print(json.dumps({"type": "tool_execution_update", "toolCallId": "tool-1", "toolName": "read", "args": {"path": "README.md"}, "partialResult": "part"}), flush=True)
        print(json.dumps({"type": "tool_execution_end", "toolCallId": "tool-1", "toolName": "read", "result": "contents", "isError": False}), flush=True)
    if command["message"] == "overflow-retry":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "context window exceeded"}
        print(json.dumps({"type": "agent_end", "messages": [error], "willRetry": False}), flush=True)
        record({"stage": "intermediate_error"})
        print(json.dumps({"type": "compaction_start", "reason": "overflow"}), flush=True)
        print(json.dumps({"type": "compaction_end", "reason": "overflow", "aborted": False, "willRetry": True}), flush=True)
        message = {"role": "assistant", "content": [{"type": "text", "text": "recovered"}], "stopReason": "stop"}
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "recovered"}}), flush=True)
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        record({"stage": "successful_agent_end"})
        print(json.dumps({"type": "agent_settled"}), flush=True)
        record({"stage": "agent_settled"})
        continue
    if command["message"] == "auto-retry":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "transient provider error"}
        print(json.dumps({"type": "agent_end", "messages": [error], "willRetry": True}), flush=True)
        record({"stage": "retrying"})
        print(json.dumps({"type": "auto_retry_end", "success": True}), flush=True)
        message = {"role": "assistant", "content": [{"type": "text", "text": "recovered"}], "stopReason": "stop"}
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "recovered"}}), flush=True)
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        record({"stage": "successful_agent_end"})
        print(json.dumps({"type": "agent_settled"}), flush=True)
        record({"stage": "agent_settled"})
        continue
    if command["message"] == "final-error":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "provider unavailable"}
        print(json.dumps({"type": "agent_end", "messages": [error], "willRetry": False}), flush=True)
        record({"stage": "final_error_agent_end"})
        print(json.dumps({"type": "agent_settled"}), flush=True)
        record({"stage": "agent_settled"})
        continue
    if command["message"] == "final-error-before-settled":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "provider unavailable before settled"}
        print(json.dumps({"type": "agent_end", "messages": [error], "willRetry": False}), flush=True)
        record({"stage": "final_error_before_settled"})
        time.sleep(60)
    if command["message"] == "retry-error":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "provider quota exhausted"}
        print(json.dumps({"type": "agent_end", "messages": [error], "willRetry": False}), flush=True)
        print(json.dumps({"type": "auto_retry_end", "success": False, "finalError": "provider quota exhausted"}), flush=True)
        print(json.dumps({"type": "agent_settled"}), flush=True)
        continue
    if command["message"] == "stream-error":
        error = {"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "stream provider unavailable"}
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "error", "reason": "error", "error": error}}), flush=True)
        continue
    if command["message"] == "unknown-ui":
        print(json.dumps({"type": "extension_ui_request", "id": "ui-1", "method": "mystery"}), flush=True)
    if command["message"] == "unknown":
        print(json.dumps({"type": "unknown"}), flush=True)
        continue
    if command["message"] == "unknown-content":
        message = {"role": "assistant", "content": [{"type": "image", "url": "image"}], "stopReason": "stop"}
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        print(json.dumps({"type": "agent_settled"}), flush=True)
        continue
    if command["message"] == "thinking-final":
        message = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "plan", "thinkingSignature": "sig"},
                {"type": "text", "text": "OK"},
            ],
            "stopReason": "stop",
        }
        print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "OK"}}), flush=True)
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        print(json.dumps({"type": "agent_settled"}), flush=True)
        continue
    if command["message"] == "non-string-content":
        message = {"role": "assistant", "content": [{"type": "text", "text": 7}], "stopReason": "stop"}
        print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
        print(json.dumps({"type": "agent_settled"}), flush=True)
        continue
    message = {"role": "assistant", "content": [{"type": "text", "text": "hello"}], "stopReason": "stop"}
    print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "hel"}}), flush=True)
    print(json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "lo"}}), flush=True)
    print(json.dumps({"type": "agent_end", "messages": [message], "willRetry": False}), flush=True)
    record({"stage": "agent_end"})
    if command["message"] == "missing-settled":
        raise SystemExit
    if command["message"] == "timeout":
        time.sleep(60)
    if command["message"] == "settled":
        time.sleep(0.1)
        print(json.dumps({"type": "agent_settled"}), flush=True)
        record({"stage": "agent_settled"})
        continue
    print(json.dumps({"type": "agent_settled"}), flush=True)
'''

LOCALE_ENVIRONMENT = {
    "LANG": "zh_CN.UTF-8",
    "LANGUAGE": "zh_CN:en",
    "LC_ALL": "zh_CN.UTF-8",
    "LC_CTYPE": "zh_CN.UTF-8",
    "LC_MESSAGES": "zh_CN.UTF-8",
    "LC_UNSAFE": "should-not-pass",
    "RUNTIME_API_KEY": "runtime-secret",
    "RUNTIME_API_BASE": "https://runtime.invalid",
    "OPENAI_API_KEY": "provider-secret",
}


def _fake_pi(tmp_path, version="0.84.3"):
    path = tmp_path / "pi"
    path.write_text(FAKE_PI.replace("0.84.3", version), encoding="utf-8")
    path.chmod(0o755)
    return path


def _fake_runtime(tmp_path, monkeypatch, environment=None):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    for name, value in (environment or {}).items():
        monkeypatch.setenv(name, value)
    return Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


def _records(tmp_path):
    path = tmp_path / "fake-pi-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


async def _wait_for_command(tmp_path, command_type):
    for _ in range(100):
        if any(item.get("command", {}).get("type") == command_type for item in _records(tmp_path)):
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"fake pi did not receive {command_type}")


async def _wait_for_stage(tmp_path, stage):
    for _ in range(100):
        if any(item.get("stage") == stage for item in _records(tmp_path)):
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"fake pi did not reach {stage}")


def _launch_records(tmp_path):
    records = (tmp_path / "fake-pi-log.jsonl").read_text(encoding="utf-8").splitlines()
    values = [json.loads(line) for line in records]
    return values[0], next(value for value in values if "command" in value)


def _command_sequence(records):
    return [
        "prompt" if item.get("command", {}).get("type") == "prompt" else
        "abort" if item.get("command", {}).get("type") == "abort" else
        item["stage"]
        for item in records
        if "stage" in item or "command" in item
    ]


def _assert_locale_filtering(launch):
    assert launch["locale"] == {
        "LANG": "zh_CN.UTF-8",
        "LANGUAGE": "zh_CN:en",
        "LC_ALL": "zh_CN.UTF-8",
        "LC_CTYPE": "zh_CN.UTF-8",
        "LC_MESSAGES": "zh_CN.UTF-8",
    }
    assert launch["unsafe_locale"] is None
    assert launch["api_key"] is None
    assert launch["forbidden"] == {
        "RUNTIME_API_BASE": None,
        "OPENAI_API_KEY": None,
        "PI_OFFLINE": None,
    }


def _assert_completed_events(observed):
    actual = [(event["type"], event["data"]) for event in observed]
    expected = [("turn_start", {"message_id": "m1", "input": "hello"}), ("delta", {"text": "hel"}), ("delta", {"text": "lo"}), ("turn_end", {"status": "completed", "result_text": "hello"})]
    assert actual == expected


def _assert_launch(launch, command):
    assert launch["argv"] == ["--mode", "rpc", "--no-session", "--append-system-prompt", "system", "--thinking", "high"]
    assert launch["api_key"] is None and launch["home"] == "/host-home" and launch["pi_dir"] == "/host-pi"
    assert launch["forbidden"] == {"RUNTIME_API_BASE": None, "OPENAI_API_KEY": None, "PI_OFFLINE": None}
    assert command["command"]["message"] == "hello"


def _assert_rich_events(observed):
    actual = [(event["type"], event["data"]) for event in observed]
    expected = [
        ("turn_start", {"message_id": "m1", "input": "rich"}),
        ("reasoning", {"phase": "started", "content_index": 0, "text": ""}),
        ("reasoning", {"phase": "updated", "content_index": 0, "text": "plan"}),
        ("reasoning", {"phase": "completed", "content_index": 0, "text": "plan"}),
        ("tool", {"phase": "started", "id": "tool-1", "name": "read", "arguments": {"path": "README.md"}}),
        ("tool", {"phase": "updated", "id": "tool-1", "name": "read", "partial_result": "part"}),
        ("tool", {"phase": "completed", "id": "tool-1", "name": "read", "result": "contents", "is_error": False}),
        ("delta", {"text": "hel"}),
        ("delta", {"text": "lo"}),
        ("turn_end", {"status": "completed", "result_text": "hello"}),
    ]
    assert actual == expected


async def test_pi_adapter_runs_fake_process_and_emits_normalized_delta(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("RUNTIME_API_KEY", "runtime-secret")
    monkeypatch.setenv("RUNTIME_API_BASE", "https://runtime.invalid")
    monkeypatch.setenv("OPENAI_API_KEY", "provider-secret")
    monkeypatch.setenv("PI_OFFLINE", "1")
    monkeypatch.setenv("HOME", "/host-home")
    monkeypatch.setenv("PI_CODING_AGENT_DIR", "/host-pi")
    adapter = PiAdapter.detect()
    runtime = Runtime(tmp_path / "data", {"pi": adapter})
    run = await runtime.launch({"adapter": "pi", "model": "default", "instructions": "system", "thinking": "high", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "hello"})
    observed = await _events(runtime, turn["id"])
    launch, command = _launch_records(tmp_path)
    _assert_launch(launch, command)
    _assert_completed_events(observed)


async def test_pi_adapter_normalizes_reasoning_and_tool_streams(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "rich"})
    observed = await _events(runtime, turn["id"])
    _assert_rich_events(observed)


async def test_pi_completes_final_message_with_thinking_and_text_blocks(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "thinking-final"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {"status": "completed", "result_text": "OK"}


async def test_pi_waits_for_settled_after_agent_end(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "settled"})
    events_task = asyncio.create_task(_events(runtime, turn["id"]))
    await _wait_for_stage(tmp_path, "agent_end")
    assert not events_task.done()
    observed = await events_task
    await _wait_for_stage(tmp_path, "agent_settled")
    assert observed[-1]["data"] == {"status": "completed", "result_text": "hello"}


async def test_pi_process_exit_after_settled_is_an_explicit_turn_error(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "settled-crash"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: pi exited with status 7",
    }
    assert not any(
        event["type"] == "turn_end" and event["data"]["status"] == "completed"
        for event in observed
    )


async def test_pi_rejects_a_foreign_response_before_normal_sequence(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "foreign-response"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_protocol: pi response does not match prompt command",
    }
    assert not any(
        event["type"] == "turn_end" and event["data"]["status"] == "completed"
        for event in observed
    )


async def test_pi_continues_after_intermediate_overflow_error(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "overflow-retry"})
    observed = await _events(runtime, turn["id"])
    records = _records(tmp_path)
    stages = [item["stage"] for item in records if "stage" in item]
    commands = [item["command"]["type"] for item in records if "command" in item]
    assert stages == ["intermediate_error", "successful_agent_end", "agent_settled"]
    assert "abort" not in commands
    assert observed[-1]["data"] == {"status": "completed", "result_text": "recovered"}


async def test_pi_accepts_successful_automatic_retry(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "auto-retry"})
    observed = await _events(runtime, turn["id"])
    stages = [item["stage"] for item in _records(tmp_path) if "stage" in item]
    assert stages == ["retrying", "successful_agent_end", "agent_settled"]
    assert observed[-1]["data"] == {"status": "completed", "result_text": "recovered"}


async def test_pi_inherits_host_locale_without_runtime_credentials(tmp_path, monkeypatch):
    runtime = _fake_runtime(tmp_path, monkeypatch, LOCALE_ENVIRONMENT)
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "hello"})
    await _events(runtime, turn["id"])
    launch, _ = _launch_records(tmp_path)
    _assert_locale_filtering(launch)


async def test_pi_keeps_final_error_after_settled(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "final-error"})
    observed = await _events(runtime, turn["id"])
    assert _command_sequence(_records(tmp_path)) == [
        "prompt", "final_error_agent_end", "agent_settled", "abort"
    ]
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: provider unavailable",
    }


async def test_pi_preserves_final_error_when_cancelled_before_settled(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(
        run["session_id"], {"id": "m1", "content": "final-error-before-settled"}
    )
    await _wait_for_stage(tmp_path, "final_error_before_settled")
    result = await runtime.cancel(turn["id"])
    observed = await _events(runtime, turn["id"])
    assert result["status"] == "error"
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: provider unavailable before settled",
    }


async def test_pi_preserves_automatic_retry_error_detail(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "retry-error"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: provider quota exhausted",
    }


async def test_pi_preserves_stream_error_detail(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "stream-error"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: stream provider unavailable",
    }


async def test_pi_rejects_unknown_extension_ui_method(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "unknown-ui"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_protocol: unsupported pi extension UI method: mystery",
    }
    await _wait_for_command(tmp_path, "abort")


INVALID_CONTENTS = (
    ("unknown-content", "pi assistant content block is invalid"),
    ("non-string-content", "pi assistant text is invalid"),
)


@pytest.mark.parametrize(("prompt", "detail"), INVALID_CONTENTS)
async def test_pi_rejects_invalid_assistant_content(tmp_path, monkeypatch, prompt, detail):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": prompt})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": f"pi_protocol: {detail}",
    }
    await _wait_for_command(tmp_path, "abort")


async def test_pi_protocol_error_stops_the_fake_process(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "instructions": "system", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "invalid"})
    observed = await _events(runtime, turn["id"])
    await _wait_for_command(tmp_path, "abort")
    assert observed[-1]["data"]["status"] == "error"


async def test_pi_rejects_unknown_event_through_runtime(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "unknown"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_protocol: unsupported pi event: unknown",
    }
    await _wait_for_command(tmp_path, "abort")


async def test_pi_rejected_prompt_is_an_explicit_protocol_error(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "reject"})
    observed = await _events(runtime, turn["id"])
    await _wait_for_command(tmp_path, "abort")
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_protocol: pi rejected the prompt command",
    }


async def test_pi_adapter_cancels_a_turn_through_runtime(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "cancel"})
    await _wait_for_command(tmp_path, "prompt")
    result = await runtime.cancel(turn["id"])
    observed = await _events(runtime, turn["id"])
    await _wait_for_command(tmp_path, "abort")
    assert result["status"] == "cancelled"
    assert observed[-1]["data"] == {"status": "cancelled", "result_text": None}


async def test_pi_preserves_protocol_error_during_cancel(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(
        run["session_id"], {"id": "m1", "content": "cancel-protocol-error"}
    )
    await _wait_for_stage(tmp_path, "cancel-ready")
    result = await runtime.cancel(turn["id"])
    observed = await _events(runtime, turn["id"])
    assert result["status"] == "error"
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_protocol: unsupported pi event: unknown",
    }


async def test_pi_process_exit_is_an_explicit_turn_error(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "crash"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {"status": "error", "result_text": None, "error": "pi_process: pi exited with status 7"}


async def test_pi_eof_before_agent_end_is_a_protocol_error(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "incomplete"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {"status": "error", "result_text": None, "error": "pi_protocol: pi exited before agent_end"}


async def test_pi_eof_after_agent_end_requires_settled(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect()})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "missing-settled"})
    observed = await _events(runtime, turn["id"])
    assert observed[-1]["data"] == {"status": "error", "result_text": None, "error": "pi_protocol: pi exited before agent_settled"}


async def test_pi_settled_wait_is_bounded(tmp_path, monkeypatch):
    _fake_pi(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runtime = Runtime(tmp_path / "data", {"pi": PiAdapter.detect(timeout=0.05)})
    run = await runtime.launch({"adapter": "pi", "workspace": str(tmp_path)}, session_id="session-pi")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "timeout"})
    started = time.monotonic()
    observed = await _events(runtime, turn["id"])
    assert time.monotonic() - started < 1
    assert observed[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "pi_process: pi timed out after 0.05s",
    }


def test_pi_detection_reports_missing_executable(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(PiAdapterError, match="pi_not_found"):
        PiAdapter.detect()


def test_pi_detection_reports_incompatible_version(tmp_path, monkeypatch):
    _fake_pi(tmp_path, "0.85.0")
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    with pytest.raises(PiAdapterError, match="pi_configuration: unsupported pi version: 0.85.0"):
        PiAdapter.detect()
