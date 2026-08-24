// 收敛方案 A — 一级模块 地图/对话/轨迹/Agent + 项目选择闭环。事实图谱复用生产 GraphView/ResearchNode。
import { Activity, ArrowLeft, ArrowRight, Bot, Check, ChevronDown, ChevronRight, FolderOpen, LogOut, Map, MessageSquare, Play, Plus, RefreshCw, Sparkles } from "lucide-react";
import { useState } from "react";
import { GraphView } from "../../graph/GraphView";
import "../../map.css";
import { ACTIVITY, GRAPH_NODE_MAP, GRAPH_NODES, KIND, NODE_MAP, graphEdgesAll, threadRuns } from "./seed";
import { MentionComposer, RunCard, statusClass } from "./shared";

const MODULES = [["map", "地图", Map], ["chat", "对话", MessageSquare], ["trace", "轨迹", Activity], ["agents", "Agent", Bot]];
const BUSY_NODES = new Set(["E-021"]);
const NO_NEW = new Set();
const A_VIEWS = ["map", "chat", "trace", "agents"];
const RUNTIMES = [
  { id: "Codex · ACP", detail: "codex 0.149.0 · ~/.codex/config.toml", ready: true },
  { id: "Claude Code · CLI", detail: "claude · PATH", ready: true },
  { id: "Qwen Researcher · ACP", detail: "qwen · ACP 预检通过", ready: true },
];
const MODELS = {
  "Codex · ACP": ["gpt-5.6-codex", "gpt-5.2"],
  "Claude Code · CLI": ["claude-sonnet-4.6"],
  "Qwen Researcher · ACP": ["qwen3-max"],
};
const SKILLS = [
  { id: "agent-creation", detail: "把需求变成可用的 Agent", source: ".agents/skills/agent-creation/SKILL.md" },
  { id: "benchmark-design", detail: "设计并校准能力评测", source: ".agents/skills/benchmark-design/SKILL.md" },
  { id: "codebase-design", detail: "深模块与薄接口设计", source: ".agents/skills/codebase-design/SKILL.md" },
  { id: "code-review", detail: "按规范和需求审查改动", source: ".agents/skills/code-review/SKILL.md" },
  { id: "grilling", detail: "压力测试计划与决策", source: ".agents/skills/grilling/SKILL.md" },
];
const MCP_SERVERS = [
  { id: "openaiDeveloperDocs", detail: "HTTP · 可用", source: "~/.codex/config.toml" },
  { id: "anysearch", detail: "HTTP · 可用", source: "research-world/projects/orbits-49/.mcp.json" },
];

export function VariantA({ state }) {
  if (state.view === "projects") return <ProjectSelect state={state} />;
  const view = A_VIEWS.includes(state.view) ? state.view : "map";
  return <div className="crt-a"><Sidebar state={state} view={view} /><MainView state={state} view={view} /></div>;
}

/* —— 项目选择 Hero —— */
function ProjectSelect({ state }) {
  return <main className="crt-projects"><pre className="crt-projects-net" aria-hidden="true">{NET}</pre>
    <section className="crt-projects-hero"><span>研究项目入口</span><h1>Research World</h1>
      <p>选择一个研究项目进入工作台;事实、对话与执行轨迹都属于项目。</p></section>
    <div className="crt-project-list">{state.projects.map((project) => <button key={project.id}
      className={project.id === state.project.id ? "active" : ""} onClick={() => state.enterProject(project.id)}>
      <span className="crt-project-name"><b>{project.name}</b><small>{project.question}</small></span>
      <span className="crt-project-counts"><b>{project.nodes}</b> 节点 · <b>{project.runs}</b> 运行</span>
      <time>{project.updated}</time><ArrowRight size={16} /></button>)}
      <button className="crt-project-new" onClick={state.newProject}><Plus size={15} />新建项目</button></div>
  </main>;
}

const NET = `
      ·           ·                ·
   ( o )───────( o )            ( o )
      ·        │   ╲              │        ·
 ·           ( o )  ╲          ( o )
      ·      │      ( o )        │   ·
           ( o )───────╲       ( o )
      ·        ·        ( o )     ·      ·
`.repeat(3);

