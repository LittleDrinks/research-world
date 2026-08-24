// 变体 E — Kort 字符场: 与 A/D 同 seed 同交互, 但结构改为 顶栏页签 + 横向记录条;
// 动效全部走 canvas 程序化字符场(kort-ai-ascii 手法): 正弦波背景 / 图谱边字符流 / 运行状态频谱, 不用 baked 帧数据。
import { useEffect, useMemo, useRef, useState } from "react";
import { ACTIVITY, GRAPH_NODES, GRAPH_NODE_MAP, KIND, graphEdgesAll, threadRuns } from "./seed";
import { insertMention, mentionChoices } from "./shared";
import "./kort-runtime.css";

const MODULES = [["map", "地图"], ["chat", "对话"], ["trace", "轨迹"], ["agents", "Agent"]];
const A_VIEWS = ["map", "chat", "trace", "agents"];
const REDUCED = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const GLYPHS = " ·:-=+*#%@";
const VIOLET = ["#2a1b66", "#322272", "#38277b", "#3e2d83", "#46348c", "#4f3d95", "#5947a0",
  "#6757af", "#7568bd", "#867bca", "#9890d5", "#aaa3df", "#bcb7e8", "#cecaf0"];
const POS = { "Q-001": [24, 60], "S-014": [24, 250], "D-008": [360, 30], "D-011": [360, 190], "D-013": [360, 350], "E-021": [640, 90], "E-022": [640, 290] };
const NODE_W = 240, NODE_H = 84, BUSY = new Set(["E-021"]);

export function VariantE({ state }) {
  if (state.view === "projects") return <EProjects state={state} />;
  const view = A_VIEWS.includes(state.view) ? state.view : "map";
  return <div className="ae-root">
    <ETopBar state={state} view={view} /><EStrip state={state} view={view} /><EMain state={state} view={view} />
  </div>;
}

