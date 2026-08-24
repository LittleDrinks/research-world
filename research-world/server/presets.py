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


def require_tools_ready(catalog: dict, value: dict) -> None:
    states = _tool_states(catalog)
    blocked = [
        _tool_issue(states.get(tool, {"id": tool, "status": "missing"}))
        for tool in value.get("tools", [])
        if states.get(tool, {}).get("status") != "ready"
    ]
    if blocked:
        raise ValueError(", ".join(blocked))


def _tool_states(catalog: dict) -> dict[str, dict]:
    states = {}
    for preset in catalog.get("presets", []):
        for tool in preset.get("tools", []):
            states[tool["id"]] = {**states.get(tool["id"], {}), **tool}
    for tool in catalog.get("tools", []):
        states[tool["id"]] = {**states.get(tool["id"], {}), **tool}
    return states


def _tool_issue(tool: dict) -> str:
    state = " / ".join(filter(None, [tool["status"], tool.get("reason")]))
    return f"tool unavailable: {tool['id']} ({state})"


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
