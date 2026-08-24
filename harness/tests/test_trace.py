import json

from httpx import Response

from helpers import completion, create_session, run_turn, tool_call

KINDS = {"turn_start", "model_request", "model_response", "tool_call",
         "tool_result", "turn_end"}


def test_trace_jsonl_schema_and_seq(client, model_route, data_dir):
    s = create_session(client, tools=[{"type": "fs"}])
    model_route.mock(side_effect=[
        Response(200, json=completion(tool_calls=[
            tool_call("glob", {"pattern": "*.txt"})])),
        Response(200, json=completion("finished"))])
    t = run_turn(client, s["id"])
    text = client.get(f"/sessions/{s['id']}/trace").text
    lines = [json.loads(x) for x in text.splitlines() if x.strip()]
    assert lines, "trace must not be empty"
    for i, rec in enumerate(lines):
        assert {"ts", "session_id", "turn_id", "seq", "kind",
                "data"} <= rec.keys()
        assert rec["seq"] == i, "seq must be monotonic 0..n-1"
        assert rec["session_id"] == s["id"]
        assert rec["turn_id"] == t["id"]
    assert KINDS <= {r["kind"] for r in lines}
    for rec in lines:
        if rec["kind"] == "model_response":
            assert set(rec["usage"]) == {"prompt_tokens", "completion_tokens"}
        else:
            assert "usage" not in rec
    tool_result = next(r for r in lines if r["kind"] == "tool_result")
    assert tool_result["data"]["is_error"] is False
    assert tool_result["data"]["content"] == "no matches"
