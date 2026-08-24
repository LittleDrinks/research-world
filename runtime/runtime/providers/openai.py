from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import httpx

from .base import Emit, EndpointUnavailable, ModelResult


class OpenAIProvider:
    id = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, timeout: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self, model, messages, tools, emit: Emit, context
    ) -> ModelResult:
        payload = _payload(model, messages, tools)
        accumulator = _Accumulator()
        try:
            await self._stream(payload, accumulator, emit)
        except httpx.TransportError as error:
            raise EndpointUnavailable(_transport_error(error)) from error
        return ModelResult(accumulator.message(), accumulator.usage)

    async def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        try:
            response = await self.client.post(
                self._url("embeddings"),
                json={"model": model, "input": texts},
                headers=self._headers(),
            )
        except httpx.TransportError as error:
            raise EndpointUnavailable(_transport_error(error)) from error
        await _check(response)
        rows = sorted(response.json()["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in rows]

    async def _stream(self, payload, accumulator, emit) -> None:
        async with self.client.stream(
            "POST", self._url("chat/completions"), json=payload, headers=self._headers()
        ) as response:
            await _check(response)
            async for line in response.aiter_lines():
                delta = accumulator.add(line)
                if delta:
                    await emit(delta)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


class _Accumulator:
    def __init__(self):
        self.text: list[str] = []
        self.calls: dict[int, dict] = defaultdict(_empty_call)
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def add(self, line: str) -> str | None:
        if not line.startswith("data: ") or line == "data: [DONE]":
            return None
        chunk = json.loads(line[6:])
        self._add_usage(chunk.get("usage"))
        choices = chunk.get("choices") or []
        return self._add_delta((choices[0].get("delta") or {}) if choices else {})

    def message(self) -> dict[str, Any]:
        value: dict[str, Any] = {"role": "assistant", "content": "".join(self.text)}
        if self.calls:
            value["tool_calls"] = [self.calls[index] for index in sorted(self.calls)]
        return value

    def _add_usage(self, usage) -> None:
        if not usage:
            return
        self.usage["prompt_tokens"] = usage.get("prompt_tokens", 0)
        self.usage["completion_tokens"] = usage.get("completion_tokens", 0)

    def _add_delta(self, delta: dict) -> str | None:
        for call in delta.get("tool_calls") or []:
            _merge_call(self.calls[call.get("index", 0)], call)
        content = delta.get("content")
        if content:
            self.text.append(content)
        return content


def _payload(model, messages, tools):
    value = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if tools:
        value["tools"] = tools
    return value


def _empty_call():
    return {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}


def _merge_call(target: dict, source: dict) -> None:
    target["id"] += source.get("id") or ""
    function = source.get("function") or {}
    target["function"]["name"] += function.get("name") or ""
    target["function"]["arguments"] += function.get("arguments") or ""


async def _check(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    await response.aread()
    if response.status_code in {408, 409, 429} or response.status_code >= 500:
        raise EndpointUnavailable(f"model endpoint returned {response.status_code}")
    raise RuntimeError(f"model endpoint returned {response.status_code}")


def _transport_error(error: httpx.TransportError) -> str:
    return f"model endpoint transport failed: {type(error).__name__}"
