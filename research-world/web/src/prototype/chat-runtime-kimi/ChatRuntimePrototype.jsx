// THROWAWAY PROTOTYPE: /prototype/chat-runtime?variant=A|B|C|D|E。
// A = 收敛工作台(地图/对话/轨迹/Agent + 项目选择闭环); D = 同层级的 ASCII 动效美学变体;
// E = kort-ai-ascii 手法的 canvas 字符场变体(顶栏页签 + 横向记录条); B/C 语义不变。
// 模型: Project > Thread > Message + ResearchRun 引用;Node 只是可钉上下文;runtime trace 只从 execution 下钻。
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PROJECTS, SEED_AGENTS, SEED_RUNS, SEED_THREADS, findExecution, makeAgent, makeRun } from "./seed";
import { VariantA } from "./VariantA";
import { VariantB } from "./VariantB";
import { VariantC } from "./VariantC";
import { VariantD } from "./VariantD";
import { VariantE } from "./VariantE";
import "./chat-runtime.css";

const VARIANTS = { A: "收敛工作台", B: "单工作区切换", C: "时间线研究日志", D: "ASCII 动效", E: "Kort 字符场" };

export function ChatRuntimePrototype() {
  const [params, setParams] = useSearchParams();
  const variant = VARIANTS[params.get("variant")] ? params.get("variant") : "A";
  const state = useChatState(variant);
  useVariantKeys(variant, params, setParams);
  return <div className={`crt-host${variant === "D" ? " crt-host-ascii" : ""}`}>
    {variant === "A" && <VariantA state={state} />}
    {variant === "B" && <VariantB state={state} />}
    {variant === "C" && <VariantC state={state} />}
    {variant === "D" && <VariantD state={state} />}
    {variant === "E" && <VariantE state={state} />}
    {import.meta.env.DEV && <Switcher variant={variant} params={params} setParams={setParams} />}
  </div>;
}

function useChatState(variant) {
  const [threads, setThreads] = useState(SEED_THREADS);
  const [runs, setRuns] = useState(SEED_RUNS);
  const [projects, setProjects] = useState(PROJECTS);
  const [projectId, setProjectId] = useState("P-01");
  const [threadId, setThreadId] = useState("T-01");
  const [view, setView] = useState("projects");
  const [mapSubview, setMapSubview] = useState("graph");
  const [selectedNodeId, setSelectedNodeId] = useState("Q-001");
  const [openRunId, setOpenRunId] = useState("RR-07");
  const [inspectorId, setInspectorId] = useState(null);
  const [traceReturn, setTraceReturn] = useState("T-01");
  const [agents, setAgents] = useState(SEED_AGENTS);
  const [agentId, setAgentId] = useState("AG-01");
  const thread = threads.find((item) => item.id === threadId) || threads[0];
  const project = projects.find((item) => item.id === projectId) || projects[0];
  const togglePin = (nodeId) => setThreads((items) => items.map((item) => pinToggled(item, thread.id, nodeId)));
  const pinNode = (nodeId) => setThreads((items) => items.map((item) => pinAdded(item, thread.id, nodeId)));
  const toggleRun = (runId) => setOpenRunId((value) => (value === runId ? null : runId));
  const send = (text) => sendIntent(text, thread.id, runs, setRuns, setThreads, setOpenRunId);
  const openTrace = (executionId) => { setTraceReturn(thread.id); setInspectorId(executionId); setView("trace"); };
  const backToChat = () => { setThreadId(traceReturn); setView("chat"); };
  const enterProject = (id) => { setProjectId(id); setView("map"); setMapSubview("graph"); };
  const newProject = () => { const id = `P-${String(projects.length + 1).padStart(2, "0")}`;
    setProjects((items) => [...items, { id, name: "未命名项目", question: "尚未写下研究问题", nodes: 0, runs: 0, updated: "刚刚" }]); enterProject(id); };
  const startRunForNode = (nodeId) => startNodeRun(nodeId, runs, setRuns, setInspectorId, setView);
  const createAgent = (mode) => { const id = `AG-${String(agents.length + 1).padStart(2, "0")}`;
    setAgents((items) => [...items, makeAgent(id, mode)]); setAgentId(id); };
  const updateAgent = (id, patch) => setAgents((items) => items.map((item) => item.id === id ? { ...item, ...patch } : item));
  return { projects, project, enterProject, newProject, exitProject: () => setView("projects"),
    threads, thread, threadId, setThreadId, runs, view, setView, mapSubview, setMapSubview,
    selectedNodeId, setSelectedNodeId, openRunId, toggleRun, inspector: findExecution(runs, inspectorId),
    setInspectorId, openTrace, backToChat, startRunForNode, togglePin, pinNode, send,
    agents, agentId, setAgentId, createAgent, updateAgent, variant };
}

function pinToggled(thread, activeId, nodeId) {
  if (thread.id !== activeId) return thread;
  const pinned = thread.pinned.includes(nodeId)
    ? thread.pinned.filter((id) => id !== nodeId) : [...thread.pinned, nodeId];
  return { ...thread, pinned };
}

function pinAdded(thread, activeId, nodeId) {
  if (thread.id !== activeId || thread.pinned.includes(nodeId)) return thread;
  return { ...thread, pinned: [...thread.pinned, nodeId] };
}

function sendIntent(text, threadId, runs, setRuns, setThreads, setOpenRunId) {
  const content = text.trim();
  if (!content) return;
  const stamp = new Date().toTimeString().slice(0, 5);
  const runId = `RR-${String(Object.keys(runs).length + 8).padStart(2, "0")}`;
  setRuns((value) => ({ ...value, [runId]: { ...makeRun(runId, content), started: stamp } }));
  setThreads((items) => items.map((item) => item.id === threadId ? { ...item, messages: [...item.messages,
    { id: `u${Date.now()}`, role: "user", time: stamp, text: content },
    { id: `a${Date.now()}`, role: "assistant", time: stamp, runs: [runId],
      text: `已启动 ${runId}:同一意图拆成 2 个执行(主执行 + 独立复核),结论写回科研日志。` }] } : item));
  setOpenRunId(runId);
}

function startNodeRun(nodeId, runs, setRuns, setInspectorId, setView) {
  const runId = `RR-${String(Object.keys(runs).length + 8).padStart(2, "0")}`;
  const run = { ...makeRun(runId, `围绕 @${nodeId} 推进`), started: new Date().toTimeString().slice(0, 5) };
  setRuns((value) => ({ ...value, [runId]: run }));
  setInspectorId(`${runId}-E1`);
  setView("trace");
}

function Switcher({ variant, params, setParams }) {
  const move = (delta) => cycleVariant(variant, delta, params, setParams);
  return <nav className="crt-switcher" aria-label="prototype variant switcher">
    <button onClick={() => move(-1)} aria-label="上一套"><ChevronLeft size={16} /></button>
    <b>{variant} — {VARIANTS[variant]}</b>
    <button onClick={() => move(1)} aria-label="下一套"><ChevronRight size={16} /></button>
  </nav>;
}

function cycleVariant(variant, delta, params, setParams) {
  const keys = Object.keys(VARIANTS);
  const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
  const updated = new URLSearchParams(params);
  updated.set("variant", next);
  setParams(updated, { replace: true });
}

function useVariantKeys(variant, params, setParams) {
  useEffect(() => {
    const handler = (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      if (event.target.closest("input, textarea, select, [contenteditable]")) return;
      cycleVariant(variant, event.key === "ArrowLeft" ? -1 : 1, params, setParams);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [variant, params, setParams]);
}
