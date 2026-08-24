// 变体 D — ASCII 动效: 与 A 同一页面层级、交互与 seed; 黑底磷光绿等宽字, 动效只表达系统状态。
import { useEffect, useMemo, useState } from "react";
import { ACTIVITY, GRAPH_NODES, GRAPH_NODE_MAP, KIND, graphEdgesAll, threadRuns } from "./seed";
import { insertMention, mentionChoices } from "./shared";
import "./ascii-runtime.css";

const MODULES = [["map", "地图"], ["chat", "对话"], ["trace", "轨迹"], ["agents", "Agent"]];
const A_VIEWS = ["map", "chat", "trace", "agents"];
const REDUCED = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function VariantD({ state }) {
  if (state.view === "projects") return <DProjects state={state} />;
  const view = A_VIEWS.includes(state.view) ? state.view : "map";
  return <div className="ad-root"><div className="ad-scan" aria-hidden="true" />
    <DSidebar state={state} view={view} /><DMain state={state} view={view} />
    <DComposer onSend={state.send} onMention={state.pinNode} pinned={state.thread.pinned} /></div>;
}

export function CharSpinner({ className = "" }) {
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (REDUCED) return undefined;
    const timer = setInterval(() => setIndex((value) => (value + 1) % frames.length), 120);
    return () => clearInterval(timer);
  }, []);
  return <span className={`ad-spinner ${className}`}>{REDUCED ? "●" : frames[index]}</span>;
}

/* —— 项目选择 Hero —— */
function DProjects({ state }) {
  return <main className="ad-projects"><div className="ad-scan" aria-hidden="true" />
    <pre className="ad-projects-net" aria-hidden="true">{D_NET}</pre>
    <header className="ad-projects-hero"><span>:: 研究项目入口 ::</span>
      <h1>RESEARCH WORLD<span className="ad-cursor">▮</span></h1>
      <p>选择研究项目进入工作台 ── 事实、对话与执行轨迹都属于项目</p></header>
    <div className="ad-project-list">{state.projects.map((project) => <button key={project.id}
      className={project.id === state.project.id ? "on" : ""} onClick={() => state.enterProject(project.id)}>
      <b>[{project.id}] {project.name}</b>
      <span>{project.question}</span>
      <small>节点 {project.nodes} · 运行 {project.runs} · {project.updated}</small></button>)}
      <button className="ad-project-new" onClick={state.newProject}>[+ 新建项目]</button></div>
  </main>;
}

const D_NET = `
      ·           ·                ·
   ( o )───────( o )            ( o )
      ·        │   ╲              │        ·
 ·           ( o )  ╲          ( o )
      ·      │      ( o )        │   ·
           ( o )───────╲       ( o )
      ·        ·        ( o )     ·      ·
`.repeat(4);

/* —— 工作台 —— */
function DSidebar({ state, view }) {
  return <aside className="ad-sidebar">
    <header><b>RESEARCH WORLD</b><small>{state.project.name}</small></header>
    <nav>{MODULES.map(([id, label]) => <button key={id} className={view === id ? "on" : ""}
      onClick={() => state.setView(id)}>{view === id ? "▣" : "▢"} {label}</button>)}</nav>
    <DRecords state={state} view={view} />
    <button className="ad-exit" onClick={state.exitProject}>[←] 退出项目</button>
  </aside>;
}

function DRecords({ state, view }) {
  const labels = { map: state.mapSubview === "graph" ? "节点" : "日志日期", chat: "对话记录", trace: "运行记录", agents: "Agent" };
  return <section className="ad-records"><header>── {labels[view]} ──</header>
    <div className="ad-records-list"><DRecordItems state={state} view={view} /></div></section>;
}

function DRecordItems({ state, view }) {
  if (view === "chat") return <>{state.threads.map((thread) => <button key={thread.id}
    className={state.threadId === thread.id ? "on" : ""} onClick={() => state.setThreadId(thread.id)}>
    {thread.id} {thread.title} <small>{thread.updated} · {threadRuns(thread).length} 运行</small></button>)}</>;
  if (view === "trace") return <>{Object.values(state.runs).flatMap((run) => run.executions.map((execution) =>
    <button key={execution.id} className={state.inspector?.execution.id === execution.id ? "on" : ""}
      onClick={() => state.openTrace(execution.id)}>{execution.id} {execution.task}
      <small>{run.id} · {execution.status}</small></button>))}</>;
  if (view === "agents") return <>{state.agents.map((agent) => <button key={agent.id}
    className={state.agentId === agent.id ? "on" : ""} onClick={() => state.setAgentId(agent.id)}>
    {agent.id} {agent.name}<small>{agent.runtime}</small></button>)}</>;
  if (state.mapSubview === "journal") return <><button className="on">今天 <small>6 条记录</small></button><button>昨天 <small>12 条记录</small></button></>;
  return <>{GRAPH_NODES.map((node) => <button key={node.id} className={state.selectedNodeId === node.id ? "on" : ""}
    onClick={() => state.setSelectedNodeId(node.id)}>( o ) {node.id} <small>{KIND[node.kind]}</small></button>)}</>;
}

