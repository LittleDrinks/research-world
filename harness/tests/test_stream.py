import json

from httpx import Response

from helpers import create_session


def sse_body(*chunks):
    return "".join(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                   for chunk in chunks) + "data: [DONE]\n\n"


def delta(content):
    return {"choices": [{"delta": {"content": content}}]}


def call_chunk(index, function, call_id=None):
    part = {"index": index, "function": function}
    if call_id:
        part["id"] = call_id
        part["type"] = "function"
    return {"choices": [{"delta": {"tool_calls": [part]}}]}


USAGE = {"choices": [], "usage": {"prompt_tokens": 7, "completion_tokens": 3}}


def stream_turn(client, sid, prompt="hi"):
    with client.stream("POST", f"/sessions/{sid}/turns/stream",
                       json={"prompt": prompt}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    lines = [line for line in body.splitlines() if line.startswith("data: ")]
    return [json.loads(line[6:]) for line in lines]


def test_stream_turn_emits_deltas_then_done(client, model_route):
    body = sse_body(delta("你好"), delta("世界"), USAGE)
    model_route.mock(return_value=Response(200, content=body))
    s = create_session(client)
    events = stream_turn(client, s["id"])
    assert [e["delta"] for e in events if "delta" in e] == ["你好", "世界"]
    done = events[-1]
    assert done["done"] is True
    assert done["turn"]["status"] == "completed"
    assert done["turn"]["result_text"] == "你好世界"
    assert done["turn"]["usage"] == {"prompt_tokens": 7, "completion_tokens": 3}


def test_stream_turn_persists_messages_and_assembled_trace(client, model_route):
    model_route.mock(return_value=Response(200, content=sse_body(delta("ab"), USAGE)))
    s = create_session(client)
    stream_turn(client, s["id"])
    detail = client.get(f"/sessions/{s['id']}").json()
    assert detail["message_count"] == 2
    trace = client.get(f"/sessions/{s['id']}/trace").text
    assert trace.count('"kind": "model_response"') == 1
    assert '"content": "ab"' in trace
    assert "delta" not in trace


def test_stream_turn_retries_429_then_streams(client, model_route):
    model_route.mock(side_effect=[Response(429, json={"error": "rate limited"}),
                                  Response(200, content=sse_body(delta("ok"), USAGE))])
    s = create_session(client)
    events = stream_turn(client, s["id"])
    assert events[-1]["turn"]["status"] == "completed"
    assert events[-1]["turn"]["result_text"] == "ok"
    assert model_route.call_count == 2


def test_stream_turn_4xx_fails_fast(client, model_route):
    model_route.mock(return_value=Response(400, json={"error": "bad request"}))
    s = create_session(client)
    events = stream_turn(client, s["id"])
    assert events[-1]["turn"]["status"] == "error"
    assert model_route.call_count == 1
    assert '"kind": "error"' in client.get(f"/sessions/{s['id']}/trace").text


def test_stream_turn_continues_after_tool_call(client, model_route, data_dir):
    s = create_session(client, tools=[{"type": "fs"}])
    workspace = data_dir / "workspaces" / s["id"]
    workspace.mkdir(parents=True)
    (workspace / "a.txt").write_text("content-a")
    call = [call_chunk(0, {"name": "read_file", "arguments": ""}, "call_1"),
            call_chunk(0, {"arguments": '{"path":'}),
            call_chunk(0, {"arguments": '"a.txt"}'}), USAGE]
    model_route.mock(side_effect=[Response(200, content=sse_body(*call)),
                                  Response(200, content=sse_body(delta("read it"), USAGE))])
    events = stream_turn(client, s["id"])
    assert events[-1]["turn"]["status"] == "completed"
    assert events[-1]["turn"]["result_text"] == "read it"
    assert model_route.call_count == 2
    messages = client.get(f"/sessions/{s['id']}/messages").json()
    assert messages[2]["role"] == "tool" and messages[2]["content"] == "content-a"
