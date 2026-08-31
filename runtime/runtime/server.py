from __future__ import annotations

import os

from fastapi import FastAPI

from .http import install_error_handlers, runtime_router
from .runtime import Runtime


def create_app(runtime: Runtime) -> FastAPI:
    app = FastAPI(title="Research Agent Runtime")
    install_error_handlers(app)
    app.include_router(runtime_router(runtime))

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


async def serve(runtime: Runtime) -> None:
    from hypercorn.asyncio import serve as hypercorn_serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.getenv('RUNTIME_PORT', '8098')}"]
    config.alpn_protocols = ["h2", "http/1.1"]
    await hypercorn_serve(create_app(runtime), config)
