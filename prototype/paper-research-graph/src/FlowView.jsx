import { Background,Controls,ReactFlow } from '@xyflow/react';
import KernelNode from './KernelNode';
import { flowEdges,flowNodes,kindLabel,kinds } from './graph';
const nodeTypes={kernel:KernelNode};
export default function FlowView({paper,onSelect}){
  return <section className="flow-view">
    <div className="lane-labels">{kinds.map(kind=><span key={kind}>{kindLabel[kind]}</span>)}</div>
    <ReactFlow nodes={flowNodes(paper,onSelect)} edges={flowEdges(paper)} nodeTypes={nodeTypes} fitView fitViewOptions={{padding:.12}} minZoom={.35} maxZoom={1.4}>
      <Background color="#d7dde4" gap={24}/><Controls showInteractive={false}/>
    </ReactFlow>
  </section>;
}
