import { Handle, Position } from '@xyflow/react';
import { artifactUrl } from '../api';
import { useWorld } from '../context/WorldContext';
import { recordText } from '../utils/labels';

export function ruleLabel(condition) {
  return condition.rule === 'k-of-N' ? `${condition.k} / ${condition.members.length}` : condition.rule;
}

export function ruleMeaning(condition) {
  if (condition.rule === 'AND') return `全部 ${condition.members.length} 项共同满足`;
  if (condition.rule === 'OR') return '至少满足其中一项';
  return `${condition.members.length} 项中至少满足 ${condition.k} 项`;
}

export function JointNode({ data, selected }) {
  const condition = data.condition;
  return <article className={`joint-node ${selected ? 'selected' : ''}`} aria-label={`${condition.rule} 联合条件：${condition.title}`}>
    <Handle type="target" position={Position.Left} id="target-left" className="hidden-handle" />
    <strong>{ruleLabel(condition)}</strong><span>{condition.title}</span>
    <small>{condition.unavailable_ids.length ? '引用不再可用 · 待复核' : '联合条件 · 未经审计'}</small>
    <Handle type="source" position={Position.Right} id="source-right" className="hidden-handle" />
  </article>;
}

export function JointInspector({ condition, nodes, onSelect }) {
  const { projectId } = useWorld();
  return <aside className="inspector joint-inspector"><div className="inspector-scroll">
    <header className="inspector-header"><div className="eyebrow"><span>联合条件 · {ruleLabel(condition)}</span></div><h1>{condition.title}</h1></header>
    <p className="joint-rule">{ruleMeaning(condition)}</p><p className="muted">关系表达尚未经审计，不代表条件或结论已经成立。</p>
    {condition.unavailable_ids.length > 0 && <p className="joint-warning" role="status">部分研究对象已撤销，需重新核查此关系。</p>}
    <section className="inspector-section"><h2>目标陈述</h2><p>{condition.statement}</p><RecordLink id={condition.target_id} nodes={nodes} onSelect={onSelect} /></section>
    <section className="inspector-section"><h2>参与条件</h2><ol className="joint-members">{condition.members.map(member => <li key={member.record_id}><b>{member.role}</b><RecordLink id={member.record_id} nodes={nodes} onSelect={onSelect} /></li>)}</ol></section>
    <section className="inspector-section"><h2>为何组合</h2><p>{condition.rationale}</p></section>
    <section className="inspector-section"><h2>证据定位</h2>{condition.evidence.map((evidence, index) => <div className="joint-evidence" key={index}><p>{evidence.locator}</p><a href={artifactUrl(projectId, evidence.artifact_id)} target="_blank" rel="noreferrer">查看原文 ↗</a></div>)}</section>
  </div></aside>;
}

function RecordLink({ id, nodes, onSelect }) {
  const record = nodes.find(node => node.id === id);
  if (!record) return <span className="joint-warning">研究对象已撤销</span>;
  return <button className="joint-record-link" onClick={() => onSelect(id)}>{recordText(record)} →</button>;
}

export function JointLinks({ conditions, recordId, onSelect }) {
  const related = recordId ? conditions.filter(c => c.target_id === recordId || c.members.some(m => m.record_id === recordId)) : conditions;
  if (!related.length) return null;
  return <section className="inspector-section joint-links"><h2>联合条件</h2>{related.map(condition => <button key={condition.id} onClick={() => onSelect(condition.id)} className="joint-list-item">
    <span className="joint-badge">{ruleLabel(condition)}</span><span><b>{condition.title}</b><small>{ruleMeaning(condition)}</small></span>
  </button>)}</section>;
}
