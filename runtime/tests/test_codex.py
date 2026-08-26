import asyncio
import io
import json
import os
import platform
import shlex
import subprocess
import sys
import time
import traceback
from pathlib import Path

import pytest
from runtime.endpoints import Endpoint, load_endpoints
from runtime.providers.codex import (
    PROBE_CANDIDATE_TIMEOUT, CodexProvider, _collect, _environment, _freeze_executable, _probe,
    _sealed_snapshot, _taskkill,
)
from runtime.runtimes import CodexRuntimeAdapter, REALM, load_runtimes
from runtime.service import Runtime, _messages, _provider_context
from runtime.types import CapabilityNotFound, TraceError


@pytest.fixture(autouse=True)
def _codex_auth(monkeypatch, tmp_path):
    home = tmp_path / "credential-store"
    home.mkdir()
    (home / "auth.json").write_text('{"token":"test"}')
    monkeypatch.setenv("CODEX_HOME", str(home))


def codex_runtime(tmp_path, provider, model="gpt-5.6-sol"):
    return Runtime(tmp_path / "data", [_codex_endpoint(model)], runtimes=[CodexRuntimeAdapter(provider)])


def ready_provider(executable="echo"):
    provider = CodexProvider(executable)
    provider.status, provider.version = "ready", "0.149.1"
    return provider


class _Probe:
    def __init__(self, output="", returncode=0, error=None):
        self.output, self.returncode, self.error = output, returncode, error
        self.stdout = io.BytesIO(output.encode())
        self.stderr = io.BytesIO(b"secret")

    def wait(self, timeout):
        if self.error:
            raise self.error
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


def _budgeted_popen(clock, waits, values):
    def create(*_args, **_kwargs):
        process = values.pop(0)

        def wait(timeout):
            waits.append(timeout)
            clock[0] += min(timeout, 2.0)
            if timeout < 2.0:
                raise subprocess.TimeoutExpired([], timeout)
            return process.returncode

        process.wait = wait
        return process
    return create


def _cleanup_cost(clock):
    def cleanup(process, stdout, stderr, _deadline):
        stdout.value, stderr.value = process.output, ""
        clock[0] += 2.0
        return False
    return cleanup


def _linux_x64():
    return sys.platform == "linux" and platform.machine() in {"x86_64", "AMD64"}


def test_readiness_checks_version_without_exposing_probe_output(monkeypatch):
    calls = []
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: sys.executable)
    values = [_probe_result("codex-cli 0.149.1"), _probe_result()]
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen(calls, values))
    provider = CodexProvider.detected()
    assert provider is not None
    assert provider.version == "0.149.1"
    assert calls[0][0] == ([provider.executable, "--version"],)
    assert calls[0][1]["start_new_session"] is True
    assert set(calls[0][1]["env"]) == {"LANG", "PATH"}
    assert calls[1][0] == ([provider.executable, "login", "status"],)
    assert set(calls[1][1]["env"]) == {"CODEX_HOME", "HOME", "LANG", "PATH"}


def test_detection_shares_candidate_deadline_across_probes(monkeypatch):
    clock, waits = [0.0], []
    values = [_probe_result("codex-cli 0.149.1"), _probe_result()]
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: sys.executable)
    monkeypatch.setattr("runtime.providers.codex.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _budgeted_popen(clock, waits, values))
    monkeypatch.setattr("runtime.providers.codex._reader_cleanup_failed", _cleanup_cost(clock))
    provider = CodexProvider.detected()
    assert waits == [2.0, 1.0]
    assert provider.reason == {"code": "probe_timeout", "probe": "login status"}
    assert provider.status == "error" and "secret" not in str(provider.reason)


@pytest.mark.parametrize("session_id", [None, "thread-1"])
async def test_snapshot_failure_skips_probes_and_hides_source(monkeypatch, session_id):
    source = "/private/codex-source"
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: source)
    monkeypatch.setattr("runtime.providers.codex._freeze_executable", lambda _: None)
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _unexpected_probe)
    provider = CodexProvider.detected()

    assert provider.status == "error"
    assert provider.reason == {"code": "snapshot_unavailable", "probe": "snapshot"}
    assert provider.executable is None
    with pytest.raises(TraceError) as raised:
        await provider.start("gpt", _context(session_id))
    assert source not in str(raised.value)


def test_missing_libc_memfd_maps_to_snapshot_unavailable(monkeypatch):
    source = "/private/codex-source"
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: source)
    monkeypatch.setattr("runtime.providers.codex._snapshot_supported", lambda: True)
    monkeypatch.setattr("runtime.providers.codex._open_source", lambda _: 41)
    monkeypatch.delattr("runtime.providers.codex.os.memfd_create", raising=False)
    monkeypatch.setattr("runtime.providers.codex.ctypes.CDLL", lambda *_a, **_k: object())
    monkeypatch.setattr("runtime.providers.codex.os.close", lambda _: None)

    provider = CodexProvider.detected()
    descriptor = CodexRuntimeAdapter(provider).descriptor.public()

    assert provider.reason == {"code": "snapshot_unavailable", "probe": "snapshot"}
    assert source not in str(descriptor) and "/proc/self/fd/41" not in str(descriptor)


