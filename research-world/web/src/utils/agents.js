import { defaultRuntime, endpointIssue, runtimeIssue, runtimeRefKey } from "./runtime";

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


export function agentCatalogIssue(form, catalog) {
  const runtime = runtimeIssue(form.runtime, catalog);
  if (runtime) return runtime;
  const endpoint = endpointIssue(form, catalog);
  if (endpoint) return endpoint;
  const presets = (catalog.presets || []).flatMap((preset) => preset.tools || []);
  const blocked = blockedTools(form.tools, presets, catalog.tools || []);
  const missing = form.skills.filter((id) => !(catalog.skills || []).some((item) => item.id === id));
  const unknown = missing.concat(blocked.filter((tool) => tool.status === "missing").map((tool) => tool.id));
  if (unknown.length) return `能力未被 Runtime 识别：${unknown.join("、")}`;
  if (blocked.length) return `Tool 不可用：${blocked.map(toolStatus).join("、")}`;
  return form.runtime.id === "codex" && form.tools.length ? "Codex Runtime 不支持 Tools" : "";
}


function toolStates(tools) {
  const states = new Map();
  tools.forEach((tool) => states.set(tool.id, { ...states.get(tool.id), ...tool }));
  return states;
}


export function newAgentPayload(form, catalog, capabilities = { skills: [], tools: [] }) {
  const runtime = defaultRuntime(catalog);
  const endpoint = runtime && catalog.endpoints.find((item) => item.available
    && item.runtime_refs?.some((ref) => runtimeRefKey(ref) === runtimeRefKey(runtime))
    && catalog.models.some((model) => model.endpoint === item.id));
  const model = catalog.models.find((item) => item.endpoint === endpoint?.id);
  return { id: form.id.trim(), name: form.name.trim(), instructions: form.instructions.trim(),
    runtime: runtime ? { id: runtime.id, realm: runtime.realm } : null,
    endpoint: endpoint?.id || "", model: model?.id || "",
    skills: [...capabilities.skills], tools: [...capabilities.tools], options: { ...AGENT_OPTION_DEFAULTS } };
}
