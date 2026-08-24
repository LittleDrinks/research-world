import { Bot, ChevronDown, ChevronRight, EyeOff, SquareArrowOutUpRight } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RUN_STATUS, shortId } from "../../utils/labels";
import { StatusPill } from "../bits";
import { AdmissionControl } from "../AdmissionControl";


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
    <SourceProjection run={run} />
    {run.steps.length > 0 && <ul className="run-steps">{run.steps.map((step) =>
      <li key={step.id}><span className="mono">#{step.ordinal}</span><span>{stepSummary(step)}</span><StatusPill status={step.status} label={step.status} /></li>)}</ul>}
    {sessions.map((event) => <SessionRow key={event.id} event={event} runId={run.id} threadId={threadId} />)}
    {!sessions.length && !run.steps.length && <p className="record-empty">等待执行记录</p>}
  </div>;
}


function SourceProjection({ run }) {
  const values = run.payload?._pipeline?.values || {};
  const candidates = values.source_candidates || [];
  const sources = values.sources || [];
  if (!candidates.length) return null;
  return <section className="source-projection"><h3>Source 候选</h3><ol>{candidates.map((candidate, index) =>
    <SourceCandidate key={`${candidate.title}:${index}`} candidate={candidate} source={sources[index]} />)}</ol></section>;
}


function SourceCandidate({ candidate, source }) {
  const navigate = useNavigate();
  const relation = candidate.relationship;
  const artifact = candidate.artifact;
  const open = (id) => navigate(`/map?node=${encodeURIComponent(id)}`);
  return <li><header>{source ? <button className="text-link" onClick={() => open(source.id)}>{candidate.title}</button>
    : <b>{candidate.title}</b>}<span data-status={source?.life_state || "candidate"}>
    {sourceState(source)}</span></header><dl>
    <Row label="书目" value={`${candidate.authors.join("、")} · ${candidate.year} · ${candidate.venue}`} />
    <Row label="用途" value={`${relation.use} · ${relation.relevance}`} />
    <NodeRow label="Direction" id={relation.direction_id} onOpen={open} />
    <Row label="核验" value={`${candidate.retrieval.database} · ${candidate.retrieval.verified_at}`} />
    <Row label="Artifact" value={artifact ? `${artifact.id} · ${artifact.media_type} · ${artifact.sha256}` : "全文不可得"} />
    {source?.rejection_reason && <Row label="驳回理由" value={source.rejection_reason} />}
  </dl>{source && <AdmissionControl node={source} />}</li>;
}


function Row({ label, value }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}


function NodeRow({ label, id, onOpen }) {
  return <div><dt>{label}</dt><dd><button className="text-link" onClick={() => onOpen(id)}>{id}</button></dd></div>;
}


function sourceState(source) {
  return { pending: "待 Admission", admitted: "已准入", ghost: "已驳回" }[source?.life_state] || "候选";
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
