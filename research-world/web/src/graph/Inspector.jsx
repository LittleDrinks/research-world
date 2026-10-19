import { JointLinks } from './JointCondition';
import ReactMarkdown from 'react-markdown';
import { recordImpact } from '../api';
import { useWorld } from '../context/WorldContext';
import { Check, Copy, GitBranch, Trash2 } from "lucide-react";
import { useState } from "react";
import { Modal } from "../components/Modal";
import { ArtifactDownload } from "../components/map/ArtifactDownload";
import { KIND_LABELS, recordText } from "../utils/labels";
import {PublishDocument} from '../artifacts/PublishDocument';


export function Inspector({ node, nodes, edges, artifacts = [], conditions = [], onSelect, onDeleteRecord, onDeleteRelation }) {
  const {pending,setPending,busy,requestRemoval,confirm} = useRemoval(node,onDeleteRecord,onDeleteRelation);
  if (!node) return <aside className="inspector inspector-empty">选择节点查看上下文。</aside>;
  return <aside className="inspector"><div className="inspector-scroll"><NodeHeader node={node} />
    <NodeRecord node={node} /><RecordActions node={node} onRequest={requestRemoval} />
    <Relations node={node} nodes={nodes} edges={edges} onSelect={onSelect} onDelete={(edge) => setPending({ kind: "Relation", id: edge.id })} />
    <JointLinks conditions={conditions} recordId={node.id} onSelect={onSelect} />
    <section className="inspector-section"><PublishDocument node={node}/></section>
    <Artifacts node={node} artifacts={artifacts} /><details className="node-details"><summary>详情</summary><NodeIdEntry node={node} /></details>
  </div><DeleteDialog pending={pending} busy={busy} onClose={() => setPending(null)} onConfirm={confirm} /></aside>;
}


function NodeHeader({ node }) {
  return <header className="inspector-header"><div className="eyebrow"><span>{KIND_LABELS[node.kind] || node.kind}</span></div>
    <h1>{recordText(node)}</h1></header>;
}


function NodeRecord({ node }) {
  const extra = Object.entries(node.content).filter(([key]) => !['title','text','attachments','origin','note'].includes(key));
  return <section className="inspector-section node-body">
    <ReactMarkdown>{String(node.content.text || '')}</ReactMarkdown>
    {node.content.note&&<p className="muted">{String(node.content.note)}</p>}
    {extra.length>0&&<details className="node-details"><summary>来源与记录信息</summary><dl className="node-record">{extra.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{formatContent(value)}</dd></div>)}</dl></details>}
  </section>;
}

function formatContent(value) {
  return typeof value === "string" ? value : JSON.stringify(value);
}


function RecordActions({ node, onRequest }) {
  return <section className="inspector-section"><button className="button secondary" aria-label={`删除 Record ${node.id}`} title={`删除 Record ${node.id}`} onClick={onRequest}><Trash2 size={15} />撤销研究对象</button></section>;
}


function Relations({ node, nodes, edges, onSelect, onDelete }) {
  const related = relatedRecords(node, nodes, edges);
  return <section className="inspector-section"><h2><GitBranch size={15} />直接关系</h2>{related.length ? <ul className="relation-list">
    {related.map(({ edge, adjacentId, record }) => <li key={edge.id}><div className="relation-row"><button className="relation-link" onClick={() => onSelect(adjacentId)}><span className={`polarity ${edge.polarity}`}>{relationLabel(edge,node,record)}</span><b>{record ? recordText(record) : adjacentId}</b></button><button className="icon-button" aria-label={`删除 Relation ${edge.id}`} title={`删除 Relation ${edge.id}`} onClick={(event) => { event.stopPropagation(); onDelete(edge); }}><Trash2 size={15} /></button></div></li>)}
  </ul> : <p className="muted">暂无关系</p>}</section>;
}


function DeleteDialog({ pending, busy, onClose, onConfirm }) {
  if (!pending) return null;
  const kind = pending.kind;
  return <Modal title={`确认撤销 ${kind === "Record" ? "研究对象" : "关系"}`} open onClose={busy ? () => {} : onClose}>
    <div className="delete-confirmation"><p>撤销后不再用于后续研究，历史记录保留。</p><code className="mono">{pending.id}</code>
      {kind === "Record" ? <div><p>以下 {pending.affected.length} 个对象及其关联关系将不再可用，Artifact 保留：</p><ul>{pending.affected.map(record=><li key={record.id}>{record.content.title || record.id}</li>)}</ul></div> : <p>两端 Record 保持不变。</p>}
      <div className="form-actions"><button type="button" className="button secondary" disabled={busy} onClick={onClose}>取消</button><button type="button" className="button primary" disabled={busy} onClick={onConfirm}><Trash2 size={15} />{busy ? "撤销中..." : "确认撤销"}</button></div>
    </div>
  </Modal>;
}


function relatedRecords(node, nodes, edges) {
  const byId = new Map(nodes.map((record) => [record.id, record]));
  return edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => {
    const adjacentId = edge.source === node.id ? edge.target : edge.source;
    return { edge, adjacentId, record: byId.get(adjacentId) };
  });
}


function relationLabel(edge,node,record) {
  const outgoing=edge.source===node.id;
  if(['supports','refutes'].includes(edge.polarity)&&[node.kind,record?.kind].includes('question'))return '关系无效：问题不是证据';
  const labels={supports:['支持该节点','被该节点支持'],refutes:['反驳该节点','被该节点反驳'],depends_on:['依赖该节点','被该节点依赖']};
  return labels[edge.polarity]?.[outgoing?0:1]||edge.polarity;
}


function Artifacts({ node, artifacts }) {
  const byId = new Map(artifacts.map((artifact) => [artifact.id, artifact]));
  const names = new Map((Array.isArray(node.content.attachments) ? node.content.attachments : []).filter(value=>value && typeof value === "object").map(value => [value.id,value.name]));
  const linked = node.artifact_ids.map((id) => ({ id, name:names.get(id), artifact: byId.get(id) }));
  if (!linked.length) return null;
  return <details className="inspector-section node-details"><summary>研究资料（{linked.length}）</summary><ul className="audit-evidence">
    {linked.map(({ id, name, artifact }) => <li key={id}><span className="mono">{name || (artifact ? `${artifact.media_type} · ${id}` : id)}</span>{artifact && <ArtifactDownload artifact={artifact} />}</li>)}
  </ul></details>;
}


function NodeIdEntry({ node }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard.writeText(node.id); setCopied(true); };
  return <section className="inspector-section"><h2>节点 ID</h2><div className="node-id">
    <code className="mono">{node.id}</code><button className="icon-button" aria-label={copied ? "已复制节点 ID" : "复制节点 ID"} title={copied ? "已复制" : "复制节点 ID"} onClick={copy}>
      {copied ? <Check size={15} /> : <Copy size={15} />}</button></div></section>;
}

function useRemoval(node,onDeleteRecord,onDeleteRelation){
  const {projectId, setError} = useWorld();
  const requestRemoval = async () => {
    try { setPending({kind:"Record", id:node.id, affected:await recordImpact(projectId,node.id)}); }
    catch(error) { setError(error.message); }
  };
  const [pending, setPending] = useState(null);
  const [busy, setBusy] = useState(false);
  const confirm = async () => {
    if (!pending) return;
    setBusy(true);
    try { await (pending.kind === "Record" ? onDeleteRecord(pending.id) : onDeleteRelation(pending.id)); setPending(null); }
    catch { /* parent reports the failed operation */ }
    finally { setBusy(false); }
  };
  return {pending,setPending,busy,requestRemoval,confirm};
}
