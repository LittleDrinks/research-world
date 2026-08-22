import base64

import pytest

from server import runner_controller


def test_execution_id_reuses_persisted_result(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    calls = []

    def execute(spec):
        calls.append(spec)
        return {"exit_code": 0, "stdout": "done"}

    monkeypatch.setattr(runner_controller, "run_container", execute)
    first = runner_controller.run_once("step:one", {"command": ["true"]})
    second = runner_controller.run_once("step:one", {"command": ["changed"]})

    assert first == second
    assert first["execution_id"] == "step:one"
    assert calls == [{"command": ["true"]}]


def test_invalid_base64_is_a_persisted_execution_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("RW_DATA_ROOT", str(tmp_path))
    spec = {"files": {"input.txt": "not base64"}}

    first = runner_controller.run_once("step:invalid", spec)
    second = runner_controller.run_once("step:invalid", {})

    assert first == second
    assert first["exit_code"] == 2
    assert "base64" in first["stderr"]


def test_input_file_cannot_escape_workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    encoded = base64.b64encode(b"data").decode()

    with pytest.raises(ValueError, match="escapes workspace"):
        runner_controller.write_files(root, {"../outside.txt": encoded})

    assert not (tmp_path / "outside.txt").exists()
