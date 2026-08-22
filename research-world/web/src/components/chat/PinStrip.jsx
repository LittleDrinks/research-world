import { Pin, X } from "lucide-react";
import { useState } from "react";
import { nodeText, shortId } from "../../utils/labels";
import { NodePeek } from "./NodePeek";


export function PinStrip({ nodes, onRemove }) {
  const [peekId, setPeekId] = useState("");
  if (!nodes.length) return null;
  return <section className="pin-strip" aria-label="钉住的节点">
    <div className="pin-chips">{nodes.map((node) => <PinChip key={node.id} node={node} active={peekId === node.id}
      onToggle={() => setPeekId(peekId === node.id ? "" : node.id)} onRemove={() => onRemove(node.id)} />)}</div>
    {peekId && <NodePeek nodeId={peekId} />}</section>;
}


function PinChip({ node, active, onToggle, onRemove }) {
  return <span className={`pin-chip kind-${node.kind} ${active ? "active" : ""}`}>
    <button className="pin-chip-main" onClick={onToggle} title={nodeText(node)}>
      <Pin size={11} /><b className="mono">{shortId(node.id)}</b><em>{nodeText(node)}</em></button>
    <button className="pin-chip-remove" aria-label={`移除 ${shortId(node.id)}`} onClick={onRemove}><X size={12} /></button></span>;
}
