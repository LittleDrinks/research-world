from __future__ import annotations

import asyncio
import hashlib
import json
from contextlib import asynccontextmanager
from urllib.parse import urlsplit, urlunsplit

from acp import (
    PROTOCOL_VERSION,
    ReadTextFileResponse,
    RequestError,
    connect_to_agent,
    resource_link_block,
    text_block,
)
from acp.schema import (
    AgentMessageChunk,
    ClientCapabilities,
    Implementation,
    TextContentBlock,
)
from acp.ws import create_websocket_stream
from json_repair import repair_json


class RuntimeCapabilityError(RuntimeError):
    pass


class RuntimeRequestError(ValueError):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


def _raise_request_error(error: RequestError) -> None:
    data = error.data if isinstance(error.data, dict) else {}
    message = str(data.get("details") or error)
    if error.code == -32602:
        raise RuntimeRequestError(message, data.get("code")) from None
    raise RuntimeCapabilityError(message) from error


class RuntimeClient:
    def __init__(self, url: str, project_id: str | None = None):
        self.url = _websocket_url(url)
        self.project_id = project_id
        self.kernel = None

    def bind_kernel(self, kernel) -> None:
        self.kernel = kernel

    async def recognize(self, workspace: str) -> dict:
        return await self._extension("runtime/discover", {"workspace": workspace})

    async def validate_agent(self, agent_spec: dict) -> dict:
        return await self._extension(
            "runtime/agents/validate", {"agent_spec": agent_spec}
        )

    async def launch(self, agent_spec: dict, workspace: str, **values) -> str:
        payload = {"agent_spec": agent_spec, "workspace": workspace, **values}
        result = await self._extension("runtime/launch", payload)
        return result["session_id"]

    async def inspect(self, session_id: str) -> dict:
        return await self._extension("runtime/inspect", {"session_id": session_id})

    async def embed(
        self, endpoint: str, model: str, texts: list[str]
    ) -> list[list[float]]:
        result = await self._extension(
            "runtime/embed", {"endpoint": endpoint, "model": model, "texts": texts}
        )
        return result["value"]

    async def prompt_stream(
        self,
        session_id: str,
        message: str,
        project_id: str | None = None,
        node_ids: list[str] | None = None,
    ):
        client = KernelClient(self._kernel(), project_id or self.project_id)
        async with self._connect(client) as connection:
            blocks = _prompt_blocks(message, node_ids or [])
            task = asyncio.create_task(connection.prompt(session_id, blocks))
            async for update in _updates(client, task):
                yield update
            try:
                response = await task
            except RequestError as error:
                _raise_request_error(error)
            yield {"type": "done", "stop_reason": response.stop_reason}

    async def prompt(
        self, session_id: str, message: str, project_id: str | None = None
    ) -> str:
        parts = []
        async for event in self.prompt_stream(session_id, message, project_id):
            if event["type"] == "delta":
                parts.append(event["text"])
        return "".join(parts)

    def json(
        self,
        agent_spec: dict,
        instruction: str,
        payload: dict,
        required: tuple[str, ...],
        operation_id: str | None = None,
    ) -> dict:
        return asyncio.run(
            self._json(agent_spec, instruction, payload, required, operation_id)
        )

    async def _json(
        self, agent_spec, instruction, payload, required, operation_id=None
    ):
        requested = _operation_session_id(operation_id) if operation_id else None
        session_id = await self.launch(
            agent_spec, await self._workspace(), session_id=requested
        )
        if cached := _cached_json(await self.inspect(session_id), required, session_id):
            return cached
        prompt = f"{instruction}\nReturn one JSON object and no prose.\n{json.dumps(payload, ensure_ascii=False)}"
        for _ in range(2):
            await self.prompt(session_id, prompt, self.project_id)
            view = await self.inspect(session_id)
            turn = view["turns"][-1]
            value, missing = _validated_json(turn["output"] or "", required)
            if not missing:
                return _json_result(value, session_id, turn)
            prompt = _json_correction(missing)
        raise ValueError(f"runtime response missing required field '{missing[0]}'")

    async def _extension(self, method: str, params: dict) -> dict:
        try:
            async with self._connect(
                KernelClient(self._kernel(), self.project_id)
            ) as connection:
                return await connection.ext_method(method, params)
        except RequestError as error:
            _raise_request_error(error)

    @asynccontextmanager
    async def _connect(self, client):
        transport = await create_websocket_stream(self.url)
        connection = connect_to_agent(client, transport)
        await connection.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=ClientCapabilities(),
            client_info=Implementation(
                name="research-kernel", title="Research Kernel", version="0.1.0"
            ),
        )
        try:
            yield connection
        finally:
            await connection.close()

    async def _workspace(self) -> str:
        if self.project_id is None:
            raise RuntimeError("project-bound RuntimeClient required")
        from .kernel import KernelQuery

        return await self._kernel().query(KernelQuery("workspace", self.project_id))

    def _kernel(self):
        if self.kernel is None:
            raise RuntimeError("RuntimeClient requires a bound ResearchKernel")
        return self.kernel


