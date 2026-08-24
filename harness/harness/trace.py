import json
import time
from pathlib import Path


def append(trace_dir, session_id, turn_id, kind, data, usage=None):
    path = Path(trace_dir) / f"{session_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": time.time(), "session_id": session_id, "turn_id": turn_id,
           "seq": _next_seq(path), "kind": kind, "data": data}
    if usage is not None:
        rec["usage"] = usage
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read(trace_dir, session_id):
    path = Path(trace_dir) / f"{session_id}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _next_seq(path):
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)
