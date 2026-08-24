import { useMemo, useState } from "react";
import { DRAFTS, ENDPOINTS, PREPARE_STEPS, PROFILES, RUNTIMES, SKILLS, TOOLS } from "./seed";

export function usePrototypeState() {
  const state = useCoreState();
  const profile = useMemo(() => selectedProfile(state), [state.profiles, state.selectedId]);
  const readiness = useMemo(() => readinessFor(profile), [profile]);
  const draftReadiness = useMemo(() => readinessFor(state.draft), [state.draft]);
  const visibleAgents = useMemo(() => filterProfiles(state), [state.profiles, state.agentQuery]);
  return { ...state, profile, readiness, draftReadiness, visibleAgents, ...buildActions(state) };
}

function useCoreState() {
  const [profiles, setProfiles] = useState(PROFILES);
  const [selectedId, setSelectedId] = useState(PROFILES[0].id);
  const [activeTab, setActiveTab] = useState("runtime");
  const [agentQuery, setAgentQuery] = useState("");
  const [catalogQuery, setCatalogQuery] = useState("");
  const [inventoryState, setInventoryState] = useState("content");
  const [notice, setNotice] = useState("");
  const [draft, setDraft] = useState(null);
  const [prepare, setPrepare] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  return { profiles, setProfiles, selectedId, setSelectedId, activeTab, setActiveTab, agentQuery, setAgentQuery, catalogQuery, setCatalogQuery, inventoryState, setInventoryState, notice, setNotice, draft, setDraft, prepare, setPrepare, deleteOpen, setDeleteOpen };
}

function buildActions(state) {
  return { ...profileActions(state), ...draftActions(state), ...prepareActions(state) };
}

function profileActions(state) {
  return {
    patchProfile: (value) => patchProfile(state, value),
    toggleCapability: (type, id) => toggleProfileCapability(state, type, id),
    refresh: () => refreshInventory(state),
    copyAgent: () => copyAgent(state),
    deleteAgent: () => deleteAgent(state),
    save: () => saveProfile(state),
  };
}

function draftActions(state) {
  return {
    beginDraft: () => state.setDraft({ step: "choose", mode: null, goal: "" }),
    chooseDraft: (mode) => chooseDraft(state, mode),
    patchDraft: (value) => state.setDraft((current) => ({ ...current, ...value })),
    toggleDraftCapability: (type, id) => toggleDraftCapability(state, type, id),
    generateDraft: () => generateDraft(state),
    confirmDraft: () => confirmDraft(state),
  };
}

function prepareActions(state) {
  return {
    openPrepare: (runtime) => openPrepare(state, runtime),
    advancePrepare: () => advancePrepare(state),
    runPrepare: () => runPrepare(state),
    cancelPrepare: () => cancelPrepare(state),
    retryPrepare: () => retryPrepare(state),
  };
}

function selectedProfile(state) {
  return state.profiles.find((item) => item.id === state.selectedId) || state.profiles[0];
}

function filterProfiles(state) {
  const needle = state.agentQuery.trim().toLowerCase();
  const rows = state.profiles.map((item) => ({ ...item, readiness: readinessFor(item) }));
  if (!needle) return rows;
  return rows.filter((item) => profileSearchText(item).includes(needle));
}

function profileSearchText(item) {
  return [item.name, item.id, item.preset, item.runtime, item.model].join(" ").toLowerCase();
}

function patchProfile(state, value) {
  state.setProfiles((items) => items.map((item) => (
    item.id === state.selectedId ? { ...item, ...value, modified: "unsaved" } : item
  )));
}

function toggleProfileCapability(state, type, id) {
  const profile = selectedProfile(state);
  patchProfile(state, { [type]: toggled(profile[type], id) });
}

function toggleDraftCapability(state, type, id) {
  state.setDraft((current) => ({ ...current, [type]: toggled(current[type], id) }));
}

function toggled(values, id) {
  return values.includes(id) ? values.filter((item) => item !== id) : [...values, id];
}

function refreshInventory(state) {
  state.setInventoryState("refreshing");
  window.setTimeout(() => state.setInventoryState("content"), 600);
}

