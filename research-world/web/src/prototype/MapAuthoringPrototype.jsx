// THROWAWAY PROTOTYPE: three variants of node authoring on /map?prototype=agent-node&variant=.
import { Background, Controls, Handle, MiniMap, Position, ReactFlow } from "@xyflow/react";
import { ArrowLeft, ArrowRight, Bot, Braces, Check, ChevronDown, CircleHelp, ExternalLink,
  Network, PanelRight, RotateCcw, Settings2, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { SignalEdge } from "../graph/SignalEdge";
import { PROTOTYPE_GROUPS, prototypeTasks } from "./prototypeSeed";
import "./map-authoring-prototype.css";


const VARIANTS = { A: "节点内配置", B: "Profile 检查器", C: "编排工作台" };
const AGENTS = ["Codex", "Pi", "Claude Code", "Qwen Researcher"];
const CHANNELS = ["ACP", "CLI"];
const NODE_TYPES = { prototype: PrototypeNode };
const EDGE_TYPES = { signal: SignalEdge };
let lastNodeClick = { id: "", time: 0 };


function edge(id, source, target, polarity, active = false) {
  return { id, source, target, type: "signal", data: { polarity, active }, style: { strokeWidth: polarity === "lineage" ? 2 : 3.5 } };
}


export function MapAuthoringPrototype() {
  const [params, setParams] = useSearchParams();
  const variant = VARIANTS[params.get("variant")] ? params.get("variant") : "A";
  const [tasks, setTasks] = useState(prototypeTasks);
  const [selectedId, setSelectedId] = useState("D-002");
  const [viewMode, setViewMode] = useState("research");
  const [workbench, setWorkbench] = useState(false);
  const selected = tasks.find((item) => item.id === selectedId) || tasks[0];
  useVariantKeys(variant, params, setParams);
  const update = (id, patch) => setTasks((items) => items.map((item) => item.id === id ? { ...item, ...patch } : item));
  return <section className={`authoring-prototype variant-${variant.toLowerCase()}`}>
    {workbench ? <WorkbenchTop task={selected} close={() => setWorkbench(false)} />
      : <PrototypeHeader variant={variant} tasks={tasks} viewMode={viewMode} setViewMode={setViewMode} />}
    {workbench ? <NodeWorkbench tasks={tasks} task={selected} select={setSelectedId} update={(patch) => update(selected.id, patch)} />
      : <ProjectWorkspace tasks={tasks} selected={selected} select={setSelectedId}>
        <VariantBody variant={variant} tasks={tasks} selected={selected} select={setSelectedId} update={update} open={() => setWorkbench(true)} viewMode={viewMode} />
      </ProjectWorkspace>}
    <StateSurface variant={variant} selected={selected} viewMode={viewMode} />
    <VariantSwitcher variant={variant} params={params} setParams={setParams} />
  </section>;
}


function PrototypeHeader({ variant, tasks, viewMode, setViewMode }) {
  return <header className="proto-header"><div><span className="proto-kicker">交互原型</span><b>研究地图 / 素数分布</b></div>
    <ViewModeToggle value={viewMode} change={setViewMode} /><div className="proto-header-meta"><Network size={15} /><span>{tasks.length} 节点</span><span>{tasks.length - 1} 关系</span><span>{VARIANTS[variant]}</span></div></header>;
}


function ViewModeToggle({ value, change }) {
  return <div className="proto-mode-toggle" aria-label="节点状态视图"><button className={value === "research" ? "active" : ""} onClick={() => change("research")}>研究</button>
    <button className={value === "authoring" ? "active" : ""} onClick={() => change("authoring")}>编排</button></div>;
}


function VariantBody(props) {
  if (props.variant === "B") return <VariantB {...props} />;
  if (props.variant === "C") return <VariantC {...props} />;
  return <VariantA {...props} />;
}


function ProjectWorkspace({ tasks, selected, select, children }) {
  return <div className="project-workspace"><ProjectNodeRail tasks={tasks} selected={selected} select={select} />{children}</div>;
}


function VariantA({ tasks, selected, select, update, open, viewMode }) {
  return <div className="proto-layout proto-layout-a"><PrototypeGraph tasks={tasks} selected={selected} select={select} update={update} open={open} mode="inline" viewMode={viewMode} />
    <ProjectDefaults selected={selected} update={update} open={open} /></div>;
}


function VariantB({ tasks, selected, select, update, open, viewMode }) {
  return <div className="proto-layout proto-layout-b"><PrototypeGraph tasks={tasks} selected={selected} select={select} update={update} open={open} mode="compact" viewMode={viewMode} />
    <ProfileInspector task={selected} update={(patch) => update(selected.id, patch)} open={open} /></div>;
}


function VariantC({ tasks, selected, select, update, open, viewMode }) {
  return <div className="proto-layout proto-layout-c"><AuthoringDesk task={selected} update={(patch) => update(selected.id, patch)} open={open} />
    <MiniGraph tasks={tasks} selected={selected} select={select} update={update} open={open} viewMode={viewMode} /></div>;
}


function PrototypeGraph({ tasks, selected, select, update, open, mode, viewMode }) {
  const edges = useMemo(() => graphEdges(tasks), [tasks]);
  const nodes = useMemo(() => tasks.map((item) => ({ id: item.id, type: "prototype", position: item.position,
    data: { ...item, mode, viewMode, selected: item.id === selected.id, update: (patch) => update(item.id, patch), open } })), [tasks, selected.id, update, open, mode, viewMode]);
  const overview = mode === "mini";
  return <div className="proto-graph"><ReactFlow nodes={nodes} edges={edges} nodeTypes={NODE_TYPES} edgeTypes={EDGE_TYPES} onNodeClick={(_, node) => selectGraphNode(node, select, open)} nodesDraggable={false} fitView={overview} defaultViewport={{ x: 30, y: 140, zoom: .65 }} fitViewOptions={{ padding: .08, maxZoom: .55 }} minZoom={.18} maxZoom={1.3} proOptions={{ hideAttribution: true }}>
    <Background gap={24} size={1} color="var(--graph-dot)" /><Controls showInteractive={false} /><MiniMap pannable zoomable /></ReactFlow></div>;
}


function selectGraphNode(node, select, open) {
  const time = performance.now();
  const doubleClick = lastNodeClick.id === node.id && time - lastNodeClick.time < 450;
  lastNodeClick = { id: node.id, time };
  select(node.id);
  if (doubleClick) open();
}


function graphEdges(tasks) {
  const byId = new Map(tasks.map((item) => [item.id, item]));
  return tasks.filter((item) => item.parent && byId.has(item.parent)).map((item) => edge(`edge-${item.id}`, item.parent, item.id,
    item.type === "experiment" ? "supports" : item.type === "review" ? "refutes" : "lineage", item.executionState === "运行"));
}


function PrototypeNode({ data }) {
  if (data.mode !== "inline") return <CompactNode data={data} />;
  return <InlineNode data={data} />;
}


function InlineNode({ data }) {
  return <article className={nodeClass(data, "inline")} onDoubleClickCapture={(event) => openCard(event, data.open)}><NodeHandles /><NodeTitle data={data} />
    <label className="proto-field"><span>Agent</span><select className="nodrag" value={data.agent} onChange={(event) => data.update({ agent: event.target.value })}>{AGENTS.map(option)}</select></label>
    <p className="proto-prompt">{data.prompt}</p><button className="proto-open nodrag" onClick={data.open}>节点设置 <ExternalLink size={13} /></button></article>;
}


function CompactNode({ data }) {
  return <article className={nodeClass(data, "compact")} onDoubleClickCapture={(event) => openCard(event, data.open)}><NodeHandles /><NodeTitle data={data} />
    <p className="proto-prompt">{data.prompt}</p><footer><span><Bot size={13} />{data.agent}</span><span>{data.channel}</span><button className="nodrag" onClick={data.open}><PanelRight size={14} /></button></footer></article>;
}


function NodeTitle({ data }) {
  const status = data.viewMode === "authoring" ? data.authoringState : data.scienceState;
  return <header><span className="proto-id">{data.id}</span><span className={`proto-status state-${stateClass(status)}`}>{status}</span><h3>{data.title}</h3></header>;
}


function nodeClass(data, mode) {
  return ["proto-node", `proto-node-${mode}`, `execution-${executionClass(data.executionState)}`, data.selected && "selected"].filter(Boolean).join(" ");
}


function openCard(event, open) {
  if (event.target.closest("select,button,input,textarea")) return;
  event.stopPropagation(); open();
}


function NodeHandles() {
  return <><Handle type="target" position={Position.Left} /><Handle type="source" position={Position.Right} /></>;
}


function option(value) {
  return <option key={value} value={value}>{value}</option>;
}


function stateClass(value) {
  return { 待审: "pending", 待审查: "pending", 待验证: "pending", 已采纳: "admitted", 已支持: "supported", 已反驳: "refuted",
    已驳回: "refuted", 草稿: "draft", 已配置: "configured", 已锁定: "locked" }[value] || "muted";
}


function executionClass(value) {
  return { 运行: "running", 排队: "queued", 失败: "failed", 完成: "completed", 空闲: "idle" }[value] || "idle";
}


function ProjectNodeRail({ tasks, selected, select }) {
  return <aside className="project-node-rail"><header><Network size={16} /><b>研究地图</b><span>{tasks.length}</span></header>
    <div className="project-node-tree"><div className="project-node-title"><b>素数分布研究</b><small>一个面板对应一个项目</small></div>
      {PROTOTYPE_GROUPS.map((group) => <TreeGroup key={group} group={group} tasks={tasks} selected={selected} select={select} />)}</div>
    <button className="proto-reset-layout" onClick={() => window.location.reload()}><RotateCcw size={15} />重置布局</button></aside>;
}


function TreeGroup({ group, tasks, selected, select }) {
  const members = tasks.filter((item) => item.group === group);
  if (!members.length) return null;
  return <details className="tree-group" open><summary><ChevronDown size={13} /><b>{group}</b><span>{members.length}</span></summary>{members.map((item) => <button key={item.id} className={item.id === selected.id ? "active" : ""} onClick={() => select(item.id)}>
    <b>{item.title}</b><span>{item.id}</span></button>)}</details>;
}


function ProjectDefaults({ selected, update, open }) {
  return <aside className="proto-defaults"><header><Settings2 size={16} /><b>Agent 设置</b></header><p className="proto-muted">项目默认值，节点可覆盖</p>
    <AgentFields task={selected} update={(patch) => update(selected.id, patch)} compact />
    <button className="button secondary" onClick={open}>打开 {selected.id} 工作台</button></aside>;
}


function ProfileInspector({ task, update, open }) {
  return <aside className="proto-profile"><header><div><span>{task.id}</span><h2>{task.title}</h2></div><button className="icon-button" onClick={open} title="打开节点工作台"><ExternalLink size={17} /></button></header>
    <section><h3>Prompt 速览</h3><p>{task.prompt}</p></section><section><h3>执行 Profile</h3><AgentFields task={task} update={update} /></section>
    <section><h3>能力</h3><ToolChips tools={task.tools} /></section><button className="button primary" onClick={open}><SlidersHorizontal size={15} />配置并启动</button></aside>;
}


function AgentFields({ task, update, compact = false }) {
  return <div className={`agent-fields ${compact ? "compact" : ""}`}><SelectField label="Agent" value={task.agent} values={AGENTS} change={(agent) => update({ agent })} />
    <SelectField label="通道" value={task.channel} values={CHANNELS} change={(channel) => update({ channel })} />
    {!compact && <><TextField label="模型" value={task.model} change={(model) => update({ model })} /><SelectField label="权限" value={task.permission} values={["按需确认", "失败时确认", "完全自动"]} change={(permission) => update({ permission })} /></>}</div>;
}


function SelectField({ label, value, values, change }) {
  return <label className="proto-field"><span>{label}</span><select value={value} onChange={(event) => change(event.target.value)}>{values.map(option)}</select></label>;
}


function TextField({ label, value, change }) {
  return <label className="proto-field"><span>{label}</span><input value={value} onChange={(event) => change(event.target.value)} /></label>;
}


function ToolChips({ tools }) {
  return <div className="tool-chips">{tools.map((tool) => <span key={tool}><Check size={12} />{tool}</span>)}</div>;
}


function AuthoringDesk({ task, update, open }) {
  return <main className="authoring-desk"><header><div><span>{task.kind} · {task.id}</span><h1>{task.title}</h1></div><button className="button secondary" onClick={open}><ExternalLink size={15} />完整设置</button></header>
    <label className="proto-field"><span>Task Prompt</span><textarea value={task.prompt} onChange={(event) => update({ prompt: event.target.value })} rows="5" /></label>
    <section><h3>验收标准</h3><ol>{task.acceptance.map((item) => <li key={item}>{item}</li>)}</ol></section><BlockStack task={task} /></main>;
}


function BlockStack({ task }) {
  return <section><h3>任务块</h3><div className="block-row"><span><Braces size={15} />执行实验</span><b>{task.id}#B-001</b><em>继承 Task</em></div>
    <div className="block-row"><span><CircleHelp size={15} />双审证据</span><b>{task.id}#R-001</b><em>Claude Code</em></div></section>;
}


function MiniGraph(props) {
  return <aside className="mini-graph"><header><Network size={16} /><b>结构速览</b></header><PrototypeGraph {...props} mode="mini" /></aside>;
}


function NodeWorkbench({ tasks, task, select, update }) {
  return <div className="workbench-body"><ProjectNodeRail tasks={tasks} selected={task} select={select} />
    <main className="workbench-main"><WorkbenchTitle task={task} /><div className="workbench-scroll"><RunSummary task={task} /><PromptEditor task={task} update={update} /><Acceptance task={task} /><BlockStack task={task} /></div></main>
    <AgentPane task={task} update={update} /></div>;
}


function WorkbenchTop({ task, close }) {
  return <header className="workbench-top"><button className="button secondary" onClick={close}><ArrowLeft size={15} />返回画布</button><b>{task.id} · {task.title}</b><button className="icon-button" onClick={close} title="关闭"><X size={18} /></button></header>;
}


function RunSummary({ task }) {
  return <section className="run-summary"><div><span>活动运行</span><b>RUN-001 · 准备执行环境</b></div><strong>{task.executionState}</strong><div><span>依赖</span><b>2 / 3 已就绪</b></div></section>;
}


function WorkbenchTitle({ task }) {
  return <header className="workbench-title"><div><span>{task.kind}</span><span>{task.scienceState}</span><span>{task.authoringState}</span></div><h1>{task.title}</h1><code>{task.id}</code></header>;
}


function AgentPane({ task, update }) {
  return <aside className="workbench-agent"><header><Bot size={16} /><b>Agent 设置</b><span>{task.channel}</span></header><div><Inheritance /><AgentFields task={task} update={update} /><TextField label="Provider" value={task.provider} change={(provider) => update({ provider })} /><TextField label="工作目录" value={task.workspace} change={(workspace) => update({ workspace })} /><ToolChips tools={task.tools} /></div></aside>;
}


function PromptEditor({ task, update }) {
  return <section><h2>任务设计</h2><TextField label="Goal" value={task.goal} change={(goal) => update({ goal })} />
    <label className="proto-field"><span>Task Prompt</span><textarea value={task.prompt} onChange={(event) => update({ prompt: event.target.value })} rows="8" /></label></section>;
}


function Acceptance({ task }) {
  return <section><h2>验收标准</h2><ol className="acceptance">{task.acceptance.map((item, index) => <li key={item}><span>{index + 1}</span>{item}</li>)}</ol></section>;
}


function Inheritance() {
  return <label className="inheritance"><input type="checkbox" defaultChecked /><span><b>继承项目默认值</b><small>执行开始后锁定配置快照</small></span></label>;
}


function StateSurface({ variant, selected, viewMode }) {
  const state = { variant, view_mode: viewMode, node_ref: selected.id, science: selected.scienceState, authoring: selected.authoringState,
    execution: selected.executionState, agent: selected.agent, channel: selected.channel, model: selected.model };
  return <details className="proto-state"><summary>Prototype state</summary><pre>{JSON.stringify(state, null, 2)}</pre></details>;
}


function VariantSwitcher({ variant, params, setParams }) {
  const move = (delta) => setVariant(variant, delta, params, setParams);
  return <div className="variant-switcher"><button onClick={() => move(-1)} title="上一个变体"><ArrowLeft size={16} /></button><b>{variant} — {VARIANTS[variant]}</b><button onClick={() => move(1)} title="下一个变体"><ArrowRight size={16} /></button></div>;
}


function setVariant(variant, delta, params, setParams) {
  const keys = Object.keys(VARIANTS);
  const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
  const updated = new URLSearchParams(params);
  updated.set("prototype", "agent-node"); updated.set("variant", next); setParams(updated, { replace: true });
}


function useVariantKeys(variant, params, setParams) {
  useEffect(() => {
    const handler = (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key) || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
      setVariant(variant, event.key === "ArrowLeft" ? -1 : 1, params, setParams);
    };
    window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler);
  }, [variant, params, setParams]);
}