/* —— 工作台侧栏 —— */
function Sidebar({ state, view }) {
  return <aside className="crt-project-sidebar">
    <header><b>Research World</b><small>{state.project.name}</small></header>
    <nav className="crt-module-nav">{MODULES.map(([id, label, Icon]) => <button key={id}
      className={view === id ? "selected" : ""} onClick={() => state.setView(id)}>
      <Icon size={15} /><span>{label}</span></button>)}</nav>
    <RecordTree state={state} view={view} />
    <button className="crt-project-exit" onClick={state.exitProject}><LogOut size={15} /><span>退出项目</span></button>
  </aside>;
}

function RecordTree({ state, view }) {
  const [open, setOpen] = useState(true);
  const labels = { map: state.mapSubview === "graph" ? "节点" : "日志日期", chat: "对话记录", trace: "运行记录", agents: "Agent" };
  return <section className="crt-record-tree">
    <button className="crt-record-heading" onClick={() => setOpen((value) => !value)}>
      {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}<b>{labels[view]}</b></button>
    {open && <RecordItems state={state} view={view} />}
  </section>;
}

function RecordItems({ state, view }) {
  if (view === "chat") return <ThreadRecords state={state} />;
  if (view === "trace") return <TraceRecords state={state} />;
  if (view === "agents") return <AgentRecords state={state} />;
  return state.mapSubview === "graph" ? <NodeRecords state={state} /> : <JournalRecords />;
}

function ThreadRecords({ state }) {
  return <div className="crt-record-list">{state.threads.map((thread) => <button key={thread.id}
    className={state.threadId === thread.id ? "selected" : ""} onClick={() => state.setThreadId(thread.id)}>
    <b>{thread.title}</b><small>{thread.id} · {thread.updated} · {threadRuns(thread).length} 次运行</small></button>)}</div>;
}

function TraceRecords({ state }) {
  return <div className="crt-record-list">{Object.values(state.runs).flatMap((run) => run.executions.map((execution) =>
    <button key={execution.id} className={state.inspector?.execution.id === execution.id ? "selected" : ""}
      onClick={() => state.openTrace(execution.id)}><b>{execution.task}</b>
      <small>{run.id} · {execution.id} · {execution.status}</small></button>))}</div>;
}

function NodeRecords({ state }) {
  return <div className="crt-record-list">{GRAPH_NODES.map((node) => <button key={node.id}
    className={state.selectedNodeId === node.id ? "selected" : ""} onClick={() => state.setSelectedNodeId(node.id)}>
    <b>{node.id} · {node.payload.title}</b><small>{KIND[node.kind]}</small></button>)}</div>;
}

function JournalRecords() {
  return <div className="crt-record-list"><button className="selected"><b>今天</b><small>6 条记录</small></button>
    <button><b>昨天</b><small>12 条记录</small></button></div>;
}

function AgentRecords({ state }) {
  return <div className="crt-record-list">{state.agents.map((agent) => <button key={agent.id}
    className={state.agentId === agent.id ? "selected" : ""} onClick={() => state.setAgentId(agent.id)}>
    <b>{agent.name}</b><small>{agent.id} · {agent.runtime}</small></button>)}</div>;
}

/* —— 主区 —— */
function MainView({ state, view }) {
  if (view === "chat") return <ThreadMain state={state} />;
  if (view === "trace") return <TracePage state={state} />;
  if (view === "agents") return <AgentsView state={state} />;
  return <MapView state={state} />;
}

function MapView({ state }) {
  return <main className="crt-map">
    <header className="crt-map-bar"><div><b>研究地图</b><span>{GRAPH_NODES.length} 个节点 · {graphEdgesAll().length} 条关系</span></div>
      <nav className="crt-segmented"><button className={state.mapSubview === "graph" ? "on" : ""} onClick={() => state.setMapSubview("graph")}>事实图谱</button>
        <button className={state.mapSubview === "journal" ? "on" : ""} onClick={() => state.setMapSubview("journal")}>科研日志</button></nav></header>
    {state.mapSubview === "graph" ? <FactGraph state={state} /> : <JournalPane />}
  </main>;
}

