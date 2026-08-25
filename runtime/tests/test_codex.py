import asyncio
import json
import subprocess

import pytest
from runtime.providers.codex import CodexProvider, _collect, _taskkill
from runtime.runtimes import CodexRuntimeAdapter, REALM, load_runtimes
from runtime.service import Runtime, _messages, _provider_context


def codex_runtime(tmp_path, provider):
    return Runtime(tmp_path / "data", [], runtimes=[CodexRuntimeAdapter(provider)])


def ready_provider(executable="echo"):
    provider = CodexProvider(executable)
    provider.status, provider.version = "ready", "0.149.1"
    return provider


class _Probe:
    def __init__(self, output="", returncode=0, error=None):
        self.output, self.returncode, self.error = output, returncode, error

    def communicate(self, timeout):
        if self.error:
            raise self.error
        return self.output, "secret"

    def wait(self, timeout):
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


def _probe_result(output="", returncode=0):
    return _Probe(output, returncode)


def _probe_from(value):
    if isinstance(value, subprocess.CompletedProcess):
        return _probe_result(returncode=value.returncode)
    return _Probe(error=value)


def _popen(calls, values):
    def create(*args, **kwargs):
        calls.append((args, kwargs))
        value = values.pop(0)
        if isinstance(value, FileNotFoundError):
            raise value
        return value
    return create


def test_readiness_checks_version_without_exposing_probe_output(monkeypatch):
    calls = []
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    values = [_probe_result("codex-cli 0.149.1"), _probe_result()]
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen(calls, values))
    provider = CodexProvider.detected()
    assert provider is not None
    assert provider.version == "0.149.1"
    assert calls[0][0] == (["/bin/codex", "--version"],)
    assert calls[0][1]["start_new_session"] is True
    assert calls[1][0] == (["/bin/codex", "login", "status"],)


def test_readiness_keeps_invalid_version_candidate(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], [_probe_result("unknown")]))
    descriptor = load_runtimes()[1].descriptor.public()
    assert descriptor["status"] == "error"
    assert descriptor["reason"] == {"code": "probe_invalid_output", "probe": "version"}


def test_readiness_rejects_parseable_incompatible_version(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], [_probe_result("codex-cli 0.149.2")]))
    provider = CodexProvider.detected()
    assert provider.status == "unsupported"
    assert provider.reason == {"code": "version_incompatible", "probe": "version"}


@pytest.mark.parametrize(
    "result, status, code",
    [
        (subprocess.CompletedProcess([], 1), "auth-required", "auth_missing"),
        (subprocess.TimeoutExpired([], 2), "error", "probe_timeout"),
        (FileNotFoundError(), "found", "auth_probe_unavailable"),
    ],
)
def test_readiness_uses_only_safe_login_status(monkeypatch, result, status, code):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    values = [_probe_result("codex-cli 0.149.1"), _probe_from(result)]
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], values))
    provider = CodexProvider.detected()
    assert provider.status == status
    assert provider.reason == {"code": code, "probe": "login status"}


def test_codex_command_uses_official_exec_jsonl_contract():
    provider = ready_provider()
    assert provider._command("gpt-test", _context()) == _fresh_command(provider)
    assert provider._command("gpt-test", _context("thread-1")) == _resume_command(provider)


def _context(session_id=None):
    return {"workspace": "/tmp", "sandbox": "workspace-write", "reasoning_effort": "medium", "provider_session_id": session_id}


def _fresh_command(provider):
    return [provider.executable, "exec", "--json", "--skip-git-repo-check", "-m", "gpt-test", "-c", 'model_reasoning_effort="medium"', "-s", "workspace-write", "-"]


def _resume_command(provider):
    return [provider.executable, "exec", "resume", "--json", "--skip-git-repo-check", "-m", "gpt-test", "-c", 'model_reasoning_effort="medium"', "thread-1", "-"]


def test_provider_context_reads_agent_options_and_session_id():
    meta = {"workspace": "/tmp", "agent_spec": {"options": {"sandbox": "read-only"}}}
    events = [{"session_id": "s-codex", "type": "session_meta", "data": {}}]
    context = _provider_context(meta, events)
    assert context["sandbox"] == "read-only"
    assert context["runtime_session_id"] == "s-codex"


