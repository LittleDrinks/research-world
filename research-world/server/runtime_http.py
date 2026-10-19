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
            base_url=url.rstrip("/"), transport=transport, timeout=60
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

    async def catalog(self):
        return _response_json(await self._client.get('/api/v1/runtime/catalog'))

    async def validate(self, spec):
        return _response_json(await self._client.post('/api/v1/runtime/validate', json=spec))

    async def inspect(self, session_id):
        return _response_json(await self._client.get(f'/api/v1/runtime/sessions/{session_id}'))

    async def export(self, session_id):
        return _response_json(await self._client.get(f'/api/v1/runtime/sessions/{session_id}/export'))

    async def workspace(self,project_id,method='GET',model=None,stop=False):
        path=f'/api/v1/runtime/projects/{project_id}/workspace'+('/stop' if stop else '')
        response=await self._client.request(method,path,json={'model':model} if model else None,timeout=70)
        return _response_json(response)

    async def workspaces(self):
        return _response_json(await self._client.get('/api/v1/runtime/workspaces'))

    async def select_candidates(self, values):
        return _response_json(await self._client.post('/api/v1/runtime/mmr', json=values))

    async def workspace_file(self, project_id, path):
        response = await self._client.get(f'/api/v1/runtime/projects/{project_id}/workspace/file', params={'path': path})
        return _response_json(response)['content']

    async def delete_project(self, project_id):
        return _response_json(await self._client.delete(f'/api/v1/runtime/projects/{project_id}'))

    async def cancel(self, turn_id):
        return _response_json(await self._client.post(f'/api/v1/runtime/turns/{turn_id}/cancel'))

    async def subscribe(self, turn_id, after_seq=-1):
        import json
        path = f'/api/v1/runtime/turns/{turn_id}/events'
        async with self._client.stream('GET', path, params={'after_seq': after_seq}, timeout=None) as response:
            if response.is_error:
                await response.aread()
                _response_json(response)
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    yield json.loads(line[6:])


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
