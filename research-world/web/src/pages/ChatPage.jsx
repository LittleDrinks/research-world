import { MessagesSquare, Plus, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { createThread, getThread, pinNode, restartThread, sendPrompt, unpinNode } from "../api";
import { EmptyState } from "../components/bits";
import { Composer } from "../components/chat/Composer";
import { LaunchControl } from "../components/chat/LaunchControl";
import { MessageList } from "../components/chat/MessageList";
import { PinStrip } from "../components/chat/PinStrip";
import { RunCard } from "../components/chat/RunCard";
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


function useSend(threadId, setDetail) {
  const { projectId, refresh, setError } = useWorld();
  const [sending, setSending] = useState(false);
  const [streaming, setStreaming] = useState("");
  const [pending, setPending] = useState("");
  const send = async (text) => {
    setSending(true); setPending(text); setStreaming(" ");
    let reply = "";
    try {
      await sendPrompt(threadId, text, (event, payload) => {
        if (event === "delta") { reply += payload.text; setStreaming(reply || " "); }
        if (event === "error") throw new Error(payload.detail || "答复失败");
      });
      setDetail(await getThread(threadId)); await refresh(projectId); return true;
    } catch (error) { setError(error.message); return false; }
    finally { setSending(false); setStreaming(""); setPending(""); }
  };
  return { sending, streaming, pending, send };
}


function usePin(threadId, setDetail) {
  const { setError } = useWorld();
  const patch = (thread) => setDetail((value) => ({ ...value, nodes: thread.nodes }));
  const pin = async (nodeId) => {
    try { patch(await pinNode(threadId, nodeId)); return true; }
    catch (error) { setError(error.message); return false; }
  };
  const unpin = (nodeId) => unpinNode(threadId, nodeId).then(patch).catch((error) => setError(error.message));
  return { pin, unpin };
}


function ThreadFailed({ onRetry }) {
  const navigate = useNavigate();
  return <EmptyState icon={MessagesSquare} title="Thread 载入失败" hint="服务端未返回该对话，可能已被删除或暂时不可用。">
    <div className="empty-actions"><button className="button primary" onClick={onRetry}>重试</button>
      <button className="button secondary" onClick={() => navigate(-1)}>返回</button></div></EmptyState>;
}


function ThreadView({ threadId }) {
  const { data, setError } = useWorld();
  const { detail, failed, retry, setDetail } = useThreadDetail(threadId);
  const { sending, streaming, pending, send } = useSend(threadId, setDetail);
  const { pin, unpin } = usePin(threadId, setDetail);
  if (failed) return <ThreadFailed onRetry={retry} />;
  if (!detail) return <div className="page-loading">正在载入 Thread...</div>;
  const messages = [...(detail.runtime?.messages || [])];
  if (pending) messages.push({ role: "user", content: pending });
  return <section className="chat-page">
    <ThreadHeader detail={detail} sending={sending} onRestart={() => restartThread(threadId).then(setDetail).catch((error) => setError(error.message))} />
    <PinStrip nodes={detail.nodes} onRemove={unpin} />
    <MessageList messages={messages} streaming={sending ? streaming : ""} />
    <RunSection runs={threadRuns(data.runs, detail)} threadId={threadId} />
    <LaunchControl thread={detail} />
    <Composer pinnedNodes={detail.nodes} sending={sending} onSend={send} onPin={pin} /></section>;
}


function RunSection({ runs, threadId }) {
  if (!runs.length) return null;
  return <section className="chat-runs"><header>研究运行 · {runs.length}</header>
    {runs.map((run) => <RunCard key={run.id} run={run} threadId={threadId} />)}</section>;
}


function ThreadHeader({ detail, sending, onRestart }) {
  const agent = useWorld().data.agents.find((item) => item.id === detail.agent_id);
  return <header className="thread-header"><div><h1>{detail.title}</h1><span>{agent?.name || detail.agent_id} · {detail.nodes.length} 个引用节点{sending ? " · 正在回复" : ""}</span></div>
    <button className="icon-button" aria-label="重启会话" title="重启会话" onClick={onRestart}><RotateCcw size={16} /></button></header>;
}
