from __future__ import annotations

import os

from fastapi import FastAPI

from .http import install_error_handlers, runtime_router
from .runtime import Runtime
from .product_http import product_router
from .bridge import bridge_router
from .workspace.manager import Workspaces
from .workspace.http import workspace_router
from .workspace.tools import WorkspaceTools, workspace_tools_router


def create_app(runtime: Runtime, bridge=None, workspaces=None) -> FastAPI:
    app = FastAPI(title="Research Agent Runtime")
    install_error_handlers(app)
    _input_errors(app)
    app.include_router(runtime_router(runtime))
    app.include_router(product_router(runtime))
    workspaces = workspaces or Workspaces()
    app.include_router(workspace_router(runtime,workspaces))
    if bridge is not None:
        bridge.workspace_tools = WorkspaceTools(bridge, workspaces)
        app.include_router(bridge_router(bridge))
        app.include_router(workspace_tools_router(bridge))

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


async def serve(runtime: Runtime, bridge=None) -> None:
    from hypercorn.asyncio import serve as hypercorn_serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.getenv('RUNTIME_PORT', '8098')}"]
    config.alpn_protocols = ["h2", "http/1.1"]
    config.accesslog = "-"
    await hypercorn_serve(create_app(runtime, bridge), config)


def _input_errors(app):
    from fastapi.responses import JSONResponse

    async def invalid(_, error):
        status = 404 if isinstance(error, KeyError) else 422
        return JSONResponse({'detail': str(error)}, status_code=status)

    for kind in (KeyError, ValueError):
        app.add_exception_handler(kind, invalid)
