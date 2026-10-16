from __future__ import annotations

import hashlib
import json
import re

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()
FULL_TEXT = "Complete article text. Results: measured evidence supports the E2E Direction."


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/v1/chat/completions")
async def completions(request: Request):
    value = await request.json()
    stream = _stream(_message(value["messages"]))
    return StreamingResponse(stream, media_type="text/event-stream")


@app.post("/v1/embeddings")
async def embeddings(request: Request) -> dict:
    value = await request.json()
    rows = [{"index": index, "embedding": _vector(text)} for index, text in enumerate(value["input"])]
    return {"object": "list", "data": rows, "model": value["model"]}


def _message(messages: list[dict]) -> dict:
    prompt = _prompt(messages)
    if "检索并交叉核验" in prompt:
        return _source_message(messages)
    if "生成恰好 count" in prompt:
        return _json_message({"candidates": _directions(prompt)})
    if "把 node 与 outputs" in prompt:
        return _json_message({"claims": [_claim()]})
    if "审核 direction" in prompt:
        return _json_message(_review(prompt))
    raise ValueError("unexpected E2E model prompt")


def _source_message(messages: list[dict]) -> dict:
    if not any(message.get("role") == "tool" for message in messages):
        return _store_call()
    match = re.search(r'"direction_id":\s*"(node:[0-9a-f]+)"', _prompt(messages))
    return _json_message({"source_candidates": _sources(match.group(1), _stored_artifact(messages))})


def _store_call() -> dict:
    arguments = {"action": "store", "path": "sources/e2e-full-text.txt",
                 "content": FULL_TEXT, "media_type": "text/plain"}
    call = {"index": 0, "id": "call-store-source", "type": "function",
            "function": {"name": "project_files", "arguments": json.dumps(arguments)}}
    return {"role": "assistant", "content": "", "tool_calls": [call]}


def _stored_artifact(messages: list[dict]) -> dict:
    content = next(message["content"] for message in messages if message.get("role") == "tool")
    stored = json.loads(content)
    return {**stored["artifact"], "project_file": stored["project_file"]}


def _sources(direction_id: str, artifact: dict) -> list[dict]:
    return [_available_source(direction_id, artifact), _unavailable_source(direction_id)]


def _available_source(direction_id: str, artifact: dict) -> dict:
    relation = {"direction_id": direction_id, "use": "supports", "relevance": "Direct full-text evidence.",
                "claims": ["The Direction is supported."],
                "locations": [{"locator": "Results, paragraph 1", "quote": "Measured evidence supports the E2E Direction."}]}
    full_text = {key: artifact[key] for key in ("id", "project_file", "media_type", "sha256")}
    return {**_bibliography("E2E admitted source"), "license": "CC-BY-4.0", "access_status": "open",
            "artifact": full_text, "relationship": relation, "retrieval": _retrieval(), "unresolved_questions": []}


def _unavailable_source(direction_id: str) -> dict:
    relation = {"direction_id": direction_id, "use": "background",
                "relevance": "Metadata is relevant but complete text is unavailable.", "claims": [], "locations": []}
    return {**_bibliography("E2E unavailable source"), "license": "unknown",
            "access_status": "full_text_unavailable", "artifact": None, "relationship": relation,
            "retrieval": _retrieval(), "unresolved_questions": ["Complete text could not be retrieved."]}


def _bibliography(title: str) -> dict:
    slug = title.lower().replace(" ", "-")
    return {"title": title, "authors": ["Ada Researcher"], "year": 2026,
            "venue": "Journal of E2E Evidence", "url": f"https://example.test/{slug}",
            "source_type": "journal_article"}


def _retrieval() -> dict:
    return {"query": "E2E auditable evidence", "database": "Crossref; OpenAlex",
            "verified_at": "2026-08-24T00:00:00Z"}


def _directions(prompt: str) -> list[dict]:
    count = int(re.search(r'"count":\s*(\d+)', prompt).group(1))
    return [{"title": f"E2E Direction {index}",
             "text": f"Test distinct deterministic source mechanism {index}."}
            for index in range(1, count + 1)]


def _claim() -> dict:
    return {"text": "The proposed mechanism is testable.", "verdict": "supported",
            "evidence": ["project question"]}


def _review(prompt: str) -> dict:
    evidence = re.search(r'"id":\s*"(node:[0-9a-f]+)"', prompt).group(1)
    return {"decision": "approve", "argument": "The Direction is testable.",
            "evidence": [evidence], "needs_experiment": False}


def _json_message(value: dict) -> dict:
    return {"role": "assistant", "content": json.dumps(value)}


def _prompt(messages: list[dict]) -> str:
    return "\n".join(str(message.get("content") or "") for message in messages)


def _vector(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode()).digest()
    return [(value - 127.5) / 127.5 for value in digest]


async def _stream(message: dict):
    chunk = {"choices": [{"delta": message}],
             "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
    yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"
