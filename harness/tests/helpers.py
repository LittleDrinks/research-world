import json

API = "https://api.test/v1"
MODEL_URL = f"{API}/chat/completions"


def completion(content=None, tool_calls=None, pt=10, ct=5):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": pt, "completion_tokens": ct}}


def tool_call(name, args, call_id="call_1"):
    return {"id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


def create_session(client, **kw):
    r = client.post("/sessions", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def run_turn(client, sid, prompt="hi", **kw):
    r = client.post(f"/sessions/{sid}/turns", json={"prompt": prompt, **kw})
    assert r.status_code == 200, r.text
    return r.json()
