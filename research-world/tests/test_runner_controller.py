import base64
import json

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


def test_input_file_cannot_escape_workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    encoded = base64.b64encode(b"data").decode()

    with pytest.raises(ValueError, match="escapes workspace"):
        runner_controller.write_files(root, {"../outside.txt": encoded})

    assert not (tmp_path / "outside.txt").exists()


def execution_spec(**changes):
    spec = {
        "image": "busybox:1.36",
        "command": ["true"],
        "files": {},
        "seed": 0,
        "limits": {"cpus": 1, "memory_mb": 64, "pids": 32},
    }
    return {**spec, **changes}
