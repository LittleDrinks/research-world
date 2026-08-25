import asyncio
import subprocess

import pytest
from runtime.providers.codex import CodexProvider, _collect
from runtime.runtimes import REALM, RuntimeAdapter, RuntimeDescriptor
from runtime.service import Runtime, _provider_context
from tests.helpers import endpoint


def test_readiness_checks_version_without_exposing_probe_output(monkeypatch):
    called = {}
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda *args, **kwargs: called.update(args=args, kwargs=kwargs) or subprocess.CompletedProcess([], 0, "codex-cli 0.149.1", "secret"),
    )
    provider = CodexProvider.detected()
    assert provider is not None
    assert provider.version == "0.149.1"
    assert called["args"] == (['/bin/codex', '--version'],)
    assert called["kwargs"]["stderr"] is subprocess.DEVNULL


def test_readiness_rejects_missing_or_invalid_version(monkeypatch):
    monkeypatch.setattr("runtime.providers.codex.shutil.which", lambda _: "/bin/codex")
    monkeypatch.setattr(
        "runtime.providers.codex.subprocess.run",
        lambda *_, **__: subprocess.CompletedProcess([], 0, "unknown", "secret"),
    )
    assert CodexProvider.detected() is None


def test_codex_command_uses_official_exec_jsonl_contract():
    provider = CodexProvider("echo")
    context = {"workspace": "/tmp", "sandbox": "workspace-write"}
    assert provider._command("gpt-test", context) == [
        provider.executable, "exec", "--json", "--skip-git-repo-check", "-m",
        "gpt-test", "-c", 'model_reasoning_effort="medium"', "-s",
        "workspace-write", "-",
    ]
    context["provider_session_id"] = "thread-1"
    assert provider._command("gpt-test", context) == [
        provider.executable, "exec", "resume", "--json", "--skip-git-repo-check",
        "-m", "gpt-test", "-c", 'model_reasoning_effort="medium"', "thread-1", "-",
    ]


def test_provider_context_reads_agent_options_and_session_id():
    meta = {"workspace": "/tmp", "agent_spec": {"options": {"sandbox": "read-only"}}}
    events = [{"session_id": "s-codex", "type": "session_meta", "data": {}}]
    context = _provider_context(meta, events)
    assert context["sandbox"] == "read-only"
    assert context["runtime_session_id"] == "s-codex"


class Process:
    def __init__(self, stdout=b"", stderr=b"", returncode=0, hang=False):
        self.stdout, self.stderr, self.returncode, self.hang = stdout, stderr, returncode, hang
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


@pytest.mark.parametrize("process, message", [(Process(returncode=2, stderr=b"secret"), "exited 2"), (Process(b"not-json\n"), "invalid JSONL"), (Process(b'["wrong"]\n'), "invalid JSONL"), (Process(b'{"type":"turn.completed","usage":[]}\n'), "invalid JSONL"), (Process(b'{"type":"turn.failed"}\n'), "failed terminal stream")])
async def test_collect_rejects_cli_errors_without_stderr(process, message):
    with pytest.raises(RuntimeError, match=message) as raised:
        await _collect(process, "prompt", lambda _: None, 1)
    assert "secret" not in str(raised.value)


async def test_codex_timeout_kills_process():
    process = Process(hang=True, returncode=None)
    with pytest.raises(RuntimeError, match="timed out after"):
        await _collect(process, "prompt", lambda _: None, 0.001)
    assert process.killed


async def test_runtime_records_declared_cli_trace_error(monkeypatch, tmp_path):
    provider = CodexProvider("echo")
    monkeypatch.setattr(provider, "_start", lambda *_: _process(Process(b"not-json\n")))
    runtime = Runtime(
        tmp_path / "data", [endpoint(provider, "codex", ("gpt-test",))],
        runtimes=[RuntimeAdapter(RuntimeDescriptor("codex", REALM))],
    )
    spec = {"id": "researcher", "name": "Researcher", "runtime": {"id": "codex", "realm": "container:runtime"}, "endpoint": "codex", "model": "gpt-test", "instructions": "Answer."}
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    with pytest.raises(RuntimeError, match="invalid JSONL"):
        await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    error = runtime.inspect(launched["session_id"])["events"][-2]["data"]
    assert error == {"code": "cli_invalid_jsonl", "message": "codex returned invalid JSONL"}


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
    runtime = Runtime(tmp_path / "data", [endpoint(provider, "codex", ("gpt-test",))])
    spec = {"id": "researcher", "name": "Researcher", "runtime": {"id": "codex", "realm": "container:runtime"}, "endpoint": "codex", "model": "gpt-test", "instructions": "Answer."}
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    task = asyncio.create_task(runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}]))
    await started.wait()
    runtime.cancel(launched["session_id"])
    release.set()
    assert (await task)["status"] == "cancelled"
    assert process.terminated
    assert runtime.inspect(launched["session_id"])["turns"][-1]["status"] == "cancelled"


async def test_runtime_preserves_capability_snapshot_and_recovers_resume(tmp_path):
    provider = ScriptedProvider()
    runtime = Runtime(tmp_path / "data", [endpoint(provider, "codex", ("gpt-test",))])
    spec = {"id": "researcher", "name": "Researcher", "runtime": {"id": "codex", "realm": "container:runtime"}, "endpoint": "codex", "model": "gpt-test", "instructions": "Answer."}
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec})
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "one"}])
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "two"}])
    session = runtime.inspect(launched["session_id"])["session"]
    assert session["agent_spec"]["endpoint"] == "codex"
    snapshot = session["capability_snapshot"]["runtime"]
    assert set(snapshot) == {"id", "realm", "executable", "version", "status", "capabilities"}
    assert snapshot["id"] == "codex"
    assert snapshot["realm"] == "container:runtime"
    assert provider.contexts[1]["provider_session_id"] == "thread-1"


class ScriptedProvider:
    id = "codex"

    def __init__(self):
        self.contexts = []

    async def generate(self, model, messages, tools, emit, context):
        self.contexts.append(context)
        text = "first" if len(self.contexts) == 1 else "second"
        await emit(text)
        return type("Result", (), {"message": {"role": "assistant", "content": text}, "usage": {}, "provider_session_id": "thread-1"})()

    async def embed(self, model, texts):
        return []