def test_freeze_keeps_snapshot_when_source_close_fails(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex._open_source", lambda _: 41)
    monkeypatch.setattr("runtime.providers.codex._sealed_snapshot", lambda _: 42)
    monkeypatch.setattr("runtime.providers.codex.os.close", _close_failure)

    assert _freeze_executable("/private/codex-source") == 42


def test_sealed_snapshot_keeps_copy_failure_when_close_fails(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex._memfd_create", lambda: 42)
    monkeypatch.setattr("runtime.providers.codex._copy_fd", _copy_failure)
    monkeypatch.setattr("runtime.providers.codex.os.close", _close_failure)

    with pytest.raises(OSError, match="copy"):
        _sealed_snapshot(41)


def _unexpected_probe(*_args, **_kwargs):
    raise AssertionError("snapshot failure must not probe the source")


def test_readiness_keeps_invalid_version_candidate(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: sys.executable)
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], [_probe_result("unknown")]))
    descriptor = load_runtimes()[0].descriptor.public()
    assert descriptor["status"] == "error"
    assert descriptor["reason"] == {"code": "probe_invalid_output", "probe": "version"}


def test_readiness_rejects_parseable_incompatible_version(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: sys.executable)
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
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: sys.executable)
    values = [_probe_result("codex-cli 0.149.1"), _probe_from(result)]
    monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], values))
    provider = CodexProvider.detected()
    assert provider.status == status
    assert provider.reason == {"code": code, "probe": "login status"}


def test_probe_caps_noisy_stdout_before_buffering(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.PROBE_OUTPUT_LIMIT", 128)
    result = _probe([sys.executable, "-c", "import sys;sys.stdout.write('x'*1000000)"], "test", deadline=time.monotonic() + PROBE_CANDIDATE_TIMEOUT)
    assert len(result.stdout) == 128
    assert result.stderr == ""


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_probe_kills_same_group_reader_child_and_returns_error(monkeypatch, tmp_path):
    monkeypatch.setattr("runtime.providers.codex.PROBE_CLEANUP_SLICE", 0.05)
    pid_file = tmp_path / "pid"
    child = f"import os,time;open({str(pid_file)!r},'w').write(str(os.getpid()));time.sleep(10)"
    parent = f"import pathlib,subprocess,sys,time;subprocess.Popen([sys.executable,'-c',{child!r}]);p=pathlib.Path({str(pid_file)!r});exec('while not p.exists(): time.sleep(.001)')"
    result = _probe([sys.executable, "-c", parent], "test", deadline=time.monotonic() + PROBE_CANDIDATE_TIMEOUT)
    assert result[2]["code"] == "probe_timeout"
    assert not _pid_exists(int(pid_file.read_text()))


def _pid_exists(pid):
    path = Path(f"/proc/{pid}/stat")
    for _ in range(50):
        if not path.exists() or path.read_text().split()[2] == "Z":
            return False
        time.sleep(0.01)
    return True


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
async def test_stop_kills_same_group_descendant_after_parent_exit(monkeypatch, tmp_path):
    monkeypatch.setattr("runtime.providers.codex.TERMINATE_TIMEOUT", 0.05)
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-c", _term_ignoring_parent(tmp_path / "pid"),
        start_new_session=True,
    )
    await process.wait()
    pid = int((tmp_path / "pid").read_text())
    await CodexProvider().stop(process)
    assert await _process_gone(pid)


def _term_ignoring_parent(path):
    child = f"import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);open({str(path)!r},'w').write(str(os.getpid()));time.sleep(10)"
    return f"import pathlib,subprocess,sys,time;subprocess.Popen([sys.executable,'-c',{child!r}]);p=pathlib.Path({str(path)!r});exec('while not p.exists(): time.sleep(.001)')"


async def _process_gone(pid):
    for _ in range(50):
        if not os.path.exists(f"/proc/{pid}"):
            return True
        await asyncio.sleep(0.01)
    return False


def test_codex_command_uses_official_exec_jsonl_contract():
    provider = ready_provider()
    assert provider._command("gpt-test", _context()) == _fresh_command(provider)
    assert provider._command("gpt-test", _context("thread-1")) == _resume_command(provider)


def test_runtime_dockerfile_pins_the_audited_codex_release():
    dockerfile = Path(__file__).parents[1] / "Dockerfile"
    content = dockerfile.read_text()
    assert "npm install --global @openai/codex@0.149.1-linux-x64" in content
    assert "vendor/x86_64-unknown-linux-musl/bin/codex" in content
    assert "codex.js" not in content and "/usr/local/bin/node" not in content


