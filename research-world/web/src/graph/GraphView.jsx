import { Background, Controls, MiniMap, MarkerType, ReactFlow, ReactFlowProvider, useReactFlow, useStore } from "@xyflow/react";
import { useEffect, useMemo, useState } from "react";
import { edgeHandles, layoutGraph } from "./layout";
import { ResearchNode } from "./ResearchNode";
import { JointNode } from "./JointCondition";
import { SignalEdge } from "./SignalEdge";


const NODE_TYPES = { research: ResearchNode, joint: JointNode };
const EDGE_TYPES = { signal: SignalEdge };
const EMPTY_LAYOUT = { signature: "", nodes: [], routes: new Map() };
const NODE_COLORS = Object.fromEntries(["question", "source", "direction", "experiment"].map(kind => [kind, `var(--kind-${kind})`]));


export function GraphView(props) {
  return <ReactFlowProvider><GraphCanvas {...props} /></ReactFlowProvider>;
}

function GraphCanvas({ nodes, edges, selectedId, onSelect }) {
  const [positions,setPositions]=useState({});
  const aspectRatio = useStore(state => state.height ? Math.max(.4, Math.round(10 * state.width / state.height) / 10) : 1);
  const signature = `${graphSignature(nodes, edges)}:${aspectRatio}`;
  const layout = useGraphLayout(nodes, edges, signature, aspectRatio);
  const flowNodes = useMemo(() => decorateNodes(layout.nodes, nodes, selectedId).map(n=>positions[n.id]?{...n,position:positions[n.id]}:n), [layout.nodes, nodes, selectedId,positions]);
  const flowEdges = useMemo(() => decorateEdges(edges, flowNodes, selectedId, layout.routes,positions), [edges, flowNodes, selectedId, layout.routes,positions]);
  const fit = { padding: .14, maxZoom: 1 };
  const moved=changes=>{const next=changes.filter(c=>c.type==='position'&&c.position);if(next.length)setPositions(p=>({...p,...Object.fromEntries(next.map(c=>[c.id,c.position]))}));};
  return <ReactFlow nodes={flowNodes} edges={flowEdges} nodeTypes={NODE_TYPES} edgeTypes={EDGE_TYPES} onNodesChange={moved} onNodeClick={(_, node) => onSelect(node.id)} nodesDraggable nodesConnectable={false} fitView fitViewOptions={fit} minZoom={.15} maxZoom={1.5} proOptions={{ hideAttribution: true }}>
    <FitOnChange signature={layout.signature} options={fit} />
    <Background gap={24} size={1} color="var(--graph-dot)" /><MiniMap pannable zoomable nodeColor={(node) => NODE_COLORS[node.data.kind] || "#4b5563"} maskColor="var(--minimap-mask)" /><Controls showInteractive={false} />
  </ReactFlow>;
}


function graphSignature(nodes, edges) {
  return `${nodes.map((node) => node.id).join("|")}::${edges.map((edge) => `${edge.source}>${edge.target}:${edge.polarity}`).join("|")}`;
}


function useGraphLayout(nodes, edges, signature, aspectRatio) {
  const [layout, setLayout] = useState(EMPTY_LAYOUT);
  useEffect(() => {
    let current = true;
    layoutGraph(nodes, edges, aspectRatio).then((value) => { if (current) setLayout({ signature, ...value }); });
    return () => { current = false; };
  }, [signature]);
  return layout.signature === signature ? layout : EMPTY_LAYOUT;
}


function decorateNodes(layout, nodes, selectedId) {
  const values = new Map(nodes.map((node) => [node.id, node]));
  return layout.map((node) => ({ ...node, selected: node.id === selectedId, data: values.get(node.id) }));
}


function decorateEdges(edges, nodes, selectedId, routes,positions) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  return edges.map((edge, index) => ({ id: `edge-${index}`, source: edge.source, target: edge.target,
    ...edgeHandles(edge, nodeMap), type: "signal", data: { ...edge, route: positions[edge.source]||positions[edge.target]?undefined:routes.get(`edge-${index}`),
      incident: [edge.source, edge.target, edge.jointId].includes(selectedId), muted: Boolean(selectedId) && ![edge.source, edge.target, edge.jointId].includes(selectedId) },
    markerEnd:{type:MarkerType.ArrowClosed,width:16,height:16,color:edge.polarity==='supports'?'var(--state-success)':edge.polarity==='refutes'?'var(--state-failed)':edge.polarity==='joint'?'var(--state-selected)':
      [edge.source,edge.target].includes(selectedId)?'var(--state-selected)':'var(--text-faint)'},
    style: { strokeWidth: [edge.source,edge.target].includes(selectedId)?2:1.5,
      strokeDasharray: edge.polarity === "refutes" ? "7 5" : undefined } }));
}


function FitOnChange({ signature, options }) {
  const { fitView } = useReactFlow();
  const size = useStore(state => `${state.width}:${state.height}`);
  useEffect(() => { if (signature) requestAnimationFrame(() => fitView(options)); }, [signature, size]);
  return null;
}
