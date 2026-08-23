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
        f"tool unavailable: {tool['id']} ({tool['status']})"
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


def require_tools_ready(catalog: dict, value: dict) -> None:
    status = {
        item["id"]: item.get("status", "ready") for item in catalog.get("tools", [])
    }
    blocked = [
        f"{tool} ({status.get(tool, 'missing')})"
        for tool in value.get("tools", [])
        if status.get(tool, "missing") != "ready"
    ]
    if blocked:
        raise ValueError(f"tool unavailable: {', '.join(blocked)}")


def _preset(preset_id: str, catalog: dict) -> dict:
    for preset in catalog.get("presets", []):
        if preset["id"] == preset_id:
            return preset
    raise ValueError(f"unknown preset: {preset_id}")


def _defaults(catalog: dict) -> dict:
    endpoints = [item for item in catalog.get("endpoints", []) if item.get("available")]
    if not endpoints:
        raise ValueError("no available endpoint in runtime catalog")
    endpoint = endpoints[0]
    models = [
        item for item in catalog.get("models", []) if item["endpoint"] == endpoint["id"]
    ]
    return {"endpoint": endpoint["id"], "model": models[0]["id"] if models else ""}
