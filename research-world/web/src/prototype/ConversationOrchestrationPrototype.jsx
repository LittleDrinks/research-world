// THROWAWAY PROTOTYPE: four conversation/orchestration models on /chat?prototype=orchestration&variant=.
import { ArrowLeft, ArrowRight, Bot, Braces, ChevronDown, CircleHelp, GitBranch,
  MessageSquare, Network, Play, Plus, SendHorizontal, Settings2, Sparkles, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PROTOTYPE_GROUPS, prototypeTasks } from "./prototypeSeed";
import "./conversation-orchestration-prototype.css";


const VARIANTS = { A: "节点对话", B: "Runtime 房间", C: "Orchestrator 控制台", D: "Workflow 编排" };
const AGENTS = ["Codex", "Pi", "Claude Code", "Qwen Researcher"];
const RUNTIMES = [
  runtime("RT-01", "Codex", "ACP", "运行中", "检验短区间密度", "gpt-5.6-codex"),
  runtime("RT-02", "Pi", "ACP", "就绪", "构造反例与边界", "gpt-5.2"),
  runtime("RT-03", "Claude Code", "CLI", "已完成", "复核统计脚本", "claude-sonnet"),
];
const STEPS = ["准备可复现环境", "执行数值实验", "独立复核证据", "写回节点状态"];


export function ConversationOrchestrationPrototype() {
  const [params, setParams] = useSearchParams();
  const variant = VARIANTS[params.get("variant")] ? params.get("variant") : "A";
  const [selectedId, setSelectedId] = useState("D-008");
  const [thread, setThread] = useState("orchestrator");
  const [runtimes, setRuntimes] = useState(RUNTIMES);
  const [runtimeId, setRuntimeId] = useState("RT-01");
  const task = prototypeTasks().find((item) => item.id === selectedId) || prototypeTasks()[0];
  useVariantKeys(variant, params, setParams);
  const state = { task, selectedId, setSelectedId, thread, setThread, runtimes, setRuntimes, runtimeId, setRuntimeId };
  return <section className="conversation-prototype"><Variant variant={variant} state={state} />
    <PrototypeState variant={variant} state={state} /><VariantSwitcher variant={variant} params={params} setParams={setParams} /></section>;
}


function Variant({ variant, state }) {
  if (variant === "B") return <RuntimeRoom state={state} />;
  if (variant === "C") return <OrchestratorConsole state={state} />;
  if (variant === "D") return <WorkflowStudio state={state} />;
  return <NodeConversation state={state} />;
}


function NodeConversation({ state }) {
  return <div className="conversation-layout node-conversation"><ConversationRail state={state} />
    <main className="conversation-thread"><ThreadHeader state={state} /><MessageLog state={state} /><Composer state={state} /></main>
    <RuntimeDock state={state} /></div>;
}


function RuntimeRoom({ state }) {
  return <div className="conversation-layout runtime-room"><ConversationRail state={state} />
    <main className="runtime-board"><BoardHeader task={state.task} /><div className="runtime-lanes">{state.runtimes.map((item) => <RuntimeLane key={item.id} item={item} state={state} />)}</div></main>
    <RuntimeInspector state={state} /></div>;
}


function OrchestratorConsole({ state }) {
  return <div className="conversation-layout orchestrator-console"><ContextShelf state={state} />
    <main className="orchestrator-thread"><ThreadHeader state={{ ...state, thread: "orchestrator" }} /><MessageLog state={{ ...state, thread: "orchestrator" }} /><Composer state={state} orchestrator /></main>
    <GeneratedWorkflow state={state} /></div>;
}


function WorkflowStudio({ state }) {
  return <div className="conversation-layout workflow-studio"><PresetShelf state={state} />
    <main className="workflow-canvas"><BoardHeader task={state.task} /><WorkflowSteps state={state} /></main>
    <WorkflowTest state={state} /></div>;
}


