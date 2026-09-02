from __future__ import annotations

import os
from contextlib import asynccontextmanager

from acp.http.asgi import create_asgi_app
from fastapi import FastAPI

from .acp_agent import RuntimeAgent
from .config import prepare_codex_home
from .service import Runtime


def create_app(runtime: Runtime | None = None) -> FastAPI:
    prepare_codex_home()
    service = runtime or Runtime()
    app = FastAPI(title="Research Agent Runtime", lifespan=lambda _: _lifespan(service))

    @app.get("/health")
    async def health():
        return {"ok": True}

    app.mount("/acp", create_asgi_app(lambda connection: RuntimeAgent(service)))
    return app


@asynccontextmanager
async def _lifespan(runtime: Runtime):
    try:
        yield
    finally:
        await runtime.close()


async def serve() -> None:
    from hypercorn.asyncio import serve as hypercorn_serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.getenv('RUNTIME_PORT', '8098')}"]
    config.alpn_protocols = ["h2", "http/1.1"]
    config.accesslog = "-"
    await hypercorn_serve(create_app(), config)
