import { useMemo, useState } from "react";
import { CAPABILITIES, DEFAULT_DRAFT, PROVIDERS, RUNTIMES } from "./seed";

export function usePrototypeState() {
  const core = useCoreState();
  const runtime = RUNTIMES.find((item) => item.id === core.draft.runtimeId) || RUNTIMES[0];
  const provider = PROVIDERS.find((item) => item.id === core.draft.providerId) || PROVIDERS[0];
  const inventory = useMemo(() => filterInventory(core.query), [core.query]);
  return { ...core, runtime, provider, inventory, ...buildActions(core) };
}

function useCoreState() {
  const [draft, setDraft] = useState({ ...DEFAULT_DRAFT });
  const [agents, setAgents] = useState([{ id: "agent:reviewer", name: "Independent Reviewer", runtime: "codex" }]);
  const [scan, setScan] = useState({ status: "done", label: "刚刚完成", count: 20 });
  const [tests, setTests] = useState({});
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("skills");
  const [notice, setNotice] = useState("");
  return { draft, setDraft, agents, setAgents, scan, setScan, tests, setTests, query, setQuery, group, setGroup, notice, setNotice };
}

function buildActions({ draft, setDraft, agents, setAgents, setScan, setTests, setNotice }) {
  const patch = (value) => setDraft((current) => ({ ...current, ...value }));
  const selectRuntime = (item) => item.status === "ready" && patch({ channel: "cli", runtimeId: item.id, model: item.models[0], effort: item.efforts[1] || item.efforts[0] });
  const selectProvider = (item) => item.status === "ready" && patch({ channel: "api", providerId: item.id,
    model: item.models[0] || "", effort: item.efforts[1] || item.efforts[0] });
  const toggle = (type, id) => setDraft((current) => ({ ...current, selected: toggleSelected(current.selected, type, id) }));
  const test = (key) => runTimed(setTests, key);
  const rescan = () => runScan(setScan);
  const beginNew = () => startDraft(setDraft, setNotice);
  const create = () => createAgent(draft, agents, setAgents, setDraft, setNotice);
  return { patch, selectRuntime, selectProvider, toggle, test, rescan, beginNew, create };
}

function filterInventory(query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return CAPABILITIES;
  return Object.fromEntries(Object.entries(CAPABILITIES).map(([key, items]) => [key, items.filter((item) =>
    `${item.name} ${item.source} ${item.path} ${item.detail}`.toLowerCase().includes(needle))]));
}

function toggleSelected(selected, type, id) {
  const current = selected[type];
  const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
  return { ...selected, [type]: next };
}

function runTimed(setTests, key) {
  setTests((value) => ({ ...value, [key]: "testing" }));
  window.setTimeout(() => setTests((value) => ({ ...value, [key]: "passed" })), 650);
}

function runScan(setScan) {
  setScan({ status: "scanning", label: "正在扫描", count: 0 });
  window.setTimeout(() => setScan({ status: "done", label: "刚刚完成", count: 20 }), 850);
}

function startDraft(setDraft, setNotice) {
  setDraft({ ...DEFAULT_DRAFT, id: "agent:new", name: "", instructions: "", selected: { skills: [], tools: [], mcp: [] } });
  setNotice("已开启空白 Agent 草稿；确认前不会写入任何配置。\n原型中的创建也只保存在页面内存。");
}

function createAgent(draft, agents, setAgents, setDraft, setNotice) {
  const suffix = String(agents.length + 1).padStart(2, "0");
  const next = { id: `agent:${suffix}`, name: draft.name || `Agent ${suffix}`, runtime: draft.channel === "cli" ? draft.runtimeId : draft.providerId };
  setAgents((items) => [...items, next]);
  setDraft((value) => ({ ...value, id: next.id }));
  setNotice(`已在内存中创建 ${next.id}`);
}
