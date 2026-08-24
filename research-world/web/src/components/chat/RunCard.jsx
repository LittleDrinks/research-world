import { Bot, ChevronDown, ChevronRight, EyeOff, SquareArrowOutUpRight } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RUN_STATUS, shortId } from "../../utils/labels";
import { StatusPill } from "../bits";


export function RunCard({ run, threadId, onDismiss }) {
  const [open, setOpen] = useState(false);
  const sessions = run.events.filter((event) => event.type === "agent_session" && event.payload?.session_id);
  const Toggle = open ? ChevronDown : ChevronRight;
  return <article className={`run-card ${open ? "open" : ""}`}>
    <div className="run-card-head-row">
      <button className="run-card-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <Toggle size={14} /><b className="mono">{shortId(run.id)}</b><span>{run.definition_snapshot?.name || run.pipeline_id}</span>
        <StatusPill status={run.status} label={RUN_STATUS[run.status]} /><em>{sessions.length} 个会话 · {run.steps.length} 个执行</em></button>
      <TraceLink runId={run.id} threadId={threadId} />
      {["completed", "failed"].includes(run.status) && <DismissRun runId={run.id} onDismiss={onDismiss} />}</div>
    {open && <RunBody run={run} sessions={sessions} threadId={threadId} />}</article>;
}


function RunBody({ run, sessions, threadId }) {
  return <div className="run-card-body">
    {run.steps.length > 0 && <ul className="run-steps">{run.steps.map((step) =>
      <li key={step.id}><span className="mono">#{step.ordinal}</span><span>{stepSummary(step)}</span><StatusPill status={step.status} label={step.status} /></li>)}</ul>}
    {sessions.map((event) => <SessionRow key={event.id} event={event} runId={run.id} threadId={threadId} />)}
    {!sessions.length && !run.steps.length && <p className="record-empty">等待执行记录</p>}
  </div>;
}


function DismissRun({ runId, onDismiss }) {
  return <button className="icon-button run-card-dismiss" aria-label={`从当前列表移除运行 ${shortId(runId)}`}
    title="从当前列表移除（不删除）" onClick={() => onDismiss(runId)}><EyeOff size={15} /></button>;
}


function TraceLink({ runId, threadId }) {
  const navigate = useNavigate();
  const open = (event) => {
    event.stopPropagation();
    navigate(`/traces/${encodeURIComponent(runId)}${threadId ? `?from=${encodeURIComponent(threadId)}` : ""}`);
  };
  return <button className="icon-button run-card-trace" aria-label="查看轨迹" title="查看轨迹" onClick={open}><SquareArrowOutUpRight size={15} /></button>;
}


function stepSummary(step) {
  return step.payload?.command || step.payload?.summary || step.payload?.title || step.stage;
}


function SessionRow({ event, runId, threadId }) {
  const navigate = useNavigate();
  const sessionId = event.payload.session_id;
  const open = () => navigate(`/traces/${encodeURIComponent(runId)}?session=${encodeURIComponent(sessionId)}${threadId ? `&from=${encodeURIComponent(threadId)}` : ""}`);
  return <button className="session-row" onClick={open} aria-label={`打开会话 ${sessionId} 轨迹`}>
    <Bot size={13} /><b>{event.actor}</b><span className="mono">{sessionId.slice(0, 14)}</span>
    {event.payload.usage?.prompt_tokens ? <small>{event.payload.usage.prompt_tokens} tokens</small> : <small />}
    <ChevronRight size={15} /></button>;
}
