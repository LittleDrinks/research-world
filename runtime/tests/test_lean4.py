import base64
import json

import httpx
import respx

from runtime.lean4 import BoundLean4, Lean4Adapter, _verify_spec
from runtime.tools import ToolBox

RUNNER = "http://runner"
SOURCE = "import Mathlib\nexample : True := by trivial"


class ArtifactClient:
    def __init__(self):
        self.calls = []

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        return {"id": "artifact:" + "a" * 64}


def runner_result(exit_code=0, stdout="", stderr=""):
    return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}


def operations(bound):
    return {item["function"]["name"]: item["function"] for item in bound.specs}


@respx.mock
async def test_projection_and_operation_contract():
    ready = respx.post(f"{RUNNER}/images/inspect").mock(
        return_value=httpx.Response(200, json={"available": True})
    )
    adapter = Lean4Adapter(RUNNER)

    public = adapter.inspect()
    functions = operations(await adapter.open())

    assert set(public) == {"id", "name", "description", "source", "status"}
    assert public["id"] == "lean4"
    assert public["status"] == "ready"
    assert functions["tool__lean4__version"]["parameters"]["properties"] == {}
    assert functions["tool__lean4__verify"]["parameters"]["required"] == ["source"]
    assert ready.call_count == 2


@respx.mock
def test_projection_is_unavailable_when_runner_fails():
    respx.post(f"{RUNNER}/images/inspect").mock(side_effect=httpx.ConnectError("offline"))

    assert Lean4Adapter(RUNNER).inspect()["status"] == "unavailable"


@respx.mock
async def test_verified_source_is_captured_as_lean_artifact(tmp_path):
    respx.post(f"{RUNNER}/images/inspect").mock(
        return_value=httpx.Response(200, json={"available": True})
    )
    respx.post(f"{RUNNER}/run").mock(return_value=httpx.Response(200, json=runner_result()))
    client = ArtifactClient()
    adapter = Lean4Adapter(RUNNER)

    async with ToolBox(tmp_path, {}, ("lean4",), {"lean4": adapter}, client) as tools:
        content, failed = await tools.call(
            "s-proof", "tool__lean4__verify", json.dumps({"source": SOURCE})
        )

    assert failed is False
    assert json.loads(content)["content"]["status"] == "verified"
    assert client.calls == [("research/capture_artifact", _capture())]


def _capture():
    return {"content": SOURCE, "media_type": "text/x-lean", "tool": "tool__lean4__verify"}


@respx.mock
async def test_failed_proof_returns_structured_diagnostics():
    message = {"severity": "error", "kind": "typeMismatch", "data": "type mismatch"}
    respx.post(f"{RUNNER}/run").mock(
        return_value=httpx.Response(200, json=runner_result(1, json.dumps(message)))
    )

    outcome = await BoundLean4(RUNNER).invoke(
        "tool__lean4__verify", {"source": "example : False := by trivial"}, "s-one"
    )

    result = json.loads(outcome.content)
    assert result["status"] == "rejected"
    assert result["diagnostics"] == [message]


@respx.mock
async def test_sorry_warning_is_rejected():
    warning = {"severity": "error", "kind": "declarationUsesSorry", "data": "uses sorry"}
    respx.post(f"{RUNNER}/run").mock(
        return_value=httpx.Response(200, json=runner_result(1, json.dumps(warning)))
    )

    outcome = await BoundLean4(RUNNER).invoke(
        "tool__lean4__verify", {"source": "example : False := by sorry"}, "s-sorry"
    )

    assert json.loads(outcome.content)["status"] == "rejected"


@respx.mock
async def test_bound_timeout_raises():
    respx.post(f"{RUNNER}/run").mock(
        return_value=httpx.Response(200, json=runner_result(124, stderr="timeout"))
    )

    try:
        await BoundLean4(RUNNER).invoke("tool__lean4__verify", {"source": SOURCE}, "s-time")
    except RuntimeError as error:
        assert "timed out" in str(error)
    else:
        raise AssertionError("timeout must fail the Tool invocation")


def test_verify_spec_has_fixed_sandbox_contract():
    spec = _verify_spec(SOURCE, "s-proof")

    assert spec["image"] == "ai4sci-lean4:4.33.1"
    assert spec["command"] == [
        "sh",
        "-c",
        "cd /opt/mathlib && exec lake env lean --json -DwarningAsError=true /workspace/Main.lean",
    ]
    assert base64.b64decode(spec["files"]["Main.lean"]).decode() == SOURCE
    assert spec["limits"] == {"cpus": 1, "memory_mb": 1024, "pids": 64, "wall_seconds": 30}
    assert set(spec) == {"execution_id", "image", "command", "files", "seed", "limits"}


async def test_input_contract_rejects_extra_and_oversized_source():
    bound = BoundLean4(RUNNER)
    for values in ({"source": SOURCE, "command": "x"}, {"source": "x" * (256 * 1024 + 1)}):
        try:
            await bound.invoke("tool__lean4__verify", values, "s-input")
        except ValueError:
            continue
        raise AssertionError("invalid source must fail")