class Process:
    def __init__(self, stdout=b"", stderr=b"", returncode=0, hang=False):
        self.stdout, self.stderr, self.returncode, self.hang = (
            stdout,
            stderr,
            returncode,
            hang,
        )
        self.killed = self.terminated = False
        self.stopped = asyncio.Event()

    async def communicate(self, _prompt):
        if self.hang:
            await self.stopped.wait()
        return self.stdout, self.stderr

    def kill(self):
        self.killed, self.returncode = True, -9

    def terminate(self):
        self.terminated, self.returncode = True, -15
        self.stopped.set()

    async def wait(self):
        return self.returncode


async def test_collect_normalizes_jsonl_into_model_result():
    process = Process(
        b'{"type":"thread.started","thread_id":"thread-1"}\n'
        b'{"type":"turn.started"}\n'
        b'{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"answer"}}\n'
        b'{"type":"turn.completed","usage":{"input_tokens":3,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":2,"reasoning_output_tokens":0}}\n'
    )
    emitted = []

    async def emit(text):
        emitted.append(text)

    result = await _collect(process, "prompt", emit, 1)
    assert result.message == {"role": "assistant", "content": "answer"}
    assert result.usage == {"prompt_tokens": 3, "completion_tokens": 2}
    assert result.provider_session_id == "thread-1"
    assert emitted == ["answer"]


@pytest.mark.parametrize(
    "process, message",
    [
        (Process(returncode=2, stderr=b"secret"), "exited 2"),
        (Process(b"not-json\n"), "invalid JSONL"),
        (Process(b'["wrong"]\n'), "invalid JSONL"),
        (Process(b'{"type":"turn.completed","usage":[]}\n'), "invalid JSONL"),
        (
            Process(
                b'{"type":"thread.started","thread_id":"thread-1"}\n'
                b'{"type":"turn.started"}\n'
                b'{"type":"turn.failed","error":{"message":"failed"}}\n'
            ),
            "failed terminal stream",
        ),
    ],
)
async def test_collect_rejects_cli_errors_without_stderr(process, message):
    with pytest.raises(RuntimeError, match=message) as raised:
        await _collect(process, "prompt", lambda _: None, 1)
    assert "secret" not in str(raised.value)


@pytest.mark.parametrize(
    "event",
    [
        b'{"type":"thread.started"}\n',
        b'{"type":"thread.started","thread_id":[]}\n',
        b'{"type":"thread.started","thread_id":" "}\n',
        b'{"type":"item.completed"}\n',
        b'{"type":"item.completed","item":[]}\n',
        b'{"type":"item.completed","item":{"type":[]}}\n',
        b'{"type":"item.completed","item":{"type":"agent_message"}}\n',
        b'{"type":"item.completed","item":{"type":"agent_message","text":{}}}\n',
        b'{"type":"turn.completed","usage":[]}\n',
        b'{"type":"turn.completed","usage":{"input_tokens":true}}\n',
        b'{"type":"turn.completed","usage":{"output_tokens":-1}}\n',
        b'{"type":[]}\n',
    ],
)
async def test_collect_rejects_malformed_event_shapes(event):
    process = Process(event + b'{"type":"turn.completed"}\n')
    with pytest.raises(RuntimeError, match="invalid JSONL") as raised:
        await _collect(process, "prompt", lambda _: None, 1)
    assert getattr(raised.value, "code") == "cli_invalid_jsonl"


@pytest.mark.parametrize(
    "terminal",
    [
        b'{"type":"turn.failed","error":{"message":"failed"}}',
    ],
)
async def test_collect_rejects_failed_terminal(terminal):
    process = Process(
        b'{"type":"thread.started","thread_id":"thread-1"}\n'
        b'{"type":"turn.started"}\n'
        + terminal
        + b"\n"
    )
    with pytest.raises(RuntimeError, match="failed terminal stream") as raised:
        await _collect(process, "prompt", lambda _: None, 1)
    assert getattr(raised.value, "code") == "cli_stream_failed"


@pytest.mark.parametrize(
    "stream",
    [
        b'{"type":"turn.completed"}\n',
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"turn.completed"}\n',
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"turn.completed"}\n'
        b'{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"late"}}\n',
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"turn.cancelled"}\n'
        b'{"type":"turn.completed"}\n',
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"turn.failed","error":{"message":[]}}\n',
        b'{"type":"thread.started","thread_id":"one"}\n'
        b'{"type":"turn.failed","error":{}}\n',
    ],
)
async def test_collect_rejects_ambiguous_stream_state(stream):
    with pytest.raises(RuntimeError, match="invalid JSONL") as raised:
        await _collect(Process(stream), "prompt", lambda _: None, 1)
    assert raised.value.code == "cli_invalid_jsonl"


