import { useMemo, useState } from "react";
import { AGENTS, DEFAULT_PROFILE, PREPARE_STEPS } from "./seed";

export function usePrototypeState() {
  const state = useCoreState();
  const visibleAgents = useMemo(() => filterAgents(state.agents, state.agentQuery), [state.agents, state.agentQuery]);
  return { ...state, visibleAgents, ...buildActions(state) };
}

function useCoreState() {
  const [agents, setAgents] = useState(AGENTS);
  const [selectedId, setSelectedId] = useState(AGENTS[0].id);
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [activeTab, setActiveTab] = useState("runtime");
  const [agentQuery, setAgentQuery] = useState("");
  const [catalogQuery, setCatalogQuery] = useState("");
  const [inventoryState, setInventoryState] = useState("content");
  const [notice, setNotice] = useState("");
  const [draft, setDraft] = useState(null);
  const [prepare, setPrepare] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  return { agents, setAgents, selectedId, setSelectedId, profile, setProfile, activeTab, setActiveTab, agentQuery, setAgentQuery, catalogQuery, setCatalogQuery, inventoryState, setInventoryState, notice, setNotice, draft, setDraft, prepare, setPrepare, deleteOpen, setDeleteOpen };
}

function buildActions(state) {
  return {
    patchProfile: (value) => state.setProfile((current) => ({ ...current, ...value })),
    toggleCapability: (type, id) => toggleCapability(state, type, id),
    refresh: () => refreshInventory(state),
    beginDraft: () => state.setDraft({ step: "choose", mode: null, goal: "" }),
    chooseDraft: (mode) => chooseDraft(state, mode),
    patchDraft: (value) => state.setDraft((current) => ({ ...current, ...value })),
    generateDraft: () => state.setDraft((current) => ({ ...current, step: "confirm", mode: "orchestrator" })),
    confirmDraft: () => confirmDraft(state),
    openPrepare: () => state.setPrepare({ state: "plan", steps: PREPARE_STEPS }),
    runPrepare: () => runPrepare(state),
    deleteAgent: () => deleteAgent(state),
    save: () => state.setNotice("Prototype：Profile 已保存到页面内存。"),
  };
}

function filterAgents(agents, query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return agents;
  return agents.filter((item) => `${item.name} ${item.id} ${item.runtime} ${item.model}`.toLowerCase().includes(needle));
}

function toggleCapability(state, type, id) {
  state.setProfile((current) => {
    const values = current[type];
    const next = values.includes(id) ? values.filter((item) => item !== id) : [...values, id];
    return { ...current, [type]: next };
  });
}

function refreshInventory(state) {
  state.setInventoryState("refreshing");
  window.setTimeout(() => state.setInventoryState("content"), 900);
}

function chooseDraft(state, mode) {
  const step = mode === "orchestrator" ? "describe" : "confirm";
  state.setDraft({ step, mode, goal: "", name: mode === "preset" ? "Source Researcher Copy" : "Untitled Agent" });
}

function confirmDraft(state) {
  const index = state.agents.length + 1;
  const name = state.draft.name || `Agent ${index}`;
  const item = { id: `agent:draft-${index}`, name, preset: state.draft.mode, runtime: "Codex CLI", model: "gpt-5.6-sol", status: "ready", modified: "now" };
  state.setAgents((items) => [...items, item]);
  state.setDraft(null);
  state.setNotice(`Prototype：已确认 ${item.id}，未调用 prepare 或模型。`);
}

function runPrepare(state) {
  state.setPrepare((current) => ({ ...current, state: "running", steps: setStepState(current.steps, "running") }));
  window.setTimeout(() => state.setPrepare((current) => ({ ...current, state: "done", steps: setStepState(current.steps, "succeeded") })), 1200);
}

function setStepState(steps, value) {
  return steps.map((item) => ({ ...item, state: value }));
}

function deleteAgent(state) {
  state.setAgents((items) => items.filter((item) => item.id !== state.selectedId));
  state.setSelectedId(AGENTS[1].id);
  state.setDeleteOpen(false);
  state.setNotice("Prototype：Agent 已从页面内存删除。" );
}
