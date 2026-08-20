import json
import sqlite3
import time
import uuid
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY, role_prompt TEXT, model TEXT, tools TEXT,
  workspace TEXT, status TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS turns(
  id TEXT PRIMARY KEY, session_id TEXT, prompt TEXT, status TEXT,
  result_text TEXT, usage TEXT, started_at REAL, completed_at REAL);
CREATE TABLE IF NOT EXISTS messages(
  session_id TEXT, seq INTEGER, role TEXT, content TEXT, tool_calls TEXT,
  tool_call_id TEXT, PRIMARY KEY(session_id, seq));
CREATE TABLE IF NOT EXISTS benchmarks(id TEXT PRIMARY KEY, name TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS cases(
  benchmark_id TEXT, case_id TEXT, prompt TEXT, tools TEXT, expect TEXT,
  PRIMARY KEY(benchmark_id, case_id));
CREATE TABLE IF NOT EXISTS benchmark_runs(
  id TEXT PRIMARY KEY, benchmark_id TEXT, role_prompt TEXT, model TEXT,
  tools TEXT, started_at REAL, completed_at REAL);
CREATE TABLE IF NOT EXISTS case_results(
  run_id TEXT, case_id TEXT, session_id TEXT, metrics TEXT,
  PRIMARY KEY(run_id, case_id));
"""


class Store:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        with closing(self._conn()) as c:
            c.executescript(SCHEMA)
            c.execute("PRAGMA journal_mode=WAL")
            c.commit()

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _one(self, sql, args=()):
        with closing(self._conn()) as c:
            return c.execute(sql, args).fetchone()

    def _all(self, sql, args=()):
        with closing(self._conn()) as c:
            return c.execute(sql, args).fetchall()

    def _w(self, sql, args):
        with closing(self._conn()) as c:
            c.execute(sql, args)
            c.commit()

    def create_session(self, role_prompt=None, model=None, tools=None, workspace=None):
        sid = uuid.uuid4().hex[:12]
        self._w("INSERT INTO sessions VALUES(?,?,?,?,?,?,?)",
                (sid, role_prompt, model, json.dumps(tools or []), workspace,
                 "active", time.time()))
        return self.get_session(sid)

    def get_session(self, sid):
        r = self._one("SELECT * FROM sessions WHERE id=?", (sid,))
        if not r:
            return None
        d = dict(r)
        d["tools"] = json.loads(d["tools"])
        return d

    def append_message(self, sid, role, content=None, tool_calls=None, tool_call_id=None):
        with closing(self._conn()) as c:
            seq = c.execute(
                "SELECT COALESCE(MAX(seq),-1)+1 FROM messages WHERE session_id=?",
                (sid,)).fetchone()[0]
            c.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)",
                      (sid, seq, role, content,
                       json.dumps(tool_calls) if tool_calls else None, tool_call_id))
            c.commit()
        return seq

    def list_messages(self, sid):
        rows = self._all("SELECT * FROM messages WHERE session_id=? ORDER BY seq", (sid,))
        return [_message(dict(r)) for r in rows]

    def message_count(self, sid):
        return self._one("SELECT COUNT(*) FROM messages WHERE session_id=?", (sid,))[0]

    def create_turn(self, sid, prompt):
        tid = uuid.uuid4().hex[:12]
        usage = json.dumps({"prompt_tokens": 0, "completion_tokens": 0})
        self._w("INSERT INTO turns(id,session_id,prompt,status,usage,started_at) "
                "VALUES(?,?,?,?,?,?)", (tid, sid, prompt, "running", usage, time.time()))
        return self.get_turn(sid, tid)

    def finish_turn(self, tid, status, result_text, usage):
        self._w("UPDATE turns SET status=?, result_text=?, usage=?, completed_at=? "
                "WHERE id=?", (status, result_text, json.dumps(usage), time.time(), tid))

    def get_turn(self, sid, tid):
        r = self._one("SELECT * FROM turns WHERE id=? AND session_id=?", (tid, sid))
        if not r:
            return None
        d = dict(r)
        d["usage"] = json.loads(d["usage"])
        return d

    def session_usage(self, sid):
        rows = self._all("SELECT usage FROM turns WHERE session_id=?", (sid,))
        usages = [json.loads(r["usage"]) for r in rows]
        return {"prompt_tokens": sum(u["prompt_tokens"] for u in usages),
                "completion_tokens": sum(u["completion_tokens"] for u in usages)}

    def create_benchmark(self, name, cases):
        bid = uuid.uuid4().hex[:12]
        with closing(self._conn()) as c:
            c.execute("INSERT INTO benchmarks VALUES(?,?,?)", (bid, name, time.time()))
            for case in cases:
                c.execute("INSERT INTO cases VALUES(?,?,?,?,?)",
                          (bid, case["id"], case["prompt"],
                           json.dumps(case.get("tools") or []),
                           json.dumps(case.get("expect") or {})))
            c.commit()
        return self.get_benchmark(bid)

    def get_benchmark(self, bid):
        r = self._one("SELECT * FROM benchmarks WHERE id=?", (bid,))
        if not r:
            return None
        d = dict(r)
        d["cases"] = [_case(dict(x)) for x in self._all(
            "SELECT *, case_id AS id FROM cases WHERE benchmark_id=?", (bid,))]
        return d

    def create_run(self, bid, role_prompt=None, model=None, tools=None):
        rid = uuid.uuid4().hex[:12]
        self._w("INSERT INTO benchmark_runs(id,benchmark_id,role_prompt,model,tools,"
                "started_at) VALUES(?,?,?,?,?,?)",
                (rid, bid, role_prompt, model, json.dumps(tools or []), time.time()))
        return rid

    def finish_run(self, rid):
        self._w("UPDATE benchmark_runs SET completed_at=? WHERE id=?", (time.time(), rid))

    def save_case_result(self, rid, case_id, session_id, metrics):
        self._w("INSERT INTO case_results VALUES(?,?,?,?)",
                (rid, case_id, session_id, json.dumps(metrics)))

    def get_run(self, rid):
        r = self._one("SELECT * FROM benchmark_runs WHERE id=?", (rid,))
        if not r:
            return None
        d = dict(r)
        d["tools"] = json.loads(d["tools"])
        d["results"] = [dict(x, metrics=json.loads(x["metrics"])) for x in
                        self._all("SELECT * FROM case_results WHERE run_id=?", (rid,))]
        return d


def _message(r):
    m = {"seq": r["seq"], "role": r["role"], "content": r["content"]}
    if r["tool_calls"]:
        m["tool_calls"] = json.loads(r["tool_calls"])
    if r["tool_call_id"]:
        m["tool_call_id"] = r["tool_call_id"]
    return m


def _case(r):
    r["tools"] = json.loads(r["tools"])
    r["expect"] = json.loads(r["expect"])
    return r
