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


def test_trace_projects_controlled_report_messages_from_publish_results(tmp_path):
    store = TraceStore(tmp_path)
    store.create("s1", {"agent": {"id": "researcher"}})
    result = {"status": "published", "title": "Orbit", "publication": {"id": "publication:p1", "thread_id": "thread:t1", "created_at": "2026-08-26T00:00:00Z", "secret": "ignored"}, "stages": [{"name": "projection", "status": "completed"}, {"name": "persistence", "status": "completed"}], "assessment": {"delivery_level": 4, "minimum_source_level": "published", "gaps": []}}
    store.append("s1", "tool_result", {"name": "publish_report", "content": json.dumps(result), "is_error": False}, "t1")
    value = inspect_trace(store.read("s1"))
    assert value["reports"] == [{"status": "published", "title": "Orbit", "publication": {"id": "publication:p1", "thread_id": "thread:t1", "created_at": "2026-08-26T00:00:00Z"}, "stages": [{"name": "projection", "status": "completed"}, {"name": "persistence", "status": "completed"}], "assessment": {"delivery_level": 4, "minimum_source_level": "published", "gaps": []}, "turn_id": "t1", "seq": 1}]


def test_trace_keeps_the_exact_failed_report_stage(tmp_path):
    store = TraceStore(tmp_path)
    store.create("s1", {"agent": {"id": "researcher"}})
    result = {"status": "failed", "stages": [{"name": "projection", "status": "completed"}, {"name": "citation_validation", "status": "failed"}], "assessment": {"gaps": [{"code": "source_missing", "path": "facts[0]", "value": "secret"}]}}
    store.append("s1", "tool_result", {"name": "publish_report", "content": json.dumps(result), "is_error": False}, "t1")
    report = inspect_trace(store.read("s1"))["reports"][0]
    assert report["stages"] == result["stages"]
    assert report["assessment"]["gaps"][0]["value"] is None
    assert (report["turn_id"], report["seq"]) == ("t1", 1)