function DMain({ state, view }) {
  if (view === "chat") return <DChat state={state} />;
  if (view === "trace") return <DTrace state={state} />;
  if (view === "agents") return <DAgents state={state} />;
  return <DMap state={state} />;
}

/* —— 地图: ASCII 图谱 / 科研日志 —— */
function DMap({ state }) {
  return <main className="ad-map">
    <header className="ad-bar"><span>:: 研究地图 · {GRAPH_NODES.length} 节点 · {graphEdgesAll().length} 关系 ::</span>
      <nav><button className={state.mapSubview === "graph" ? "on" : ""} onClick={() => state.setMapSubview("graph")}>[事实图谱]</button>
        <button className={state.mapSubview === "journal" ? "on" : ""} onClick={() => state.setMapSubview("journal")}>[科研日志]</button></nav></header>
    {state.mapSubview === "graph" ? <DGraph state={state} /> : <DJournal />}
  </main>;
}

function DGraph({ state }) {
  const selected = GRAPH_NODE_MAP[state.selectedNodeId] || GRAPH_NODES[0];
  return <div className="ad-map-workspace"><DGraphCanvas state={state} selected={selected} /><DGraphDetail state={state} node={selected} /></div>;
}

const POS = { "Q-001": [24, 60], "S-014": [24, 250], "D-008": [360, 30], "D-011": [360, 190], "D-013": [360, 350], "E-021": [640, 90], "E-022": [640, 290] };
const NODE_W = 240;
const NODE_H = 84;

function DGraphCanvas({ state, selected }) {
  const edges = useMemo(() => graphEdgesAll().map((edge) => ({ edge, from: POS[edge.source], to: POS[edge.target] })), []);
  return <div className="ad-graph">
    <svg className="ad-graph-edges" width="900" height="470" aria-hidden="true">{edges.map(({ edge, from, to }) => {
      const incident = edge.source === selected.id || edge.target === selected.id;
      const sameColumn = from[0] === to[0];
      const x1 = sameColumn ? from[0] + NODE_W / 2 : from[0] + NODE_W, y1 = sameColumn ? from[1] + NODE_H : from[1] + NODE_H / 2;
      const x2 = sameColumn ? to[0] + NODE_W / 2 : to[0], y2 = sameColumn ? to[1] : to[1] + NODE_H / 2;
      const mid = (x1 + x2) / 2;
      const points = sameColumn ? `${x1},${y1} ${x2},${y2}` : `${x1},${y1} ${mid},${y1} ${mid},${y2} ${x2},${y2}`;
      return <g key={`${edge.source}:${edge.target}`}>
        <polyline points={points} className={`ad-edge-base ${edge.polarity} ${incident ? "incident" : ""}`} />
        <polyline points={points} className={`ad-edge ${edge.polarity} ${incident ? "incident" : ""}`} /></g>;
    })}</svg>
    {GRAPH_NODES.map((node) => <button key={node.id} style={{ left: POS[node.id][0], top: POS[node.id][1] }}
      className={`ad-gnode ${node.id === selected.id ? "on" : ""} life-${node.life_state} ${BUSY_D.has(node.id) ? "busy" : ""}`}
      onClick={() => state.setSelectedNodeId(node.id)}>
      <span>( o ) {node.id} {BUSY_D.has(node.id) && <CharSpinner />}</span><b>{node.payload.title}</b>
      <small>【{node.state || lifeLabelD(node)}】</small></button>)}
  </div>;
}

const BUSY_D = new Set(["E-021"]);

function lifeLabelD(node) {
  return { pending: "待审查", admitted: "已入图", ghost: "已驳回" }[node.life_state] || node.life_state;
}

function DGraphDetail({ node, state }) {
  const related = graphEdgesAll().filter((edge) => edge.source === node.id || edge.target === node.id);
  const relLabel = (edge) => edge.polarity === "supports" ? "支持" : edge.polarity === "refutes" ? "反驳" : "派生";
  return <aside className="ad-detail">
    <header>── {node.id} · {KIND[node.kind]} ──</header>
    <p className="ad-detail-title">{node.payload.title}</p>
    {Object.entries(node.payload).filter(([key]) => key !== "title").map(([key, value]) => <div className="ad-kv" key={key}>
      <span>{key}</span><em>{value}</em></div>)}
    <header>── 证据关系 ({related.length}) ──</header>
    {related.map((edge) => { const otherId = edge.source === node.id ? edge.target : edge.source;
      return <button key={otherId} className="ad-rel" onClick={() => state.setSelectedNodeId(otherId)}>
        <b className={edge.polarity === "refutes" ? "ad-err" : "ad-ok"}>{relLabel(edge)}</b> → {otherId} {GRAPH_NODE_MAP[otherId].payload.title}</button>; })}
    <div className="ad-detail-actions">
      <button onClick={() => state.pinNode(node.id)}>[+ 钉入当前对话]</button>
      <button className="ad-primary" onClick={() => state.startRunForNode(node.id)}>[▶ 发起工作流]</button></div>
  </aside>;
}