async def test_codex_timeout_kills_process():
    process = Process(hang=True, returncode=None)
    with pytest.raises(RuntimeError, match="timed out after"):
        await _collect(process, "prompt", lambda _: None, 0.001)
    assert process.terminated


async def test_timeout_uses_term_then_kill_sequence():
    process = Process(hang=True, returncode=None)
    calls = []
    process.terminate = lambda: calls.append("term")
    process.kill = lambda: (calls.append("kill"), setattr(process, "returncode", -9), process.stopped.set())
    with pytest.raises(RuntimeError, match="timed out after"):
        await _collect(process, "prompt", _ignore, 0.001)
    assert calls == ["term", "kill"]


async def test_timeout_kills_the_process_group_child(monkeypatch):
    process = TreeProcess(hang=True, returncode=None)
    monkeypatch.setattr("runtime.providers.codex.os.getpgid", lambda _: 71)
    monkeypatch.setattr("runtime.providers.codex.os.killpg", lambda *_: process.kill())
    with pytest.raises(RuntimeError, match="timed out after"):
        await _collect(process, "prompt", lambda _: None, 0.001)
    assert not process.child_alive


async def test_windows_timeout_kills_process_tree_without_sigkill(monkeypatch):
    process = TreeProcess(hang=True, returncode=None)
    calls = []
    monkeypatch.setattr("runtime.providers.codex.os.name", "nt")
    monkeypatch.delattr("runtime.providers.codex.signal.SIGKILL")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda args, **_: calls.append(args) or process.kill(),
    )
    with pytest.raises(RuntimeError, match="timed out after") as raised:
        await _collect(process, "prompt", lambda _: None, 0.001)
    assert raised.value.code == "cli_timeout"
    assert calls == [["taskkill", "/PID", "71", "/T", "/F"]]
    assert not process.child_alive


def test_windows_taskkill_is_bounded(monkeypatch):
    process = TreeProcess(returncode=None)
    monkeypatch.setattr("runtime.providers.codex.os.name", "nt")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired([], 2)),
    )
    _taskkill(process)
    assert process.returncode is None


async def test_runtime_records_declared_cli_trace_error(monkeypatch, tmp_path):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(b"not-json\n")))
    runtime = codex_runtime(tmp_path, provider)
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()})
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    error = runtime.inspect(launched["session_id"])["events"][-2]["data"]
    assert error == {
        "code": "cli_invalid_jsonl",
        "message": "codex returned invalid JSONL",
    }


async def _process(process):
    return process


async def test_cancel_terminates_active_process(monkeypatch, tmp_path):
    provider = ready_provider()
    process = Process(hang=True, returncode=None)
    started, release = asyncio.Event(), asyncio.Event()
    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", _created_after(started, release, process))
    runtime = codex_runtime(tmp_path, provider)
    task, session = await _active_task(runtime, tmp_path, started)
    runtime.cancel(session)
    release.set()
    assert (await task)["status"] == "cancelled"
    assert process.terminated
    assert runtime.inspect(session)["turns"][-1]["status"] == "cancelled"
    assert not runtime.runtimes._values[("codex", REALM)]._processes


async def test_cancel_terminates_process_group_after_child_exists(
    monkeypatch, tmp_path
):
    provider = ready_provider()
    process = TreeProcess(hang=True, returncode=None)
    started = asyncio.Event()
    process.communicate = _started_communicate(process, started)
    monkeypatch.setattr(provider, "start", lambda *_: _process(process))
    monkeypatch.setattr("runtime.providers.codex.os.getpgid", lambda _: 71)
    monkeypatch.setattr(
        "runtime.providers.codex.os.killpg", lambda *_: process.terminate()
    )
    runtime = codex_runtime(tmp_path, provider)
    task, session = await _active_task(runtime, tmp_path, started)
    runtime.cancel(session)
    assert (await task)["status"] == "cancelled"
    assert not process.child_alive


def _started_communicate(process, started):
    async def communicate(prompt):
        started.set()
        return await Process.communicate(process, prompt)
    return communicate