class KernelClient:
    def __init__(self, kernel, project_id):
        self.kernel = kernel
        self.project_id = project_id
        self.updates: asyncio.Queue = asyncio.Queue()

    async def session_update(self, session_id, update, **kwargs):
        await self.updates.put(update)

    async def read_text_file(self, session_id, path, **kwargs):
        node = await self._node(path.lstrip("@"))
        return ReadTextFileResponse(content=_node_document(node))

    async def ext_method(self, method: str, params: dict) -> dict | list:
        extension = method.lstrip("_")
        if extension == "research/capture_artifact":
            return await self._capture_artifact(params)
        if extension == "research/submit_observation":
            return await self._submit_observation(params)
        if extension == "research/report_validate":
            return await self._report_validate(params)
        if extension == "research/report_projection":
            return await self._report_projection(params)
        if extension == "research/export_bibtex":
            return await self._export_bibtex(params)
        if extension != "research/graph_query":
            raise RuntimeError(f"unsupported client extension: {method}")
        if params["action"] == "get":
            return await self._node(params["node_id"])
        if params["action"] == "search":
            return await self._search(params.get("query", ""))
        raise ValueError("unknown graph action")

    async def ext_notification(self, method: str, params: dict) -> None:
        return None

    async def _node(self, node_id: str) -> dict:
        from .kernel import KernelQuery

        values = {"node_id": _canonical_node_id(node_id)}
        return await self.kernel.query(
            KernelQuery("admitted_node", self.project_id, values)
        )

    async def _search(self, text: str) -> list[dict]:
        from .kernel import KernelQuery

        return await self.kernel.query(
            KernelQuery("graph_search", self.project_id, {"text": text})
        )

    async def _report_validate(self, params: dict) -> dict:
        from .kernel import KernelQuery

        values = {"facts": params.get("facts")}
        return await self.kernel.query(
            KernelQuery("report_validate", self.project_id, values)
        )

    async def _report_projection(self, params: dict) -> dict:
        from .kernel import KernelQuery

        return await self.kernel.query(
            KernelQuery("report_projection", self.project_id)
        )

    async def _export_bibtex(self, params: dict) -> dict:
        from .kernel import KernelQuery

        values = {"artifact_id": params["artifact_id"]}
        return await self.kernel.query(
            KernelQuery("report_bibtex", self.project_id, values)
        )

    async def _capture_artifact(self, params: dict) -> dict:
        from .kernel import KernelCommand

        values = {
            "content": params["content"].encode(),
            "media_type": params["media_type"],
        }
        return await self.kernel.command(
            KernelCommand("capture_artifact", self.project_id, values)
        )

    async def _submit_observation(self, params: dict) -> dict:
        from .kernel import KernelCommand

        return await self.kernel.command(
            KernelCommand("observation", self.project_id, params)
        )


