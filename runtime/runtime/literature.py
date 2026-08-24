from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

import httpx

BASE_HEADERS = {"User-Agent": "ResearchWorld/0.1 (literature research)"}
TIMEOUT = 20.0


async def crossref(values: dict) -> str:
    action = _action(values, {"search", "get"})
    if action == "get":
        data = await _json(f"https://api.crossref.org/works/{quote(_text(values, 'doi'), safe='')}")
        return _dump(data["message"])
    params = {"query.bibliographic": _text(values, "query"), "rows": _limit(values)}
    data = await _json("https://api.crossref.org/works", params)
    return _dump(data["message"]["items"])


async def openalex(values: dict) -> str:
    action = _action(values, {"search", "get"})
    if action == "get":
        work_id = quote(_text(values, "id"), safe="")
        return _dump(await _json(f"https://api.openalex.org/works/{work_id}"))
    params = {"search": _text(values, "query"), "per-page": _limit(values)}
    return _dump((await _json("https://api.openalex.org/works", params))["results"])


async def arxiv(values: dict) -> str:
    action = _action(values, {"search", "get"})
    params = _arxiv_params(action, values)
    xml = await _text_response("https://export.arxiv.org/api/query", params)
    return _dump(_arxiv_entries(xml))


async def pubmed(values: dict) -> str:
    action = _action(values, {"search", "metadata", "full_text"})
    if action == "search":
        params = {"db": "pubmed", "term": _text(values, "query"), "retmode": "json", "retmax": _limit(values)}
        return _dump((await _json(_entrez("esearch.fcgi"), params))["esearchresult"])
    if action == "metadata":
        params = {"db": "pubmed", "id": _text(values, "id"), "retmode": "json"}
        return _dump(await _json(_entrez("esummary.fcgi"), params))
    params = {"db": "pmc", "id": _text(values, "pmcid"), "retmode": "xml"}
    return await _text_response(_entrez("efetch.fcgi"), params)


async def project_files(bound, values: dict) -> str:
    action = _action(values, {"store", "read"})
    path = _workspace_path(bound.workspace, _text(values, "path"))
    if action == "read":
        return path.read_text(encoding="utf-8")
    content = _text(values, "content")
    artifact = await _capture(bound, content, _text(values, "media_type"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return _dump({"project_file": str(path.relative_to(bound.workspace)), "artifact": artifact})


async def _capture(bound, content: str, media_type: str) -> dict:
    if bound.client is None:
        raise RuntimeError("client does not provide artifact capture")
    values = {"content": content, "media_type": media_type}
    return await bound.client.ext_method("research/capture_artifact", values)


async def _json(url: str, params: dict | None = None) -> dict:
    text = await _text_response(url, params)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("literature endpoint returned a non-object")
    return value


async def _text_response(url: str, params: dict | None = None) -> str:
    async with httpx.AsyncClient(headers=BASE_HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url, params=params)
    response.raise_for_status()
    return response.text


def _arxiv_params(action: str, values: dict) -> dict:
    if action == "get":
        return {"id_list": _text(values, "id")}
    return {"search_query": f"all:{_text(values, 'query')}", "max_results": _limit(values)}


def _arxiv_entries(xml: str) -> list[dict]:
    root = ElementTree.fromstring(xml)
    namespace = {"a": "http://www.w3.org/2005/Atom"}
    return [_arxiv_entry(entry, namespace) for entry in root.findall("a:entry", namespace)]


def _arxiv_entry(entry, namespace: dict) -> dict:
    links = entry.findall("a:link", namespace)
    return {
        "id": _xml_text(entry, "a:id", namespace),
        "title": _xml_text(entry, "a:title", namespace),
        "summary": _xml_text(entry, "a:summary", namespace),
        "published": _xml_text(entry, "a:published", namespace),
        "authors": [_xml_text(author, "a:name", namespace) for author in entry.findall("a:author", namespace)],
        "pdf_url": next((link.get("href") for link in links if link.get("type") == "application/pdf"), None),
    }


def _xml_text(node, path: str, namespace: dict) -> str:
    found = node.find(path, namespace)
    return " ".join((found.text or "").split()) if found is not None else ""


def _workspace_path(workspace: Path, value: str) -> Path:
    path = (workspace / value).resolve()
    if not path.is_relative_to(workspace):
        raise ValueError("path escapes workspace")
    return path


def _action(values: dict, allowed: set[str]) -> str:
    action = values.get("action")
    if action not in allowed:
        raise ValueError(f"action must be one of: {', '.join(sorted(allowed))}")
    return action


def _text(values: dict, field: str) -> str:
    value = values.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _limit(values: dict) -> int:
    value = values.get("limit", 5)
    if not isinstance(value, int) or not 1 <= value <= 10:
        raise ValueError("limit must be an integer from 1 to 10")
    return value


def _entrez(path: str) -> str:
    return f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{path}"


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)
