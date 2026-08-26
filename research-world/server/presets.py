from __future__ import annotations

DEFAULT_OPTIONS = {
    "reasoning_effort": "medium",
    "sandbox": "read-only",
    "max_rounds": 12,
    "token_budget": 200000,
}


def agent_draft(preset_id: str, catalog: dict) -> dict:
    preset = _preset(preset_id, catalog)
    spec = {**preset["spec"], **_defaults(catalog), "options": dict(DEFAULT_OPTIONS)}
    issues = [
        _tool_issue(tool)
        for tool in preset["tools"]
        if tool["status"] != "ready"
    ]
    return {
        "preset_id": preset["id"],
        "reason": preset["description"],
        "spec": spec,
        "tools": preset["tools"],
        "confirmable": not issues,
        "issues": issues,
    }


def _tool_issue(tool: dict) -> str:
    state = " / ".join(filter(None, [tool["status"], tool.get("reason")]))
    return f"tool unavailable: {tool['id']} ({state})"


def _preset(preset_id: str, catalog: dict) -> dict:
    for preset in catalog.get("presets", []):
        if preset["id"] == preset_id:
            return preset
    raise ValueError(f"unknown preset: {preset_id}")


def _defaults(catalog: dict) -> dict:
    runtime = next(
        (item for item in catalog.get("runtimes", [])
         if item.get("id") == "codex" and item.get("status") == "ready"), None
    )
    if runtime is None:
        raise ValueError("no ready Codex runtime in runtime catalog")
    runtime_ref = {"id": runtime["id"], "realm": runtime["realm"]}
    for endpoint in catalog.get("endpoints", []):
        if not endpoint.get("available") or runtime_ref not in endpoint.get("runtime_refs", []):
            continue
        model = next((item for item in catalog.get("models", [])
                      if item["endpoint"] == endpoint["id"]), None)
        if model:
            return {"runtime": runtime_ref,
                    "endpoint": endpoint["id"], "model": model["id"]}
    raise ValueError("no available Endpoint/Model pair in runtime catalog")
