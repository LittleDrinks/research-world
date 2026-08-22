from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .agents import AgentRegistry
from .config import ROOT, load_settings
from .library import list_packages
from .runtime_client import RuntimeClient
from .threads import ThreadManager
from .workflows import default_engine
from .world import World, node_text


def create_app(
    world: World,
    runtime: RuntimeClient | None = None,
    agents: AgentRegistry | None = None,
) -> FastAPI:
    settings = load_settings()
    runtime = runtime or RuntimeClient(settings.runtime_url, world)
    agents = agents or AgentRegistry(settings.agents_root)
    app = FastAPI(title="Research World", version="2")
    error_handlers(app)
    project_routes(app, world)
    graph_routes(app, world)
    thread_routes(app, world, runtime, agents)
    runtime_routes(app, world, runtime, agents)
    workflow_routes(app, world)
    tool_routes(app, world)
    frontend_routes(app)
    return app


def error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KeyError)
    async def missing(_request, _error):
        return JSONResponse({"detail": "not found"}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(_request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)


def project_routes(app: FastAPI, world: World) -> None:
    health_route(app)
    project_collection_routes(app, world)
    project_state_routes(app, world)


def health_route(app: FastAPI) -> None:
    @app.get("/api/v1/health")
    async def health():
        return {"ok": True}


def project_collection_routes(app: FastAPI, world: World) -> None:
    @app.get("/api/v1/projects")
    async def projects():
        return project_cards(world)

    @app.post("/api/v1/projects", status_code=201)
    async def create_project(request: Request):
        value = await request.json()
        try:
            return world.create_project(
                value["name"],
                Path(value["root"]),
                value["question"],
                value.get("assembly"),
            )
        except ValueError as error:
            raise HTTPException(400, str(error)) from error


def project_state_routes(app: FastAPI, world: World) -> None:
    @app.get("/api/v1/bootstrap")
    async def bootstrap(project_id: str | None = None):
        return bootstrap_data(world, project_id)

    @app.patch("/api/v1/projects/{project_id}")
    async def update_project(project_id: str, request: Request):
        value = await request.json()
        return world.set_auto(project_id, bool(value["auto"]))


def graph_routes(app: FastAPI, world: World) -> None:
    graph_node_routes(app, world)
    graph_edge_routes(app, world)


def graph_node_routes(app: FastAPI, world: World) -> None:
    @app.get("/api/v1/nodes/{node_id}")
    async def node(node_id: str):
        return get_or_404(world.node, node_id)

    @app.post("/api/v1/projects/{project_id}/nodes", status_code=201)
    async def create_node(project_id: str, request: Request):
        value = await request.json()
        state = {key: value[key] for key in NODE_STATE_KEYS if key in value}
        return world.create_node(project_id, value["kind"], value["payload"], **state)

    @app.patch("/api/v1/nodes/{node_id}")
    async def update_node(node_id: str, request: Request):
        value = await request.json()
        state = {key: value[key] for key in UPDATE_KEYS if key in value}
        return world.update_node(node_id, value.get("payload"), **state)


def graph_edge_routes(app: FastAPI, world: World) -> None:
    @app.post("/api/v1/projects/{project_id}/edges", status_code=201)
    async def create_edge(project_id: str, request: Request):
        value = await request.json()
        ensure_project_node(world, project_id, value["source"])
        return world.add_edge(value["source"], value["target"], value["polarity"])


def thread_routes(
    app: FastAPI,
    world: World,
    runtime: RuntimeClient,
    agents: AgentRegistry,
) -> None:
    manager = ThreadManager(world, runtime, agents)
    thread_collection_routes(app, world, manager)
    thread_message_routes(app, manager)
    thread_node_routes(app, manager)


def thread_collection_routes(app, world, manager) -> None:
    @app.get("/api/v1/projects/{project_id}/threads")
    async def threads(project_id: str):
        get_or_404(world.project, project_id)
        return world.threads(project_id)

    @app.post("/api/v1/projects/{project_id}/threads", status_code=201)
    async def create_thread(project_id: str, request: Request):
        value = await request.json()
        return await manager.create(
            project_id,
            value.get("title", "新对话"),
            value.get("agent_id", "research-assistant"),
            value.get("node_ids", []),
        )


def thread_message_routes(app, manager) -> None:
    @app.get("/api/v1/threads/{thread_id}")
    async def thread(thread_id: str):
        return await manager.detail(thread_id)

    @app.post("/api/v1/threads/{thread_id}/prompts")
    async def prompt(thread_id: str, request: Request):
        value = await request.json()
        return StreamingResponse(
            relay(manager.prompt(thread_id, value["message"])),
            media_type="text/event-stream",
        )

    @app.post("/api/v1/threads/{thread_id}/restart")
    async def restart(thread_id: str):
        return await manager.restart(thread_id)


def thread_node_routes(app, manager) -> None:
    @app.post("/api/v1/threads/{thread_id}/nodes")
    async def pin_node(thread_id: str, request: Request):
        return manager.pin(thread_id, (await request.json())["node_id"])

    @app.delete("/api/v1/threads/{thread_id}/nodes/{node_id}")
    async def unpin_node(thread_id: str, node_id: str):
        return manager.unpin(thread_id, node_id)


def runtime_routes(
    app: FastAPI,
    world: World,
    runtime: RuntimeClient,
    agents: AgentRegistry,
) -> None:
    runtime_session_routes(app, world, runtime)
    agent_routes(app, agents)


def runtime_session_routes(app, world, runtime) -> None:
    @app.get("/api/v1/runtime/catalog")
    async def catalog(project_id: str):
        project = get_or_404(world.project, project_id)
        return await runtime.recognize(project["root"])

    @app.get("/api/v1/runtime/sessions/{session_id}")
    async def session(session_id: str):
        return await runtime.inspect(session_id)


def agent_routes(app, agents) -> None:
    @app.get("/api/v1/agents")
    async def all_agents():
        return agents.all()

    @app.get("/api/v1/agents/{agent_id}")
    async def agent(agent_id: str):
        return get_or_404(agents.get, agent_id)

    @app.put("/api/v1/agents/{agent_id}")
    async def save_agent(agent_id: str, request: Request):
        return agents.save(agent_id, await request.json())


def workflow_routes(app: FastAPI, world: World) -> None:
    workflow_collection_routes(app, world)
    workflow_control_routes(app, world)


def workflow_collection_routes(app: FastAPI, world: World) -> None:
    @app.get("/api/v1/projects/{project_id}/workflows")
    async def workflows(project_id: str):
        return [workflow_view(world, item) for item in world.workflows(project_id)]

    @app.post("/api/v1/projects/{project_id}/workflows", status_code=201)
    async def start_workflow(project_id: str, request: Request):
        value = await request.json()
        return world.create_workflow(
            project_id, value["node_id"], value["kind"], value.get("payload")
        )


def workflow_control_routes(app: FastAPI, world: World) -> None:
    @app.post("/api/v1/workflows/{workflow_id}/confirm", status_code=202)
    async def confirm(workflow_id: str):
        workflow = world.workflow(workflow_id)
        run_async(default_engine(world, workflow["project_id"]).confirm, workflow_id)
        return workflow

    @app.post("/api/v1/workflows/{workflow_id}/resolve", status_code=202)
    async def resolve(workflow_id: str, request: Request):
        value = await request.json()
        workflow = world.workflow(workflow_id)
        run_async(
            default_engine(world, workflow["project_id"]).resolve,
            workflow_id,
            value["decision"],
            value["reason"],
        )
        return workflow


def tool_routes(app: FastAPI, world: World) -> None:
    @app.get("/api/v1/library")
    async def library():
        return list_packages()

    @app.post("/api/v1/tools/graph-query")
    async def graph_query(request: Request):
        args = (await request.json())["arguments"]
        if args["action"] == "get":
            return graph_node_payload(world, args["project_id"], args["node_id"])
        if args["action"] == "search":
            return [
                node_summary(node)
                for node in world.search(args["project_id"], args["query"])
            ]
        raise HTTPException(400, "unknown action")


def graph_node_payload(world: World, project_id: str, node_id: str) -> dict:
    node = get_or_404(world.node, node_id)
    if node["project_id"] != project_id:
        raise HTTPException(404, "not found")
    return node["payload"]


def node_summary(node: dict) -> dict:
    return {
        "id": node["id"],
        "kind": node["kind"],
        "life_state": node["life_state"],
        "summary": node_text(node["payload"]),
    }


NODE_STATE_KEYS = {
    "parent_id",
    "lineage_id",
    "life_state",
    "direction_status",
    "working",
}
UPDATE_KEYS = {
    "life_state",
    "direction_status",
    "working",
    "rejection_reason",
    "rebuttal",
}


def bootstrap_data(world: World, project_id: str | None) -> dict:
    projects = project_cards(world)
    selected = project_id or (projects[0]["id"] if projects else None)
    if not selected:
        return empty_bootstrap()
    get_or_404(world.project, selected)
    workflows = [workflow_view(world, item) for item in world.workflows(selected)]
    return {
        "projects": projects,
        "active_project_id": selected,
        "nodes": world.nodes(selected),
        "edges": world.edges(selected),
        "workflows": workflows,
        "threads": world.threads(selected),
        "slots": slot_view(workflows),
    }


def empty_bootstrap() -> dict:
    return {
        "projects": [],
        "active_project_id": None,
        "nodes": [],
        "edges": [],
        "workflows": [],
        "threads": [],
        "slots": [],
    }


def project_cards(world: World) -> list[dict]:
    cards = []
    for project in world.projects():
        nodes = world.nodes(project["id"])
        cards.append(
            {
                **project,
                "title": project["name"],
                "node_count": len(nodes),
                "workflow_count": len(world.workflows(project["id"])),
            }
        )
    return cards


def ensure_project_node(world: World, project_id: str, node_id: str) -> None:
    if get_or_404(world.node, node_id)["project_id"] != project_id:
        raise HTTPException(400, "node belongs to another project")


def get_or_404(getter, value: str):
    try:
        return getter(value)
    except KeyError as error:
        raise HTTPException(404, "not found") from error


def workflow_view(world: World, workflow: dict) -> dict:
    return {
        **workflow,
        "steps": world.steps(workflow["id"]),
        "events": world.workflow_events(workflow["id"]),
    }


def slot_view(workflows: list[dict], count: int = 2) -> list[dict]:
    active = [
        item
        for item in workflows
        if item["status"] in {"queued", "running", "waiting_human"}
    ]
    return [
        {"index": index + 1, "workflow": active[index] if index < len(active) else None}
        for index in range(count)
    ]


def run_async(function, *args) -> None:
    threading.Thread(target=function, args=args, daemon=True).start()


async def relay(events):
    try:
        async for event in events:
            event_type = event.pop("type")
            yield sse_frame(event_type, event)
    except Exception as error:  # noqa: BLE001 - stream failures become SSE errors.
        yield sse_frame("error", {"detail": str(error)})


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


settings = load_settings()
world = World(settings.database, settings.artifacts)
app = create_app(world, RuntimeClient(settings.runtime_url, world))