async def test_explicit_cancel_drives_bounded_stop_and_unregisters(monkeypatch, tmp_path):
    provider, process, stopped = ready_provider(), TreeProcess(returncode=None), asyncio.Event()
    monkeypatch.setattr(provider, "stop", _stops_process(process, stopped))
    runtime = codex_runtime(tmp_path, provider)
    adapter = runtime.runtimes._values[("codex", REALM)]
    session = "s-cancel"
    runtime._active_turns[session] = ("t-cancel", adapter)
    adapter._processes[session] = process
    runtime.cancel(session)
    await adapter._stops[session]
    assert stopped.is_set() and not process.child_alive and not adapter._processes


async def test_runtime_preserves_capability_snapshot_and_recovers_resume(
    tmp_path, monkeypatch
):
    provider = ready_provider()
    contexts = []
    monkeypatch.setattr(provider, "start", _resuming_start(contexts))
    runtime = codex_runtime(tmp_path, provider)
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()})
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "two"}])
    session = runtime.inspect(launched["session_id"])["session"]
    assert session["agent_spec"]["endpoint"] == "codex"
    snapshot = session["capability_snapshot"]["runtime"]
    assert set(snapshot) == _DESCRIPTOR_FIELDS
    assert "runtime_binding" not in session
    assert snapshot["id"] == "codex"
    assert snapshot["realm"] == "container:runtime"
    assert "streaming" not in snapshot["capabilities"]
    assert contexts[1]["provider_session_id"] == "thread-1"


async def test_fresh_runtime_restores_the_persisted_binding(tmp_path, monkeypatch):
    first, second, contexts = ready_provider(), ready_provider(), []
    monkeypatch.setattr(first, "start", _resuming_start([]))
    runtime = codex_runtime(tmp_path, first)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    await runtime.prompt(session, [{"type": "text", "text": "one"}])
    monkeypatch.setattr(second, "start", _resuming_start(contexts))
    restored = codex_runtime(tmp_path, second)
    result = await restored.prompt(session, [{"type": "text", "text": "two"}])
    assert result["status"] == "completed"
    assert contexts[0]["provider_session_id"] == "thread-1"


async def test_fresh_runtime_rejects_changed_persisted_endpoint(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", _resuming_start([]))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    monkeypatch.setenv("CODEX_MODEL", "other")
    with pytest.raises(RuntimeError, match="persisted endpoint binding"):
        await codex_runtime(tmp_path, ready_provider()).prompt(session, [])


async def test_fresh_runtime_rejects_changed_private_executable_identity(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", _resuming_start([]))
    first = codex_runtime(tmp_path, provider)
    session = (await first.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    assert first.trace.read(session)[0]["data"]["runtime_binding"]["runtime"]
    monkeypatch.setattr("runtime.providers.codex._executable_identity", lambda _: "changed")
    with pytest.raises(RuntimeError, match="persisted runtime executable"):
        await codex_runtime(tmp_path, ready_provider()).prompt(session, [])


async def test_unprobed_provider_is_not_advertised_ready(tmp_path):
    runtime = codex_runtime(tmp_path, CodexProvider("echo"))
    catalog = await runtime.recognize(str(tmp_path))
    assert next(item for item in catalog["runtimes"] if item["id"] == "codex")["status"] == "found"
    assert all(item["id"] != "codex" for item in catalog["endpoints"])


@pytest.mark.parametrize("path, result, status, code", [
    (None, None, "missing", "not_on_path"),
    ("/bin/codex", subprocess.TimeoutExpired([], 2), "error", "probe_timeout"),
])
def test_discovery_keeps_unready_codex_descriptor(monkeypatch, path, result, status, code):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: path)
    if result:
        monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], [_Probe(error=result)]))
    descriptor = load_runtimes()[1].descriptor.public()
    assert descriptor["status"] == status
    assert descriptor["reason"]["code"] == code
    assert descriptor["executable"] == "codex"
    assert {"display_name", "source", "last_checked_at"} <= set(descriptor)
    assert not {"path", "resolved_path"} & set(descriptor)


