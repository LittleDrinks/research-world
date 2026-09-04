import asyncio
import json
import subprocess
import sys

import pytest
from runtime.endpoints import Endpoint
from runtime.providers.pi import PiEventParser, PiProvider
from runtime.runtimes import PiRuntimeAdapter, REALM
from runtime.service import Runtime
from runtime.types import TraceError


FORBIDDEN_ENV = {
    "RUNTIME_API_KEY",
    "RUNTIME_API_BASE",
    "OPENAI_API_KEY",
    "ZAI_CODING_CN_API_KEY",
}


class RpcStdin:
    def __init__(self, process):
        self.process = process
        self.commands = []
        self.closed = False

    def write(self, data):
        text = data.decode() if isinstance(data, bytes) else data
        self.commands.extend(json.loads(line) for line in text.splitlines())
        self.process.events.append(self.commands[-1]["type"])

    async def drain(self):
        return None

    def is_closing(self):
        return self.closed

    def close(self):
        self.closed = True
        self.process.events.append("close")
        self.process.finish()

    async def wait_closed(self):
        return None


class RpcProcess:
    def __init__(self):
        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdin = RpcStdin(self)
        self.returncode = None
        self.pid = 4242
        self.events = []
        self.done = asyncio.Event()

    def feed(self, *events):
        for event in events:
            self.stdout.feed_data(_jsonl(event))

    def feed_raw(self, value):
        self.stdout.feed_data(value)

    def finish(self, returncode=0):
        if self.returncode is not None:
            return
        self.returncode = returncode
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self.done.set()

    async def wait(self):
        await self.done.wait()
        return self.returncode

    def terminate(self):
        self.events.append("terminate")
        self.finish(-15)

    def kill(self):
        self.events.append("kill")
        self.finish(-9)


async def test_start_uses_rpc_and_runtime_session_without_default_model(
    monkeypatch, tmp_path
):
    args, kwargs = await _launch(monkeypatch, tmp_path)

    assert _flag(args, "--mode") == "rpc"
    assert _flag(args, "--session-id") == "s-native"
    assert "--model" not in args
    assert {"--offline", "--no-approve"} <= set(args)
    assert _flag(args, "--append-system-prompt") == "system facts"
    assert kwargs["cwd"] == str(tmp_path)


async def test_start_does_not_inherit_runtime_or_provider_credentials(
    monkeypatch, tmp_path
):
    args, kwargs = await _launch(monkeypatch, tmp_path)
    environment = kwargs["env"]

    assert environment["HOME"] == "/pi-home"
    assert environment["PI_CODING_AGENT_DIR"] == "/pi-agent"
    assert not FORBIDDEN_ENV & environment.keys()
    assert "runtime-secret" not in str((args, environment))


async def test_prompt_ack_is_not_completion_and_only_latest_user_is_sent():
    provider, process, emitted = _provider(), RpcProcess(), []
    task = asyncio.create_task(provider.collect(process, _messages(), _capture(emitted), ("s-native",)))
    await _wait_for_command(process)
    command = process.stdin.commands[0]

    process.feed(_ack(command["id"]))
    await asyncio.sleep(0)
    assert not task.done()
    assert command["message"] == "latest" and "old" not in json.dumps(command)
    process.feed(*_successful_events())
    result = await asyncio.wait_for(task, 1)
    assert result.continuation_id == "s-native"
    assert process.stdin.closed and process.returncode == 0


async def test_collect_projects_text_final_usage_and_tool_lifecycle():
    provider, process, emitted = _provider(), RpcProcess(), []
    process.feed(_ack("prompt-1"), *_successful_events())
    collected = await provider.collect(
        process, _messages(), _capture(emitted), ("s-native",)
    )
    _assert_collection(collected, emitted)


def _assert_collection(collected, emitted):
    result, items = collected.result, collected.result.provider_items
    assert emitted == ["hel", "lo"]
    assert result.message == {"role": "assistant", "content": "hello"}
    assert result.usage == _expected_usage()
    _assert_tool_items(items)


def _assert_tool_items(items):
    assert [(item["phase"], item["item"]["id"]) for item in items] == [
        ("started", "tool-1"), ("completed", "tool-1")
    ]
    assert all("read" in json.dumps(item) for item in items)
    assert "README.md" in json.dumps(items[0])
    assert "contents" in json.dumps(items[1])


async def test_stop_sends_abort_and_converges():
    provider, process = _provider(), RpcProcess()

    await asyncio.wait_for(provider.stop(process), 1)

    assert process.stdin.commands[0]["type"] == "abort"
    assert process.events.index("abort") < len(process.events) - 1
    assert process.returncode is not None


def test_detection_accepts_only_the_pinned_pi_version(monkeypatch):
    result = subprocess.CompletedProcess([], 0, "0.84.3", "")
    provider = _detect(monkeypatch, result)
    assert (provider.status, provider.version, provider.reason) == (
        "ready", "0.84.3", None,
    )


