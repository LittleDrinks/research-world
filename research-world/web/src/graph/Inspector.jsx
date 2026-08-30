import { Check, Copy, GitBranch } from "lucide-react";
import { useState } from "react";
import { KIND_LABELS, recordText } from "../utils/labels";


export function Inspector({ node, nodes, edges, artifacts = [], onSelect }) {
  if (!node) return <aside className="inspector inspector-empty">选择节点查看上下文。</aside>;
  return <aside className="inspector"><div className="inspector-scroll"><NodeHeader node={node} />
    <NodeRecord node={node} /><Relations node={node} nodes={nodes} edges={edges} onSelect={onSelect} />
    <Artifacts node={node} artifacts={artifacts} /><NodeIdEntry node={node} />
  </div></aside>;
}


function NodeHeader({ node }) {
  return <header className="inspector-header"><div className="eyebrow"><span>{KIND_LABELS[node.kind] || node.kind}</span></div>
    <h1>{recordText(node)}</h1></header>;
}


function NodeRecord({ node }) {
  const entries = Object.entries(node.content);
  return <section className="inspector-section"><h2>节点记录</h2><dl className="node-record">
    {entries.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{formatContent(value)}</dd></div>)}
  </dl></section>;
}


function formatContent(value) {
  return typeof value === "string" ? value : JSON.stringify(value);
}


function Relations({ node, nodes, edges, onSelect }) {
  const related = relatedRecords(node, nodes, edges);
  return <section className="inspector-section"><h2><GitBranch size={15} />直接关系</h2>{related.length ? <ul className="relation-list">
    {related.map(({ edge, adjacentId, record }) => <li key={edge.id}><button onClick={() => onSelect(adjacentId)}><span className={`polarity ${edge.polarity}`}>{relationLabel(edge.polarity)}</span><b>{record ? recordText(record) : adjacentId}</b></button></li>)}
  </ul> : <p className="muted">暂无关系</p>}</section>;
}


function relatedRecords(node, nodes, edges) {
  const byId = new Map(nodes.map((record) => [record.id, record]));
  return edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => {
    const adjacentId = edge.source === node.id ? edge.target : edge.source;
    return { edge, adjacentId, record: byId.get(adjacentId) };
  });
}


function relationLabel(polarity) {
  return { supports: "支持", refutes: "反驳", depends_on: "依赖" }[polarity] || polarity;
}


function Artifacts({ node, artifacts }) {
  const byId = new Map(artifacts.map((artifact) => [artifact.id, artifact]));
  const linked = node.artifact_ids.map((id) => ({ id, artifact: byId.get(id) }));
  if (!linked.length) return null;
  return <section className="inspector-section"><h2>关联 Artifact</h2><ul className="audit-evidence">
    {linked.map(({ id, artifact }) => <li key={id} className="mono">{artifact ? `${artifact.media_type} · ${id}` : id}</li>)}
  </ul></section>;
}


function NodeIdEntry({ node }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard.writeText(node.id); setCopied(true); };
  return <section className="inspector-section"><h2>节点 ID</h2><div className="node-id">
    <code className="mono">{node.id}</code><button className="icon-button" aria-label={copied ? "已复制节点 ID" : "复制节点 ID"} title={copied ? "已复制" : "复制节点 ID"} onClick={copy}>
      {copied ? <Check size={15} /> : <Copy size={15} />}</button></div></section>;
}