function FactGraph({ state }) {
  const selected = GRAPH_NODE_MAP[state.selectedNodeId] || GRAPH_NODES[0];
  return <div className="crt-map-workspace">
    <div className="graph-canvas"><GraphView nodes={GRAPH_NODES} edges={graphEdgesAll()}
      selectedId={selected.id} onSelect={state.setSelectedNodeId} newIds={NO_NEW} busyIds={BUSY_NODES} /></div>
    <GraphInspector node={selected} state={state} />
  </div>;
}

function GraphInspector({ node, state }) {
  return <aside className="inspector"><div className="inspector-scroll">
    <header className="inspector-header"><div className="eyebrow"><span>{KIND[node.kind]}</span><span>{node.state || lifeLabel(node)}</span></div>
      <h1>{node.payload.title}</h1></header>
    <section className="inspector-section"><h2>节点记录</h2><dl className="node-record">
      {Object.entries(node.payload).filter(([key]) => key !== "title").map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section>
    <Relations node={node} state={state} />
    <button className="button secondary crt-inspector-action" onClick={() => state.pinNode(node.id)}><Plus size={14} />钉入当前对话</button>
    <button className="button primary crt-inspector-action" onClick={() => state.startRunForNode(node.id)}><Play size={14} />发起工作流</button>
  </div></aside>;
}

function lifeLabel(node) {
  return { pending: "待审查", admitted: "已入图", ghost: "已驳回" }[node.life_state] || node.life_state;
}

function Relations({ node, state }) {
  const related = graphEdgesAll().filter((edge) => edge.source === node.id || edge.target === node.id)
    .map((edge) => ({ edge, other: GRAPH_NODE_MAP[edge.source === node.id ? edge.target : edge.source] }));
  const label = (edge) => edge.polarity === "supports" ? "支持" : edge.polarity === "refutes" ? "反驳" : "派生";
  return <section className="inspector-section"><h2>证据关系</h2>
    {!related.length && <p className="muted">暂无关系</p>}
    <ul className="relation-list">{related.map(({ edge, other }) => <li key={`${edge.source}:${edge.target}`}>
      <button onClick={() => state.setSelectedNodeId(other.id)}>
        <span className={`polarity ${edge.polarity}`}>{label(edge)}</span><b>{other.payload.title}</b>
      </button></li>)}</ul></section>;
}

function JournalPane() {
  return <ol className="crt-timeline crt-map-journal">{ACTIVITY.map((item) => <li className="crt-entry fact" key={item.id}>
    <time>{item.time}</time><i /><div className="crt-entry-body"><p className="crt-fact"><b>{item.kind}</b>{item.text}<span>{item.ref}</span></p></div>
  </li>)}</ol>;
}

/* —— 对话 —— */
function ThreadMain({ state }) {
  const thread = state.thread;
  return <main className="crt-a-main">
    <header className="crt-thread-header"><div><span>{thread.id}</span><h1>{thread.title}</h1></div></header>
    <NodeContextTools nodeIds={thread.pinned} state={state} />
    <MessageStream thread={thread} state={state} />
    <MentionComposer onSend={state.send} onMention={state.pinNode} pinned={thread.pinned} />
  </main>;
}

function NodeContextTools({ nodeIds, state }) {
  const [activeId, setActiveId] = useState(null);
  const active = NODE_MAP[activeId];
  return <section className="crt-node-tools">
    <div className="crt-pinstrip">{nodeIds.map((id) => <NodeToolButton key={id} node={NODE_MAP[id]}
      active={id === activeId} onClick={() => setActiveId(id === activeId ? null : id)} />)}</div>
    {active && <NodeToolPreview node={active} state={state} onClose={() => setActiveId(null)} />}
  </section>;
}

function NodeToolButton({ node, active, onClick }) {
  if (!node) return null;
  return <button className={`crt-node-tool kind-${node.kind} ${active ? "active" : ""}`} onClick={onClick}>
    <FolderOpen size={12} /><b>@{node.id}</b><span>{node.title}</span><ChevronDown size={12} /></button>;
}

function NodeToolPreview({ node, state, onClose }) {
  const openMap = () => { state.setSelectedNodeId(node.id); state.setView("map"); };
  return <div className="crt-node-preview"><div><b>{node.id} · {KIND[node.kind]}</b><span>{node.state}</span>
    <p>{node.title}</p></div><button onClick={openMap}>在地图中打开</button>
    <button onClick={() => { state.togglePin(node.id); onClose(); }}>移除引用</button></div>;
}

function MessageStream({ thread, state }) {
  return <div className="crt-messages">{thread.messages.map((message) => <Message key={message.id} message={message} state={state} />)}</div>;
}

function Message({ message, state }) {
  return <article className={`crt-msg ${message.role}`}><span>{message.role === "user" ? "你" : "研究助手"} · {message.time}</span>
    <p><MentionText text={message.text} /></p>
    {(message.runs || []).map((runId) => <RunCard key={runId} run={state.runs[runId]}
      expanded={state.openRunId === runId} onToggle={() => state.toggleRun(runId)} onOpenTrace={state.openTrace} />)}
  </article>;
}

function MentionText({ text }) {
  return text.split(/(@[A-Z]-\d{3})/g).map((part, index) => part.startsWith("@")
    ? <button className="crt-inline-mention" key={`${part}-${index}`}>{part}</button> : part);
}

/* —— 轨迹(session → turn → step) —— */
function TracePage({ state }) {
  const selected = state.inspector || firstExecution(state.runs);
  const { run, execution } = selected;
  const session = execution.session;
  return <main className="crt-trace-page">
    <header className="crt-trace-head"><button className="crt-ghost-button" onClick={state.backToChat}><ArrowLeft size={14} />返回对话</button>
      <div><span>轨迹 / {run.id} / {execution.id}</span><h1>{execution.task}</h1></div>
      <i className={`crt-status ${statusClass(execution.status)}`}>{execution.status}</i></header>
    <dl className="crt-session-meta">
      <div><dt>Runtime</dt><dd>{session.runtime}</dd></div><div><dt>模型</dt><dd>{session.model}</dd></div>
      <div><dt>开始</dt><dd>{session.started}</dd></div><div><dt>工作区</dt><dd>{session.workspace}</dd></div>
    </dl>
    <div className="crt-session">{session.turns.map((turn) => <Turn key={turn.id} turn={turn} />)}</div>
  </main>;
}

function firstExecution(runs) {
  const run = Object.values(runs)[0];
  return { run, execution: run.executions[0] };
}

function Turn({ turn }) {
  return <section className="crt-turn">
    <header><span>TURN {turn.id}</span><b>{turn.label}</b></header>
    <ol>{turn.steps.map((step, index) => <Step key={index} step={step} index={index} />)}</ol>
  </section>;
}

function Step({ step, index }) {
  if (step.type === "message") return <li className={`crt-step message ${step.actor}`}>
    <span className="crt-step-tag">{step.actor === "user" ? "你" : "助手"}</span><p>{step.text}</p><time>{step.time}</time></li>;
  return <ToolStep step={step} index={index} />;
}

function ToolStep({ step, index }) {
  const call = step.type === "tool_call";
  return <li className={`crt-step tool ${call ? "call" : "result"}`}>
    <span className="crt-step-tag">{call ? "工具调用" : "工具结果"}</span>
    <details><summary><b>{step.tool}</b>{!call && <i className={`crt-step-status ${step.status === "running" ? "running" : ""}`}>{step.status}</i>}
      <ChevronRight size={13} className="crt-step-chevron" /></summary>
      <pre>{call ? step.input : step.output}</pre></details>
    <time>{step.time}</time></li>;
}

/* —— Agent —— */
function AgentsView({ state }) {
  const agent = state.agents.find((item) => item.id === state.agentId) || state.agents[0];
  return <main className="crt-agents">
    <header className="crt-agents-head"><h1>{agent.name}</h1>
      <div><button className="crt-ghost-button" onClick={() => state.createAgent("blank")}><Plus size={14} />从空白创建</button>
        <button className="crt-ghost-button" onClick={() => state.createAgent("draft")}><Sparkles size={14} />AI 起草</button></div></header>
    <div className="crt-agent-editor">
      <section className="crt-agent-common">
        <label><span>名称</span><input value={agent.name} onChange={(event) => state.updateAgent(agent.id, { name: event.target.value })} /></label>
        <DetectedRuntime agent={agent} state={state} />
        <label><span>Instructions</span><textarea rows="5" value={agent.instructions}
          onChange={(event) => state.updateAgent(agent.id, { instructions: event.target.value })} placeholder="这个 Agent 怎么工作…" /></label>
        <div className="crt-agent-row">
          <DetectedModel agent={agent} state={state} />
          <label><span>推理强度</span><select value={agent.thinking} onChange={(event) => state.updateAgent(agent.id, { thinking: event.target.value })}>
            {["低", "中", "高"].map((value) => <option key={value}>{value}</option>)}</select></label></div>
        <CapabilityPicker label="Skills" catalog={SKILLS} selected={agent.skills}
          onChange={(skills) => state.updateAgent(agent.id, { skills })} />
      </section>
      <details className="crt-agent-advanced"><summary>高级设置<ChevronRight size={13} /></summary>
        <div className="crt-agent-row">
          <label><span>权限</span><select value={agent.advanced.permission}
            onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, permission: event.target.value } })}>
            {["只读", "工作区写入", "完全"].map((value) => <option key={value}>{value}</option>)}</select></label>
          <label><span>并发</span><input value={agent.advanced.concurrency}
            onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, concurrency: event.target.value } })} /></label></div>
        <ListEditor label="环境变量" items={agent.advanced.env} placeholder="KEY=value"
          onChange={(env) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, env } })} />
        <CapabilityPicker label="MCP 服务" catalog={MCP_SERVERS} selected={agent.advanced.mcp}
          onChange={(mcp) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, mcp } })} />
      </details>
    </div>
  </main>;
}