function chooseDraft(state, mode) {
  if (mode === "orchestrator") {
    state.setDraft({ step: "describe", mode, goal: "" });
    return;
  }
  state.setDraft({ ...clone(DRAFTS[mode]), step: "confirm", mode });
}

function generateDraft(state) {
  state.setDraft((current) => ({
    ...clone(DRAFTS.orchestrator), goal: current.goal, step: "confirm", mode: "orchestrator",
  }));
}

function confirmDraft(state) {
  const readiness = readinessFor(state.draft);
  if (readiness.status !== "ready") return;
  const profile = { ...state.draft, modified: "now" };
  delete profile.step;
  delete profile.mode;
  delete profile.rationale;
  delete profile.goal;
  state.setProfiles((items) => [...items, profile]);
  state.setSelectedId(profile.id);
  state.setDraft(null);
  state.setNotice(`已创建 ${profile.id}；未调用 prepare 或模型。`);
}

function copyAgent(state) {
  const source = selectedProfile(state);
  const id = copyId(source.id, state.profiles);
  const copy = { ...clone(source), id, name: `${source.name} Copy`, preset: `copy:${source.id}`, modified: "now" };
  state.setProfiles((items) => [...items, copy]);
  state.setSelectedId(id);
  state.setNotice(`已复制为 ${id}；两个 Profile state 相互独立。`);
}

function copyId(id, profiles) {
  const base = `${id}-copy`;
  let next = base;
  let index = 2;
  while (profiles.some((item) => item.id === next)) next = `${base}-${index++}`;
  return next;
}

function deleteAgent(state) {
  const remaining = state.profiles.filter((item) => item.id !== state.selectedId);
  state.setProfiles(remaining);
  state.setSelectedId(remaining[0]?.id || "");
  state.setDeleteOpen(false);
  state.setNotice("Profile 已从 prototype 页面内存删除。");
}

function saveProfile(state) {
  if (readinessFor(selectedProfile(state)).status !== "ready") return;
  state.setProfiles((items) => items.map((item) => (
    item.id === state.selectedId ? { ...item, modified: "now" } : item
  )));
  state.setNotice("Profile snapshot 已保存到 prototype 页面内存。");
}

function openPrepare(state, runtime) {
  const target = runtime || RUNTIMES.find((item) => item.status === "missing");
  state.setPrepare({ state: "plan", target, outcome: "succeeded", steps: clone(PREPARE_STEPS), logs: ["plan · CLI 计划已生成"] });
}

function advancePrepare(state) {
  state.setPrepare((current) => ({
    ...current, state: "confirm", logs: [...current.logs, "confirm · 等待用户二次确认"],
  }));
}

function runPrepare(state) {
  state.setPrepare((current) => ({
    ...current, state: "running", steps: stepState(current.steps, "running"), logs: [...current.logs, "running · 开始受控 CLI prepare"],
  }));
  window.setTimeout(() => finishPrepare(state), 450);
}

function finishPrepare(state) {
  state.setPrepare((current) => {
    if (!current || current.state !== "running") return current;
    const result = current.outcome;
    return { ...current, state: result, steps: stepState(current.steps, result), logs: [...current.logs, `${result} · 脱敏日志已保留`] };
  });
}

function cancelPrepare(state) {
  state.setPrepare((current) => ({
    ...current, state: "cancelled", logs: [...current.logs, "cancelled · 用户取消，未继续写入"],
  }));
}

function retryPrepare(state) {
  state.setPrepare((current) => ({
    ...current, state: "confirm", steps: stepState(current.steps, "queued"), logs: [...current.logs, "retry · 保留旧日志并重新确认"],
  }));
}

function stepState(steps, value) {
  return steps.map((item) => ({ ...item, state: value }));
}

export function readinessFor(profile) {
  if (!profile?.id && !profile?.runtime && !profile?.endpoint) return blankReadiness(profile);
  const runtime = RUNTIMES.find((item) => item.id === profile.runtime && item.realm === profile.realm);
  const endpoint = ENDPOINTS.find((item) => item.id === profile.endpoint);
  const issues = readinessIssues(profile, runtime, endpoint);
  return { status: issues.length ? "blocked" : "ready", issues, groups: readinessGroups(profile, runtime, endpoint) };
}

