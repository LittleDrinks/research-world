from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .app import app
from .kernel import KernelCommand, KernelQuery, ResearchKernel, default_kernel


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


def main(
    argv=None, kernel: ResearchKernel | None = None, output=None, error=None
) -> int:
    args = parser().parse_args(argv)
    output, error = output or sys.stdout, error or sys.stderr
    try:
        value = asyncio.run(dispatch(args, kernel or default_kernel()))
        print(json.dumps({"ok": True, "data": value}), file=output)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI renders failures as JSON.
        print(json.dumps({"ok": False, "error": str(exc)}), file=error)
        return 2


async def dispatch(args, kernel: ResearchKernel):
    if args.group == "serve":
        return await serve(args)
    if args.group == "doctor":
        return await doctor_embedding(kernel) if args.embedding else {"ok": True}
    if args.group == "project":
        return await project_command(args, kernel)
    project = await kernel.query(
        KernelQuery("project_by_name", values={"name": args.project})
    )
    return await kernel.query(KernelQuery("graph", project["id"]))


async def project_command(args, kernel: ResearchKernel):
    if args.action == "list":
        return await kernel.query(KernelQuery("projects"))
    value = json.loads(args.file.read_text()) if args.file else json.load(sys.stdin)
    values = {key: value[key] for key in ("name", "title", "question")}
    return await kernel.command(KernelCommand("create_project", values=values))


async def doctor_embedding(kernel: ResearchKernel) -> dict:
    endpoint = os.environ["RW_EMBEDDING_ENDPOINT"]
    model = os.getenv("RW_EMBEDDING_MODEL", "qwen3.7-text-embedding")
    values = {"endpoint": endpoint, "model": model}
    dimensions = await kernel.query(KernelQuery("embedding_dimensions", values=values))
    return {"ok": True, "dimensions": dimensions}


async def serve(args):
    import uvicorn

    config = uvicorn.Config(app, host=args.host, port=args.port)
    await uvicorn.Server(config).serve()
    return {"stopped": True}


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
