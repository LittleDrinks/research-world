from __future__ import annotations

import json
from base64 import b64decode
from binascii import Error as Base64Error

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from .config import ROOT
from .kernel import KernelCommand, KernelQuery, ResearchKernel, default_kernel
from .library import list_packages


def create_app(kernel: ResearchKernel) -> FastAPI:
    app = FastAPI(title="Research World", version="2")
    register_routes(app, kernel)
    return app


def register_routes(app, kernel) -> None:
    error_handlers(app)
    health_routes(app)
    project_routes(app, kernel)
    project_state_routes(app, kernel)
    project_export_routes(app, kernel)
    remaining_routes(app, kernel)


def remaining_routes(app, kernel) -> None:
    graph_node_routes(app, kernel)
    graph_evidence_routes(app, kernel)
    thread_routes(app, kernel)
    thread_prompt_routes(app, kernel)
    thread_pin_routes(app, kernel)
    runtime_routes(app, kernel)
    agent_routes(app, kernel)
    pipeline_definition_routes(app, kernel)
    pipeline_run_routes(app, kernel)
    pipeline_control_routes(app, kernel)
    library_routes(app)
    graph_tool_routes(app, kernel)
    report_routes(app, kernel)
    frontend_routes(app)


def error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KeyError)
    async def missing(_request, _error):
        return JSONResponse({"detail": "not found"}, status_code=404)

    app.add_exception_handler(PermissionError, missing)

    @app.exception_handler(ValueError)
    async def invalid(_request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    app.add_exception_handler(TypeError, invalid)


def health_routes(app) -> None:
    @app.get("/api/v1/health")
    async def health():
        return {"ok": True}


def project_routes(app, kernel) -> None:
    @app.get("/api/v1/projects")
    async def projects():
        return await kernel.query(KernelQuery("projects"))

    @app.post("/api/v1/projects", status_code=201)
    async def create_project(request: Request):
        return await kernel.command(
            KernelCommand("create_project", values=await request.json())
        )


def project_state_routes(app, kernel) -> None:
    @app.patch("/api/v1/projects/{project_id}")
    async def update_project(project_id: str, request: Request):
        value = await request.json()
        return await kernel.command(
            KernelCommand("set_auto", project_id, {"enabled": value["auto"]})
        )

    @app.get("/api/v1/bootstrap")
    async def bootstrap(project_id: str | None = None):
        return await kernel.query(KernelQuery("bootstrap", project_id))


def project_export_routes(app, kernel) -> None:
    @app.get("/api/v1/projects/{project_id}/export")
    async def export_project(project_id: str):
        content = await kernel.query(KernelQuery("project_export", project_id))
        return _export_response(project_id, content)


def _export_response(project_id: str, content: bytes) -> Response:
    filename = f'{project_id.replace(":", "-")}-export.zip'
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def graph_node_routes(app, kernel) -> None:
    @app.get("/api/v1/nodes/{node_id}")
    async def node(node_id: str, project_id: str | None = None):
        return await kernel.query(KernelQuery("node", project_id, {"node_id": node_id}))

    @app.post("/api/v1/projects/{project_id}/nodes", status_code=201)
    async def create_node(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("submit_node", project_id, await request.json())
        )

    @app.post("/api/v1/projects/{project_id}/nodes/{node_id}/admission")
    async def resolve_admission(project_id: str, node_id: str, request: Request):
        values = {**(await request.json()), "node_id": node_id}
        return await kernel.command(
            KernelCommand("resolve_admission", project_id, values)
        )


def graph_evidence_routes(app, kernel) -> None:
    @app.post("/api/v1/projects/{project_id}/edges", status_code=201)
    async def create_edge(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("add_edge", project_id, await request.json())
        )

    @app.post("/api/v1/projects/{project_id}/observations", status_code=201)
    async def observation(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("observation", project_id, await request.json())
        )

    @app.post("/api/v1/projects/{project_id}/artifacts", status_code=201)
    async def artifact(project_id: str, request: Request):
        values = _artifact_values(await request.json())
        return await kernel.command(
            KernelCommand("capture_artifact", project_id, values)
        )


def thread_routes(app, kernel) -> None:
    @app.get("/api/v1/projects/{project_id}/threads")
    async def threads(project_id: str):
        return await kernel.query(KernelQuery("threads", project_id))

    @app.post("/api/v1/projects/{project_id}/threads", status_code=201)
    async def create_thread(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("create_thread", project_id, await request.json())
        )

    @app.get("/api/v1/threads/{thread_id}")
    async def thread(thread_id: str):
        return await kernel.query(
            KernelQuery("thread", values={"thread_id": thread_id})
        )


def thread_prompt_routes(app, kernel) -> None:
    @app.post("/api/v1/threads/{thread_id}/prompts")
    async def prompt(thread_id: str, request: Request):
        values = {"thread_id": thread_id, "message": (await request.json())["message"]}
        events = await kernel.command(KernelCommand("thread_prompt", values=values))
        return StreamingResponse(relay(events), media_type="text/event-stream")

    @app.post("/api/v1/threads/{thread_id}/restart")
    async def restart(thread_id: str):
        return await kernel.command(
            KernelCommand("restart_thread", values={"thread_id": thread_id})
        )


def thread_pin_routes(app, kernel) -> None:
    @app.post("/api/v1/threads/{thread_id}/nodes")
    async def pin_node(thread_id: str, request: Request):
        values = {"thread_id": thread_id, "node_id": (await request.json())["node_id"]}
        return await kernel.command(KernelCommand("pin_thread", values=values))

    @app.delete("/api/v1/threads/{thread_id}/nodes/{node_id}")
    async def unpin_node(thread_id: str, node_id: str):
        return await kernel.command(
            KernelCommand(
                "unpin_thread", values={"thread_id": thread_id, "node_id": node_id}
            )
        )


def runtime_routes(app, kernel) -> None:
    @app.get("/api/v1/runtime/catalog")
    async def catalog(project_id: str):
        return await kernel.query(KernelQuery("catalog", project_id))

    @app.get("/api/v1/runtime/sessions/{session_id}")
    async def session(session_id: str):
        return await kernel.query(
            KernelQuery("session", values={"session_id": session_id})
        )


def agent_routes(app, kernel) -> None:
    @app.get("/api/v1/agents")
    async def all_agents():
        return await kernel.query(KernelQuery("agents"))

    @app.get("/api/v1/agents/{agent_id}")
    async def agent(agent_id: str):
        return await kernel.query(KernelQuery("agent", values={"agent_id": agent_id}))

    agent_command_routes(app, kernel)


def agent_command_routes(app, kernel) -> None:
    @app.post("/api/v1/agents", status_code=201)
    async def create_agent(request: Request, project_id: str):
        values = {"value": await request.json()}
        command = KernelCommand("create_agent", project_id=project_id, values=values)
        return await kernel.command(command)

    @app.post("/api/v1/projects/{project_id}/agent-drafts", status_code=201)
    async def draft_agent(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("draft_agent", project_id, await request.json())
        )

    @app.put("/api/v1/agents/{agent_id}")
    async def save_agent(agent_id: str, request: Request, project_id: str):
        values = {"agent_id": agent_id, "value": await request.json()}
        return await kernel.command(
            KernelCommand("save_agent", project_id=project_id, values=values)
        )


def pipeline_definition_routes(app, kernel) -> None:
    @app.get("/api/v1/pipelines")
    async def pipelines():
        return await kernel.query(KernelQuery("pipelines"))

    @app.put("/api/v1/pipelines/{pipeline_id}")
    async def save_pipeline(pipeline_id: str, request: Request):
        values = {"pipeline_id": pipeline_id, "value": await request.json()}
        return await kernel.command(KernelCommand("save_pipeline", values=values))


def pipeline_run_routes(app, kernel) -> None:
    @app.get("/api/v1/projects/{project_id}/runs")
    async def runs(project_id: str):
        return await kernel.query(KernelQuery("runs", project_id))

    @app.post("/api/v1/projects/{project_id}/runs", status_code=201)
    async def start_run(project_id: str, request: Request):
        return await kernel.command(
            KernelCommand("start_run", project_id, await request.json())
        )


def pipeline_control_routes(app, kernel) -> None:
    @app.post("/api/v1/runs/{run_id}/confirm", status_code=202)
    async def confirm(run_id: str):
        return await kernel.command(
            KernelCommand("confirm_run", values={"run_id": run_id})
        )

    @app.post("/api/v1/runs/{run_id}/resolve", status_code=202)
    async def resolve(run_id: str, request: Request):
        decision = await request.json()
        values = {"run_id": run_id, **decision}
        return await kernel.command(KernelCommand("resolve_run", values=values))


def library_routes(app) -> None:
    @app.get("/api/v1/library")
    async def library():
        return list_packages()


def graph_tool_routes(app, kernel) -> None:
    @app.post("/api/v1/tools/graph-query")
    async def graph_query(request: Request):
        args = (await request.json())["arguments"]
        if args["action"] == "get":
            node = await kernel.query(
                KernelQuery(
                    "admitted_node",
                    args["project_id"],
                    {"node_id": args["node_id"]},
                )
            )
            return node["payload"]
        if args["action"] == "search":
            return await kernel.query(
                KernelQuery("graph_search", args["project_id"], {"text": args["query"]})
            )
        raise HTTPException(400, "unknown action")


def report_routes(app, kernel) -> None:
    @app.get("/api/v1/projects/{project_id}/report/projection")
    async def report_projection(project_id: str):
        return await kernel.query(KernelQuery("report_projection", project_id))

    @app.post("/api/v1/projects/{project_id}/report/validate")
    async def validate_report(project_id: str, request: Request):
        values = await request.json()
        return await kernel.query(KernelQuery("report_validate", project_id, values))

    @app.get("/api/v1/projects/{project_id}/report/bibtex")
    async def export_bibtex(project_id: str, artifact_id: str):
        values = {"artifact_id": artifact_id}
        return await kernel.query(KernelQuery("report_bibtex", project_id, values))


def _artifact_values(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"content_base64", "media_type"}:
        raise ValueError("artifact requires only content_base64 and media_type")
    try:
        content = b64decode(value["content_base64"], validate=True)
    except (Base64Error, TypeError) as error:
        raise ValueError("artifact content_base64 must be valid base64") from error
    return {"content": content, "media_type": value["media_type"]}


_ERROR_TEXT = {"session_spec_invalid": "此对话的 Agent 配置已变更，需要重启会话"}


async def relay(events):
    try:
        async for event in events:
            event_type = event.pop("type")
            yield sse_frame(event_type, event)
    except Exception as error:  # noqa: BLE001
        yield sse_frame("error", _error_payload(error))


def _error_payload(error: Exception) -> dict:
    code = getattr(error, "code", None)
    detail = _ERROR_TEXT.get(code) if code else None
    payload = {"detail": detail or str(error)}
    return {**payload, "code": code} if code else payload


def sse_frame(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def frontend_routes(app: FastAPI) -> None:
    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str):
        dist = ROOT / "web" / "dist"
        asset = dist / path
        if path and asset.is_file():
            return FileResponse(asset)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html")
        raise HTTPException(404, "frontend not built")


kernel = default_kernel()
app = create_app(kernel)
