import json

from httpx import Response

from harness import tools as toolmod
from helpers import completion, create_session, run_turn, tool_call

WRITE = [{"type": "fs", "mode": "write"}]
READ = [{"type": "fs"}]


def test_write_then_edit_file(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    out, err = toolmod.dispatch(WRITE, "write_file",
                                '{"path": "a.txt", "content": "hello world"}',
                                ws, "s", "t")
    assert not err and (ws / "a.txt").read_text() == "hello world"
    out, err = toolmod.dispatch(WRITE, "edit_file",
                                json.dumps({"path": "a.txt", "old_string": "world",
                                            "new_string": "harness"}),
                                ws, "s", "t")
    assert not err and (ws / "a.txt").read_text() == "hello harness"


def test_edit_missing_old_string_is_error(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "a.txt").write_text("hello")
    out, err = toolmod.dispatch(WRITE, "edit_file",
                                json.dumps({"path": "a.txt", "old_string": "zzz",
                                            "new_string": "y"}),
                                ws, "s", "t")
    assert err and "old_string not found" in out


def test_read_mode_rejects_write_tools(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    names = {s["function"]["name"] for s in toolmod.openai_specs(READ)}
    assert names == {"read_file", "grep", "glob"}
    write_names = {s["function"]["name"] for s in toolmod.openai_specs(WRITE)}
    assert write_names == names | {"write_file", "edit_file"}
    out, err = toolmod.dispatch(READ, "write_file",
                                '{"path": "a.txt", "content": "x"}', ws, "s", "t")
    assert err and "not enabled" in out
    assert not (ws / "a.txt").exists()


def test_write_path_escape_rejected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    out, err = toolmod.dispatch(WRITE, "write_file",
                                '{"path": "../evil.txt", "content": "x"}',
                                ws, "s", "t")
    assert err and "escapes workspace" in out
    assert not (tmp_path / "evil.txt").exists()


def test_session_with_custom_workspace(client, model_route, data_dir):
    custom = data_dir / "workspaces" / "attempt-1"
    s = create_session(client, tools=WRITE, workspace=str(custom))
    assert s["workspace"] == str(custom)
    model_route.mock(side_effect=[
        Response(200, json=completion(tool_calls=[
            tool_call("write_file", {"path": "report.md", "content": "# R"})])),
        Response(200, json=completion("wrote it"))])
    t = run_turn(client, s["id"])
    assert t["status"] == "completed"
    assert (custom / "report.md").read_text() == "# R"
    assert not (data_dir / "workspaces" / s["id"]).exists()
    messages = client.get(f"/sessions/{s['id']}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant", "tool", "assistant"]


def test_workspace_outside_data_root_rejected(client, tmp_path):
    r = client.post("/sessions", json={"workspace": str(tmp_path)})
    assert r.status_code == 400
    r = client.post("/sessions", json={"workspace": "relative/path"})
    assert r.status_code == 400
