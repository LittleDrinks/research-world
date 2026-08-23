from __future__ import annotations

import json
from contextlib import AsyncExitStack
from typing import Self

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from .connectors import Connector


class McpTools:
    def __init__(self, servers: list[Connector]):
        self.servers = servers
        self.stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.names: dict[str, tuple[str, str]] = {}
        self.specs: list[dict] = []

    async def __aenter__(self) -> Self:
        await self.stack.__aenter__()
        try:
            for server in self.servers:
                await self._connect(server)
        except BaseException as error:  # noqa: BLE001 - cancellation must close sessions
            await self._abort(error)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.stack.__aexit__(exc_type, exc, tb)

    async def call(self, name: str, arguments: dict) -> tuple[str, bool]:
        server_id, tool_name = self.names[name]
        result = await self.sessions[server_id].call_tool(tool_name, arguments)
        content = [
            item.model_dump(by_alias=True, exclude_none=True) for item in result.content
        ]
        return json.dumps(content, ensure_ascii=False), bool(result.isError)

    async def _connect(self, server: Connector) -> None:
        streams = await self.stack.enter_async_context(_transport(self.stack, server))
        read, write = streams[:2]
        session = await self.stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.sessions[server.id] = session
        await self._load_tools(server.id, session)

    async def _abort(self, error: BaseException) -> None:
        try:
            await self.stack.aclose()
        except BaseException as cleanup_error:
            raise RuntimeError("connector session failed") from cleanup_error
        raise RuntimeError("connector session failed") from error

    async def _load_tools(self, server_id: str, session: ClientSession) -> None:
        result = await session.list_tools()
        for tool in result.tools:
            public_name = f"mcp__{server_id}__{tool.name}"
            self.names[public_name] = (server_id, tool.name)
            self.specs.append(_spec(public_name, tool))


def _transport(stack: AsyncExitStack, server: Connector):
    config = server.resolved_config()
    if server.transport == "stdio":
        params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env"),
        )
        return stdio_client(params)
    if server.transport == "sse":
        return sse_client(config["url"], headers=config.get("headers"))
    client = httpx.AsyncClient(headers=config.get("headers"))
    stack.push_async_callback(client.aclose)
    return streamable_http_client(config["url"], http_client=client)


def _spec(name, tool):
    data = tool.model_dump(by_alias=True, exclude_none=True)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": data.get("description", ""),
            "parameters": data.get("inputSchema", {}),
        },
    }