async def test_collect_accepts_complete_item_lifecycle():
    stream = b'{"type":"thread.started","thread_id":"one"}\n{"type":"turn.started"}\n'
    stream += b'{"type":"item.started","item":{"id":"one","type":"todo_list","items":[]}}\n'
    stream += b'{"type":"item.updated","item":{"id":"one","type":"todo_list","items":[]}}\n'
    stream += b'{"type":"item.completed","item":{"id":"one","type":"todo_list","items":[]}}\n'
    stream += b'{"type":"item.completed","item":{"id":"answer","type":"agent_message","text":"ok"}}\n'
    stream += _usage_line()
    result = await _collect(Process(stream), "prompt", lambda _: asyncio.sleep(0), 1)
    assert result.message["content"] == "ok"


async def test_collect_accepts_release_completed_only_items_and_updates():
    result = await _collect(Process(_release_valid_stream()), "prompt", _ignore, 1)
    assert result.message["content"] == "answer"


async def test_inspect_projects_every_official_item_and_repeated_update(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(_all_items_stream())))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    await runtime.prompt(session, [{"type": "text", "text": "one"}])
    turn = runtime.inspect(session)["turns"][0]
    assert {item["type"] for item in turn["provider_items"]} == _official_types()
    phases = [event["data"]["phase"] for event in turn["events"] if event["type"] == "provider_item"]
    assert phases.count("updated") == 2 and turn["provider_items"][-1]["type"] == "agent_message"


async def test_failed_stream_persists_items_and_terminal_error(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(_failed_stream())))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    with pytest.raises(RuntimeError, match="failed terminal stream"):
        await runtime.prompt(session, [{"type": "text", "text": "one"}])
    events = runtime.inspect(session)["turns"][0]["events"]
    assert [event["type"] for event in events][-4:] == ["provider_item", "provider_terminal", "error", "turn_end"]


@pytest.mark.parametrize("item", [
    {"id": "x", "type": "future_item"},
    {"id": "x", "type": "agent_message", "text": "x", "extra": True},
])
async def test_collect_rejects_unknown_official_item_forms(item):
    stream = _stream([{"type": "item.completed", "item": item}])
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(stream), "prompt", _ignore, 1)


async def test_collect_accepts_top_level_error_before_failed_turn():
    stream = b'{"type":"thread.started","thread_id":"one"}\n'
    stream += b'{"type":"turn.started"}\n{"type":"error","message":"fatal"}\n'
    stream += b'{"type":"turn.failed","error":{"message":"fatal"}}\n'
    with pytest.raises(RuntimeError, match="failed terminal stream") as raised:
        await _collect(Process(stream), "prompt", _ignore, 1)
    assert raised.value.code == "cli_stream_failed"


def _release_valid_stream():
    rows = [
        b'{"type":"thread.started","thread_id":"one"}', b'{"type":"turn.started"}',
        b'{"type":"item.completed","item":{"id":"a","type":"agent_message","text":"answer"}}',
        b'{"type":"item.completed","item":{"id":"r","type":"reasoning","text":"summary"}}',
        b'{"type":"item.completed","item":{"id":"w","type":"error","message":"warning"}}',
        b'{"type":"item.started","item":{"id":"f","type":"file_change","changes":[],"status":"in_progress"}}',
        b'{"type":"item.completed","item":{"id":"f","type":"file_change","changes":[],"status":"completed"}}',
        b'{"type":"item.started","item":{"id":"t","type":"todo_list","items":[]}}',
        b'{"type":"item.updated","item":{"id":"t","type":"todo_list","items":[]}}',
        b'{"type":"item.updated","item":{"id":"t","type":"todo_list","items":[]}}',
        b'{"type":"item.completed","item":{"id":"t","type":"todo_list","items":[]}}',
        _usage_line().strip(), b"",
    ]
    return b"\n".join(rows)


def _all_items_stream():
    return _stream(_official_items() + [{"type": "item.completed", "item": _agent()}])


def _failed_stream():
    return _stream([{"type": "item.completed", "item": _error()}], failed=True)


def _stream(events, failed=False):
    rows = [{"type": "thread.started", "thread_id": "one"}, {"type": "turn.started"}, *events]
    rows.append({"type": "turn.failed", "error": {"message": "fatal"}} if failed else _usage())
    return b"\n".join(json.dumps(row, separators=(",", ":")).encode() for row in rows) + b"\n"


