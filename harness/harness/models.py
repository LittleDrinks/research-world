import json
import time
from contextlib import contextmanager

import httpx


class ModelError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class ModelClient:
    def __init__(self, api_base, api_key, default_model, backoff=(0.5, 1.0, 2.0),
                 timeout=120.0):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.backoff = tuple(backoff)
        self._client = httpx.Client(timeout=timeout)

    def chat(self, messages, tools=None, model=None):
        payload = {"model": model or self.default_model, "messages": messages}
        if tools:
            payload["tools"] = tools
        err = None
        for attempt in range(len(self.backoff) + 1):
            body, err = self._once(payload)
            if body is not None:
                return _parse(body)
            if attempt < len(self.backoff):
                time.sleep(self.backoff[attempt])
        raise ModelError(f"model call failed after retries: {err}")

    def chat_stream(self, messages, tools=None, model=None):
        payload = {"model": model or self.default_model, "messages": messages,
                   "stream": True, "stream_options": {"include_usage": True}}
        if tools:
            payload["tools"] = tools
        deltas, calls = [], {}
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        with self._open(payload) as response:
            for line in response.iter_lines():
                delta = _apply_chunk(line, deltas, calls, usage)
                if delta:
                    yield delta
        message = {"role": "assistant", "content": "".join(deltas)}
        if calls:
            message["tool_calls"] = [calls[index] for index in sorted(calls)]
        return message, usage

    def _once(self, payload):
        url, headers = self._endpoint()
        try:
            r = self._client.post(url, json=payload, headers=headers)
        except httpx.TransportError as e:
            return None, e
        if r.status_code == 429 or r.status_code >= 500:
            return None, ModelError(f"model {r.status_code}: {r.text[:200]}")
        if r.status_code >= 400:
            raise ModelError(f"model {r.status_code}: {r.text[:200]}", r.status_code)
        return r.json(), None

    def _endpoint(self):
        return (f"{self.api_base}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}"})

    @contextmanager
    def _open(self, payload):
        url, headers = self._endpoint()
        err, opened = None, False
        for attempt in range(len(self.backoff) + 1):
            try:
                with self._client.stream("POST", url, json=payload, headers=headers) as r:
                    _check(r)
                    opened = True
                    yield r
                    return
            except httpx.TransportError as e:
                if opened:
                    raise
                err = e
            except ModelError as e:
                if e.status is not None:
                    raise
                err = e
            if attempt < len(self.backoff):
                time.sleep(self.backoff[attempt])
        raise ModelError(f"model call failed after retries: {err}")


def _check(response):
    if response.status_code < 400:
        return
    response.read()
    status = response.status_code if 400 <= response.status_code < 500 and response.status_code != 429 else None
    raise ModelError(f"model {response.status_code}: {response.text[:200]}", status)


def _apply_chunk(line, deltas, calls, usage):
    if not line.startswith("data: ") or line == "data: [DONE]":
        return None
    chunk = json.loads(line[6:])
    if chunk.get("usage"):
        usage["prompt_tokens"] = chunk["usage"].get("prompt_tokens", 0)
        usage["completion_tokens"] = chunk["usage"].get("completion_tokens", 0)
    choices = chunk.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    for part in delta.get("tool_calls") or []:
        _accumulate_call(calls, part)
    content = delta.get("content")
    if content:
        deltas.append(content)
    return content


def _accumulate_call(calls, part):
    slot = calls.setdefault(part.get("index", 0),
                            {"id": None, "type": "function",
                             "function": {"name": "", "arguments": ""}})
    if part.get("id"):
        slot["id"] = part["id"]
    function = part.get("function") or {}
    slot["function"]["name"] += function.get("name") or ""
    slot["function"]["arguments"] += function.get("arguments") or ""


def _parse(body):
    msg = body["choices"][0]["message"]
    usage = body.get("usage") or {}
    return msg, {"prompt_tokens": usage.get("prompt_tokens", 0),
                 "completion_tokens": usage.get("completion_tokens", 0)}
