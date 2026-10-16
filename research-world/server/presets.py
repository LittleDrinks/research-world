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
    issues = _preset_issues(preset)
    return {
        "preset_id": preset["id"],
        "reason": preset["description"],
        "spec": spec,
        "tools": preset["tools"],
        "skills": preset.get("skills", []),
        "confirmable": not issues,
        "issues": issues,
    }


def require_capabilities_ready(catalog: dict, value: dict) -> None:
    tool_states = _capability_states(catalog, "tools")
    issues = [
        _tool_issue(tool_states.get(tool, {"id": tool, "status": "missing"}))
        for tool in value.get("tools", [])
        if tool_states.get(tool, {}).get("status") != "ready"
    ]
    skill_states = _capability_states(catalog, "skills")
    issues.extend(
        _skill_issue(skill_states.get(skill, {"id": skill, "status": "missing"}))
        for skill in value.get("skills", [])
        if skill_states.get(skill, {}).get("status") != "ready"
    )
    if issues:
        raise ValueError(", ".join(issues))


def _preset_issues(preset: dict) -> list[str]:
    tools = [_tool_issue(item) for item in preset["tools"] if item["status"] != "ready"]
    skills = [_skill_issue(item) for item in preset.get("skills", []) if item["status"] != "ready"]
    return [*tools, *skills]


def _capability_states(catalog: dict, key: str) -> dict[str, dict]:
    states = {}
    for preset in catalog.get("presets", []):
        for item in preset.get(key, []):
            states[item["id"]] = {**states.get(item["id"], {}), **item}
    for item in catalog.get(key, []):
        status = item.get("status", "ready")
        states[item["id"]] = {**states.get(item["id"], {}), **item, "status": status}
    return states


def _tool_issue(tool: dict) -> str:
    state = " / ".join(filter(None, [tool["status"], tool.get("reason")]))
    return f"tool unavailable: {tool['id']} ({state})"


def _skill_issue(skill: dict) -> str:
    state = " / ".join(filter(None, [skill["status"], skill.get("reason")]))
    return f"skill unavailable: {skill['id']} ({state})"


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
