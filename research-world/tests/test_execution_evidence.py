import pytest

from server.clients import RunnerClient
from server.execution_evidence import (
    build_evidence,
    compare_replay,
    verify_evidence,
)


def test_hashes_are_stable_across_file_order():
    first = build_evidence(spec({"b.py": "Yg==", "a.py": "YQ=="}), output())
    second = build_evidence(spec({"a.py": "YQ==", "b.py": "Yg=="}), output())

    assert first["input_hash"] == second["input_hash"]
    assert first["content_hash"] == second["content_hash"]
    assert all(field in first for field in (*spec(), *output()))


def test_verification_detects_tampered_output():
    evidence = build_evidence(spec(), output())
    evidence["stdout"] = "changed"

    check = verify_evidence(evidence)

    assert check["ok"] is False
    assert check["code"] == "content_hash_mismatch"


def test_replay_distinguishes_input_and_content_mismatch():
    expected = build_evidence(spec(), output())
    changed_input = build_evidence(spec(command=["echo", "changed"]), output())
    changed_output = build_evidence(spec(), output(stdout="changed"))

    assert compare_replay(expected, changed_input)["code"] == "input_mismatch"
    assert compare_replay(expected, changed_output)["code"] == "content_mismatch"
    assert compare_replay(expected, expected)["ok"] is True


def test_runner_client_rejects_tampered_evidence(monkeypatch):
    evidence = build_evidence(spec(), output())
    response = Response({**evidence, "stdout": "changed"})
    monkeypatch.setattr("server.clients.httpx.post", lambda *args, **kwargs: response)

    result = RunnerClient("http://runner").run({"execution_id": "step:one", **spec()})

    assert result["failure"]["code"] == "content_hash_mismatch"


def test_command_must_be_an_array():
    with pytest.raises(ValueError, match="array"):
        build_evidence(spec(command="python main.py"), output())


def test_unrecorded_execution_input_is_rejected():
    with pytest.raises(ValueError, match="Additional properties"):
        build_evidence({**spec(), "network": "host"}, output())


def spec(files=None, **changes):
    value = {
        "image": "python:3.12-slim",
        "command": ["python", "main.py"],
        "files": files or {},
        "seed": 7,
        "limits": {"cpus": 1, "memory_mb": 128, "pids": 32},
    }
    return {**value, **changes}


def output(**changes):
    return {
        "exit_code": 0,
        "stdout": "result\n",
        "stderr": "",
        **changes,
    }


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload
