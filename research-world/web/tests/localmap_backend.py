import argparse
import os
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from server.kernel_http import kernel_graph_router
from server.kernel_interface import create_kernel


def _data_root() -> Path:
    value = os.getenv("RW_LOCALMAP_TEST_DATA")
    return Path(value) if value else Path(tempfile.gettempdir()) / f"rw-localmap-{os.getpid()}"


def _bootstrap(kernel, project_id: str | None):
    projects = kernel.list_projects()
    selected = kernel.get_project(project_id) if project_id else projects[0]
    return {
        "projects": projects,
        "active_project_id": selected.id,
        "nodes": [],
        "edges": [],
        "runs": [],
        "pipelines": [],
        "threads": [],
        "slots": [],
    }


def create_test_app() -> FastAPI:
    root = _data_root()
    kernel = create_kernel(root / "kernel.db", root / "artifacts")
    project = kernel.create_project("LocalMap browser", "Orbit research")
    app = FastAPI()
    app.include_router(kernel_graph_router(kernel))

    @app.get("/api/v1/health")
    def health():
        return {"ok": True}

    @app.get("/api/v1/bootstrap")
    def bootstrap(project_id: str | None = None):
        return _bootstrap(kernel, project_id or project.id)

    @app.get("/api/v1/agents")
    def agents():
        return []

    return app


app = create_test_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18135)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port)