def _context(session_id=None):
    return {"workspace": "/tmp", "sandbox": "workspace-write", "reasoning_effort": "medium", "provider_session_id": session_id, "codex_home": "/tmp/sessions/s-one/codex-home"}


def _fresh_command(provider):
    return [provider.executable, "exec", "--json", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "--disable", "shell_tool", "-m", "gpt-test", "-c", 'model_reasoning_effort="medium"', "-s", "workspace-write", "-"]


def _resume_command(provider):
    return [provider.executable, "exec", "resume", "--json", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "--disable", "shell_tool", "-m", "gpt-test", "-c", 'model_reasoning_effort="medium"', "thread-1", "-"]


def test_codex_session_home_is_per_session_and_restart_stable(tmp_path):
    first = str(tmp_path / "sessions" / "s-one" / "codex-home")
    second = str(tmp_path / "sessions" / "s-two" / "codex-home")
    assert first != second and first.endswith("s-one/codex-home")


async def test_codex_session_copies_only_auth_into_restricted_child_environment(monkeypatch, tmp_path):
    source, calls = tmp_path / "credential-store", []
    (source / "config.toml").write_text("mcp_servers = {}")
    monkeypatch.setenv("RUNTIME_API_KEY", "runtime-secret")
    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", _record_launches(calls))
    runtime = codex_runtime(tmp_path, ready_provider())
    await _launch_and_prompt(runtime, tmp_path, "auth")
    home, environment = Path(calls[0][1]["env"]["CODEX_HOME"]), calls[0][1]["env"]
    assert (home / "auth.json").read_text() == (source / "auth.json").read_text()
    assert (home / "auth.json").stat().st_mode & 0o777 == 0o600
    assert not (home / "config.toml").exists() and set(environment) == _child_environment_keys()
    assert "RUNTIME_API_KEY" not in environment


def _child_environment_keys():
    return {"CODEX_HOME", "HOME", "LANG", "PATH"}


async def test_codex_launch_isolated_across_sessions_and_restart(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", _record_launches(calls))
    first = codex_runtime(tmp_path, ready_provider())
    one = await _launch_and_prompt(first, tmp_path, "one")
    await _launch_and_prompt(first, tmp_path, "two")
    await codex_runtime(tmp_path, ready_provider()).prompt(one, [{"type": "text", "text": "again"}])
    assert len({call[1]["env"]["CODEX_HOME"] for call in calls}) == 2
    assert all(_isolated_codex_command(call) for call in calls)


async def test_codex_rejects_selected_runtime_tools(tmp_path):
    runtime = codex_runtime(tmp_path, ready_provider())
    with pytest.raises(RuntimeError, match="cannot expose selected Tool"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec(tools=["publish_report"])})


def test_provider_context_reads_agent_options_and_session_id():
    meta = {"agent_spec": {"options": {"sandbox": "read-only"}}}
    state = {"workspace": "/tmp"}
    events = [{"session_id": "s-codex", "type": "session_meta", "data": {}}]
    context = _provider_context(meta, state, events)
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
    assert result.usage == _usage_values(3, 2)
    assert not hasattr(result, "provider_session_id")
    assert emitted == ["answer"]


async def test_collect_redacts_thread_id_before_public_results():
    process = Process(
        b'{"type":"thread.started","thread_id":"secret-thread"}\n'
        b'{"type":"turn.started"}\n'
        b'{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"secret-thread remains hidden"}}\n'
        b'{"type":"turn.completed","usage":{"input_tokens":3,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":2,"reasoning_output_tokens":0}}\n'
    )
    emitted = []

    async def emit(text):
        emitted.append(text)

    result = await _collect(process, "prompt", emit, 1)

    assert "secret-thread" not in str(result)
    assert "remains hidden" in result.message["content"]


async def test_runtime_never_persists_or_projects_collected_thread_id(monkeypatch, tmp_path):
    stream = (
        b'{"type":"thread.started","thread_id":"secret-thread"}\n'
        b'{"type":"turn.started"}\n'
        b'{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"secret-thread remains visible"}}\n'
        + _usage_line()
    )
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(stream)))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]

    result = await runtime.prompt(session, [{"type": "text", "text": "one"}])
    raw, view = runtime.trace.path(session).read_text(), runtime.inspect(session)

    assert "secret-thread" not in str((result, raw, view))
    assert "remains visible" in result["result_text"]


async def test_runtime_trace_preserves_all_codex_usage_counters(monkeypatch, tmp_path):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(_usage_stream())))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    result = await runtime.prompt(session, [{"type": "text", "text": "one"}])
    response = next(event for event in runtime.inspect(session)["events"] if event["type"] == "model_response")
    assert response["data"]["usage"] == _usage_values(3, 2, 1, 4, 5)
    assert result["usage"] == _usage_values(3, 2, 1, 4, 5)
    assert runtime.inspect(session)["turns"][0]["events"][-1]["data"]["usage"] == _usage_values(3, 2, 1, 4, 5)


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
    result = await task
    assert result["status"] == "cancelled"
    assert result["usage"] == _usage_values(0, 0, 0, 0, 0)
    assert process.terminated
    turn = runtime.inspect(session)["turns"][-1]
    assert turn["status"] == "cancelled"
    assert turn["events"][-1]["data"]["usage"] == _usage_values(0, 0, 0, 0, 0)
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


