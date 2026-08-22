from __future__ import annotations

from .agents import AgentRegistry
from .runtime_client import RuntimeClient
from .world import World


class ThreadManager:
    def __init__(
        self, world: World, runtime: RuntimeClient, agents: AgentRegistry
    ) -> None:
        self.world = world
        self.runtime = runtime
        self.agents = agents

    async def create(
        self,
        project_id: str,
        title: str = "新对话",
        agent_id: str = "research-assistant",
        node_ids: list[str] | None = None,
    ) -> dict:
        project = self.world.project(project_id)
        nodes = self._nodes(project_id, node_ids or [])
        session_id = await self.runtime.launch(
            self.agents.get(agent_id),
            project["root"],
            invoker={"kind": "human", "id": project_id},
            mode="resume",
        )
        thread = self.world.create_thread(project_id, title, session_id, agent_id)
        for node in nodes:
            thread = self.world.pin_thread_node(thread["id"], node["id"])
        return await self.detail(thread["id"])

    async def detail(self, thread_id: str) -> dict:
        thread = self.world.thread(thread_id)
        trace = await self.runtime.inspect(thread["session_id"])
        return {**thread, "runtime": trace}

    async def prompt(self, thread_id: str, message: str):
        thread = self.world.thread(thread_id)
        if not message.strip():
            raise ValueError("message cannot be empty")
        node_ids = [node["id"] for node in thread["nodes"]]
        events = self.runtime.prompt_stream(
            thread["session_id"], message.strip(), thread["project_id"], node_ids
        )
        async for event in events:
            yield event
        self.world.touch_thread(thread_id)

    async def restart(self, thread_id: str) -> dict:
        thread = self.world.thread(thread_id)
        project = self.world.project(thread["project_id"])
        session_id = await self.runtime.launch(
            self.agents.get(thread["agent_id"]),
            project["root"],
            invoker={"kind": "human", "id": thread_id},
            mode="resume",
        )
        self.world.update_thread_session(thread_id, session_id)
        return await self.detail(thread_id)

    def pin(self, thread_id: str, node_id: str) -> dict:
        return self.world.pin_thread_node(thread_id, node_id)

    def unpin(self, thread_id: str, node_id: str) -> dict:
        return self.world.unpin_thread_node(thread_id, node_id)

    def _nodes(self, project_id: str, node_ids: list[str]) -> list[dict]:
        nodes = [self.world.node(node_id) for node_id in node_ids]
        if any(node["project_id"] != project_id for node in nodes):
            raise ValueError("thread node belongs to another project")
        return nodes