def _official_items():
    return [
        {"type": "item.completed", "item": _reasoning()}, {"type": "item.completed", "item": _error()},
        {"type": "item.started", "item": _command("in_progress")}, {"type": "item.completed", "item": _command("completed")},
        {"type": "item.started", "item": _file("in_progress")}, {"type": "item.completed", "item": _file("completed")},
        {"type": "item.started", "item": _mcp("in_progress")}, {"type": "item.completed", "item": _mcp("completed")},
        {"type": "item.started", "item": _collab("in_progress")}, {"type": "item.completed", "item": _collab("completed")},
        {"type": "item.started", "item": _web()}, {"type": "item.completed", "item": _web()}, *_todos(),
    ]


def _official_types():
    return {"agent_message", "reasoning", "command_execution", "file_change", "mcp_tool_call", "collab_tool_call", "web_search", "todo_list", "error"}


def _agent():
    return {"id": "agent", "type": "agent_message", "text": "answer"}


def _reasoning():
    return {"id": "reason", "type": "reasoning", "text": "summary"}


def _error():
    return {"id": "error", "type": "error", "message": "warning"}


def _command(status):
    return {"id": "command", "type": "command_execution", "command": "pwd", "aggregated_output": "", "exit_code": 0, "status": status}


def _file(status):
    return {"id": "file", "type": "file_change", "changes": [{"path": "a", "kind": "update"}], "status": status}


def _mcp(status):
    return {"id": "mcp", "type": "mcp_tool_call", "server": "s", "tool": "t", "arguments": {}, "result": None, "error": None, "status": status}


def _collab(status):
    return {"id": "collab", "type": "collab_tool_call", "tool": "wait", "sender_thread_id": "s", "receiver_thread_ids": [], "prompt": None, "agents_states": {}, "status": status}


def _web():
    return {"id": "web", "type": "web_search", "query": "q", "action": {"type": "search", "query": "q", "queries": ["q"]}}


def _todos():
    item = {"id": "todo", "type": "todo_list", "items": [{"text": "x", "completed": False}]}
    return [{"type": "item.started", "item": item}, {"type": "item.updated", "item": item}, {"type": "item.updated", "item": item}, {"type": "item.completed", "item": item}]


def _usage():
    return {"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}}


async def _ignore(_text):
    return None


@pytest.mark.parametrize("stream", [
    b'{"type":"item.completed","item":{"type":"agent_message","text":"x"}}\n{"type":"thread.started","thread_id":"one"}\n{"type":"turn.completed"}\n',
    b'{"type":"thread.started","thread_id":"one"}\n{"type":"turn.started"}\n',
])
async def test_collect_rejects_illegal_lifecycle_order(stream):
    with pytest.raises(RuntimeError):
        await _collect(Process(stream), "prompt", lambda _: None, 1)


@pytest.mark.parametrize("item_events", [
    b'{"type":"item.updated","item":{"id":"one","type":"agent_message"}}\n',
    b'{"type":"item.started","item":{"id":"one","type":"agent_message"}}\n{"type":"item.completed","item":{"id":"one","type":"agent_message","text":"x"}}\n{"type":"item.completed","item":{"id":"one","type":"agent_message","text":"x"}}\n',
    b'{"type":"item.started","item":{"id":"one","type":"agent_message"}}\n',
    b'{"type":"item.started","item":{"type":"agent_message"}}\n',
])
async def test_collect_rejects_invalid_item_lifecycle(item_events):
    stream = b'{"type":"thread.started","thread_id":"one"}\n{"type":"turn.started"}\n'
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(stream + item_events + b'{"type":"turn.completed"}\n'), "p", lambda _: None, 1)


async def test_launch_binding_ignores_adapter_replacement(monkeypatch, tmp_path):
    original, replacement = ready_provider(), ready_provider()
    monkeypatch.setattr(original, "start", lambda *_: _process(_completed_process()))
    monkeypatch.setattr(replacement, "start", lambda *_: _process(Process(b"broken\n")))
    runtime = codex_runtime(tmp_path, original)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    runtime.runtimes._values[("codex", REALM)] = CodexRuntimeAdapter(replacement)
    assert (await runtime.prompt(session, [{"type": "text", "text": "one"}]))["status"] == "completed"


async def test_caller_cancellation_during_start_stops_created_process(monkeypatch, tmp_path):
    provider, process = ready_provider(), Process(hang=True, returncode=None)
    started, ready = asyncio.Event(), asyncio.Event()
    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", _created_after(started, ready, process))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    task = asyncio.create_task(runtime.prompt(session, [{"type": "text", "text": "one"}]))
    await started.wait()
    task.cancel()
    ready.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.terminated
    assert runtime.inspect(session)["turns"][-1]["status"] == "cancelled"