def test_detection_distinguishes_missing_pi(monkeypatch):
    monkeypatch.setattr("runtime.providers.pi.shutil.which", lambda _: None)
    provider = PiProvider.detected()
    assert provider.status == "missing"
    assert provider.reason == {"code": "not_on_path", "probe": "path"}


@pytest.mark.parametrize(
    "result,status,code",
    [
        (subprocess.CompletedProcess([], 1, "", "failed"), "error", "probe_failed"),
        (subprocess.CompletedProcess([], 0, "unknown", ""), "error", "probe_invalid_output"),
        (subprocess.CompletedProcess([], 0, "0.85.0", ""), "incompatible", "version_incompatible"),
    ],
)
def test_detection_classifies_version_failures(monkeypatch, result, status, code):
    provider = _detect(monkeypatch, result)
    assert provider.status == status
    assert provider.reason == {"code": code, "probe": "version"}


def test_detection_classifies_version_timeout(monkeypatch):
    def timeout(_):
        raise subprocess.TimeoutExpired([], 5)

    monkeypatch.setattr("runtime.providers.pi.shutil.which", lambda _: sys.executable)
    monkeypatch.setattr("runtime.providers.pi._version_probe", timeout)
    provider = PiProvider.detected()
    assert provider.reason == {"code": "probe_timeout", "probe": "version"}


def test_thinking_events_project_as_reasoning_items():
    parser = PiEventParser()
    parser.consume({"type": "message_start", "message": _assistant("")})
    for event in _thinking_events():
        parser.consume(event)
    assert [item["phase"] for item in parser.items] == [
        "started", "updated", "completed",
    ]
    assert parser.items[-1]["item"]["text"] == "private reasoning"


async def test_runtime_restart_resumes_same_native_session_with_latest_turn(tmp_path):
    contexts, processes = [], []
    first = _runtime(tmp_path, _runtime_provider(contexts, processes))
    session = await _launch_pi(first, tmp_path)
    await first.prompt(session, [{"type": "text", "text": "one"}])
    await first.prompt(session, [{"type": "text", "text": "two"}])
    await first.close()
    restored = _runtime(tmp_path, _runtime_provider(contexts, processes))
    await restored.prompt(session, [{"type": "text", "text": "three"}])
    assert {item["runtime_session_id"] for item in contexts} == {session}
    assert [item.stdin.commands[0]["message"] for item in processes] == ["one", "two", "three"]
    assert restored.state.read(session)["provider_session_id"] == session
    await restored.close()


async def _launch(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "runtime.providers.pi.asyncio.create_subprocess_exec", _record(calls)
    )
    _credential_environment(monkeypatch)
    provider = _provider()
    await provider.start("default", _context(tmp_path), _messages())
    return calls[0]


def _record(calls):
    async def create(*args, **kwargs):
        calls.append((args, kwargs))
        return RpcProcess()
    return create


def _credential_environment(monkeypatch):
    monkeypatch.setenv("HOME", "/pi-home")
    monkeypatch.setenv("PI_CODING_AGENT_DIR", "/pi-agent")
    for name in FORBIDDEN_ENV:
        monkeypatch.setenv(name, "runtime-secret")


def _provider():
    return PiProvider(sys.executable, timeout=0.2)


def _detect(monkeypatch, result):
    monkeypatch.setattr("runtime.providers.pi.shutil.which", lambda _: sys.executable)
    monkeypatch.setattr("runtime.providers.pi._version_probe", lambda _: result)
    return PiProvider.detected()


def _runtime_provider(contexts, processes):
    provider = _provider()
    provider.status, provider.version = "ready", "0.84.3"
    provider.start = _runtime_start(contexts, processes)
    return provider


def _runtime_start(contexts, processes):
    async def start(_model, context, _messages):
        process = RpcProcess()
        process.runtime_session_id = context["runtime_session_id"]
        process.feed(_ack("prompt-1"), *_successful_events())
        contexts.append(context)
        processes.append(process)
        return process

    return start


def _runtime(tmp_path, provider):
    endpoint = Endpoint(
        "pi", "Pi local config", "pi", ("default",), (), 200, None,
        available=True,
    )
    return Runtime(tmp_path / "data", [endpoint], [PiRuntimeAdapter(provider)])


async def _launch_pi(runtime, tmp_path):
    value = {
        "workspace": str(tmp_path), "session_id": "s-native",
        "session_name": "Native thread", "agent_spec": _pi_spec(),
    }
    return (await runtime.launch(value))["session_id"]


def _pi_spec():
    return {
        "id": "pi-chat", "name": "Pi", "runtime": {"id": "pi", "realm": REALM},
        "endpoint": "pi", "model": "default", "instructions": "Answer.",
        "skills": [], "tools": [],
    }