def _blocked_communicate(process, started, release):
    async def communicate(prompt):
        started.set()
        result = await Process.communicate(process, prompt)
        await release.wait()
        return result
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
    assert session["agent_spec"]["endpoint"] == "primary"
    assert {"runtime", "endpoint", "model", "instructions", "skills", "tools"} <= set(session["agent_spec"])
    assert session["agent_spec"]["runtime"] == {"id": "codex", "realm": "container:runtime"}
    snapshot = session["capability_snapshot"]["runtime"]
    assert set(snapshot) == _DESCRIPTOR_FIELDS
    assert "runtime_binding" not in session
    assert snapshot["id"] == "codex"
    assert snapshot["realm"] == "container:runtime"
    assert "streaming" not in snapshot["capabilities"]
    assert "adapter" not in session["endpoint_snapshot"]
    assert "executable" not in json.dumps(session)
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
    with pytest.raises(RuntimeError, match="persisted endpoint binding"):
        await codex_runtime(tmp_path, ready_provider(), "other").prompt(session, [])


async def test_fresh_runtime_rejects_changed_private_executable_identity(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", _resuming_start([]))
    first = codex_runtime(tmp_path, provider)
    session = (await first.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    assert first.state.read(session)["runtime_binding"]
    monkeypatch.setattr("runtime.providers.codex._executable_identity", lambda _: "changed")
    with pytest.raises(RuntimeError, match="persisted runtime executable"):
        await codex_runtime(tmp_path, ready_provider()).prompt(session, [])


async def test_unprobed_provider_is_not_advertised_ready(tmp_path):
    runtime = codex_runtime(tmp_path, CodexProvider("echo"))
    catalog = await runtime.recognize(str(tmp_path))
    assert next(item for item in catalog["runtimes"] if item["id"] == "codex")["status"] == "found"
    assert all(item["id"] != "codex" for item in catalog["endpoints"])


async def test_loaded_catalog_codex_rejects_unavailable_endpoint(tmp_path, monkeypatch):
    _catalog_endpoint(monkeypatch)
    runtime = Runtime(tmp_path / "data", load_endpoints(), runtimes=[CodexRuntimeAdapter(ready_provider())])
    catalog = await runtime.recognize(str(tmp_path))
    assert not catalog["endpoints"][0]["available"]
    with pytest.raises(CapabilityNotFound, match="endpoint is not available"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()})


@pytest.mark.parametrize("endpoint, model, error", [("missing", "gpt-5.6-sol", "endpoint"), ("primary", "missing", "model")])
async def test_loaded_catalog_codex_rejects_missing_declarations(tmp_path, monkeypatch, endpoint, model, error):
    _catalog_endpoint(monkeypatch)
    runtime = Runtime(tmp_path / "data", load_endpoints(), runtimes=[CodexRuntimeAdapter(ready_provider())])
    with pytest.raises(CapabilityNotFound, match=f"{error} is not available"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec(endpoint=endpoint, model=model)})


@pytest.mark.parametrize("path, result, status, code", [
    (None, None, "missing", "not_on_path"),
    (sys.executable, subprocess.TimeoutExpired([], 2), "error", "probe_timeout"),
])
def test_discovery_keeps_unready_codex_descriptor(monkeypatch, path, result, status, code):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: path)
    if result:
        monkeypatch.setattr("runtime.providers.codex.subprocess.Popen", _popen([], [_Probe(error=result)]))
    descriptor = load_runtimes()[0].descriptor.public()
    assert descriptor["status"] == status
    assert descriptor["reason"]["code"] == code
    assert "executable" not in descriptor
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


async def test_collect_accepts_release_completed_only_file_change():
    result = await _collect(Process(_release_valid_stream()), "prompt", _ignore, 1)
    assert result.message["content"] == "answer"


async def test_collect_rejects_started_file_change():
    events = [
        {"type": "item.started", "item": _file("in_progress")},
        {"type": "item.completed", "item": _file("completed")},
    ]
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(_stream(events)), "prompt", _ignore, 1)


async def test_collect_accepts_query_only_web_search():
    result = await _collect(Process(_stream(_query_only_web_events())), "prompt", _ignore, 1)
    assert result.provider_items[1]["item"]["action"] == {"type": "search", "query": "q"}