async def test_caller_cancellation_stops_and_unregisters_process(monkeypatch, tmp_path):
    provider, process, started = ready_provider(), TreeProcess(hang=True, returncode=None), asyncio.Event()
    async def communicate(prompt):
        started.set()
        return await Process.communicate(process, prompt)
    process.communicate = communicate
    monkeypatch.setattr(provider, "start", lambda *_: _process(process))
    monkeypatch.setattr("runtime.providers.codex.os.getpgid", lambda _: 71)
    monkeypatch.setattr("runtime.providers.codex.os.killpg", lambda *_: process.terminate())
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    task = asyncio.create_task(runtime.prompt(session, [{"type": "text", "text": "one"}]))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    adapter = runtime.runtimes._values[("codex", REALM)]
    assert not process.child_alive and not adapter._processes


async def test_idle_or_late_cancel_does_not_cancel_later_turn(monkeypatch, tmp_path):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(_completed_process()))
    runtime = codex_runtime(tmp_path, provider)
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()})
    runtime.cancel(launched["session_id"])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    runtime.cancel(launched["session_id"])
    result = await runtime.prompt(
        launched["session_id"], [{"type": "text", "text": "two"}]
    )
    assert result["status"] == "completed"
    assert [turn["status"] for turn in runtime.inspect(launched["session_id"])["turns"]] == ["completed"] * 2


def test_cancelled_or_unfinished_turns_are_not_replayed():
    messages = _messages(_replay_events(), {"agent_spec": _spec()})
    assert messages == [
        {"role": "system", "content": "Answer."},
        {"role": "user", "content": "keep"},
    ]


def test_provider_session_uses_only_completed_replayable_turn():
    events = [
        _turn_start("done", "keep"), {"type": "model_response", "turn_id": "done", "data": {"provider_session_id": "good"}}, _turn_end("done", "completed"),
        _turn_start("cancelled", "drop"), {"type": "model_response", "turn_id": "cancelled", "data": {"provider_session_id": "bad"}}, _turn_end("cancelled", "cancelled"),
        _turn_start("open", "drop"), {"type": "model_response", "turn_id": "open", "data": {"provider_session_id": "open"}},
    ]
    meta = {"session_id": "s", "type": "session_meta", "data": {}}
    assert _provider_context({"workspace": "/tmp", "agent_spec": {"options": {}}}, [meta, *events])["provider_session_id"] == "good"


def _replay_events():
    return [
        _turn_start("cancelled", "drop"), _turn_end("cancelled", "cancelled"),
        _turn_start("keep", "keep"),
    ]


def _turn_start(turn_id, text):
    return {"type": "turn_start", "turn_id": turn_id, "data": {"prompt": [{"type": "text", "text": text}]}}


def _turn_end(turn_id, status):
    return {"type": "turn_end", "turn_id": turn_id, "data": {"status": status}}


_DESCRIPTOR_FIELDS = {"id", "realm", "display_name", "executable", "version", "source", "last_checked_at", "status", "capabilities", "reason"}


def _completed_process():
    return Process(b'{"type":"thread.started","thread_id":"thread-1"}\n{"type":"turn.started"}\n{"type":"item.completed","item":{"id":"one","type":"agent_message","text":"answer"}}\n' + _usage_line())


def _usage_line():
    return b'{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":1,"reasoning_output_tokens":0}}\n'


def _resuming_start(contexts):
    async def start(_, context):
        contexts.append(context)
        return _completed_process()
    return start


def _created_after(started, ready, process):
    async def start(*_args, **_kwargs):
        started.set()
        await ready.wait()
        return process
    return start


def _stops_process(process, stopped):
    async def stop(_process):
        stopped.set()
        process.kill()

    return stop


async def _active_task(runtime, tmp_path, started):
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    task = asyncio.create_task(runtime.prompt(session, [{"type": "text", "text": "one"}]))
    await started.wait()
    return task, session


def _spec():
    return {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": REALM},
        "endpoint": "codex",
        "model": "gpt-5.6-sol",
        "instructions": "Answer.",
    }


class TreeProcess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pid = 71
        self.child_alive = True

    def kill(self):
        self.child_alive = False
        super().kill()

    def terminate(self):
        self.child_alive = False
        super().terminate()
