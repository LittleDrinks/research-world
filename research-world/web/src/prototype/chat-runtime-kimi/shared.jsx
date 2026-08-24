// 共享件: RunCard / RuntimeInspector / 钉住 chips / Composer / ActivityList。布局在各变体内自行决定。
import { Bot, ChevronDown, ChevronRight, Pin, SendHorizontal, X } from "lucide-react";
import { useState } from "react";
import { KIND, NODE_MAP, NODES } from "./seed";

export function statusClass(status) {
  return { 运行中: "running", 已完成: "done", 排队中: "queued", 失败: "failed" }[status] || "queued";
}

export function PinChip({ nodeId, onRemove }) {
  const node = NODE_MAP[nodeId];
  if (!node) return null;
  return <span className={`crt-pin kind-${node.kind}`} title={node.title}>
    <Pin size={11} /><b>{node.id}</b><em>{node.title}</em>
    {onRemove && <button aria-label={`移除 ${node.id}`} onClick={onRemove}><X size={12} /></button>}
  </span>;
}

export function PinPicker({ pinned, onAdd }) {
  const options = NODES.filter((node) => !pinned.includes(node.id));
  if (!options.length) return null;
  return <select className="crt-pin-picker" value="" aria-label="钉入节点上下文"
    onChange={(event) => event.target.value && onAdd(event.target.value)}>
    <option value="">+ 钉入节点上下文</option>
    {options.map((node) => <option key={node.id} value={node.id}>{node.id} · {KIND[node.kind]} · {node.title}</option>)}
  </select>;
}

export function RunCard({ run, expanded, onToggle, onOpenTrace }) {
  const Toggle = expanded ? ChevronDown : ChevronRight;
  return <article className={`crt-run ${expanded ? "open" : ""}`}>
    <button className="crt-run-head" onClick={onToggle} aria-expanded={expanded}>
      <Toggle size={14} /><b>{run.id}</b><span>{run.intent}</span>
      <i className={`crt-status ${statusClass(run.status)}`}>{run.status}</i>
      <em>{run.executions.length} 个执行</em>
    </button>
    {expanded && <div className="crt-run-body">
      {run.findings.length > 0 && <ul className="crt-findings">{run.findings.map((f) => <li key={f}>{f}</li>)}</ul>}
      {run.executions.map((ex) => <ExecutionRow key={ex.id} execution={ex} onOpen={() => onOpenTrace(ex.id)} />)}
    </div>}
  </article>;
}

function ExecutionRow({ execution, onOpen }) {
  return <button className="crt-exec" onClick={onOpen} aria-label={`打开 ${execution.id} 轨迹`}>
    <span className="crt-exec-agent"><Bot size={13} /><b>{execution.agent}</b><small>{execution.channel} · {execution.model}</small></span>
    <span className="crt-exec-body"><b>{execution.task}</b><small>{execution.summary}</small>
      <span className="crt-exec-prompt">{execution.prompt}</span>
      <span className="crt-skill-list">{execution.skills.map((skill) => <i key={skill}>{skill}</i>)}</span>
    </span>
    <i className={`crt-status ${statusClass(execution.status)}`}>{execution.status}</i>
    <ChevronRight className="crt-exec-arrow" size={16} />
  </button>;
}

export function RuntimeInspector({ run, execution, onClose }) {
  return <div className="crt-inspector-panel">
    <header><b>执行轨迹</b><span>{execution.id} · {run.id}</span>
      <button className="crt-icon" aria-label="关闭" onClick={onClose}><X size={15} /></button></header>
    <dl className="crt-inspector-meta">
      <div><dt>执行者</dt><dd>{execution.agent} · {execution.channel}</dd></div>
      <div><dt>模型</dt><dd>{execution.model}</dd></div>
      <div><dt>状态</dt><dd>{execution.status}</dd></div>
      <div><dt>任务</dt><dd>{execution.task}</dd></div>
    </dl>
    <ol className="crt-trace">{execution.trace.map((event, index) => <li key={index} className={event.actor}>
      <span className="crt-trace-index">{String(index + 1).padStart(2, "0")}</span>
      <strong>{actorLabel(event.actor)}</strong><p>{event.text}</p><time>{event.time}</time>
    </li>)}</ol>
  </div>;
}

function actorLabel(actor) {
  return { system: "系统", assistant: "助手", tool: "工具" }[actor] || actor;
}

export function InspectorDrawer({ state }) {
  const { run, execution } = state.inspector;
  return <aside className="crt-drawer"><RuntimeInspector run={run} execution={execution} onClose={() => state.setInspectorId(null)} /></aside>;
}

export function InspectorModal({ state }) {
  const { run, execution } = state.inspector;
  return <div className="crt-modal" onClick={() => state.setInspectorId(null)}>
    <div className="crt-modal-box" onClick={(event) => event.stopPropagation()}>
      <RuntimeInspector run={run} execution={execution} onClose={() => state.setInspectorId(null)} />
    </div>
  </div>;
}

export function Composer({ onSend, placeholder }) {
  const [draft, setDraft] = useState("");
  const submit = () => { if (draft.trim()) { onSend(draft); setDraft(""); } };
  const keyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent?.isComposing && event.keyCode !== 229) { event.preventDefault(); submit(); }
  };
  return <div className="crt-composer">
    <textarea aria-label="消息" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown} placeholder={placeholder} />
    <button className="crt-send" aria-label="发送" title="发送" disabled={!draft.trim()} onClick={submit}><SendHorizontal size={17} /></button>
  </div>;
}

export function MentionComposer({ onSend, onMention, pinned }) {
  const [draft, setDraft] = useState("");
  const choices = mentionChoices(draft);
  const submit = () => { if (draft.trim()) { onSend(draft); setDraft(""); } };
  const choose = (node) => { setDraft(insertMention(draft, node.id)); onMention(node.id); };
  const keyDown = (event) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent?.isComposing || event.keyCode === 229) return;
    event.preventDefault(); submit();
  };
  return <div className="crt-composer-wrap">
    {choices.length > 0 && <div className="crt-mention-menu">{choices.map((node) => <button key={node.id} onClick={() => choose(node)}>
      <b>@{node.id}</b><span>{KIND[node.kind]} · {node.title}</span>{pinned.includes(node.id) && <i>已引用</i>}
    </button>)}</div>}
    <div className="crt-composer"><textarea aria-label="消息" value={draft} onChange={(event) => setDraft(event.target.value)}
      onKeyDown={keyDown} placeholder="发消息，输入 @ 引用节点" />
      <button className="crt-send" aria-label="发送" title="发送" disabled={!draft.trim()} onClick={submit}><SendHorizontal size={17} /></button>
    </div>
  </div>;
}

export function mentionChoices(draft) {
  const match = draft.match(/(?:^|\s)@([^\s@]*)$/);
  if (!match) return [];
  const query = match[1].toLowerCase();
  return NODES.filter((node) => `${node.id} ${node.title}`.toLowerCase().includes(query)).slice(0, 5);
}

export function insertMention(draft, nodeId) {
  return draft.replace(/(?:^|\s)@([^\s@]*)$/, (value) => `${value.startsWith(" ") ? " " : ""}@${nodeId} `);
}

export function ActivityList({ items }) {
  return <ol className="crt-activity">{items.map((item) => <li key={item.id}>
    <time>{item.time}</time><i className={`crt-kind k-${item.kind}`}>{item.kind}</i><p>{item.text}</p><span className="crt-ref">{item.ref}</span>
  </li>)}</ol>;
}