/* —— canvas 字符场基础设施 —— */
function AsciiCanvas({ className = "", draw, deps = [] }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");
    let raf = 0, width = 0, height = 0, last = -1;
    const paint = (ms) => { ctx.clearRect(0, 0, width, height); draw(ctx, width, height, ms / 1000); };
    const resize = () => {
      const box = canvas.getBoundingClientRect();
      const dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.max(2, Math.round(box.width * dpr));
      canvas.height = Math.max(2, Math.round(box.height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      width = box.width; height = box.height; paint(0);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(canvas); resize();
    if (!REDUCED) {
      const loop = (ms) => { const tick = Math.floor(ms / 90); if (tick !== last) { last = tick; paint(ms); } raf = requestAnimationFrame(loop); };
      raf = requestAnimationFrame(loop);
    }
    return () => { cancelAnimationFrame(raf); observer.disconnect(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return <canvas ref={ref} className={className} aria-hidden="true" />;
}

function drawWave(ctx, width, height, t) {
  const cell = 12;
  ctx.font = `11px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  for (let y = 0; y < height / cell; y += 1) for (let x = 0; x < width / cell; x += 1) {
    const v = (Math.sin(x * 0.3 + t * 0.8) + Math.sin(y * 0.42 - t * 0.55) + Math.sin((x + y) * 0.17 + t * 0.35) + 3) / 6;
    if (v < 0.46) continue;
    ctx.fillStyle = VIOLET[Math.min(13, Math.floor(v * 14))];
    ctx.fillText(GLYPHS[Math.min(9, Math.floor((v - 0.46) / 0.54 * 10))], x * cell + 6, y * cell + 6);
  }
}

function buildLine(points, offset) {
  const segs = [];
  let total = 0;
  for (let i = 1; i < points.length; i += 1) {
    const len = Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
    segs.push({ a: points[i - 1], b: points[i], start: total, len }); total += len;
  }
  const at = (d) => {
    const seg = segs.find((s) => d <= s.start + s.len) || segs[segs.length - 1];
    const k = Math.min(1, Math.max(0, (d - seg.start) / (seg.len || 1)));
    return [seg.a[0] + (seg.b[0] - seg.a[0]) * k, seg.a[1] + (seg.b[1] - seg.a[1]) * k];
  };
  return { at, total, offset };
}

function drawFlow(lines) {
  return (ctx, width, height, t) => {
    ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (const line of lines) {
      const head = ((t * 80 + line.offset) % (line.total + 70)) - 35;
      for (let d = 0; d < line.total; d += 7) {
        const [x, y] = line.at(d);
        const dist = head - d;
        if (dist > 0 && dist < 42) {
          ctx.fillStyle = VIOLET[Math.max(4, 13 - Math.floor(dist / 3.2))];
          ctx.fillText(dist < 9 ? "@" : "+", x, y);
        } else { ctx.fillStyle = "rgba(117, 104, 189, 0.3)"; ctx.fillText("·", x, y); }
      }
    }
  };
}

function drawMeter(active) {
  return (ctx, width, height, t) => {
    ctx.font = "9px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    const step = Math.max(4, Math.floor(height / 4));
    for (let i = 0; i * 8 < width; i += 1) {
      const v = active ? (Math.sin(i * 1.7 + t * 5) + Math.sin(i * 0.9 - t * 3.1) + 2) / 4 : 0.3 + 0.12 * Math.sin(i * 1.3);
      const levels = Math.max(1, Math.round(v * (height / step)));
      for (let j = 0; j < levels; j += 1) {
        ctx.fillStyle = VIOLET[Math.min(13, 4 + Math.floor((j / levels) * 9))];
        ctx.fillText("▮", i * 8 + 4, height - j * step - step / 2);
      }
    }
  };
}

function Pulse() {
  const frames = ["◐", "◓", "◑", "◒"];
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (REDUCED) return undefined;
    const timer = setInterval(() => setIndex((value) => (value + 1) % frames.length), 160);
    return () => clearInterval(timer);
  }, []);
  return <span className="ae-pulse">{REDUCED ? "●" : frames[index]}</span>;
}

/* —— 项目选择 —— */
function EProjects({ state }) {
  return <main className="ae-projects">
    <AsciiCanvas className="ae-wave" draw={drawWave} />
    <header className="ae-hero"><span>* RESEARCH WORLD / PROJECT MATRIX</span>
      <h1>选择研究项目</h1>
      <p>事实、对话与执行轨迹都属于项目 —— 选定后进入工作台</p></header>
    <div className="ae-project-list">{state.projects.map((project) => <button key={project.id}
      className={project.id === state.project.id ? "on" : ""} onClick={() => state.enterProject(project.id)}>
      <b>{project.id} · {project.name}</b><span>{project.question}</span>
      <small>节点 {project.nodes} · 运行 {project.runs} · {project.updated}</small></button>)}
      <button className="ae-project-new" onClick={state.newProject}>+ 新建项目</button></div>
  </main>;
}

/* —— 顶栏 + 记录条 —— */
function ETopBar({ state, view }) {
  return <header className="ae-top">
    <div className="ae-brand"><span className="ae-mark">*</span><b>Research World</b><small>{state.project.name}</small></div>
    <nav className="ae-tabs">{MODULES.map(([id, label]) => <button key={id} className={view === id ? "on" : ""}
      onClick={() => state.setView(id)}>{label}</button>)}</nav>
    <button className="ae-exit" onClick={state.exitProject}>退出项目 →</button>
  </header>;
}

function EStrip({ state, view }) {
  const labels = { map: "节点", chat: "对话记录", trace: "运行记录", agents: "Agent" };
  return <div className="ae-strip">
    <span className="ae-strip-label">{labels[view]}</span>
    <div className="ae-strip-items"><EStripItems state={state} view={view} /></div>
    {view === "map" && <nav className="ae-segmented">
      <button className={state.mapSubview === "graph" ? "on" : ""} onClick={() => state.setMapSubview("graph")}>事实图谱</button>
      <button className={state.mapSubview === "journal" ? "on" : ""} onClick={() => state.setMapSubview("journal")}>科研日志</button></nav>}
  </div>;
}

function EStripItems({ state, view }) {
  if (view === "chat") return <>{state.threads.map((thread) => <button key={thread.id}
    className={state.threadId === thread.id ? "on" : ""} onClick={() => state.setThreadId(thread.id)}>
    {thread.id} {thread.title}<small>{threadRuns(thread).length} 运行</small></button>)}</>;
  if (view === "trace") return <>{Object.values(state.runs).flatMap((run) => run.executions.map((execution) =>
    <button key={execution.id} className={state.inspector?.execution.id === execution.id ? "on" : ""}
      onClick={() => state.openTrace(execution.id)}>{execution.id} {execution.task}
      <small className={`ae-st-${execution.status}`}>{execution.status}</small></button>))}</>;
  if (view === "agents") return <>{state.agents.map((agent) => <button key={agent.id}
    className={state.agentId === agent.id ? "on" : ""} onClick={() => state.setAgentId(agent.id)}>
    {agent.id} {agent.name}<small>{agent.runtime}</small></button>)}</>;
  return <>{GRAPH_NODES.map((node) => <button key={node.id} className={state.selectedNodeId === node.id ? "on" : ""}
    onClick={() => state.setSelectedNodeId(node.id)}>{node.id}<small>{KIND[node.kind]}</small></button>)}</>;
}

function EMain({ state, view }) {
  if (view === "chat") return <EChat state={state} />;
  if (view === "trace") return <ETrace state={state} />;
  if (view === "agents") return <EAgents state={state} />;
  return <EMap state={state} />;
}

/* —— 地图: 字符流图谱 / 科研日志 —— */
function EMap({ state }) {
  if (state.mapSubview === "journal") return <EJournal />;
  const node = GRAPH_NODE_MAP[state.selectedNodeId] || GRAPH_NODES[0];
  return <main className="ae-map"><EGraph state={state} selected={node} /><EDetail state={state} node={node} /></main>;
}

function EGraph({ state, selected }) {
  const lines = useMemo(() => graphEdgesAll().map((edge, index) => {
    const from = POS[edge.source], to = POS[edge.target];
    const same = from[0] === to[0];
    const points = same
      ? [[from[0] + NODE_W / 2, from[1] + NODE_H], [to[0] + NODE_W / 2, to[1]]]
      : [[from[0] + NODE_W, from[1] + NODE_H / 2], [(from[0] + NODE_W + to[0]) / 2, from[1] + NODE_H / 2],
        [(from[0] + NODE_W + to[0]) / 2, to[1] + NODE_H / 2], [to[0], to[1] + NODE_H / 2]];
    return buildLine(points, index * 53);
  }), []);
  return <div className="ae-graph">
    <AsciiCanvas className="ae-flow" draw={useMemo(() => drawFlow(lines), [lines])} />
    {GRAPH_NODES.map((node) => <button key={node.id} style={{ left: POS[node.id][0], top: POS[node.id][1] }}
      className={`ae-gnode ${node.id === selected.id ? "on" : ""}`} onClick={() => state.setSelectedNodeId(node.id)}>
      <span>{node.id} {BUSY.has(node.id) && <Pulse />}</span><b>{node.payload.title}</b>
      <small>{KIND[node.kind]} · {node.state || lifeLabel(node)}</small></button>)}
  </div>;
}

function lifeLabel(node) {
  return { pending: "待审查", admitted: "已入图", ghost: "已驳回" }[node.life_state] || node.life_state;
}

function EDetail({ node, state }) {
  const related = graphEdgesAll().filter((edge) => edge.source === node.id || edge.target === node.id);
  const relLabel = (edge) => edge.polarity === "supports" ? "支持" : edge.polarity === "refutes" ? "反驳" : "派生";
  return <aside className="ae-detail">
    <header>{node.id} · {KIND[node.kind]}</header>
    <p className="ae-detail-title">{node.payload.title}</p>
    {Object.entries(node.payload).filter(([key]) => key !== "title").map(([key, value]) => <div className="ae-kv" key={key}>
      <span>{key}</span><em>{value}</em></div>)}
    <header>证据关系 ({related.length})</header>
    {related.map((edge) => { const otherId = edge.source === node.id ? edge.target : edge.source;
      return <button key={otherId} className="ae-rel" onClick={() => state.setSelectedNodeId(otherId)}>
        <b className={edge.polarity === "refutes" ? "ae-err" : ""}>{relLabel(edge)}</b> → {otherId} {GRAPH_NODE_MAP[otherId].payload.title}</button>; })}
    <div className="ae-detail-actions">
      <button onClick={() => state.pinNode(node.id)}>+ 钉入当前对话</button>
      <button className="ae-primary" onClick={() => state.startRunForNode(node.id)}>▶ 发起工作流</button></div>
  </aside>;
}

function EJournal() {
  return <main className="ae-journal">
    <AsciiCanvas className="ae-journal-pulse" draw={drawWave} />
    <ol>{ACTIVITY.map((item) => <li key={item.id}>
      <span className="ae-time">{item.time}</span><b>{item.kind}</b><p>{item.text}</p><span className="ae-ref">{item.ref}</span></li>)}</ol>
  </main>;
}

/* —— 对话 —— */
function EChat({ state }) {
  const thread = state.thread;
  return <main className="ae-chat">
    <div className="ae-pins">钉住上下文:{thread.pinned.map((id) => <span className="ae-pin" key={id}>
      @{id}<button aria-label={`移除 ${id}`} onClick={() => state.togglePin(id)}>×</button></span>)}</div>
    <div className="ae-log">{thread.messages.map((message) => <EMessage key={message.id} message={message} state={state} />)}</div>
    <EComposer onSend={state.send} onMention={state.pinNode} pinned={thread.pinned} />
  </main>;
}

function EMessage({ message, state }) {
  return <article className={`ae-msg ${message.role}`}>
    <header><span className="ae-time">{message.time}</span>{message.role === "user" ? "你" : "研究助手"}</header>
    <p><EText text={message.text} /></p>
    {(message.runs || []).map((runId) => <ERun key={runId} run={state.runs[runId]}
      expanded={state.openRunId === runId} onToggle={() => state.toggleRun(runId)} onOpenTrace={state.openTrace} />)}
  </article>;
}

function EText({ text }) {
  return <>{text.split(/(@[A-Z]-\d{3})/g).map((part, index) => part.startsWith("@")
    ? <b className="ae-mention" key={`${part}-${index}`}>{part}</b> : part)}</>;
}

function ERun({ run, expanded, onToggle, onOpenTrace }) {
  const running = run.status === "运行中";
  return <div className={`ae-run ${expanded ? "open" : ""}`}>
    <button className="ae-run-head" onClick={onToggle} aria-expanded={expanded}>
      {expanded ? "▾" : "▸"} <b>{run.id}</b> {run.intent}
      <i className={`ae-st-${run.status}`}>{run.status}</i><em>{run.executions.length} 个执行</em>
      <AsciiCanvas className="ae-run-meter" draw={drawMeter(running)} deps={[running]} /></button>
    {expanded && <div className="ae-run-body">
      {run.findings.map((finding) => <div className="ae-finding" key={finding}>· {finding}</div>)}
      {run.executions.map((execution) => <EExec key={execution.id} execution={execution} onOpen={() => onOpenTrace(execution.id)} />)}
    </div>}
  </div>;
}

function EExec({ execution, onOpen }) {
  const running = execution.status === "运行中";
  return <button className="ae-exec" onClick={onOpen}>
    <span className="ae-exec-agent">{running ? <Pulse /> : "●"} {execution.agent}<small>{execution.channel} · {execution.model}</small></span>
    <b>{execution.task}</b><small>{execution.summary}</small>
    <small className="ae-dim">prompt: {execution.prompt} · skills: {execution.skills.join(" / ")}</small>
    <i className={`ae-st-${execution.status}`}>{execution.status}</i>
    <span className="ae-open">打开轨迹 →</span></button>;
}

function EComposer({ onSend, onMention, pinned }) {
  const [draft, setDraft] = useState("");
  const choices = mentionChoices(draft);
  const submit = () => { if (draft.trim()) { onSend(draft); setDraft(""); } };
  const choose = (node) => { setDraft(insertMention(draft, node.id)); onMention(node.id); };
  const keyDown = (event) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent?.isComposing || event.keyCode === 229) return;
    event.preventDefault(); submit();
  };
  return <div className="ae-composer">
    {choices.length > 0 && <div className="ae-mention-menu">{choices.map((node) => <button key={node.id} onClick={() => choose(node)}>
      @{node.id} {KIND[node.kind]} · {node.title}{pinned.includes(node.id) ? " [已引用]" : ""}</button>)}</div>}
    <div className="ae-cli"><span>❯</span>
      <input aria-label="消息" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown}
        placeholder="发消息,输入 @ 引用节点" spellCheck="false" autoComplete="off" />
      <button aria-label="发送" disabled={!draft.trim()} onClick={submit}>↵</button></div>
  </div>;
}

/* —— 轨迹 —— */
function ETrace({ state }) {
  const selected = state.inspector || { run: Object.values(state.runs)[0], execution: Object.values(state.runs)[0].executions[0] };
  const { run, execution } = selected;
  const session = execution.session;
  const running = execution.status === "运行中";
  return <main className="ae-trace">
    <header className="ae-trace-head">
      <button className="ae-back" onClick={state.backToChat}>← 返回对话</button>
      <span>{run.id} / {execution.id} · {execution.task}</span><i className={`ae-st-${execution.status}`}>{execution.status}</i>
      <AsciiCanvas className="ae-trace-meter" draw={drawMeter(running)} deps={[running]} /></header>
    <div className="ae-session-meta">runtime {session.runtime} · model {session.model} · started {session.started} · ws {session.workspace}</div>
    <div className="ae-session">{session.turns.map((turn) => <ETurn key={turn.id} turn={turn} />)}</div>
  </main>;
}

function ETurn({ turn }) {
  return <section className="ae-turn">
    <header>TURN {turn.id} · {turn.label}</header>
    <ol>{turn.steps.map((step, index) => <EStep key={index} step={step} />)}</ol>
  </section>;
}

function EStep({ step }) {
  if (step.type === "message") return <li className={`ae-step ${step.actor}`}>
    <span className="ae-time">{step.time}</span><b>{step.actor === "user" ? "❯" : "◈"}</b><p>{step.text}</p></li>;
  const call = step.type === "tool_call";
  return <li className="ae-step tool"><span className="ae-time">{step.time}</span>
    <details><summary>{call ? "→" : "←"} {step.tool} {!call && <i>{step.status}</i>}</summary>
      <pre>{call ? step.input : step.output}</pre></details></li>;
}

/* —— Agent —— */
function EAgents({ state }) {
  const agent = state.agents.find((item) => item.id === state.agentId) || state.agents[0];
  return <main className="ae-agents">
    <header className="ae-agents-head"><span>{agent.id} · {agent.name}</span>
      <nav><button onClick={() => state.createAgent("blank")}>+ 从空白创建</button>
        <button onClick={() => state.createAgent("draft")}>✦ AI 起草</button></nav></header>
    <div className="ae-editor">
      <div className="ae-kv"><span>名称</span><input value={agent.name} onChange={(event) => state.updateAgent(agent.id, { name: event.target.value })} /></div>
      <div className="ae-kv"><span>Runtime</span><select value={agent.runtime} onChange={(event) => state.updateAgent(agent.id, { runtime: event.target.value })}>
        {["Codex · ACP", "Claude Code · CLI", "Pi · ACP", "Qwen Researcher · ACP"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ae-kv top"><span>Instructions</span><textarea rows="5" value={agent.instructions}
        onChange={(event) => state.updateAgent(agent.id, { instructions: event.target.value })} /></div>
      <div className="ae-kv"><span>模型</span><select value={agent.model} onChange={(event) => state.updateAgent(agent.id, { model: event.target.value })}>
        {["gpt-5.6-codex", "gpt-5.2", "claude-sonnet-4.6", "qwen3-max"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ae-kv"><span>推理</span><select value={agent.thinking} onChange={(event) => state.updateAgent(agent.id, { thinking: event.target.value })}>
        {["低", "中", "高"].map((value) => <option key={value}>{value}</option>)}</select></div>
      <div className="ae-kv top"><span>Skills</span><ESkills agent={agent} state={state} /></div>
      <details className="ae-advanced"><summary>高级设置(权限 / 并发 / 环境变量 / MCP)</summary>
        <div className="ae-kv"><span>权限</span><select value={agent.advanced.permission}
          onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, permission: event.target.value } })}>
          {["只读", "工作区写入", "完全"].map((value) => <option key={value}>{value}</option>)}</select></div>
        <div className="ae-kv"><span>并发</span><input value={agent.advanced.concurrency}
          onChange={(event) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, concurrency: event.target.value } })} /></div>
        <EListEditor label="环境变量" items={agent.advanced.env} onChange={(env) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, env } })} />
        <EListEditor label="MCP" items={agent.advanced.mcp} onChange={(mcp) => state.updateAgent(agent.id, { advanced: { ...agent.advanced, mcp } })} />
      </details>
    </div>
  </main>;
}

function ESkills({ agent, state }) {
  return <div className="ae-skills">{agent.skills.map((skill) => <i key={skill}>{skill}
    <button aria-label={`移除 ${skill}`} onClick={() => state.updateAgent(agent.id, { skills: agent.skills.filter((item) => item !== skill) })}>×</button></i>)}
    <input placeholder="+ 添加后回车" onKeyDown={(event) => { if (event.key === "Enter" && event.target.value.trim()) {
      state.updateAgent(agent.id, { skills: [...agent.skills, event.target.value.trim()] }); event.target.value = ""; } }} /></div>;
}

function EListEditor({ label, items, onChange }) {
  return <div className="ae-kv top"><span>{label}</span><div className="ae-skills">
    {items.map((item) => <i key={item}>{item}<button aria-label="删除" onClick={() => onChange(items.filter((value) => value !== item))}>×</button></i>)}
    <input placeholder="+ 回车添加" onKeyDown={(event) => { if (event.key === "Enter" && event.target.value.trim()) {
      onChange([...items, event.target.value.trim()]); event.target.value = ""; } }} /></div></div>;
}