@pytest.mark.parametrize("action", [
    {"type": "open_page", "url": "https://example.test"},
    {"type": "find_in_page", "url": "https://example.test", "pattern": "q"},
    {"type": "other"}, {"type": "search", "query": "other"},
])
async def test_collect_rejects_nonquery_or_mismatched_web_actions(action):
    item = {"id": "web", "type": "web_search", "query": "q", "action": action}
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(_stream([{"type": "item.started", "item": item}])), "p", _ignore, 1)


async def test_collect_rejects_second_turn_after_terminal():
    stream = _stream([{"type": "item.completed", "item": _agent()}])
    stream += b'{"type":"turn.started"}\n'
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(stream), "p", _ignore, 1)


@pytest.mark.parametrize("phase, status", [("started", "completed"), ("completed", "in_progress")])
async def test_collect_rejects_mismatched_item_phase_status(phase, status):
    event = {"type": f"item.{phase}", "item": _command(status)}
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await _collect(Process(_stream([event])), "prompt", _ignore, 1)


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


async def test_failed_stream_redacts_current_and_result_continuations(tmp_path, monkeypatch):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(_continuation_failure_stream())))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    runtime.state.update(session, {"provider_session_id": "current-continuation"})

    with pytest.raises(RuntimeError, match="failed terminal stream"):
        await runtime.prompt(session, [{"type": "text", "text": "one"}])
    raw, public = runtime.trace.path(session).read_text(), runtime.inspect(session)
    assert all(value not in raw and value not in str(public) for value in ["current-continuation", "result-continuation"])
    assert "unrelated fact" in raw and "unrelated fact" in str(public)


async def test_completed_resumed_stream_redacts_current_and_result_continuations(tmp_path, monkeypatch):
    provider, contexts, emitted = ready_provider(), [], []
    monkeypatch.setattr(provider, "start", _resuming_continuation_start(contexts))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    runtime.state.update(session, {"provider_session_id": "current-continuation"})

    result = await runtime.prompt(session, [{"type": "text", "text": "one"}], emit=_capture(emitted))
    raw, public = runtime.trace.path(session).read_text(), runtime.inspect(session)

    assert contexts[0]["provider_session_id"] == "current-continuation"
    assert all(value not in str(item) for value in ["current-continuation", "result-continuation"] for item in [emitted, result, raw, public])
    assert "unrelated fact" in str((emitted, result, raw, public))


async def test_completed_stream_redacts_nested_continuation_key_everywhere(tmp_path, monkeypatch):
    provider, emitted = ready_provider(), []
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(_continuation_key_stream())))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]

    result = await runtime.prompt(session, [{"type": "text", "text": "one"}], emit=_capture(emitted))
    raw, public = runtime.trace.path(session).read_text(), runtime.inspect(session)

    assert all("result-continuation" not in str(item) for item in [emitted, result, raw, public])
    arguments = public["turns"][0]["provider_items"][0]["arguments"]
    assert set(arguments) == {"<redacted>", "<redacted>#2"}
    assert set(arguments.values()) == {"secret-value", "preserved-value"}


async def test_official_collab_child_continuations_are_private_at_every_boundary(tmp_path, monkeypatch):
    values = ["thread-parent-opaque", "thread-sender-opaque", "thread-receiver-opaque", "thread-state-key-opaque"]
    emitted, provider = [], ready_provider()
    stream = _collab_continuation_stream()
    collected = await provider.collect(Process(stream), [{"role": "user", "content": "p"}], _capture(emitted), ("parent",))
    assert collected.continuation_id == "thread-parent-opaque"
    assert all(value not in str(item) for value in values for item in [collected.result, emitted])
    monkeypatch.setattr(provider, "start", lambda *_: _process(Process(stream)))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    result = await runtime.prompt(session, [{"type": "text", "text": "one"}], emit=_capture(emitted))
    raw, public = runtime.trace.path(session).read_text(), runtime.inspect(session)
    assert all(value not in str(item) for value in values for item in [result, emitted, raw, public])
    assert "waiting for collaborator" in raw and "waiting for collaborator" in str(public)
    assert runtime.state.read(session)["provider_session_id"] == "thread-parent-opaque"


async def test_collect_keeps_assistant_text_for_short_thread_id():
    emitted = []
    result = await _collect(Process(_short_thread_stream()), "prompt", _capture(emitted), 1)

    assert emitted == ["an answer"]
    assert result.message["content"] == "an answer"
    assert result.provider_items[1]["item"]["arguments"]["thread"] == "<redacted>"


@pytest.mark.parametrize("session_id", [None, "thread-1"])
async def test_codex_executes_frozen_native_object_after_path_replacement(tmp_path, session_id):
    executable, replacement = tmp_path / "codex", tmp_path / "replacement"
    _native_script(executable, "frozen")
    provider = CodexProvider(str(executable))
    _native_script(replacement, "replacement")
    replacement.replace(executable)

    process = await provider.start("gpt", _context(session_id))
    stdout, _ = await process.communicate()

    assert stdout == b"frozen"