function DJournal() {
  return <ol className="ad-journal">{ACTIVITY.map((item, index) => <li key={item.id} className={index === 0 ? "ad-type" : ""}>
    <span className="ad-time">[{item.time}]</span> ◆ <b>{item.kind}</b> {item.text} <span className="ad-ref">{item.ref}</span></li>)}</ol>;
}

/* —— 对话 —— */
function DChat({ state }) {
  const thread = state.thread;
  return <main className="ad-chat">
    <header className="ad-bar"><span>:: {thread.id} · {thread.title} ::</span></header>
    <div className="ad-pinstrip">钉住:{thread.pinned.map((id) => <span className="ad-pin" key={id}>
      [@{id}]<button aria-label={`移除 ${id}`} onClick={() => state.togglePin(id)}>×</button></span>)}</div>
    <div className="ad-log">{thread.messages.map((message) => <DMessage key={message.id} message={message} state={state} />)}</div>
  </main>;
}

function DMessage({ message, state }) {
  return <article className={`ad-msg ${message.role}`}>
    <span className="ad-time">[{message.time}]</span> {message.role === "user" ? "❯" : "◈"} <DText text={message.text} />
    {(message.runs || []).map((runId) => <DRun key={runId} run={state.runs[runId]}
      expanded={state.openRunId === runId} onToggle={() => state.toggleRun(runId)} onOpenTrace={state.openTrace} />)}
  </article>;
}

function DText({ text }) {
  return <>{text.split(/(@[A-Z]-\d{3})/g).map((part, index) => part.startsWith("@")
    ? <b className="ad-mention" key={`${part}-${index}`}>{part}</b> : part)}</>;
}

function DRun({ run, expanded, onToggle, onOpenTrace }) {
  return <div className="ad-run">
    <button className="ad-run-head" onClick={onToggle} aria-expanded={expanded}>
      {expanded ? "▾" : "▸"} [{run.id}] {run.intent} <b className={`ad-st-${run.status}`}>【{run.status}】</b> {run.executions.length} 个执行</button>
    {expanded && <div className="ad-run-body">
      {run.findings.map((finding) => <div className="ad-finding" key={finding}>· {finding}</div>)}
      {run.executions.map((execution) => <button key={execution.id} className="ad-exec" onClick={() => onOpenTrace(execution.id)}>
        <span>{execution.status === "运行中" ? <CharSpinner /> : "●"} {execution.agent} · {execution.channel} · {execution.model}</span>
        <b>{execution.task} <i className={`ad-st-${execution.status}`}>【{execution.status}】</i></b>
        <small>{execution.summary}</small>
        <small className="ad-dim">prompt: {execution.prompt} · skills: {execution.skills.join(" / ")}</small>
        <span className="ad-open">[打开轨迹 →]</span></button>)}
    </div>}
  </div>;
}

function DComposer({ onSend, onMention, pinned }) {
  const [draft, setDraft] = useState("");
  const choices = mentionChoices(draft);
  const submit = () => { if (draft.trim()) { onSend(draft); setDraft(""); } };
  const choose = (node) => { setDraft(insertMention(draft, node.id)); onMention(node.id); };
  const keyDown = (event) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent?.isComposing || event.keyCode === 229) return;
    event.preventDefault(); submit();
  };
  return <div className="ad-composer">
    {choices.length > 0 && <div className="ad-mention-menu">{choices.map((node) => <button key={node.id} onClick={() => choose(node)}>
      @{node.id} {KIND[node.kind]} · {node.title}{pinned.includes(node.id) ? " [已引用]" : ""}</button>)}</div>}
    <div className="ad-cli"><span>research:~$</span>
      <input aria-label="消息" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown}
        placeholder="发消息,输入 @ 引用节点" spellCheck="false" autoComplete="off" />
      <span className="ad-cursor">▮</span></div>
  </div>;
}

