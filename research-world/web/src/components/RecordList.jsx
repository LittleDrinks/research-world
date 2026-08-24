import { ChevronDown, ChevronRight, Plus } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { createThread } from "../api";
import { useWorld } from "../context/WorldContext";
import { KIND_LABELS, nodeText, RUN_STATUS, shortId } from "../utils/labels";
import { NewAgentDialog } from "./agents/NewAgentDialog";


const TITLES = { "/map": "节点", "/chat": "对话", "/traces": "运行", "/agents": "Agent" };


export function RecordList({ module, close }) {
  const [open, setOpen] = useState(true);
  if (module === "/settings") return <div className="record-list" />;
  const Toggle = open ? ChevronDown : ChevronRight;
  return <section className="record-list">
    <header><button className="record-toggle" aria-expanded={open} onClick={() => setOpen(!open)}><Toggle size={14} />{TITLES[module]}</button>
      {module === "/chat" && <NewThreadButton close={close} />}
      {module === "/agents" && <NewAgentButton close={close} />}</header>
    {open && <div className="record-items"><Records module={module} close={close} /></div>}</section>;
}


function Records({ module, close }) {
  const { data } = useWorld();
  if (module === "/map") return <NodeRecords nodes={data.nodes} close={close} />;
  if (module === "/chat") return <ThreadRecords threads={data.threads} close={close} />;
  if (module === "/traces") return <RunRecords runs={data.runs} close={close} />;
  return <AgentRecords agents={data.agents} close={close} />;
}


function NodeRecords({ nodes, close }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const selected = params.get("node");
  if (!nodes.length) return <p className="record-empty">暂无节点</p>;
  return nodes.map((node) => <button key={node.id} className={`record-item ${node.id === selected ? "selected" : ""}`}
    onClick={() => { navigate(`/map?node=${encodeURIComponent(node.id)}`); close(); }}>
    <i className={`kind-dot kind-${node.kind}`} /><span>{nodeText(node)}</span><small>{KIND_LABELS[node.kind]}</small></button>);
}


function ThreadRecords({ threads, close }) {
  const navigate = useNavigate();
  const { threadId } = useParams();
  if (!threads.length) return <p className="record-empty">暂无对话，点击 + 新建</p>;
  return threads.map((thread) => <button key={thread.id} className={`record-item ${thread.id === threadId ? "selected" : ""}`}
    onClick={() => { navigate(`/chat/${encodeURIComponent(thread.id)}`); close(); }}>
    <span>{thread.title}</span><small>{thread.nodes.length ? `${thread.nodes.length} 引用` : ""}</small></button>);
}


function RunRecords({ runs, close }) {
  const navigate = useNavigate();
  const { runId } = useParams();
  if (!runs.length) return <p className="record-empty">暂无运行</p>;
  return runs.map((run) => <button key={run.id} className={`record-item ${run.id === runId ? "selected" : ""}`}
    onClick={() => { navigate(`/traces/${encodeURIComponent(run.id)}`); close(); }}>
    <span className="mono">{shortId(run.id)}</span><small>{RUN_STATUS[run.status] || run.status}</small></button>);
}


function AgentRecords({ agents, close }) {
  const navigate = useNavigate();
  const { agentId } = useParams();
  if (!agents.length) return <p className="record-empty">暂无 Agent</p>;
  return agents.map((agent) => <button key={agent.id} className={`record-item ${agent.id === agentId ? "selected" : ""}`}
    onClick={() => { navigate(`/agents/${encodeURIComponent(agent.id)}`); close(); }}>
    <span>{agent.name || agent.id}</span><small className="mono">{agent.model}</small></button>);
}


function NewAgentButton({ close }) {
  const { projectId, refresh, setError } = useWorld();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const done = async (agent) => {
    try { await refresh(projectId); close(); navigate(`/agents/${encodeURIComponent(agent.id)}`); }
    catch (error) { setError(error.message); }
  };
  return <>
    <button className="icon-button record-add" aria-label="新建 Agent" title="新建 Agent" onClick={() => setOpen(true)}><Plus size={15} /></button>
    <NewAgentDialog open={open} onClose={() => setOpen(false)} done={done} /></>;
}


function NewThreadButton({ close }) {
  const { projectId, refresh, setError } = useWorld();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const create = async () => {
    setBusy(true);
    try { const thread = await createThread(projectId, {}); await refresh(projectId); close(); navigate(`/chat/${encodeURIComponent(thread.id)}`); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return <button className="icon-button record-add" aria-label="新建对话" title="新建对话" disabled={busy} onClick={create}><Plus size={15} /></button>;
}
