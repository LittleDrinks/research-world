import time
from pathlib import Path

from . import tools as toolmod
from . import trace as tr


def run_turn(store, model, data_dir, session, prompt, max_rounds=12,
             timeout_seconds=600, token_budget=200000):
    turn = store.create_turn(session["id"], prompt)
    store.append_message(session["id"], "user", prompt)
    _t(data_dir, session, turn["id"], "turn_start", {"prompt": prompt})
    start = time.monotonic()
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    status, result = "limit", None
    try:
        for _ in range(max_rounds):
            if time.monotonic() - start > timeout_seconds or _over(usage, token_budget):
                break
            done, result = _round(store, model, data_dir, session, turn["id"], usage)
            if done:
                status = "completed"
                break
    except Exception as e:
        status = "error"
        _t(data_dir, session, turn["id"], "error",
           {"error": f"{type(e).__name__}: {e}"})
    store.finish_turn(turn["id"], status, result, usage)
    _t(data_dir, session, turn["id"], "turn_end",
       {"status": status, "result_text": result})
    return store.get_turn(session["id"], turn["id"])


def run_turn_stream(store, model, data_dir, session, prompt, max_rounds=12,
                    timeout_seconds=600, token_budget=200000):
    turn = store.create_turn(session["id"], prompt)
    store.append_message(session["id"], "user", prompt)
    _t(data_dir, session, turn["id"], "turn_start", {"prompt": prompt})
    start = time.monotonic()
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    status, result = "limit", None
    try:
        for _ in range(max_rounds):
            if time.monotonic() - start > timeout_seconds or _over(usage, token_budget):
                break
            done, result = yield from _round_stream(store, model, data_dir, session,
                                                    turn["id"], usage)
            if done:
                status = "completed"
                break
    except Exception as e:
        status = "error"
        _t(data_dir, session, turn["id"], "error",
           {"error": f"{type(e).__name__}: {e}"})
    store.finish_turn(turn["id"], status, result, usage)
    _t(data_dir, session, turn["id"], "turn_end",
       {"status": status, "result_text": result})
    yield {"done": True, "turn": store.get_turn(session["id"], turn["id"])}


def _stream_deltas(stream):
    while True:
        try:
            yield {"delta": next(stream)}
        except StopIteration as stop:
            return stop.value


def _round_stream(store, model, data_dir, session, turn_id, usage):
    specs = toolmod.openai_specs(session["tools"])
    _t(data_dir, session, turn_id, "model_request",
       {"tools": [s["function"]["name"] for s in specs]})
    stream = model.chat_stream(_messages(store, session), specs or None,
                               model=session.get("model"))
    msg, u = yield from _stream_deltas(stream)
    usage["prompt_tokens"] += u["prompt_tokens"]
    usage["completion_tokens"] += u["completion_tokens"]
    _t(data_dir, session, turn_id, "model_response",
       {"content": msg.get("content"), "tool_calls": msg.get("tool_calls")}, u)
    store.append_message(session["id"], "assistant", msg.get("content"),
                         tool_calls=msg.get("tool_calls"))
    calls = msg.get("tool_calls") or []
    for call in calls:
        _dispatch(store, data_dir, session, turn_id, call)
    return (not calls), msg.get("content")


def _over(usage, token_budget):
    return usage["prompt_tokens"] + usage["completion_tokens"] >= token_budget


def _t(data_dir, session, turn_id, kind, data, usage=None):
    return tr.append(Path(data_dir) / "traces", session["id"], turn_id,
                     kind, data, usage)


def _messages(store, session):
    out = []
    if session.get("role_prompt"):
        out.append({"role": "system", "content": session["role_prompt"]})
    for m in store.list_messages(session["id"]):
        out.append({k: v for k, v in m.items() if k != "seq"})
    return out


def _round(store, model, data_dir, session, turn_id, usage):
    specs = toolmod.openai_specs(session["tools"])
    _t(data_dir, session, turn_id, "model_request",
       {"tools": [s["function"]["name"] for s in specs]})
    msg, u = model.chat(_messages(store, session), specs or None,
                        model=session.get("model"))
    usage["prompt_tokens"] += u["prompt_tokens"]
    usage["completion_tokens"] += u["completion_tokens"]
    _t(data_dir, session, turn_id, "model_response",
       {"content": msg.get("content"), "tool_calls": msg.get("tool_calls")}, u)
    store.append_message(session["id"], "assistant", msg.get("content"),
                         tool_calls=msg.get("tool_calls"))
    calls = msg.get("tool_calls") or []
    for call in calls:
        _dispatch(store, data_dir, session, turn_id, call)
    return (not calls), msg.get("content")


def _dispatch(store, data_dir, session, turn_id, call):
    fn = call.get("function") or {}
    name = fn.get("name", "")
    _t(data_dir, session, turn_id, "tool_call",
       {"tool_call_id": call.get("id"), "name": name,
        "arguments": fn.get("arguments")})
    content, is_error = toolmod.dispatch(
        session["tools"], name, fn.get("arguments"),
        _workspace(data_dir, session), session["id"], turn_id)
    _t(data_dir, session, turn_id, "tool_result",
       {"tool_call_id": call.get("id"), "name": name,
        "is_error": is_error, "content": content})
    store.append_message(session["id"], "tool", content,
                         tool_call_id=call.get("id"))


def _workspace(data_dir, session):
    if session.get("workspace"):
        ws = Path(session["workspace"])
    else:
        ws = Path(data_dir) / "workspaces" / session["id"]
    ws.mkdir(parents=True, exist_ok=True)
    return ws