@pytest.mark.parametrize("session_id", [None, "thread-1"])
async def test_codex_identity_check_cannot_race_frozen_execution(tmp_path, session_id):
    executable, replacement = tmp_path / "codex", tmp_path / "replacement"
    _native_script(executable, "verified")
    provider = CodexProvider(str(executable))
    assert provider.executable_identity
    _native_script(replacement, "replacement")
    replacement.replace(executable)

    process = await provider.start("gpt", _context(session_id))
    stdout, _ = await process.communicate()

    assert stdout == b"verified"


@pytest.mark.skipif(not _linux_x64(), reason="sealed snapshots require Linux/x64")
def test_detection_probes_only_the_private_snapshot(monkeypatch, tmp_path):
    executable = tmp_path / "codex"
    _probe_mutating_script(executable)
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: str(executable))

    provider = CodexProvider.detected()

    assert provider.status == "ready"
    _close_provider(provider)


@pytest.mark.skipif(not _linux_x64(), reason="sealed snapshots require Linux/x64")
@pytest.mark.parametrize("mutation", ["replace", "overwrite"])
@pytest.mark.parametrize("session_id", [None, "thread-1"])
async def test_detected_snapshot_survives_source_mutation(tmp_path, monkeypatch, mutation, session_id):
    executable = tmp_path / "codex"
    _codex_script(executable, "snapshot")
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: str(executable))
    provider = CodexProvider.detected()
    _mutate_source(executable, mutation)

    process = await provider.start("gpt", _context(session_id))
    stdout, _ = await process.communicate()

    assert provider.status == "ready"
    assert stdout == b"snapshot"
    _close_provider(provider)


@pytest.mark.skipif(not _linux_x64(), reason="sealed snapshots require Linux/x64")
def test_provider_close_releases_all_snapshot_fds(tmp_path):
    executable = tmp_path / "codex"
    _codex_script(executable, "snapshot")
    baseline = _fd_count()
    providers = [CodexProvider(str(executable)) for _ in range(4)]

    assert _fd_count() >= baseline + len(providers)
    for provider in providers:
        provider.close()
    assert _fd_count() == baseline


@pytest.mark.skipif(not _linux_x64(), reason="sealed snapshots require Linux/x64")
async def test_runtime_close_releases_provider_snapshot(tmp_path):
    provider = ready_provider()
    descriptor = provider._fd
    runtime = codex_runtime(tmp_path, provider)

    await runtime.close()

    assert descriptor is not None
    assert not os.path.exists(f"/proc/self/fd/{descriptor}")


async def test_runtime_close_converges_active_and_pending_starts(monkeypatch, tmp_path):
    active, pending = Process(hang=True, returncode=None), Process(hang=True, returncode=None)
    active_ready, pending_ready, release, collect_release = (asyncio.Event() for _ in range(4))
    active.communicate = _blocked_communicate(active, active_ready, collect_release)
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", _active_then_pending(active, pending, pending_ready, release))
    monkeypatch.setattr("runtime.providers.codex.TERMINATE_TIMEOUT", 0.01)
    runtime = codex_runtime(tmp_path, provider)
    first = await _prompt_task(runtime, tmp_path, "s-active")
    await active_ready.wait()
    second = await _prompt_task(runtime, tmp_path, "s-pending")
    await pending_ready.wait()

    early, terminated = await _close_race(runtime, active, pending, release)
    adapter = runtime.runtimes._values[("codex", REALM)]

    try:
        assert not early and terminated
        assert not (adapter._starts or adapter._processes or adapter._stops or adapter._stopped)
    finally:
        collect_release.set()
        await asyncio.gather(first, second, return_exceptions=True)


async def test_os_exec_failure_hides_runtime_execution_details(monkeypatch, tmp_path):
    executable = tmp_path / "codex"
    _codex_script(executable, "snapshot")
    provider = ready_provider(str(executable))
    leaked = f"/proc/self/fd/{provider._fd} {executable} transport-private config-private"
    monkeypatch.setattr("runtime.providers.codex.asyncio.create_subprocess_exec", _os_exec_failure(leaked))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]

    with pytest.raises(RuntimeError) as raised:
        await runtime.prompt(session, [{"type": "text", "text": "one"}])
    raw, public = runtime.trace.path(session).read_text(), runtime.inspect(session)
    assert all(value not in str((raised.value, raw, public)) for value in leaked.split())
    assert raised.value.code == "cli_unavailable"
    assert raised.value.__cause__ is None and raised.value.__context__ is None
    assert all(value not in "".join(traceback.format_exception(raised.value)) for value in leaked.split())
    await _close_runtime(runtime, provider)


def _native_script(path, output):
    path.write_text(f"#!/bin/sh\nprintf {output}")
    path.chmod(0o755)


