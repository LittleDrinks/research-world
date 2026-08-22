import { Activity, GitBranch, MessageSquare, Play } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createThread } from "../api";
import { useWorld } from "../context/WorldContext";
import { RUN_STATUS, shortId } from "../utils/labels";


const LABELS = { question: "问题", source: "来源", direction: "方向", experiment: "实验",
  pending: "待审查", admitted: "已入图", ghost: "已驳回", proposed: "待验证", supported: "已支持", refuted: "已反驳" };


export function Inspector({ node, nodes, edges, run, onSelect, onStart, onOpen }) {
  if (!node) return <aside className="inspector inspector-empty">选择节点查看上下文。</aside>;
  return <aside className="inspector"><div className="inspector-scroll"><NodeHeader node={node} run={run} onStart={onStart} onOpen={onOpen} />
    <NodeRecord node={node} /><Relations node={node} nodes={nodes} edges={edges} onSelect={onSelect} />
    <Rebuttal node={node} /><DiscussEntry node={node} /></div></aside>;
}


function NodeHeader({ node, run, onStart, onOpen }) {
  const title = node.payload?.title || node.payload?.text || "未命名节点";
  return <header className="inspector-header"><div className="eyebrow"><span>{LABELS[node.kind]}</span><span>{LABELS[node.life_state]}</span>{node.direction_status && <span>{LABELS[node.direction_status]}</span>}</div>
    <h1>{title}</h1>{node.rejection_reason && <p className="rejection-reason">{node.rejection_reason}</p>}
    {run && <button className="button primary workflow-start" onClick={() => onOpen(run)}><Activity size={16} />{RUN_STATUS[run.status] || run.status} · 查看轨迹</button>}
    {!run && <PipelineLauncher node={node} onStart={onStart} />}</header>;
}


function PipelineLauncher({ node, onStart }) {
  const { data } = useWorld();
  const pipelines = data.pipelines;
  const [pipelineId, setPipelineId] = useState("");
  const [busy, setBusy] = useState(false);
  const effective = pipelines.some((item) => item.id === pipelineId) ? pipelineId : pipelines[0]?.id || "";
  if (!pipelines.length) return null;
  const launch = () => { setBusy(true); Promise.resolve(onStart(node, effective)).finally(() => setBusy(false)); };
  return <div className="pipeline-launcher">
    <select aria-label="选择流程" value={effective} onChange={(event) => setPipelineId(event.target.value)}>
      {pipelines.map((pipeline) => <option key={pipeline.id} value={pipeline.id}>{pipeline.name || pipeline.id}</option>)}</select>
    <button className="button primary" disabled={busy || !effective} onClick={launch}><Play size={15} />发起运行</button></div>;
}


function NodeRecord({ node }) {
  const entries = Object.entries(node.payload || {}).filter(([, value]) => value !== null && typeof value !== "object");
  return <section className="inspector-section"><h2>节点记录</h2><dl className="node-record">{entries.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{String(value)}</dd></div>)}</dl></section>;
}


function Relations({ node, nodes, edges, onSelect }) {
  const byId = new Map(nodes.map((item) => [item.id, item]));
  const related = edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => ({ edge, node: byId.get(edge.source === node.id ? edge.target : edge.source) })).filter((item) => item.node);
  return <section className="inspector-section"><h2><GitBranch size={15} />证据关系</h2>{related.length ? <ul className="relation-list">{related.map(({ edge, node: item }) => <li key={`${edge.source}:${edge.target}:${edge.polarity}`}><button onClick={() => onSelect(item.id)}><span className={`polarity ${edge.polarity}`}>{edge.polarity === "supports" ? "支持" : "反驳"}</span><b>{item.payload?.title || item.payload?.text}</b></button></li>)}</ul> : <p className="muted">暂无关系</p>}</section>;
}


function Rebuttal({ node }) {
  if (!node.rebuttal) return null;
  return <section className="inspector-section"><h2>双审意见</h2><div className="rebuttal-grid">{Object.entries(node.rebuttal).map(([reviewer, value]) => <div key={reviewer}><b>{reviewer === "reviewer_a" ? "审查 A" : "审查 B"}</b><p>{value.rebuttal || value.feedback || value.decision}</p><span>{value.quality ?? "-"} / {value.diversity ?? "-"}</span></div>)}</div></section>;
}


function useDiscuss(node) {
  const { data, projectId, refresh, setError } = useWorld();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const thread = data.threads.find((item) => item.nodes.some((pinned) => pinned.id === node.id));
  const open = async () => {
    if (thread) return navigate(`/chat/${encodeURIComponent(thread.id)}`);
    setBusy(true);
    try {
      const created = await createThread(projectId, { node_ids: [node.id] });
      await refresh(projectId);
      navigate(`/chat/${encodeURIComponent(created.id)}`);
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return { thread, busy, open };
}


function DiscussEntry({ node }) {
  const { thread, busy, open } = useDiscuss(node);
  const label = thread ? `继续对话 · ${thread.title}` : busy ? "正在创建对话..." : "新建对话并钉入该节点";
  return <section className="inspector-section"><h2><MessageSquare size={15} />讨论</h2>
    <button className="button secondary workflow-start" disabled={busy} onClick={open}>{label}</button>
    <p className="muted mono">{shortId(node.id)}</p></section>;
}
