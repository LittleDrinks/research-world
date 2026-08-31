from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

__all__ = ["RunView", "TurnView", "RuntimeHttpError", "RuntimeHttpClient"]


class RunView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    run_id: str
    parent_run_id: str | None
    session_id: str | None
    agent_snapshot: dict[str, Any]


class TurnView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    turn_id: str
    run_id: str
    message_id: str
    status: str
    result_text: str | None


class RuntimeHttpError(RuntimeError):
    def __init__(self, status_code: int, code: str, detail: Any):
        super().__init__(f"{status_code} {code}: {detail}")
        self.status_code = status_code
        self.code = code
        self.detail = detail


class RuntimeHttpClient:
    def __init__(
        self,
        url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._client = httpx.AsyncClient(
            base_url=url.rstrip("/"), transport=transport
        )

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> RuntimeHttpClient:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def launch(
        self, agent_spec: Mapping[str, Any], session_id: str | None = None
    ) -> RunView:
        response = await self._client.post(
            "/api/v1/runtime/launch",
            json={"agent_spec": dict(agent_spec), "session_id": session_id},
        )
        return RunView.model_validate(_response_json(response))

    async def submit(
        self, session_id: str, message: Mapping[str, Any]
    ) -> TurnView:
        response = await self._client.post(
            "/api/v1/runtime/submit",
            json={"session_id": session_id, "message": dict(message)},
        )
        return TurnView.model_validate(_response_json(response))


def _response_json(response: httpx.Response) -> Any:
    if not response.is_error:
        return response.json()
    data = _error_data(response)
    raise RuntimeHttpError(
        response.status_code,
        str(data.get("code") or "http_error"),
        data.get("detail", response.text),
    )


def _error_data(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}