def _probe_mutating_script(path):
    source, replacement = shlex.quote(str(path)), shlex.quote("#!/bin/sh\nexit 7\n")
    path.write_text(f'''#!/bin/sh
if [ "$1" = "--version" ]; then
  printf %s {replacement} > {source}
  chmod 755 {source}
  printf 'codex-cli 0.149.1'
  exit 0
elif [ "$1" = "login" ]; then
  exit 0
fi
printf snapshot
''')
    path.chmod(0o755)


def _codex_script(path, output):
    path.write_text(f'''#!/bin/sh
if [ "$1" = "--version" ]; then
  printf 'codex-cli 0.149.1'
  exit 0
elif [ "$1" = "login" ]; then
  exit 0
fi
printf %s {shlex.quote(output)}
''')
    path.chmod(0o755)


def _mutate_source(path, mutation):
    if mutation == "replace":
        replacement = path.with_name("replacement")
        _codex_script(replacement, "replaced")
        replacement.replace(path)
        return
    _codex_script(path, "overwritten")


def _fd_count():
    return len(os.listdir("/proc/self/fd"))


def _close_provider(provider):
    close = getattr(provider, "close", None)
    if close is not None:
        close()


def _close_failure(*_args):
    raise OSError("close")


def _copy_failure(*_args):
    raise OSError("copy")


def _os_exec_failure(leaked):
    async def fail(*_args, **_kwargs):
        raise OSError(f"unable to exec {leaked}")
    return fail


async def _close_runtime(runtime, provider):
    close = getattr(runtime, "close", None)
    if close is not None:
        await close()
    elif provider._fd is not None:
        os.close(provider._fd)


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


def _continuation_failure_stream():
    error = {"id": "error", "type": "error", "message": "current-continuation result-continuation unrelated fact"}
    rows = [{"type": "thread.started", "thread_id": "result-continuation"}, {"type": "turn.started"}, {"type": "item.completed", "item": error}, {"type": "turn.failed", "error": {"message": error["message"]}}]
    return b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"