function ConversationRail({ state }) {
  return <aside className="conversation-rail"><header><MessageSquare size={16} /><b>对话</b><span>31</span></header>
    <button className={`orchestrator-entry ${state.thread === "orchestrator" ? "active" : ""}`} onClick={() => state.setThread("orchestrator")}><Sparkles size={16} /><span><b>Orchestrator</b><small>项目级自由对话</small></span></button>
    <NodeList state={state} /></aside>;
}


function NodeList({ state, limit }) {
  const tasks = prototypeTasks();
  const shown = limit ? tasks.slice(0, limit) : tasks;
  return <div className="conversation-node-list">{PROTOTYPE_GROUPS.map((group) => <NodeGroup key={group} group={group} tasks={shown} state={state} />)}</div>;
}


function NodeGroup({ group, tasks, state }) {
  const members = tasks.filter((item) => item.group === group);
  if (!members.length) return null;
  return <details open><summary><ChevronDown size={12} />{group}<span>{members.length}</span></summary><div>{members.map((item) => <button key={item.id} className={state.selectedId === item.id ? "active" : ""} onClick={() => selectNode(state, item.id)}><span><b>{item.title}</b><small>{item.id}</small></span><i>{runtimeCount(item.id)}</i></button>)}</div></details>;
}


function selectNode(state, id) {
  state.setSelectedId(id);
  state.setThread(id);
}


function ThreadHeader({ state }) {
  const orchestrator = state.thread === "orchestrator";
  return <header className="conversation-thread-header"><div><span>{orchestrator ? "PROJECT ORCHESTRATOR" : `${state.task.id} · 节点对话`}</span><h1>{orchestrator ? "素数分布研究" : state.task.title}</h1></div><button className="icon-button" title="新建对话"><Plus size={17} /></button></header>;
}


function MessageLog({ state }) {
  const orchestrator = state.thread === "orchestrator";
  return <div className="prototype-messages">{(orchestrator ? orchestratorMessages() : nodeMessages(state.task)).map((message, index) => <article className={message.role} key={index}><span>{message.role === "user" ? "你" : orchestrator ? "Orchestrator" : "Agent"}</span><p>{message.text}</p></article>)}</div>;
}


function Composer({ state, orchestrator = false }) {
  return <section className="prototype-composer"><div className="composer-context"><span>#{state.task.id}</span>{orchestrator && <span>@Orchestrator</span>}<button><Braces size={13} />生成 Workflow</button></div><div><textarea placeholder={orchestrator ? "描述目标，让 Orchestrator 读取节点并编排执行…" : "围绕当前节点对话，可引用 Runtime 编号…"} /><button className="icon-button prototype-send"><SendHorizontal size={17} /></button></div></section>;
}


function RuntimeDock({ state }) {
  return <aside className="runtime-dock"><header><Bot size={16} /><b>Agent Runtimes</b><button className="icon-button" title="新增 Runtime"><Plus size={15} /></button></header><section><p>挂载于 {state.task.id}</p>{state.runtimes.map((item) => <RuntimeCard key={item.id} item={item} state={state} />)}</section><WorkflowPreview /></aside>;
}


function RuntimeCard({ item, state }) {
  return <button className={`runtime-card ${state.runtimeId === item.id ? "active" : ""}`} onClick={() => state.setRuntimeId(item.id)}><span><Bot size={14} /><b>{item.id}</b><em>{item.status}</em></span><strong>{item.agent} · {item.channel}</strong><small>{item.purpose}</small></button>;
}


function WorkflowPreview() {
  return <section className="workflow-preview"><header><Workflow size={15} /><b>当前 Workflow</b><span>预设</span></header><p>复现实验 → 双审 → 回写</p>{STEPS.map((step, index) => <div key={step}><span>{index + 1}</span>{step}</div>)}</section>;
}


