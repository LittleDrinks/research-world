from __future__ import annotations

import os
from typing import Any

from acp import (
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptResponse,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AgentCapabilities,
    Implementation,
    ListSessionsResponse,
    SessionInfo,
)

from .service import Runtime


class RuntimeAgent:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.client: Client | None = None

    def on_connect(self, client: Client) -> None:
        self.client = client

    async def initialize(
        self, protocol_version: int, **kwargs: Any
    ) -> InitializeResponse:
        capabilities = AgentCapabilities(load_session=True)
        info = Implementation(
            name="research-agent-runtime",
            title="Research Agent Runtime",
            version="0.1.0",
        )
        return InitializeResponse(
            protocol_version=protocol_version,
            agent_capabilities=capabilities,
            agent_info=info,
        )

    async def new_session(self, cwd: str, **kwargs: Any) -> NewSessionResponse:
        value = {
            "workspace": cwd,
            "agent_spec": kwargs.get("agent_spec") or _default_spec(),
        }
        result = await self.runtime.launch(value)
        return NewSessionResponse(session_id=result["session_id"])

    async def load_session(
        self, cwd: str, session_id: str, **kwargs: Any
    ) -> LoadSessionResponse:
        self.runtime.inspect(session_id)
        return LoadSessionResponse()

    async def list_sessions(self, **kwargs: Any) -> ListSessionsResponse:
        values = [SessionInfo(**item) for item in self.runtime.sessions()]
        return ListSessionsResponse(sessions=values)

    async def prompt(
        self, session_id: str, prompt: list[Any], **kwargs: Any
    ) -> PromptResponse:
        blocks = [_block(item) for item in prompt]
        result = await self.runtime.prompt(
            session_id, blocks, self.client, self._emit(session_id)
        )
        reason = "end_turn" if result["status"] == "completed" else "max_turn_requests"
        return PromptResponse(stop_reason=reason)

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        self.runtime.cancel(session_id)

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "runtime/discover": lambda: self.runtime.recognize(params["workspace"]),
            "runtime/launch": lambda: self.runtime.launch(params),
            "runtime/inspect": lambda: _async_value(
                self.runtime.inspect(params["session_id"])
            ),
            "runtime/embed": lambda: self.runtime.embed(
                params["model"],
                params["texts"],
                params.get("runtime", "openai-compatible"),
            ),
        }
        value = await handlers[method.lstrip("_")]()
        return {"value": value} if isinstance(value, list) else value

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        return None

    def _emit(self, session_id: str):
        async def emit(value: str) -> None:
            if self.client:
                await self.client.session_update(
                    session_id=session_id,
                    update=update_agent_message(text_block(value)),
                )

        return emit


def _block(value):
    return (
        value.model_dump(by_alias=True, exclude_none=True)
        if hasattr(value, "model_dump")
        else dict(value)
    )


async def _async_value(value):
    return value


def _default_spec():
    runtime_id = "openai-compatible" if os.getenv("RUNTIME_API_BASE") else "codex"
    model = os.getenv("RUNTIME_MODEL") or os.getenv("CODEX_MODEL") or "gpt-5.6-sol"
    return {
        "id": "default",
        "name": "Research Assistant",
        "runtime": runtime_id,
        "model": model,
        "instructions": "Assist with scientific research.",
    }
