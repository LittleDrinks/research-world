import base64
import json
import subprocess

import pytest

from server import runner_controller


def test_execution_id_reuses_only_matching_input(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    calls = []

    def execute(spec):
        calls.append(spec)
        return {"exit_code": 0, "stdout": "done"}

    monkeypatch.setattr(runner_controller, "run_container", execute)
    spec = execution_spec(command=["true"])
    first = runner_controller.run_once("step:one", spec)
    second = runner_controller.run_once("step:one", spec)
    mismatch = runner_controller.run_once(
        "step:one", execution_spec(command=["changed"])
    )

    assert first == second
    assert first["execution_id"] == "step:one"
    assert mismatch["failure"]["code"] == "input_mismatch"
    assert calls == [spec]


def test_invalid_base64_is_a_persisted_execution_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    spec = execution_spec(files={"input.txt": "not base64"})

    first = runner_controller.run_once("step:invalid", spec)
    second = runner_controller.run_once("step:invalid", spec)

    assert first == second
    assert first["exit_code"] == 2
    assert "base64" in first["stderr"]


def test_persisted_result_tampering_is_a_structured_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(
        runner_controller,
        "run_container",
        lambda spec: {"exit_code": 0, "stdout": "done", "stderr": ""},
    )
    spec = execution_spec()
    runner_controller.run_once("step:tampered", spec)
    path = runner_controller.execution_path("step:tampered")
    persisted = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**persisted, "stdout": "changed"}), encoding="utf-8")

    result = runner_controller.run_once("step:tampered", spec)

    assert result["failure"]["code"] == "stored_content_hash_mismatch"


def test_missing_execution_id_is_a_structured_failure():
    result = runner_controller.run(execution_spec())

    assert result["failure"]["code"] == "invalid_execution_id"


def test_probe_executes_without_persisting_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(
        runner_controller, "run_container", lambda spec: {"exit_code": 0, "stdout": "ok"}
    )

    result = runner_controller.probe(execution_spec())

    assert result["exit_code"] == 0
    assert not (tmp_path / "executions").exists()


def test_input_file_cannot_escape_workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    encoded = base64.b64encode(b"data").decode()

    with pytest.raises(ValueError, match="escapes workspace"):
        runner_controller.write_files(root, {"../outside.txt": encoded})

    assert not (tmp_path / "outside.txt").exists()


def test_docker_command_names_and_isolates_container():
    command = runner_controller.docker_command(execution_spec(), None, "rw-run-fixed")

    assert command[:4] == ["docker", "run", "--rm", "--name"]
    assert command[4] == "rw-run-fixed"
    assert ["--pull", "never"] == command[5:7]
    assert ["--network", "none"] == command[7:9]
    assert "--read-only" in command
    assert "/tmp:rw,noexec,nosuid,size=64m" in command
    assert ["--cpus", "1"] == command[command.index("--cpus") :][:2]
    assert ["--memory", "64m"] == command[command.index("--memory") :][:2]
    assert ["--pids-limit", "32"] == command[command.index("--pids-limit") :][:2]


def test_image_inspection_never_starts_or_pulls(monkeypatch):
    calls = []
    monkeypatch.setattr(
        runner_controller.subprocess,
        "run",
        lambda command, **options: calls.append((command, options))
        or subprocess.CompletedProcess(command, 0, "", ""),
    )

    assert runner_controller.inspect_image({"image": "ai4sci-lean4:4.33.1"}) == {
        "available": True
    }
    assert calls[0][0] == ["docker", "image", "inspect", "ai4sci-lean4:4.33.1"]


def test_wall_timeout_removes_container_and_returns_structured_result(monkeypatch):
    calls = []

    def run(command, **options):
        calls.append((command, options))
        if command[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(command, options["timeout"])
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner_controller.secrets, "token_hex", lambda size: "fixed")
    monkeypatch.setattr(runner_controller.subprocess, "run", run)

    result = runner_controller.invoke_container(execution_spec(), None)

    assert calls[0][0][3:5] == ["--name", "rw-run-fixed"]
    assert calls[0][1]["timeout"] == 300
    assert calls[1][0] == ["docker", "rm", "-f", "rw-run-fixed"]
    assert result["exit_code"] == 124
    assert result["stdout"] == ""
    assert result["stderr"] == "timeout"
    assert result["usage"]["wall_ms"] >= 0


def execution_spec(**changes):
    spec = {
        "image": "busybox:1.36",
        "command": ["true"],
        "files": {},
        "seed": 0,
        "limits": {
            "cpus": 1,
            "memory_mb": 64,
            "pids": 32,
            "wall_seconds": 300,
        },
    }
    return {**spec, **changes}