function BoardHeader({ task }) {
  return <header className="board-header"><div><span>{task.id}</span><h1>{task.title}</h1></div><select defaultValue="复现实验 + 双审"><option>复现实验 + 双审</option><option>快速探索</option><option>反例优先</option></select></header>;
}


function RuntimeLane({ item, state }) {
  return <article className={`runtime-lane ${item.status === "运行中" ? "running" : ""}`}><header><div><Bot size={16} /><b>{item.id} · {item.agent}</b></div><span>{item.status}</span></header><p>{item.purpose}</p><div className="lane-config"><span>{item.channel}</span><span>{item.model}</span></div><div className="lane-message">“已读取 #{state.task.id}，正在检查输入范围与可复现参数。”</div><button onClick={() => startRuntime(state, item.id)}><Play size={14} />{item.status === "运行中" ? "查看执行" : "启动"}</button></article>;
}


function RuntimeInspector({ state }) {
  const item = state.runtimes.find((runtimeItem) => runtimeItem.id === state.runtimeId) || state.runtimes[0];
  return <aside className="runtime-inspector"><header><Settings2 size={16} /><b>Runtime 设置</b></header><div><label><span>Agent</span><select defaultValue={item.agent}>{AGENTS.map(option)}</select></label><label><span>通道</span><select defaultValue={item.channel}><option>ACP</option><option>CLI</option></select></label><label><span>模型</span><input defaultValue={item.model} /></label><label><span>Runtime Prompt</span><textarea defaultValue={`围绕 #${state.task.id} ${item.purpose}。输出证据与失败原因。`} rows="6" /></label><button className="primary-action"><Play size={14} />保存并启动</button></div></aside>;
}


function ContextShelf({ state }) {
  return <aside className="context-shelf"><header><Network size={16} /><b>项目上下文</b></header><section><span>当前项目</span><b>素数分布研究</b><p>Orchestrator 可按编号读取节点，不默认加载全图。</p></section><section><span>已钉入</span>{[state.task, prototypeTasks()[9], prototypeTasks()[25]].map((item) => <button key={item.id} onClick={() => state.setSelectedId(item.id)}><b>{item.id}</b>{item.title}</button>)}</section><section><span>可用预设</span><button><Workflow size={14} />复现实验 + 双审</button><button><CircleHelp size={14} />反例优先审查</button></section></aside>;
}


function GeneratedWorkflow({ state }) {
  return <aside className="generated-workflow"><header><Sparkles size={16} /><b>Orchestrator 草案</b><span>未启动</span></header><section><span>目标节点</span><h2>{state.task.id} · {state.task.title}</h2><p>{state.task.goal}</p></section><section><span>Runtime 计划</span>{state.runtimes.slice(0, 2).map((item, index) => <div className="generated-step" key={item.id}><i>{index + 1}</i><p><b>{item.agent}</b><small>{index ? "独立复核并寻找反例" : "执行主实验并记录 trace"}</small></p></div>)}</section><section><span>生成的 Prompt</span><p className="prompt-draft">读取 #{state.task.id}，先验证输入和依赖，再执行实验。所有结论必须引用 artifact。</p></section><button className="primary-action"><Play size={14} />确认并启动 Workflow</button></aside>;
}


function PresetShelf({ state }) {
  return <aside className="preset-shelf"><header><Workflow size={16} /><b>Workflow 预设</b><button className="icon-button"><Plus size={15} /></button></header><section><button className="active"><b>复现实验 + 双审</b><small>4 steps · 3 runtimes</small></button><button><b>快速探索</b><small>2 steps · 1 runtime</small></button><button><b>反例优先</b><small>3 steps · 2 runtimes</small></button></section><div><span>绑定节点</span><select value={state.selectedId} onChange={(event) => state.setSelectedId(event.target.value)}>{prototypeTasks().map((item) => <option key={item.id} value={item.id}>{item.id} · {item.title}</option>)}</select></div></aside>;
}


