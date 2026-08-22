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