def _continuation_completed_stream():
    text = "current-continuation result-continuation unrelated fact"
    return _stream([{"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "text": text}}], thread_id="result-continuation")


def _continuation_key_stream():
    item = {"id": "mcp", "type": "mcp_tool_call", "server": "s", "tool": "t", "arguments": {"result-continuation": "secret-value", "<redacted>": "preserved-value"}, "result": None, "error": None, "status": "completed"}
    return _stream([{"type": "item.started", "item": {**item, "status": "in_progress"}}, {"type": "item.completed", "item": item}, {"type": "item.completed", "item": _agent()}], thread_id="result-continuation")


def _collab_continuation_stream():
    item = {
        "id": "collab", "type": "collab_tool_call", "tool": "wait",
        "sender_thread_id": "thread-sender-opaque", "receiver_thread_ids": ["thread-receiver-opaque"],
        "prompt": "thread-parent-opaque thread-sender-opaque thread-receiver-opaque thread-state-key-opaque",
        "agents_states": {"thread-state-key-opaque": {"status": "running", "message": "waiting for collaborator"}},
        "status": "completed",
    }
    return _stream([{"type": "item.started", "item": {**item, "status": "in_progress"}}, {"type": "item.completed", "item": item}, {"type": "item.completed", "item": _agent()}], thread_id="thread-parent-opaque")


def _short_thread_stream():
    item = {**_mcp("completed"), "arguments": {"thread": "a"}}
    return _stream([{"type": "item.started", "item": {**item, "status": "in_progress"}}, {"type": "item.completed", "item": item}, {"type": "item.completed", "item": {"id": "one", "type": "agent_message", "text": "an answer"}}], thread_id="a")


def _query_only_web_events():
    item = {"id": "web", "type": "web_search", "query": "q", "action": {"type": "search", "query": "q"}}
    return [{"type": "item.started", "item": item}, {"type": "item.completed", "item": item}, {"type": "item.completed", "item": _agent()}]


def _stream(events, failed=False, thread_id="one"):
    rows = [{"type": "thread.started", "thread_id": thread_id}, {"type": "turn.started"}, *events]
    rows.append({"type": "turn.failed", "error": {"message": "fatal"}} if failed else _usage())
    return b"\n".join(json.dumps(row, separators=(",", ":")).encode() for row in rows) + b"\n"


def _official_items():
    return [
        {"type": "item.completed", "item": _reasoning()}, {"type": "item.completed", "item": _error()},
        {"type": "item.started", "item": _command("in_progress")}, {"type": "item.completed", "item": _command("completed")},
        {"type": "item.completed", "item": _file("completed")},
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


async def test_cached_binding_rechecks_executable_identity(monkeypatch, tmp_path):
    provider = ready_provider()
    monkeypatch.setattr(provider, "start", lambda *_: _process(_completed_process()))
    runtime = codex_runtime(tmp_path, provider)
    session = (await runtime.launch({"workspace": str(tmp_path), "agent_spec": _spec()}))["session_id"]
    await runtime.prompt(session, [{"type": "text", "text": "one"}])
    runtime.state.update(session, {"runtime_binding": "different"})

    with pytest.raises(RuntimeError, match="persisted runtime executable"):
        await runtime.prompt(session, [{"type": "text", "text": "two"}])


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


def test_provider_session_uses_private_state():
    meta = {"session_id": "s", "type": "session_meta", "data": {}}
    state = {"workspace": "/tmp", "provider_session_id": "good"}
    context = _provider_context({"agent_spec": {"options": {}}}, state, [meta])
    assert context["provider_session_id"] == "good"


def _replay_events():
    return [
        _turn_start("cancelled", "drop"), _turn_end("cancelled", "cancelled"),
        _turn_start("keep", "keep"),
    ]


def _turn_start(turn_id, text):
    return {"type": "turn_start", "turn_id": turn_id, "data": {"prompt": [{"type": "text", "text": text}]}}


def _turn_end(turn_id, status):
    return {"type": "turn_end", "turn_id": turn_id, "data": {"status": status}}


_DESCRIPTOR_FIELDS = {"id", "realm", "display_name", "version", "source", "last_checked_at", "status", "capabilities", "reason"}


def _completed_process():
    return Process(b'{"type":"thread.started","thread_id":"thread-1"}\n{"type":"turn.started"}\n{"type":"item.completed","item":{"id":"one","type":"agent_message","text":"answer"}}\n' + _usage_line())


def _usage_line():
    return b'{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":1,"reasoning_output_tokens":0}}\n'


def _usage_values(input_tokens, output_tokens, cached=0, cache_write=0, reasoning=0):
    return {"input_tokens": input_tokens, "cached_input_tokens": cached, "cache_write_input_tokens": cache_write, "output_tokens": output_tokens, "reasoning_output_tokens": reasoning}


def _usage_stream():
    return b'{"type":"thread.started","thread_id":"thread-1"}\n{"type":"turn.started"}\n{"type":"item.completed","item":{"id":"one","type":"agent_message","text":"answer"}}\n{"type":"turn.completed","usage":{"input_tokens":3,"cached_input_tokens":1,"cache_write_input_tokens":4,"output_tokens":2,"reasoning_output_tokens":5}}\n'


def _codex_endpoint(model):
    return Endpoint("primary", "Primary", "openai-compatible", (model,), (), 1, None, available=True)


def _catalog_endpoint(monkeypatch):
    value = [{"id": "primary", "name": "Primary", "adapter": "openai-compatible", "models": ["gpt-5.6-sol"], "embedding_models": [], "base_url_env": "UNUSED_BASE", "api_key_env": "UNUSED_KEY", "priority": 1}]
    monkeypatch.setenv("RUNTIME_ENDPOINTS", json.dumps(value))


def _resuming_start(contexts):
    async def start(_, context):
        contexts.append(context)
        return _completed_process()
    return start


def _resuming_continuation_start(contexts):
    async def start(_, context):
        contexts.append(context)
        return Process(_continuation_completed_stream())
    return start


def _capture(values):
    async def emit(text):
        values.append(text)
    return emit


def _record_launches(calls):
    async def create(*args, **kwargs):
        calls.append((args, kwargs))
        return _completed_process()
    return create


async def _launch_and_prompt(runtime, path, session_id):
    launched = await runtime.launch({"workspace": str(path), "agent_spec": _spec(), "session_id": f"s-{session_id}"})
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": session_id}])
    return launched["session_id"]


def _isolated_codex_command(call):
    args, kwargs = call
    flags = {"--ignore-user-config", "--ignore-rules", "--disable", "shell_tool"}
    return flags <= set(args) and bool(kwargs["env"]["CODEX_HOME"])


def _created_after(started, ready, process):
    async def start(*_args, **_kwargs):
        started.set()
        await ready.wait()
        return process
    return start


def _active_then_pending(active, pending, started, release):
    calls = 0

    async def start(*_args):
        nonlocal calls
        calls += 1
        if calls == 1:
            return active
        started.set()
        await release.wait()
        return pending

    return start


async def _prompt_task(runtime, path, session_id):
    await runtime.launch({"workspace": str(path), "agent_spec": _spec(), "session_id": session_id})
    return asyncio.create_task(runtime.prompt(session_id, [{"type": "text", "text": "one"}]))


async def _close_race(runtime, active, pending, release):
    closers = [asyncio.create_task(runtime.close()) for _ in range(2)]
    early = await _finishes(closers[0])
    release.set()
    await asyncio.gather(*closers)
    terminated = active.terminated and pending.terminated
    pending.terminate()
    return early, terminated


async def _finishes(task):
    try:
        await asyncio.wait_for(asyncio.shield(task), 0.1)
    except TimeoutError:
        return False
    return True


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


def _spec(**extra):
    value = {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "codex", "realm": REALM},
        "endpoint": "primary",
        "model": "gpt-5.6-sol",
        "instructions": "Answer.",
    }
    value.update(extra)
    return value


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