class RuntimeEmbedding:
    def __init__(self, client: RuntimeClient, endpoint: str, model: str):
        self.client = client
        self.endpoint = endpoint
        self.model = model

    def __call__(self, text: str) -> list[float]:
        try:
            return asyncio.run(self.client.embed(self.endpoint, self.model, [text]))[0]
        except Exception as error:
            raise RuntimeCapabilityError(str(error)) from error


async def _updates(client: KernelClient, task):
    while not task.done() or not client.updates.empty():
        try:
            update = await asyncio.wait_for(client.updates.get(), timeout=0.1)
        except TimeoutError:
            continue
        event = _update_event(update)
        if event:
            yield event


def _update_event(update):
    if isinstance(update, AgentMessageChunk) and isinstance(
        update.content, TextContentBlock
    ):
        return {"type": "delta", "text": update.content.text}
    value = update.model_dump(by_alias=True, exclude_none=True)
    if value.get("sessionUpdate", "").startswith("tool_call"):
        return {"type": "tool", "update": value}
    return None


def _websocket_url(value: str) -> str:
    parsed = urlsplit(value)
    scheme = "wss" if parsed.scheme in {"https", "wss"} else "ws"
    path = parsed.path.rstrip("/") + "/acp/"
    return urlunsplit((scheme, parsed.netloc, path, "", ""))


def _canonical_node_id(value: str) -> str:
    node_id = value.lstrip("@")
    return node_id if node_id.startswith("node:") else f"node:{node_id}"


def _prompt_blocks(message: str, node_ids: list[str]) -> list:
    resources = [
        resource_link_block(node_id, node_id, title=f"Research node {node_id}")
        for node_id in node_ids
    ]
    return [text_block(message), *resources]


def _turn_usage(turn: dict) -> dict:
    event = next(
        (item for item in reversed(turn["events"]) if item["type"] == "turn_end"), {}
    )
    return event.get("data", {}).get("usage", {})


def _json_result(value: dict, session_id: str, turn: dict) -> dict:
    return {
        **value,
        "_session_id": session_id,
        "_turn_id": turn["id"],
        "_usage": _turn_usage(turn),
    }


def _cached_json(view: dict, required: tuple[str, ...], session_id: str) -> dict | None:
    for turn in reversed(view.get("turns", [])):
        value, missing = _validated_json(turn.get("output") or "", required)
        if not missing:
            return _json_result(value, session_id, turn)
    return None


def _operation_session_id(operation_id: str) -> str:
    digest = hashlib.sha256(operation_id.encode()).hexdigest()
    return f"s-op-{digest[:32]}"


def _validated_json(output: str, required: tuple[str, ...]) -> tuple[dict, list[str]]:
    try:
        value = json_object(output)
    except (TypeError, ValueError):
        return {}, ["valid JSON object"]
    return value, [field for field in required if field not in value]


def _json_correction(missing: list[str]) -> str:
    fields = ", ".join(missing)
    return f"上一个回答缺少必需字段：{fields}。重新返回符合原始契约的 JSON 对象，不要解释。"


def _node_document(node: dict) -> str:
    value = {
        key: node.get(key)
        for key in (
            "id",
            "kind",
            "life_state",
            "direction_status",
            "payload",
            "rebuttal",
        )
    }
    return json.dumps(value, ensure_ascii=False, indent=2)


def _node_summary(node: dict) -> dict:
    payload = node["payload"]
    text = payload.get("title") or payload.get("text") or payload.get("summary") or ""
    return {
        "id": node["id"],
        "kind": node["kind"],
        "life_state": node["life_state"],
        "summary": text,
    }


def json_object(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ValueError("runtime response did not contain a JSON object")
    value = repair_json(text[start:], return_objects=True)
    if not isinstance(value, dict):
        raise TypeError("runtime response must be a JSON object")
    return value
