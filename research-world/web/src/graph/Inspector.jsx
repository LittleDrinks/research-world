import { Activity, Check, Copy, GitBranch, Play } from "lucide-react";
import { useState } from "react";
import { useWorld } from "../context/WorldContext";
import { nodeText, RUN_STATUS } from "../utils/labels";


const LABELS = { question: "问题", source: "来源", direction: "方向", experiment: "实验",
  pending: "待审查", admitted: "已入图", ghost: "已驳回", proposed: "待验证", supported: "已支持", refuted: "已反驳",
  uncertain: "不确定", approve: "通过", reject: "驳回", support: "支持方", challenge: "质疑方", mechanical: "机械校验" };


export function Inspector({ node, nodes, edges, artifacts = [], run, onSelect, onStart, onOpen }) {
  if (!node) return <aside className="inspector inspector-empty">选择节点查看上下文。</aside>;
  return <aside className="inspector"><div className="inspector-scroll"><NodeHeader node={node} run={run} onStart={onStart} onOpen={onOpen} />
    <NodeRecord node={node} /><Relations node={node} nodes={nodes} edges={edges} onSelect={onSelect} />
    <Claims node={node} /><Reviews node={node} /><Artifacts node={node} artifacts={artifacts} />
    {(node.life_state === "admitted" || node.type) && <NodeIdEntry node={node} />}</div></aside>;
}


function NodeHeader({ node, run, onStart, onOpen }) {
  const kind = node.kind || node.type;
  const lifeState = node.life_state ? LABELS[node.life_state] : "";
  const title = nodeText(node);
  return <header className="inspector-header"><div className="eyebrow"><span>{LABELS[kind] || kind}</span>{lifeState && <span>{lifeState}</span>}{node.direction_status && <span>{LABELS[node.direction_status]}</span>}</div>
    <h1>{title}</h1>{node.rejection_reason && <p className="rejection-reason">{node.rejection_reason}</p>}
    {run && <button className="button primary workflow-start" onClick={() => onOpen(run)}><Activity size={16} />{RUN_STATUS[run.status] || run.status} · 查看轨迹</button>}
    {!run && node.life_state === "admitted" && onStart && <PipelineLauncher node={node} onStart={onStart} />}</header>;
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
  const entries = Object.entries(node.payload || node.content || {}).filter(([, value]) => value !== null && typeof value !== "object");
  return <section className="inspector-section"><h2>节点记录</h2><dl className="node-record">{entries.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{String(value)}</dd></div>)}</dl></section>;
}


function Relations({ node, nodes, edges, onSelect }) {
  const byId = new Map(nodes.map((item) => [item.id, item]));
  const related = edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => ({ edge, node: relatedNode(edge, node, byId) }));
  return <section className="inspector-section"><h2><GitBranch size={15} />直接关系</h2>{related.length ? <ul className="relation-list">{related.map(({ edge, node: item }) => <li key={`${edge.source}:${edge.target}:${edge.polarity}`}><button onClick={() => onSelect(item.id)}><span className={`polarity ${edge.polarity}`}>{relationLabel(edge.polarity)}</span><b>{nodeText(item)}</b></button></li>)}</ul> : <p className="muted">暂无关系</p>}</section>;
}


function relatedNode(edge, node, byId) {
  const id = edge.source === node.id ? edge.target : edge.source;
  return byId.get(id) || { id, type: "record", content: { title: id } };
}


function relationLabel(type) {
  return { supports: "支持", refutes: "反驳", depends_on: "依赖" }[type] || type;
}


function Claims({ node }) {
  const values = (node.payload || node.content)?.claims;
  const claims = Array.isArray(values) ? values.filter(isClaim) : [];
  if (!claims.length) return null;
  return <section className="inspector-section"><h2>原子主张</h2><ol className="claim-list">
    {claims.map((claim, index) => <li key={text(claim.id) || index}><header><b>{claim.text}</b><span>{label(claim.verdict)}</span></header>
      <Evidence values={claim.evidence} /></li>)}</ol></section>;
}


function Reviews({ node }) {
  if (!isRecord(node.rebuttal)) return null;
  return <section className="inspector-section"><h2>审计意见</h2><div className="review-grid">
    {Object.entries(node.rebuttal).map(([name, value]) => <Review key={name} name={name} value={value} />)}
  </div></section>;
}


function Review({ name, value }) {
  const review = isRecord(value) ? value : { argument: String(value ?? "") };
  const title = label(review.stance) || name;
  return <article><header><b>{title}</b><span>{label(review.decision || review.stance)}</span></header>
    <p>{text(review.argument) || text(review.reason)}</p><Evidence values={review.evidence} /></article>;
}


function Evidence({ values = [] }) {
  const items = Array.isArray(values) ? values.filter(text) : [];
  if (!items.length) return null;
  return <ul className="audit-evidence">{items.map((value, index) => <li key={`${value}:${index}`} className="mono">{String(value)}</li>)}</ul>;
}


function Artifacts({ node, artifacts }) {
  const ids = Array.isArray(node.artifact_ids) ? node.artifact_ids : [];
  const byId = new Map(artifacts.map((artifact) => [artifact.id, artifact]));
  if (!ids.length) return null;
  return <section className="inspector-section"><h2>关联 Artifact</h2><ul className="audit-evidence">
    {ids.map((id) => <li key={id} className="mono">{byId.get(id)?.media_type || id} · {id}</li>)}
  </ul></section>;
}


function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}


function isClaim(value) {
  return isRecord(value) && Boolean(text(value.text));
}


function text(value) {
  return typeof value === "string" ? value : "";
}


function label(value) {
  return text(value) ? LABELS[value] || value : "";
}


function NodeIdEntry({ node }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard.writeText(node.id); setCopied(true); };
  return <section className="inspector-section"><h2>节点 ID</h2><div className="node-id">
    <code className="mono">{node.id}</code>
    <button className="icon-button" aria-label={copied ? "已复制节点 ID" : "复制节点 ID"} title={copied ? "已复制" : "复制节点 ID"} onClick={copy}>
      {copied ? <Check size={15} /> : <Copy size={15} />}</button></div></section>;
}
