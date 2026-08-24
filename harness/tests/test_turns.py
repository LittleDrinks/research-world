import json

import respx
from httpx import Response

from harness import tools as toolmod
from helpers import (MODEL_URL, completion, create_session, run_turn,
                     tool_call)


def test_single_turn_no_tools(client, model_route):
    model_route.mock(return_value=Response(200, json=completion("done")))
    s = create_session(client)
    t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert t["result_text"] == "done"
    assert t["usage"] == {"prompt_tokens": 10, "completion_tokens": 5}
    detail = client.get(f"/sessions/{s['id']}").json()
    assert detail["message_count"] == 2
    assert detail["usage"] == t["usage"]


def test_two_round_tool_loop(client, model_route, data_dir):
    s = create_session(client, tools=[{"type": "fs"}])
    ws = data_dir / "workspaces" / s["id"]
    ws.mkdir(parents=True)
    (ws / "hello.txt").write_text("file-content-42")
    model_route.mock(side_effect=[
        Response(200, json=completion(tool_calls=[
            tool_call("read_file", {"path": "hello.txt"})])),
        Response(200, json=completion("the file says 42"))])
    t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert t["result_text"] == "the file says 42"
    assert model_route.call_count == 2
    second = json.loads(model_route.calls[1].request.content)
    roles = [m["role"] for m in second["messages"]]
    assert roles == ["user", "assistant", "tool"]
    assert second["messages"][2]["content"] == "file-content-42"
    assert second["messages"][2]["tool_call_id"] == "call_1"


def test_tool_exception_becomes_error_result(client, model_route):
    s = create_session(client, tools=[{"type": "fs"}])
    model_route.mock(side_effect=[
        Response(200, json=completion(tool_calls=[
            tool_call("grep", {"pattern": "[invalid("})])),
        Response(200, json=completion("recovered"))])
    t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert t["result_text"] == "recovered"
    second = json.loads(model_route.calls[1].request.content)
    tool_msg = second["messages"][2]
    assert tool_msg["role"] == "tool"
    assert "tool error" in tool_msg["content"]


def test_model_429_retries_then_success(client, model_route):
    model_route.mock(side_effect=[
        Response(429, json={"error": "rate limited"}),
        Response(429, json={"error": "rate limited"}),
        Response(200, json=completion("ok after retry"))])
    s = create_session(client)
    t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert t["result_text"] == "ok after retry"
    assert model_route.call_count == 3


def test_model_4xx_fails_turn(client, model_route):
    model_route.mock(return_value=Response(400, json={"error": "bad request"}))
    s = create_session(client)
    t = run_turn(client, s["id"])
    assert t["status"] == "error"
    assert model_route.call_count == 1
    trace = client.get(f"/sessions/{s['id']}/trace").text
    assert '"kind": "error"' in trace


def test_fs_path_escape_rejected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")
    content, is_error = toolmod.dispatch(
        [{"type": "fs"}], "read_file", '{"path": "../secret.txt"}',
        ws, "s1", "t1")
    assert is_error
    assert "escapes workspace" in content
    assert "top secret" not in content


def test_webhook_tool_callback(client):
    hook = "https://callback.test/lookup"
    s = create_session(client, tools=[{
        "type": "webhook", "name": "lookup", "description": "look things up",
        "parameters": {"type": "object", "properties": {}}, "url": hook}])
    with respx.mock(assert_all_called=False) as router:
        router.post(MODEL_URL).mock(side_effect=[
            Response(200, json=completion(tool_calls=[
                tool_call("lookup", {"q": "x"})])),
            Response(200, json=completion("webhook said hi"))])
        hook_route = router.post(hook).mock(
            return_value=Response(200, text="webhook-result"))
        t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert t["result_text"] == "webhook said hi"
    assert hook_route.called
    body = json.loads(hook_route.calls[0].request.content)
    assert body["tool"] == "lookup"
    assert body["arguments"] == {"q": "x"}
    assert body["session_id"] == s["id"]
    assert body["turn_id"] == t["id"]
