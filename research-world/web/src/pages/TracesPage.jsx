import { Activity, ArrowLeft, Check, ChevronDown, ChevronRight, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { confirmRun, getSession, resolveRun } from "../api";
import { EmptyState, StatusPill } from "../components/bits";
import { useWorld } from "../context/WorldContext";
import { formatDate, formatTime, RUN_STATUS, shortId } from "../utils/labels";
import "../traces.css";


export function TracesPage() {
  const { runId } = useParams();
  const { data, loading } = useWorld();
  if (loading) return <div className="page-loading">正在载入轨迹...</div>;
  if (!runId && data.runs.length) return <Navigate to={`/traces/${encodeURIComponent(data.runs[0].id)}`} replace />;
  if (!runId) return <EmptyState icon={Activity} title="暂无运行" hint="在对话中钉入节点并启动流程后，这里会出现轨迹。" />;
  const run = data.runs.find((item) => item.id === runId);
  if (!run) return <EmptyState icon={Activity} title="运行不存在" hint="它可能已被清理，或属于其他项目。" />;
  return <RunTrace key={run.id} run={run} />;
}


function RunTrace({ run }) {
  const [params] = useSearchParams();
  const sessions = useMemo(() => sessionEvents(run), [run]);
  const inspects = useSessionInspects(sessions);
  return <section className="traces-page">
    <RunHeader run={run} from={params.get("from")} />
    <div className="trace-tree"><RunNode run={run} sessions={sessions} inspects={inspects} focusSession={params.get("session")} /></div></section>;
}


function useRunActions(run) {
  const { refresh, setError } = useWorld();
  const key = gateKey(run);
  const [requesting, setRequesting] = useState(false);
  const [submitted, setSubmitted] = useState("");
  useEffect(() => { setSubmitted(""); }, [key]);
  const act = async (action) => {
    setRequesting(true);
    try { await action(); setSubmitted(key); await refresh(run.project_id).catch(() => {}); }
    catch (error) { setError(error.message); }
    finally { setRequesting(false); }
  };
  return { busy: requesting || submitted === key, act };
}


function gateKey(run) {
  return [run.status, run.stage, run.payload?.conflict_node || "", run.updated_at].join(":");
}


function HumanGate({ run, busy, act }) {
  if (run.payload?.conflict_node) return <div className="run-actions">
    <button className="button primary" disabled={busy} onClick={() => act(() => resolveRun(run.id, { decision: "approve", reason: "人工批准" }))}><ThumbsUp size={14} />批准</button>
    <button className="button secondary" disabled={busy} onClick={() => act(() => resolveRun(run.id, { decision: "reject", reason: "人工驳回" }))}><ThumbsDown size={14} />驳回</button></div>;
  return <div className="run-actions">
    <button className="button primary" disabled={busy} onClick={() => act(() => confirmRun(run.id))}><Check size={15} />确认继续</button></div>;
}


function RunHeader({ run, from }) {
  const { busy, act } = useRunActions(run);
  const navigate = useNavigate();
  return <header className="run-header">
    {from && <button className="button secondary" onClick={() => navigate(`/chat/${encodeURIComponent(from)}`)}><ArrowLeft size={15} />返回对话</button>}
    <div className="run-title"><h1>{run.definition_snapshot?.name || run.pipeline_id} <span className="mono">{shortId(run.id)}</span></h1>
      <span>节点 {shortId(run.node_id)} · 当前阶段 {run.stage} · {formatDate(run.created_at)}</span></div>
    <StatusPill status={run.status} label={RUN_STATUS[run.status]} />
    {run.status === "waiting_human" && <HumanGate run={run} busy={busy} act={act} />}
  </header>;
}


function sessionEvents(run) {
  return run.events.filter((event) => event.type === "agent_session" && event.payload?.session_id);
}


function useSessionInspects(sessions) {
  const [inspects, setInspects] = useState({});
  const key = sessions.map((event) => event.payload.session_id).join("|");
  useEffect(() => {
    let stale = false;
    sessions.forEach((event) => {
      const id = event.payload.session_id;
      getSession(id).then((value) => !stale && setInspects((map) => ({ ...map, [id]: value })))
        .catch(() => !stale && setInspects((map) => ({ ...map, [id]: null })));
    });
    return () => { stale = true; };
  }, [key]);
  return inspects;
}


function TreeNode({ label, meta, tone, defaultOpen, children }) {
  const [open, setOpen] = useState(Boolean(defaultOpen));
  const Toggle = open ? ChevronDown : ChevronRight;
  return <div className={`tree-node ${tone || ""}`}>
    <button className="tree-row" aria-expanded={open} onClick={() => setOpen(!open)}><Toggle size={14} />{label}{meta && <small>{meta}</small>}</button>
    {open && <div className="tree-children">{children}</div>}</div>;
}


function RunNode({ run, sessions, inspects, focusSession }) {
  const stages = run.definition_snapshot?.stages || [];
  const stageIds = new Set(stages.map((stage) => stage.id));
  const owned = (stage) => sessions.filter((event) => event.payload?.stage_id === stage.id);
  const rest = sessions.filter((event) => !stageIds.has(event.payload?.stage_id));
  return <TreeNode label={<b>RUN <span className="mono">{shortId(run.id)}</span></b>} meta={`${run.events.length} 事件`} defaultOpen>
    {stages.map((stage) => <StageNode key={stage.id} stage={stage} run={run} sessions={owned(stage)} inspects={inspects} focusSession={focusSession} />)}
    {rest.length > 0 && <TreeNode label={<b>未分组会话</b>} meta={String(rest.length)} defaultOpen>
      {rest.map((event) => <SessionNode key={event.id} event={event} inspect={inspects[event.payload.session_id]} focus={focusSession === event.payload.session_id} />)}</TreeNode>}
    {!stages.length && !rest.length && <p className="record-empty">暂无阶段与会话记录</p>}
  </TreeNode>;
}


function stageStatus(stage, run, stages) {
  const index = stages.findIndex((item) => item.id === stage.id);
  const current = stages.findIndex((item) => item.id === run.stage);
  if (run.status === "completed") return "completed";
  if (current < 0) return run.stage === stage.id && run.status === "running" ? "running" : "";
  if (index < current) return "completed";
  if (index === current && ["running", "waiting_human"].includes(run.status)) return "running";
  return "";
}


function StageNode({ stage, run, sessions, inspects, focusSession }) {
  const stages = run.definition_snapshot?.stages || [];
  const steps = run.steps.filter((step) => step.stage === stage.id);
  const status = stageStatus(stage, run, stages);
  const meta = [stage.type, stage.agent || stage.tool, status && (RUN_STATUS[status] || status)].filter(Boolean).join(" · ");
  return <TreeNode label={<b>STAGE <span className="mono">{stage.id}</span></b>} meta={meta} tone={status}
    defaultOpen={status === "running" || sessions.some((event) => event.payload.session_id === focusSession)}>
    {steps.map((step) => <StepNode key={step.id} step={step} />)}
    {sessions.map((event) => <SessionNode key={event.id} event={event} inspect={inspects[event.payload.session_id]} focus={focusSession === event.payload.session_id} />)}
    {!steps.length && !sessions.length && <p className="record-empty">暂无记录</p>}
  </TreeNode>;
}


function StepNode({ step }) {
  return <details className="tree-leaf"><summary><span className="mono">执行 #{step.ordinal}</span>
    <span>{step.payload?.command || step.payload?.summary || step.payload?.title || "步骤"}</span><StatusPill status={step.status} label={step.status} /></summary>
    <pre>{JSON.stringify({ payload: step.payload, output: step.output }, null, 2)}</pre></details>;
}


function SessionNode({ event, inspect, focus }) {
  const sessionId = event.payload.session_id;
  const meta = inspect === undefined ? "载入中..." : inspect === null ? "会话不可用"
    : `${inspect.session?.agent_spec?.model || ""} · ${inspect.status || ""}`;
  return <TreeNode label={<b>SESSION <span className="mono">{sessionId.slice(0, 14)}</span></b>} meta={`${event.actor} · ${meta}`} defaultOpen={focus}>
    {inspect?.turns?.map((turn, index) => <TurnNode key={turn.id} turn={turn} index={index} />)}
    {inspect && !inspect.turns?.length && <p className="record-empty">暂无 turn</p>}
    {inspect === null && <p className="record-empty">无法读取该会话的 trace</p>}
  </TreeNode>;
}


function pairEvents(events) {
  const results = new Map(events.filter((event) => event.type === "tool_result").map((event) => [event.data?.tool_call_id, event]));
  return events.filter((event) => event.type !== "tool_result")
    .map((event) => ({ event, result: event.type === "tool_call" ? results.get(event.data?.tool_call_id) : undefined }));
}


function TurnNode({ turn, index }) {
  const input = turn.input?.filter((block) => block.type === "text").map((block) => block.text).join("\n") || "";
  const rows = pairEvents(turn.events);
  const tools = rows.filter((row) => row.event.type === "tool_call").length;
  return <TreeNode label={<b>TURN {index + 1}</b>} meta={`${turn.status} · ${tools} 次工具调用`} defaultOpen={index === 0}>
    {input && <p className="turn-input">{input}</p>}
    {rows.map((row) => <EventRow key={row.event.seq} event={row.event} result={row.result} />)}
    {turn.output && <div className="turn-output"><b>输出</b><p>{turn.output}</p></div>}
  </TreeNode>;
}


function EventRow({ event, result }) {
  if (event.type === "tool_call") return <ToolRow event={event} result={result} />;
  if (event.type === "model_response") return <details className="tree-leaf"><summary><span>模型响应</span><span className="tree-preview">{event.data?.message?.content || ""}</span></summary>
    <pre>{JSON.stringify(event.data, null, 2)}</pre></details>;
  if (event.type === "error") return <p className="trace-error">{event.data?.error}</p>;
  return null;
}


function ToolRow({ event, result }) {
  const name = event.data?.name || "tool";
  const failed = result?.data?.is_error;
  return <details className="tree-leaf tool"><summary><span className="mono">{name}</span>
    <span className="tree-preview">{String(result?.data?.content || event.data?.arguments || "").slice(0, 80)}</span>
    {result && <StatusPill status={failed ? "failed" : "completed"} label={failed ? "失败" : "完成"} />}</summary>
    <pre>{JSON.stringify({ arguments: event.data?.arguments, result: result?.data?.content }, null, 2)}</pre></details>;
}
