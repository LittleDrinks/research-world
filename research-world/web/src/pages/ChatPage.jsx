import { MessagesSquare, Plus, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { createThread, getThread, pinNode, restartThread, sendPrompt } from "../api";
import { EmptyState } from "../components/bits";
import { Composer } from "../components/chat/Composer";
import { MessageList } from "../components/chat/MessageList";
import { ProfileDraftButton, ProfileDraftCard } from "../components/chat/ProfileDraft";
import { ResearchControls } from "../components/chat/ResearchControls";
import { ReportCard } from "../components/chat/ReportCard";
import { loadReportReplacements, replaceTrace, replacementsForThread } from "../components/chat/reportState";
import { useWorld } from "../context/WorldContext";
import "../chat.css";


export function ChatPage() {
  const { threadId } = useParams();
  const { data, loading } = useWorld();
  if (loading) return <div className="page-loading">正在载入对话...</div>;
  if (!threadId && data.threads.length) return <Navigate to={`/chat/${encodeURIComponent(data.threads[0].id)}`} replace />;
  if (!threadId) return <NoThreads />;
  return <ThreadView key={threadId} threadId={threadId} />;
}


function NoThreads() {
  const { projectId, refresh, setError } = useWorld();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const create = async () => {
    setBusy(true);
    try { const thread = await createThread(projectId, {}); await refresh(projectId); navigate(`/chat/${encodeURIComponent(thread.id)}`); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return <EmptyState icon={MessagesSquare} title="项目还没有对话" hint="对话是项目级 Thread，可钉入节点作为上下文。">
    <button className="button primary" disabled={busy} onClick={create}><Plus size={15} />新建对话</button></EmptyState>;
}


function threadRuns(runs, thread) {
  return runs.filter((run) => run.payload?.thread_id === thread.id);
}


function useThreadDetail(threadId) {
  const [state, setState] = useState({ detail: null, failed: false, epoch: 0 });
  useEffect(() => {
    let stale = false;
    getThread(threadId).then((value) => !stale && setState((s) => ({ ...s, detail: value, failed: false })))
      .catch(() => !stale && setState((s) => ({ ...s, failed: true })));
    return () => { stale = true; };
  }, [threadId, state.epoch]);
  const retry = () => setState({ detail: null, failed: false, epoch: state.epoch + 1 });
  const setDetail = (value) => setState((s) => ({ ...s, detail: typeof value === "function" ? value(s.detail) : value }));
  return { ...state, retry, setDetail };
}


function useReportRequests() {
  const sequence = useRef(0);
  return { next: () => ++sequence.current, latest: (request) => request === sequence.current };
}


function useReportReplacements(threadId) {
  const [state, setState] = useState(() => replacementState(threadId));
  const replacements = replacementsForThread(threadId, state);
  useEffect(() => {
    if (state.threadId !== threadId) setState(replacementState(threadId));
  }, [state.threadId, threadId]);
  const replace = (trace, result) => {
    setState({ threadId, replacements: replaceTrace(threadId, replacements, trace, result.publication.id) });
  };
  return { replacements, replace };
}


function replacementState(threadId) {
  return { threadId, replacements: loadReportReplacements(threadId) };
}


function promptEvent(reply, setStreaming, setReportProgress, event, payload) {
  if (event === "delta") { reply.text += payload.text; setStreaming(reply.text || " "); }
  if (event === "tool") updateReportProgress(setReportProgress, payload?.update);
  if (event !== "error") return;
  const failure = new Error(payload.detail || "答复失败");
  failure.code = payload.code;
  throw failure;
}


function updateReportProgress(setReportProgress, update) {
  if (reportStarted(update)) setReportProgress(update);
}


function reportStarted(update) {
  return update?.sessionUpdate === "tool_call" && update.title === "发布科研报告" && update.kind === "other" && update.status === "in_progress";
}


function showSendError(error, onSpecInvalid, setError) {
  if (error.code === "session_spec_invalid") onSpecInvalid();
  else setError(error.message);
}


function useSend(threadId, setDetail, onSpecInvalid) {
  const { projectId, refresh, setError } = useWorld();
  const [sending, setSending] = useState(false);
  const [streaming, setStreaming] = useState("");
  const [pending, setPending] = useState("");
  const [reportProgress, setReportProgress] = useState(false);
  const send = async (text) => {
    setSending(true); setPending(text); setStreaming(" ");
    const reply = { text: "" };
    try {
      await sendPrompt(threadId, text, (...event) => promptEvent(reply, setStreaming, setReportProgress, ...event));
      const detail = await getThread(threadId);
      setDetail(detail); setReportProgress(false); await refresh(projectId); return true;
    } catch (error) {
      showSendError(error, onSpecInvalid, setError); return false;
    } finally { setSending(false); setStreaming(""); setPending(""); }
  };
  return { sending, streaming, pending, reportProgress, send };
}


function usePin(threadId, setDetail) {
  const { setError } = useWorld();
  const patch = (thread) => setDetail((value) => ({ ...value, nodes: thread.nodes }));
  const pin = async (nodeId) => {
    try { patch(await pinNode(threadId, nodeId)); return true; }
    catch (error) { setError(error.message); return false; }
  };
  return pin;
}


function ThreadFailed({ onRetry }) {
  const navigate = useNavigate();
  return <EmptyState icon={MessagesSquare} title="Thread 载入失败" hint="服务端未返回该对话，可能已被删除或暂时不可用。">
    <div className="empty-actions"><button className="button primary" onClick={onRetry}>重试</button>
      <button className="button secondary" onClick={() => navigate(-1)}>返回</button></div></EmptyState>;
}


function useRestart(threadId, setDetail) {
  const { setError } = useWorld();
  const [specInvalid, setSpecInvalid] = useState(false);
  const restart = async () => {
    try { setDetail(await restartThread(threadId)); setSpecInvalid(false); }
    catch (error) { setError(error.message); }
  };
  return { specInvalid, flagSpecInvalid: () => setSpecInvalid(true), restart };
}


function useReportRefresh(threadId, setDetail, requests) {
  const sequence = useRef(0);
  return async (request) => {
    const refresh = ++sequence.current;
    try {
      const detail = await getThread(threadId);
      if (refresh !== sequence.current || !requests.latest(request)) return false;
      setDetail(detail);
      return true;
    } catch (error) {
      if (refresh !== sequence.current || !requests.latest(request)) return false;
      throw error;
    }
  };
}


function ThreadView({ threadId }) {
  const { data } = useWorld();
  const { detail, failed, retry, setDetail } = useThreadDetail(threadId);
  const reportRequests = useReportRequests();
  const reportState = useReportReplacements(threadId);
  const { specInvalid, flagSpecInvalid, restart } = useRestart(threadId, setDetail);
  const { sending, streaming, pending, reportProgress, send } = useSend(threadId, setDetail, flagSpecInvalid);
  const pin = usePin(threadId, setDetail);
  const refreshReports = useReportRefresh(threadId, setDetail, reportRequests);
  const [draft, setDraft] = useState(null);
  if (failed) return <ThreadFailed onRetry={retry} />; if (!detail) return <div className="page-loading">正在载入 Thread...</div>;
  return <ThreadContent data={data} detail={detail} draft={draft} pending={pending} pin={pin} reportProgress={reportProgress} reportRequests={reportRequests} reportState={reportState} sending={sending} setDraft={setDraft} onRefresh={refreshReports} onRestart={restart} onSend={send} specInvalid={specInvalid} streaming={streaming} />;
}


function ThreadContent({ data, detail, draft, pending, pin, reportProgress, reportRequests, reportState, sending, setDraft, onRefresh, onRestart, onSend, specInvalid, streaming }) {
  const messages = threadMessages(detail, pending);
  const reportTitle = data.projects.find((item) => item.id === data.active_project_id)?.name || "Research report";
  return <section className="chat-page">
    <ThreadHeader detail={detail} sending={sending} onRestart={onRestart} />
    <div className="chat-scroll"><MessageList messages={messages} streaming={sending ? streaming : ""} reports={detail.runtime?.reports || []} publications={detail.report_publications || []} reportProgress={reportProgress} replacements={reportState.replacements} requests={reportRequests} threadId={detail.id} reportTitle={reportTitle} onReportPublished={reportState.replace} onReportRefresh={onRefresh} turns={detail.runtime?.turns || []} /><div className="chat-report"><ReportCard threadId={detail.id} reports={detail.reports || []} title={reportTitle} onRefresh={onRefresh} requests={reportRequests} /></div></div>
    {specInvalid && <SpecInvalidNotice onRestart={onRestart} />}
    {draft && <ProfileDraftCard key={draft.nonce} draft={draft} onCancel={() => setDraft(null)} />}
    <Composer pinnedNodes={detail.nodes} sending={sending} onSend={onSend} onPin={pin}
      accessory={<><ResearchControls thread={detail} runs={threadRuns(data.runs, detail)} />
        <ProfileDraftButton onDraft={(value) => setDraft({ ...value, nonce: Date.now() })} /></>} /></section>;
}


function threadMessages(detail, pending) {
  const messages = [...(detail.runtime?.messages || [])];
  if (pending) messages.push({ role: "user", content: pending });
  return messages;
}


function SpecInvalidNotice({ onRestart }) {
  return <div className="spec-notice" role="status">
    <span>此对话的 Agent 配置已变更，需要重启会话</span>
    <button className="button secondary" onClick={onRestart}><RotateCcw size={14} />重启会话</button></div>;
}


function ThreadHeader({ detail, sending, onRestart }) {
  const agent = useWorld().data.agents.find((item) => item.id === detail.agent_id);
  return <header className="thread-header"><div><h1>{detail.title}</h1><span>{agent?.name || detail.agent_id} · {detail.nodes.length} 个引用节点{sending ? " · 正在回复" : ""}</span></div>
    <button className="icon-button" aria-label="重启会话" title="重启会话" onClick={onRestart}><RotateCcw size={16} /></button></header>;
}