/* —— 轨迹 —— */
function DTrace({ state }) {
  const selected = state.inspector || { run: Object.values(state.runs)[0], execution: Object.values(state.runs)[0].executions[0] };
  const { run, execution } = selected;
  const session = execution.session;
  return <main className="ad-trace">
    <header className="ad-bar"><button className="ad-back" onClick={state.backToChat}>[← 返回对话]</button>
      <span>:: 轨迹 / {run.id} / {execution.id} · {execution.task} </span>
      <b className={`ad-st-${execution.status}`}>【{execution.status}】</b></header>
    <div className="ad-session-meta">runtime {session.runtime} · model {session.model} · started {session.started} · ws {session.workspace}</div>
    <div className="ad-session">{session.turns.map((turn) => <DTurn key={turn.id} turn={turn} />)}</div>
  </main>;
}

function DTurn({ turn }) {
  return <section className="ad-turn">
    <header>── TURN {turn.id} · {turn.label} ──────────────</header>
    <ol>{turn.steps.map((step, index) => <DStep key={index} step={step} />)}</ol>
  </section>;
}

function DStep({ step }) {
  if (step.type === "message") return <li className={`ad-step ${step.actor}`}>
    <span className="ad-time">[{step.time}]</span> {step.actor === "user" ? "❯" : "◈"} {step.text}</li>;
  const call = step.type === "tool_call";
  return <li className="ad-step tool"><span className="ad-time">[{step.time}]</span>
    <details><summary>{call ? "→" : "←"} {step.tool} {!call && <i>{step.status}</i>}</summary>
      <pre>{call ? step.input : step.output}</pre></details></li>;
}

/* —— Agent —— */
function DAgents({ state }) {
  const agent = state.agents.find((item) => item.id === state.agentId) || state.agents[0];
  return <main className="ad-agents">
    <header className="ad-bar"><span>:: Agent · {agent.id} · {agent.name} ::</span>
      <nav><button onClick={() => state.createAgent("blank")}>[+ 从空白创建]</button>
        <button onClick={() => state.createAgent("draft")}>[✦ AI 起草]</button></nav></header>
    <div className="ad-editor">
      <div className="ad-kv"><span>名称</span><input value={agent.name} onChange={(event) => state.updateAgent(agent.id, { name: event.target.value })} /></div>
      <div className="ad-kv"><span>Runtime</span><select value={agent.runtime} onChange={(event) => state.updateAgent(agent.id, { runtime: event.target.value })}>
        {["Codex · ACP", "Claude Code · CLI", "Pi · ACP", "Qwen Researcher · ACP"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ad-kv top"><span>Instructions</span><textarea rows="5" value={agent.instructions}
        onChange={(event) => state.updateAgent(agent.id, { instructions: event.target.value })} /></div>
      <div className="ad-kv"><span>模型</span><select value={agent.model} onChange={(event) => state.updateAgent(agent.id, { model: event.target.value })}>
        {["gpt-5.6-codex", "gpt-5.2", "claude-sonnet-4.6", "qwen3-max"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ad-kv"><span>推理</span><select value={agent.thinking} onChange={(event) => state.updateAgent(agent.id, { thinking: event.target.value })}>
        {["低", "中", "高"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ad-kv top"><span>Skills</span><div className="ad-skills">{agent.skills.map((skill) => <i key={skill}>[{skill}
        <button aria-label={`移除 ${skill}`} onClick={() => state.updateAgent(agent.id, { skills: agent.skills.filter((item) => item !== skill) })}>×</button>]</i>)}
        <input placeholder="+ 添加后回车" onKeyDown={(event) => { if (event.key === "Enter" && event.target.value.trim()) {
          state.updateAgent(agent.id, { skills: [...agent.skills, event.target.value.trim()] }); event.target.value = ""; } }} /></div></div>
      <details className="ad-advanced"><summary>── 高级设置(权限 / 并发 / 环境变量 / MCP)──</summary>
        <div className="ad-kv"><span>权限</span><select value={agent.advanced.permission}
          onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, permission: event.target.value } })}>
          {["只读", "工作区写入", "完全"].map((value) => <option key={value}>{value}</option>)}</select></div>
        <div className="ad-kv"><span>并发</span><input value={agent.advanced.concurrency}
          onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, concurrency: event.target.value } })} /></div>
        <DListEditor label="环境变量" items={agent.advanced.env} onChange={(env) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, env } })} />
        <DListEditor label="MCP" items={agent.advanced.mcp} onChange={(mcp) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, mcp } })} />
      </details>
    </div>
  </main>;
}

function DListEditor({ label, items, onChange }) {
  return <div className="ad-kv top"><span>{label}</span><div className="ad-skills">
    {items.map((item) => <i key={item}>[{item}<button aria-label="删除" onClick={() => onChange(items.filter((value) => value !== item))}>×</button>]</i>)}
    <input placeholder="+ 回车添加" onKeyDown={(event) => { if (event.key === "Enter" && event.target.value.trim()) {
      onChange([...items, event.target.value.trim()]); event.target.value = ""; } }} /></div></div>;
}