function DetectedRuntime({ agent, state }) {
  const runtime = RUNTIMES.find((item) => item.id === agent.runtime) || RUNTIMES[0];
  const change = (event) => state.updateAgent(agent.id, { runtime: event.target.value, model: MODELS[event.target.value][0] });
  return <label><span className="crt-recognition-label">Runtime <i>{RUNTIMES.length} 个已识别</i></span>
    <select value={agent.runtime} onChange={change}>{RUNTIMES.map((item) => <option key={item.id}>{item.id}</option>)}</select>
    <RecognitionStatus detail={runtime.detail} /></label>;
}

function DetectedModel({ agent, state }) {
  const models = MODELS[agent.runtime] || [];
  return <label><span className="crt-recognition-label">模型 <i>Runtime 提供</i></span>
    <select value={agent.model} onChange={(event) => state.updateAgent(agent.id, { model: event.target.value })}>
      {models.map((value) => <option key={value}>{value}</option>)}</select>
    <RecognitionStatus detail={`${models.length} 个可用模型`} /></label>;
}

function RecognitionStatus({ detail }) {
  return <small className="crt-recognition-status"><Check size={11} />{detail}<button title="重新识别"><RefreshCw size={11} /></button></small>;
}

function CapabilityPicker({ label, catalog, selected, onChange }) {
  const toggle = (id) => onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id]);
  return <details className="crt-capability-picker"><summary><span>{label}</span>
    <b>{selected.length} 个已启用</b><em>{catalog.length} 个已识别</em><ChevronDown size={13} /></summary>
    <div className="crt-capability-list">{catalog.map((item) => <CapabilityRow key={item.id} item={item}
      checked={selected.includes(item.id)} onToggle={() => toggle(item.id)} />)}</div>
  </details>;
}

function CapabilityRow({ item, checked, onToggle }) {
  return <button className={checked ? "selected" : ""} onClick={onToggle} type="button">
    <i>{checked && <Check size={11} />}</i><span><b>{item.id}</b><small>{item.detail}</small>
      <code>{item.source}</code></span></button>;
}

function ListEditor({ label, items, placeholder, onChange }) {
  const add = (value) => value.trim() && onChange([...items, value.trim()]);
  return <div className="crt-list-editor"><span>{label}</span>
    {items.map((item) => <div className="crt-list-item" key={item}><code>{item}</code>
      <button aria-label="删除" onClick={() => onChange(items.filter((value) => value !== item))}>×</button></div>)}
    <input placeholder={`+ ${placeholder}`} onKeyDown={(event) => { if (event.key === "Enter") { add(event.target.value); event.target.value = ""; } }} /></div>;
}
