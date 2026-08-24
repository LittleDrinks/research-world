import json

from runtime.trace import TraceStore, inspect_trace


def test_trace_is_the_session_store(tmp_path):
    store = TraceStore(tmp_path)
    store.create("s1", {"agent": {"id": "researcher"}, "workspace": "/work"})
    store.append(
        "s1", "turn_start", {"prompt": [{"type": "text", "text": "问题"}]}, "t1"
    )
    store.append("s1", "turn_end", {"status": "completed", "result_text": "答案"}, "t1")

    view = inspect_trace(store.read("s1"))

    assert view["messages"] == [
        {"role": "user", "content": "问题"},
        {"role": "assistant", "content": "答案"},
    ]
    assert view["status"] == "completed"


def test_trace_repairs_a_torn_tail(tmp_path):
    store = TraceStore(tmp_path)
    store.create("s1", {"agent": {"id": "researcher"}})
    with store.path("s1").open("ab") as stream:
        stream.write(b'{"type":"turn_start"')

    events = store.read("s1")

    assert len(events) == 1
    assert store.path("s1").read_bytes().endswith(b"\n")
    assert (
        json.loads(store.path("s1").read_text().splitlines()[0])["type"]
        == "session_meta"
    )