def _context(tmp_path):
    return {
        "workspace": str(tmp_path),
        "sandbox": "workspace-write",
        "reasoning_effort": "medium",
        "runtime_session_id": "s-native",
        "session_name": "Native thread",
    }


def _messages():
    return [
        {"role": "system", "content": "system facts"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "latest"},
    ]


def _flag(args, name):
    return args[args.index(name) + 1]


async def _wait_for_command(process):
    for _ in range(20):
        if process.stdin.commands:
            return
        await asyncio.sleep(0)
    raise AssertionError("Pi prompt command was not written")


def _ack(command_id):
    return {
        "id": command_id,
        "type": "response",
        "command": "prompt",
        "success": True,
    }


def _rejected_ack():
    return {
        "id": "prompt-1",
        "type": "response",
        "command": "prompt",
        "success": False,
        "error": "model unavailable",
    }


def _successful_events():
    message = _assistant("hello")
    return [
        {"type": "agent_start"},
        _delta("hel"),
        _delta("lo"),
        _tool_start(),
        _tool_end(),
        {"type": "message_end", "message": message},
        {"type": "turn_end", "turnIndex": 0, "message": message, "toolResults": []},
        {"type": "agent_end", "messages": [message], "willRetry": False},
    ]


def _failed_events():
    message = _assistant("", "error", "provider denied request")
    return [
        {"type": "message_end", "message": message},
        {"type": "agent_end", "messages": [message], "willRetry": False},
    ]


def _delta(text):
    return {
        "type": "message_update",
        "usage": _usage(),
        "assistantMessageEvent": {
            "type": "text_delta", "contentIndex": 0, "delta": text,
        },
    }


def _thinking_events():
    base = {"type": "message_update", "usage": _usage()}
    return [
        {**base, "assistantMessageEvent": {"type": "thinking_start", "contentIndex": 0}},
        {**base, "assistantMessageEvent": {"type": "thinking_delta", "contentIndex": 0, "delta": "private "}},
        {**base, "assistantMessageEvent": {"type": "thinking_end", "contentIndex": 0, "content": "private reasoning"}},
    ]


def _tool_start():
    return {
        "type": "tool_execution_start",
        "toolCallId": "tool-1",
        "toolName": "read",
        "args": {"path": "README.md"},
    }


def _tool_end():
    return {
        "type": "tool_execution_end",
        "toolCallId": "tool-1",
        "toolName": "read",
        "result": {"content": [{"type": "text", "text": "contents"}]},
        "isError": False,
    }


def _assistant(text, stop_reason="stop", error=None):
    message = {
        "role": "assistant", "content": [{"type": "text", "text": text}],
        "api": "openai-completions", "provider": "test", "model": "test",
        "usage": _usage(), "stopReason": stop_reason, "timestamp": 1,
    }
    if error:
        message["errorMessage"] = error
    return message


def _usage():
    return {
        "input": 3, "output": 2, "cacheRead": 1, "cacheWrite": 4,
        "reasoning": 5, "totalTokens": 10,
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
    }


def _expected_usage():
    return {
        "input_tokens": 3,
        "cached_input_tokens": 1,
        "cache_write_input_tokens": 4,
        "output_tokens": 2,
        "reasoning_output_tokens": 5,
    }


def _extension_error():
    return {
        "type": "extension_error", "extensionPath": "extension.js",
        "event": "before_agent_start", "error": "extension failed",
    }


def _retry_exhausted():
    return {
        "type": "auto_retry_end", "success": False,
        "attempt": 3, "finalError": "retry exhausted",
    }


def _stream(*events):
    return b"".join(_jsonl(event) for event in events)


def _jsonl(event):
    return json.dumps(event, separators=(",", ":")).encode() + b"\n"


def _capture(values):
    async def emit(text):
        values.append(text)

    return emit


async def _ignore(_text):
    return None


@pytest.mark.parametrize(
    "raw, code",
    [
        (_stream(_ack("prompt-1")), "pi_incomplete_stream"),
        (b"not-json\n", "pi_invalid_jsonl"),
        (_stream(_rejected_ack()), "pi_rpc_rejected"),
        (_stream(_ack("prompt-1"), *_failed_events()), "pi_model_error"),
        (_stream(_ack("prompt-1"), _extension_error()), "pi_extension_error"),
        (_stream(_ack("prompt-1"), _retry_exhausted()), "pi_retry_exhausted"),
    ],
)
async def test_collect_fails_explicitly_for_rpc_and_stream_errors(raw, code):
    process = RpcProcess()
    process.feed_raw(raw)
    process.finish()

    with pytest.raises(TraceError) as raised:
        await _provider().collect(process, _messages(), _ignore, ("s-native",))
    assert raised.value.code == code
