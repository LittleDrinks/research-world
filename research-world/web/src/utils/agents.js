export const AGENT_OPTION_DEFAULTS = { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 12, token_budget: 200000 };


export function blockedTools(selected, ...groups) {
  const states = toolStates(groups.flat());
  return selected.map((id) => states.get(id) || { id, status: "missing" })
    .filter((tool) => tool.status !== "ready");
}


export function toolStatus(tool) {
  const state = [tool.status, tool.reason].filter(Boolean).join(" / ");
  return `${tool.id}（${state}）`;
}


function toolStates(tools) {
  const states = new Map();
  tools.forEach((tool) => states.set(tool.id, { ...states.get(tool.id), ...tool }));
  return states;
}


export function newAgentPayload(form, catalog, capabilities = { skills: [], tools: [] }) {
  const endpoint = catalog.endpoints.find((item) => item.available) || catalog.endpoints[0];
  const model = catalog.models.find((item) => item.endpoint === endpoint?.id);
  return { id: form.id.trim(), name: form.name.trim(), instructions: form.instructions.trim(),
    endpoint: endpoint?.id || "", model: model?.id || "",
    skills: [...capabilities.skills], tools: [...capabilities.tools], options: { ...AGENT_OPTION_DEFAULTS } };
}
