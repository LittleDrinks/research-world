import { Handle,Position } from '@xyflow/react';
import { kindLabel,stateLabel } from './graph';
export default function KernelNode({data}){
  const {node,onSelect}=data;
  return <button className={`kernel-node kind-${node.kind}`} onClick={()=>onSelect(node)}>
    <Handle type="target" position={Position.Left}/>
    <span className="node-meta"><b>{kindLabel[node.kind]}</b><i>{node.provenance}</i></span>
    <strong>{node.title}</strong><span>{node.metric||stateLabel[node.state]||''}</span>
    <Handle type="source" position={Position.Right}/>
  </button>;
}
