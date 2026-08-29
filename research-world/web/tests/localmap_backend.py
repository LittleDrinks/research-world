import argparse
import os
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from server.agents import AgentRegistry
from server.app import create_app
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
    return create_app(world_kernel, graph_kernel=graph_kernel)


app = create_test_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8095)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port)
