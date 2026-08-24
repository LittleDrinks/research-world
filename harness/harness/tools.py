import json
import re
from pathlib import Path

import httpx


class ToolError(Exception):
    pass


READ_SCHEMAS = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a UTF-8 text file inside the session workspace",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "grep",
        "description": "Search workspace files with a Python regex; "
                       "optional 'path' scopes to a subdirectory",
        "parameters": {"type": "object",
                       "properties": {"pattern": {"type": "string"},
                                      "path": {"type": "string"}},
                       "required": ["pattern"]}}},
    {"type": "function", "function": {
        "name": "glob",
        "description": "List workspace files matching a glob pattern",
        "parameters": {"type": "object",
                       "properties": {"pattern": {"type": "string"}},
                       "required": ["pattern"]}}},
]

WRITE_SCHEMAS = [
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write a UTF-8 text file inside the session workspace",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "Replace the first occurrence of old_string with "
                       "new_string in a workspace file",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "old_string": {"type": "string"},
                                      "new_string": {"type": "string"}},
                       "required": ["path", "old_string", "new_string"]}}},
]

READ_TOOLS = {"read_file", "grep", "glob"}
WRITE_TOOLS = {"write_file", "edit_file"}

FS_FUNCS = {}


def fs_tool(fn):
    FS_FUNCS[fn.__name__] = fn
    return fn


def openai_specs(session_tools):
    specs = []
    for t in session_tools:
        if t.get("type") == "fs":
            specs.extend(READ_SCHEMAS)
            if t.get("mode") == "write":
                specs.extend(WRITE_SCHEMAS)
        elif t.get("type") == "webhook":
            specs.append({"type": "function", "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters") or {"type": "object",
                                                      "properties": {}}}})
    return specs


def dispatch(specs, name, raw_arguments, workspace, session_id, turn_id):
    try:
        args = json.loads(raw_arguments or "{}")
        return _run(specs, name, args, Path(workspace), session_id, turn_id), False
    except Exception as e:
        return f"tool error: {type(e).__name__}: {e}", True


def _run(specs, name, args, workspace, session_id, turn_id):
    if name in FS_FUNCS:
        if name not in _fs_allowed(specs):
            raise ToolError(f"tool not enabled for this session: {name}")
        return FS_FUNCS[name](workspace, args)
    for spec in specs:
        if spec.get("type") == "webhook" and spec.get("name") == name:
            return _webhook(spec, args, session_id, turn_id)
    raise ToolError(f"unknown tool: {name}")


def _fs_allowed(specs):
    allowed = set()
    for t in specs:
        if t.get("type") == "fs":
            allowed |= READ_TOOLS
            if t.get("mode") == "write":
                allowed |= WRITE_TOOLS
    return allowed


def _webhook(spec, args, session_id, turn_id):
    body = {"tool": spec["name"], "arguments": args,
            "session_id": session_id, "turn_id": turn_id}
    with httpx.Client(timeout=60) as c:
        r = c.post(spec["url"], json=body, headers=spec.get("headers") or {})
    if not 200 <= r.status_code < 300:
        raise ToolError(f"webhook returned {r.status_code}: {r.text[:200]}")
    return r.text


def _resolve(workspace, path):
    root = workspace.resolve()
    p = (root / (path or ".")).resolve()
    if not p.is_relative_to(root):
        raise ToolError(f"path escapes workspace: {path}")
    return p


@fs_tool
def read_file(workspace, args):
    p = _resolve(workspace, args.get("path"))
    if not p.is_file():
        raise ToolError(f"no such file: {args.get('path')}")
    return p.read_text(errors="replace")


@fs_tool
def grep(workspace, args):
    rx = re.compile(args["pattern"])
    base = _resolve(workspace, args.get("path"))
    files = sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else [base]
    hits = [f"{f.relative_to(workspace)}:{i}:{line}" for f in files
            for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1)
            if rx.search(line)]
    return "\n".join(hits) or "no matches"


@fs_tool
def glob(workspace, args):
    root = workspace.resolve()
    hits = sorted(str(p.relative_to(root)) for p in root.glob(args["pattern"])
                  if p.is_file())
    return "\n".join(hits) or "no matches"


@fs_tool
def write_file(workspace, args):
    p = _resolve(workspace, args.get("path"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args.get("content") or "")
    return f"wrote {args.get('path')}"


@fs_tool
def edit_file(workspace, args):
    p = _resolve(workspace, args.get("path"))
    if not p.is_file():
        raise ToolError(f"no such file: {args.get('path')}")
    text = p.read_text(errors="replace")
    if args["old_string"] not in text:
        raise ToolError("old_string not found")
    p.write_text(text.replace(args["old_string"], args.get("new_string", ""), 1))
    return f"edited {args.get('path')}"
