import asyncio
import subprocess

import pytest
from runtime.providers.codex import CodexProvider, _collect
from runtime.runtimes import CodexRuntimeAdapter, REALM
from runtime.endpoints import Endpoint
from runtime.service import Runtime, _provider_context


def codex_runtime(tmp_path, provider):
    return Runtime(
        tmp_path / "data",
        [
            Endpoint(
                "codex",
                "Codex CLI",
                "unrelated",
                ("gpt-test",),
                (),
                200,
                None,
                available=True,
            )
        ],
        runtimes=[CodexRuntimeAdapter(provider)],
    )


def test_readiness_checks_version_without_exposing_probe_output(monkeypatch):
    calls = []
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda *args, **kwargs: (
            calls.append((args, kwargs))
            or subprocess.CompletedProcess([], 0, "codex-cli 0.149.1", "secret")
        ),
    )
    provider = CodexProvider.detected()
    assert provider is not None
    assert provider.version == "0.149.1"
    assert calls[0][0] == (["/bin/codex", "--version"],)
    assert calls[0][1]["stderr"] is subprocess.DEVNULL
    assert calls[1][0] == (["/bin/codex", "login", "status"],)
    assert calls[1][1]["stdout"] is subprocess.DEVNULL


def test_readiness_rejects_missing_or_invalid_version(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda *_, **__: subprocess.CompletedProcess([], 0, "unknown", "secret"),
    )
    assert CodexProvider.detected() is None


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
    responses = iter([subprocess.CompletedProcess([], 0, "codex-cli 0.149.1"), result])

    def run(*args, **kwargs):
        value = next(responses)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr("runtime.providers.codex.subprocess.run", run)
    provider = CodexProvider.detected()
    assert provider.status == status
    assert provider.reason == {"code": code, "probe": "login status"}


def test_codex_command_uses_official_exec_jsonl_contract():
    provider = CodexProvider("echo")
    context = {
        "workspace": "/tmp",
        "sandbox": "workspace-write",
        "reasoning_effort": "medium",
    }
    assert provider._command("gpt-test", context) == [
        provider.executable,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "-m",
        "gpt-test",
        "-c",
        'model_reasoning_effort="medium"',
        "-s",
        "workspace-write",
        "-",
    ]
    context["provider_session_id"] = "thread-1"
    assert provider._command("gpt-test", context) == [
        provider.executable,
        "exec",
        "resume",
        "--json",
        "--skip-git-repo-check",
        "-m",
        "gpt-test",
        "-c",
        'model_reasoning_effort="medium"',
        "thread-1",
        "-",
    ]


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
        b'{"type":"item.completed","item":{"type":"agent_message","text":"answer"}}\n'
        b'{"type":"turn.completed","usage":{"input_tokens":3,"output_tokens":2}}\n'
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
        b'{"type":"turn.cancelled"}',
    ],
)
async def test_collect_rejects_failed_or_cancelled_terminal(terminal):
    process = Process(
        b'{"type":"thread.started","thread_id":"thread-1"}\n'
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
        b'{"type":"item.completed","item":{"type":"agent_message","text":"late"}}\n',
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
    assert process.killed


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


async def test_runtime_records_declared_cli_trace_error(monkeypatch, tmp_path):
    provider = CodexProvider("echo")
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(b"not-json\n")))
    runtime = codex_runtime(tmp_path, provider)
    spec = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": "container:runtime"},
        "endpoint": "codex",
        "model": "gpt-test",
        "instructions": "Answer.",
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
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
    provider = CodexProvider("echo")
    process = Process(hang=True, returncode=None)
    started = asyncio.Event()

    release = asyncio.Event()

    async def start(*_, **__):
        started.set()
        await release.wait()
        return process

    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", start)
    runtime = codex_runtime(tmp_path, provider)
    spec = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": "container:runtime"},
        "endpoint": "codex",
        "model": "gpt-test",
        "instructions": "Answer.",
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    task = asyncio.create_task(
        runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    )
    await started.wait()
    runtime.cancel(launched["session_id"])
    release.set()
    assert (await task)["status"] == "cancelled"
    assert process.terminated
    assert runtime.inspect(launched["session_id"])["turns"][-1]["status"] == "cancelled"


async def test_cancel_terminates_process_group_after_child_exists(
    monkeypatch, tmp_path
):
    provider = CodexProvider("echo")
    process = TreeProcess(hang=True, returncode=None)
    started = asyncio.Event()

    async def communicate(prompt):
        started.set()
        return await Process.communicate(process, prompt)

    process.communicate = communicate
    monkeypatch.setattr(provider, "start", lambda *_: _process(process))
    monkeypatch.setattr("runtime.providers.codex.os.getpgid", lambda _: 71)
    monkeypatch.setattr(
        "runtime.providers.codex.os.killpg", lambda *_: process.terminate()
    )
    runtime = codex_runtime(tmp_path, provider)
    spec = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": "container:runtime"},
        "endpoint": "codex",
        "model": "gpt-test",
        "instructions": "Answer.",
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    task = asyncio.create_task(
        runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    )
    await started.wait()
    runtime.cancel(launched["session_id"])
    assert (await task)["status"] == "cancelled"
    assert not process.child_alive


async def test_runtime_preserves_capability_snapshot_and_recovers_resume(
    tmp_path, monkeypatch
):
    provider = CodexProvider("echo")
    contexts = []

    async def start(_, context):
        contexts.append(context)
        return Process(
            b'{"type":"thread.started","thread_id":"thread-1"}\n'
            b'{"type":"item.completed","item":{"type":"agent_message","text":"answer"}}\n'
            b'{"type":"turn.completed"}\n'
        )

    monkeypatch.setattr(provider, "start", start)
    runtime = codex_runtime(tmp_path, provider)
    spec = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": "container:runtime"},
        "endpoint": "codex",
        "model": "gpt-test",
        "instructions": "Answer.",
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "two"}])
    session = runtime.inspect(launched["session_id"])["session"]
    assert session["agent_spec"]["endpoint"] == "codex"
    snapshot = session["capability_snapshot"]["runtime"]
    assert set(snapshot) == {
        "id",
        "realm",
        "executable",
        "version",
        "status",
        "capabilities",
        "reason",
    }
    assert snapshot["id"] == "codex"
    assert snapshot["realm"] == "container:runtime"
    assert "streaming" not in snapshot["capabilities"]
    assert contexts[1]["provider_session_id"] == "thread-1"


async def test_idle_or_late_cancel_does_not_cancel_later_turn(monkeypatch, tmp_path):
    provider = CodexProvider("echo")
    monkeypatch.setattr(
        provider,
        "start",
        lambda *_: _process(
            Process(
                b'{"type":"thread.started","thread_id":"thread-1"}\n'
                b'{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
                b'{"type":"turn.completed"}\n'
            )
        ),
    )
    runtime = codex_runtime(tmp_path, provider)
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()})
    runtime.cancel(launched["session_id"])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    runtime.cancel(launched["session_id"])
    result = await runtime.prompt(
        launched["session_id"], [{"type": "text", "text": "two"}]
    )
    assert result["status"] == "completed"
    assert [turn["status"] for turn in runtime.inspect(launched["session_id"])["turns"]] == [
        "completed",
        "completed",
    ]


def _spec():
    return {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": REALM},
        "endpoint": "codex",
        "model": "gpt-test",
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