function WorkflowSteps({ state }) {
  return <div className="workflow-steps"><div className="workflow-start"><GitBranch size={17} /><span><b>{state.task.id}</b><small>节点状态触发</small></span></div>{STEPS.map((step, index) => <article key={step}><i>{index + 1}</i><div><span>STEP-{String(index + 1).padStart(2, "0")}</span><h2>{step}</h2><p>{index === 0 ? "Orchestrator 生成 Prompt，并绑定节点与依赖快照。" : `由 ${state.runtimes[index % state.runtimes.length].agent} 执行，失败时保留 trace。`}</p></div><select defaultValue={state.runtimes[index % state.runtimes.length].agent}>{AGENTS.map(option)}</select></article>)}</div>;
}


function WorkflowTest({ state }) {
  return <aside className="workflow-test"><header><MessageSquare size={16} /><b>试运行对话</b></header><section><span>当前 Workflow</span><b>复现实验 + 双审</b><p>绑定 {state.task.id}，运行前可让 Orchestrator 重写任一步 Prompt。</p></section><div className="test-message"><b>Orchestrator</b><p>四个步骤已就绪。STEP-03 使用独立 Runtime，避免主实验上下文污染复核。</p></div><label><span>选中步骤的 Prompt</span><textarea defaultValue={`审查 #${state.task.id} 的实验产物，主动寻找反例。`} rows="6" /></label><button className="primary-action"><Play size={14} />试运行 Workflow</button></aside>;
}


function PrototypeState({ variant, state }) {
  const value = { variant, surface: state.thread, node_ref: state.selectedId, runtime_ref: state.runtimeId, runtime_count: state.runtimes.length };
  return <details className="conversation-prototype-state"><summary>Prototype state</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}


function VariantSwitcher({ variant, params, setParams }) {
  const move = (delta) => setVariant(variant, delta, params, setParams);
  return <div className="conversation-variant-switcher"><button onClick={() => move(-1)}><ArrowLeft size={16} /></button><b>{variant} — {VARIANTS[variant]}</b><button onClick={() => move(1)}><ArrowRight size={16} /></button></div>;
}


function setVariant(variant, delta, params, setParams) {
  const keys = Object.keys(VARIANTS);
  const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
  const updated = new URLSearchParams(params);
  updated.set("prototype", "orchestration"); updated.set("variant", next); setParams(updated, { replace: true });
}


function useVariantKeys(variant, params, setParams) {
  useEffect(() => {
    const handler = (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key) || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
      setVariant(variant, event.key === 'ArrowLeft' ? -1 : 1, params, setParams);
    };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  }, [variant, params, setParams]);
}


function startRuntime(state, id) {
  state.setRuntimeId(id);
  state.setRuntimes((items) => items.map((item) => item.id === id ? { ...item, status: "运行中" } : item));
}


function runtime(id, agent, channel, status, purpose, model) {
  return { id, agent, channel, status, purpose, model };
}


function runtimeCount(id) {
  return id.charCodeAt(id.length - 1) % 3;
}


function option(value) {
  return <option key={value} value={value}>{value}</option>;
}


function orchestratorMessages() {
  return [{ role: "user", text: "围绕 #D-008 设计一个可复现、可独立复核的验证流程。" },
    { role: "assistant", text: "我会读取 D-008 及其直接证据，生成一个主实验 Runtime 和一个隔离复核 Runtime，再把结果写回节点状态。右侧是可编辑的 Workflow 草案。" }];
}


function nodeMessages(task) {
  return [{ role: "assistant", text: `已进入 ${task.id}。当前挂载 3 个 Agent Runtime，可通过 @RT-编号 指定对话对象。` },
    { role: "user", text: "@RT-02 请先找这个方向最容易失败的边界条件。" },
    { role: "assistant", text: "RT-02 已接收任务；对话上下文会与主实验隔离，结果作为节点附件返回。" }];
}
