import argparse
import os
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

from server.agents import AgentRegistry
from server.app import register_routes
from server.kernel import ResearchKernel
from server.kernel_interface import create_kernel
from server.world import World


def _data_root() -> Path:
    value = os.getenv("RW_LOCALMAP_TEST_DATA")
    return Path(value) if value else Path(tempfile.gettempdir()) / f"rw-localmap-{os.getpid()}"


def create_test_app() -> FastAPI:
    root = _data_root()
    world_kernel = ResearchKernel(
        World(root / "world.db", root / "world-artifacts"),
        projects_root=root / "projects",
        agents=AgentRegistry(root / "agents"),
    )
    graph_kernel = create_kernel(root / "kernel.db", root / "artifacts")
    app = FastAPI(title="Research World", version="2")
    add_artifact_fixture(app, graph_kernel)
    register_routes(app, world_kernel, graph_kernel)
    return app


def add_artifact_fixture(app: FastAPI, kernel) -> None:
    @app.post("/api/test-fixtures/projects/{project_id}/artifacts", status_code=201)
    async def artifact(project_id: str, request: Request):
        value = await request.json()
        return kernel.capture_artifact(
            project_id, value["content"].encode(), value["media_type"]
        )


app = create_test_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8095)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port)