function readinessIssues(profile, runtime, endpoint) {
  return [
    ...requiredIssues(profile),
    ...runtimeIssues(profile, runtime),
    ...endpointIssues(profile, endpoint),
    ...capabilityIssues(profile),
  ];
}

function requiredIssues(profile) {
  const fields = [["id", "Stable id"], ["name", "名称"], ["instructions", "Instructions"], ["workspace", "Workspace"], ["sandbox", "Sandbox"], ["reasoning", "Reasoning"]];
  return fields.filter(([key]) => !profile?.[key]?.trim()).map(([key, name]) => ({ code: `${key}_required`, message: `${name} 未决` }));
}

function runtimeIssues(profile, runtime) {
  if (!profile?.runtime || !profile?.realm) return [{ code: "runtime_required", message: "Runtime 与 realm 未决" }];
  if (!runtime) return [{ code: "runtime_unknown", message: "Runtime inventory 无对应 descriptor" }];
  return runtime.status === "ready" ? [] : [{ code: "runtime_not_ready", message: `${runtime.name}: ${runtime.reason}` }];
}

function endpointIssues(profile, endpoint) {
  if (!endpoint) return [{ code: "endpoint_required", message: "Endpoint 未决" }];
  if (!profile.model) return [{ code: "model_required", message: "Model 未决" }];
  if (!endpoint.models.includes(profile.model)) return [{ code: "model_mismatch", message: "Model 与 Endpoint 不匹配" }];
  if (!endpoint.runtimes.includes(profile.runtime)) return [{ code: "endpoint_runtime_mismatch", message: "Endpoint 与 Runtime 不匹配" }];
  return ["missing", "unknown"].includes(endpoint.secret) ? [{ code: "secret_unresolved", message: `Secret 状态为 ${endpoint.secret}` }] : [];
}

function capabilityIssues(profile) {
  const skills = unavailable(profile.skills || [], SKILLS);
  const tools = unavailable(profile.tools || [], TOOLS);
  return [...skills.map(capabilityIssue("Skill")), ...tools.map(capabilityIssue("Tool"))];
}

function capabilityIssue(kind) {
  return (item) => ({ code: `${kind.toLowerCase()}_not_ready`, message: `${kind} ${item.id}: ${item.status}` });
}

function unavailable(ids, catalog) {
  return ids.map((id) => catalog.find((item) => item.id === id) || { id, status: "missing" }).filter((item) => item.status !== "ready");
}

function readinessGroups(profile, runtime, endpoint) {
  const skills = unavailable(profile.skills || [], SKILLS);
  const tools = unavailable(profile.tools || [], TOOLS);
  return [
    group("Execution Runtime", runtime?.status === "ready", runtime ? `${runtime.id} · ${runtime.realm}` : "unresolved"),
    group("Endpoint / model", endpointReady(profile, endpoint), profile.endpoint && profile.model ? `${profile.endpoint} · ${profile.model}` : "unresolved"),
    group("Skills", !skills.length, `${profile.skills?.length || 0} selected · ${skills.length} blocked`),
    group("Tools", !tools.length, `${profile.tools?.length || 0} selected · ${tools.length} blocked`),
    group("Workspace", Boolean(profile.workspace && profile.sandbox), profile.workspace || "unresolved"),
    secretGroup(endpoint),
  ];
}

function endpointReady(profile, endpoint) {
  return Boolean(endpoint && endpoint.models.includes(profile.model) && endpoint.runtimes.includes(profile.runtime) && !["missing", "unknown"].includes(endpoint.secret));
}

function group(name, ready, detail) {
  return { name, status: ready ? "ready" : "blocked", detail };
}

function secretGroup(endpoint) {
  const status = endpoint?.secret || "unknown";
  return { name: "Secrets", status: ["configured", "not-required"].includes(status) ? "ready" : "unknown", detail: status };
}

function blankReadiness(profile) {
  const issues = requiredIssues(profile || {});
  issues.push({ code: "runtime_required", message: "Runtime 与 realm 未决" }, { code: "endpoint_required", message: "Endpoint 未决" });
  return { status: "blocked", issues, groups: readinessGroups(profile || {}, null, null) };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}
