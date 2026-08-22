from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .app import app
from .config import load_settings
from .runtime_client import RuntimeClient
from .world import World


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rw")
    groups = root.add_subparsers(dest="group", required=True)
    project_parser(groups)
    graph_parser(groups)
    doctor_parser(groups)
    return root


def project_parser(groups) -> None:
    project = groups.add_parser("project").add_subparsers(dest="action", required=True)
    create = project.add_parser("create")
    create.add_argument("--file", type=Path)
    project.add_parser("list")


def graph_parser(groups) -> None:
    graph = groups.add_parser("graph").add_subparsers(dest="action", required=True)
    show = graph.add_parser("show")
    show.add_argument("--project", required=True)


def doctor_parser(groups) -> None:
    serve = groups.add_parser("serve")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", default=8095, type=int)
    doctor = groups.add_parser("doctor")
    doctor.add_argument("--embedding", action="store_true")


def main(argv=None, world: World | None = None, output=None, error=None) -> int:
    args = parser().parse_args(argv)
    output, error = output or sys.stdout, error or sys.stderr
    try:
        value = dispatch(args, world or default_world())
        print(json.dumps({"ok": True, "data": value}), file=output)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI renders failures as JSON.
        print(json.dumps({"ok": False, "error": str(exc)}), file=error)
        return 2


def dispatch(args, world: World):
    if args.group == "serve":
        return serve(args)
    if args.group == "doctor":
        return doctor_embedding() if args.embedding else {"ok": True}
    if args.group == "project":
        return project_command(args, world)
    project = world.project_by_name(args.project)
    return {"nodes": world.nodes(project["id"]), "edges": world.edges(project["id"])}


def project_command(args, world: World):
    if args.action == "list":
        return world.projects()
    value = json.loads(args.file.read_text()) if args.file else json.load(sys.stdin)
    return world.create_project(
        value["name"],
        project_root(value["root"]),
        value["question"],
        value.get("assembly"),
    )


def doctor_embedding() -> dict:
    settings = load_settings()
    model = os.getenv("RW_EMBEDDING_MODEL", "qwen3.7-text-embedding")
    vector = asyncio.run(RuntimeClient(settings.runtime_url).embed(model, ["orbit"]))[0]
    return {"ok": True, "dimensions": len(vector)}


def project_root(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else load_settings().projects_root / path


def serve(args):
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
    return {"stopped": True}


def default_world() -> World:
    settings = load_settings()
    return World(settings.database, settings.artifacts)


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
