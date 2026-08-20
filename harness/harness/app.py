import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from . import trace as tr
from .models import ModelClient
from .session import run_turn, run_turn_stream
from .store import Store


class SessionIn(BaseModel):
    role_prompt: str | None = None
    model: str | None = None
    tools: list[dict] = []
    workspace: str | None = None
    prompt_segments: list[str] = []


class TurnIn(BaseModel):
    prompt: str
    max_rounds: int = 12
    timeout_seconds: float = 600
    token_budget: int = 200000


class BenchmarkIn(BaseModel):
    name: str
    cases: list[dict]


class RunIn(BaseModel):
    role_prompt: str | None = None
    model: str | None = None
    tools: list[dict] = []


def create_app(data_dir=None, api_base=None, api_key=None, model=None, backoff=None):
    data_dir = Path(data_dir or os.environ.get("HARNESS_DATA", "./data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    store = Store(data_dir / "harness.db")
    client = ModelClient(
        api_base or os.environ.get("HARNESS_API_BASE", ""),
        api_key or os.environ.get("HARNESS_API_KEY", ""),
        model or os.environ.get("HARNESS_MODEL", ""),
        backoff=backoff if backoff is not None else (0.5, 1.0, 2.0))
    app = FastAPI(title="harness")
    _routes(app, store, client, data_dir)
    return app


def _routes(app, store, client, data_dir):
    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/sessions")
    def new_session(body: SessionIn):
        workspace = _check_workspace(body.workspace, data_dir)
        role_prompt = _system_prompt(body.role_prompt, body.prompt_segments)
        return store.create_session(role_prompt, body.model, body.tools,
                                    workspace)

    @app.get("/sessions/{sid}")
    def get_session(sid):
        s = store.get_session(sid)
        if not s:
            raise HTTPException(404, "session not found")
        return {**s, "message_count": store.message_count(sid),
                "usage": store.session_usage(sid)}

    @app.post("/sessions/{sid}/turns")
    def new_turn(sid, body: TurnIn):
        s = store.get_session(sid)
        if not s:
            raise HTTPException(404, "session not found")
        return run_turn(store, client, data_dir, s, body.prompt, body.max_rounds,
                        body.timeout_seconds, body.token_budget)

    @app.post("/sessions/{sid}/turns/stream")
    def new_turn_stream(sid, body: TurnIn):
        s = store.get_session(sid)
        if not s:
            raise HTTPException(404, "session not found")
        events = run_turn_stream(store, client, data_dir, s, body.prompt,
                                 body.max_rounds, body.timeout_seconds, body.token_budget)
        return StreamingResponse((_sse(event) for event in events),
                                 media_type="text/event-stream")

    @app.get("/sessions/{sid}/turns/{tid}")
    def get_turn(sid, tid):
        t = store.get_turn(sid, tid)
        if not t:
            raise HTTPException(404, "turn not found")
        return t

    @app.get("/sessions/{sid}/messages")
    def get_messages(sid):
        if not store.get_session(sid):
            raise HTTPException(404, "session not found")
        return store.list_messages(sid)

    @app.get("/sessions/{sid}/trace", response_class=PlainTextResponse)
    def get_trace(sid):
        if not store.get_session(sid):
            raise HTTPException(404, "session not found")
        path = data_dir / "traces" / f"{sid}.jsonl"
        return path.read_text() if path.exists() else ""

    @app.post("/benchmarks")
    def new_benchmark(body: BenchmarkIn):
        return store.create_benchmark(body.name, body.cases)

    @app.post("/benchmarks/{bid}/runs")
    def new_run(bid, body: RunIn):
        b = store.get_benchmark(bid)
        if not b:
            raise HTTPException(404, "benchmark not found")
        rid = store.create_run(bid, body.role_prompt, body.model, body.tools)
        run = {"id": rid, "role_prompt": body.role_prompt,
               "model": body.model, "tools": body.tools}
        for case in b["cases"]:
            _run_case(store, client, data_dir, run, case)
        store.finish_run(rid)
        return _run_detail(store, rid)

    @app.get("/benchmarks/{bid}/runs/{rid}")
    def get_run(bid, rid):
        r = store.get_run(rid)
        if not r or r["benchmark_id"] != bid:
            raise HTTPException(404, "run not found")
        return _run_detail(store, rid)


def _system_prompt(role_prompt, prompt_segments):
    joined = "\n\n".join(part for part in [role_prompt or "", *prompt_segments] if part)
    return joined or None


def _sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _check_workspace(workspace, data_dir):
    if workspace is None:
        return None
    ws = Path(workspace)
    if not ws.is_absolute() or not ws.resolve().is_relative_to(data_dir):
        raise HTTPException(400, "workspace must be absolute and under HARNESS_DATA")
    return str(ws)


def _run_case(store, client, data_dir, run, case):
    sess = store.create_session(run["role_prompt"], run["model"],
                                case.get("tools") or run["tools"])
    turn = run_turn(store, client, data_dir, sess, case["prompt"])
    m = _metrics(data_dir, sess["id"], turn)
    exp = case.get("expect") or {}
    if "contains" in exp:
        m["contains_hit"] = exp["contains"] in (turn.get("result_text") or "")
    store.save_case_result(run["id"], case["id"], sess["id"], m)
    return m


def _metrics(data_dir, session_id, turn):
    recs = [r for r in tr.read(Path(data_dir) / "traces", session_id)
            if r["turn_id"] == turn["id"]]
    responses = [r for r in recs if r["kind"] == "model_response"]
    errs = [r for r in recs
            if r["kind"] == "tool_result" and r["data"].get("is_error")]
    end = turn["completed_at"] or turn["started_at"]
    return {"status": turn["status"], "rounds": len(responses),
            "tool_error_count": len(errs), "wall_ms": int((end - turn["started_at"]) * 1000),
            "prompt_tokens": sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in responses),
            "completion_tokens": sum((r.get("usage") or {}).get("completion_tokens", 0) for r in responses)}


def _run_detail(store, rid):
    r = store.get_run(rid)
    cases = [{"case_id": x["case_id"], "session_id": x["session_id"], **x["metrics"]}
             for x in r["results"]]
    return {"id": r["id"], "benchmark_id": r["benchmark_id"], "cases": cases,
            "aggregate": _aggregate(cases)}


def _aggregate(cases):
    n = len(cases)
    if not n:
        return {"cases": 0, "completion_rate": 0, "avg_rounds": 0,
                "avg_tokens": 0, "total_wall_ms": 0}
    done = sum(1 for c in cases if c["status"] == "completed")
    return {"cases": n, "completion_rate": done / n,
            "avg_rounds": sum(c["rounds"] for c in cases) / n,
            "avg_tokens": sum(c["prompt_tokens"] + c["completion_tokens"]
                              for c in cases) / n,
            "total_wall_ms": sum(c["wall_ms"] for c in cases)}
