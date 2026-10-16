export const AGENT_OPTION_DEFAULTS = { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 12, token_budget: 200000 };


export function blockedTools(selected, ...groups) {
  return blocked(selected, groups.flat());
}


export function blockedSkills(selected, ...groups) {
  return blocked(selected, groups.flat().map((item) => ({ status: "ready", ...item })));
}


export function blockedCapabilities(spec, preset, catalog) {
  return {
    tools: blockedTools(spec.tools, preset?.tools || [], catalog.tools),
    skills: blockedSkills(spec.skills, preset?.skills || [], catalog.skills),
  };
}


export function toolStatus(tool) {
  const state = [tool.status, tool.reason].filter(Boolean).join(" / ");
  return `${tool.id}（${state}）`;
}


function capabilityStates(items) {
  const states = new Map();
  items.forEach((item) => states.set(item.id, { ...states.get(item.id), ...item }));
  return states;
}


function blocked(selected, items) {
  const states = capabilityStates(items);
  return selected.map((id) => states.get(id) || { id, status: "missing" })
    .filter((item) => item.status !== "ready");
}


export function newAgentPayload(form, catalog, capabilities = { skills: [], tools: [] }) {
  const endpoint = catalog.endpoints.find((item) => item.available) || catalog.endpoints[0];
  const model = catalog.models.find((item) => item.endpoint === endpoint?.id);
  return { id: form.id.trim(), name: form.name.trim(), instructions: form.instructions.trim(),
    endpoint: endpoint?.id || "", model: model?.id || "",
    skills: [...capabilities.skills], tools: [...capabilities.tools], options: { ...AGENT_OPTION_DEFAULTS } };
}
