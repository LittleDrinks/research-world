import { Position } from "@xyflow/react";


export const NODE_WIDTH = 280;
export const NODE_HEIGHT = 128;
const KIND_ORDER = ["question", "source", "direction", "experiment"];
const OPPOSITE = { top: "bottom", right: "left", bottom: "top", left: "right" };
const HANDLE_POINTS = [[Position.Top, NODE_WIDTH / 2, 0], [Position.Right, NODE_WIDTH, NODE_HEIGHT / 2],
  [Position.Bottom, NODE_WIDTH / 2, NODE_HEIGHT], [Position.Left, 0, NODE_HEIGHT / 2]];
const HANDLES = ["target", "source"].flatMap((type) => HANDLE_POINTS.map(([position, x, y]) => (
  { id: `${type}-${position}`, type, position, x, y, width: 1, height: 1 })));
const OPTIONS = { "elk.algorithm": "layered", "elk.direction": "RIGHT", "elk.edgeRouting": "ORTHOGONAL",
  "elk.partitioning.activate": "true", "elk.separateConnectedComponents": "false",
  "elk.spacing.nodeNode": "76", "elk.spacing.edgeNode": "32",
  "elk.layered.spacing.nodeNodeBetweenLayers": "150", "elk.layered.spacing.edgeNodeBetweenLayers": "32",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX", "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP" };
let elkEngine;


function validEdges(edges, nodeMap) {
  return edges.flatMap((edge,index)=>{
    if(!nodeMap.has(edge.source)||!nodeMap.has(edge.target))return [];
    const handles=edgeHandles(edge,nodeMap);
    return [{id:`edge-${index}`,sources:[`${edge.source}:${handles.sourceHandle.split('-')[1]}`],
      targets:[`${edge.target}:${handles.targetHandle.split('-')[1]}`]}];
  });
}

function ports(node){
  const sides={top:'NORTH',right:'EAST',bottom:'SOUTH',left:'WEST'};
  return HANDLE_POINTS.map(([side,x,y])=>({id:`${node.id}:${side}`,x,y,width:0,height:0,
    layoutOptions:{'elk.port.side':sides[side]}}));
}

function inputGraph(nodes, edges) {
  const nodeMap=new Map(nodes.map(node=>[node.id,node]));
  return {id:'research-graph',layoutOptions:OPTIONS,
    children:nodes.map(node=>({id:node.id,width:NODE_WIDTH,height:NODE_HEIGHT,ports:ports(node),
      layoutOptions:{'elk.partitioning.partition':String(KIND_ORDER.indexOf(node.kind)),'elk.portConstraints':'FIXED_POS'}})),
    edges:validEdges(edges,nodeMap)};
}


async function engine() {
  if (!elkEngine) { const { default: ELK } = await import("elkjs/lib/elk.bundled.js"); elkEngine = new ELK(); }
  return elkEngine;
}


function routePoints(edge) {
  const section = edge.sections?.[0];
  return section ? [section.startPoint, ...(section.bendPoints || []), section.endPoint] : [];
}


function edgeRoutes(edges) {
  return new Map((edges || []).map((edge) => [edge.id, routePoints(edge)]).filter(([, points]) => points.length > 1));
}


export async function layoutGraph(nodes, edges) {
  if (!nodes.length) return { nodes: [], routes: new Map() };
  const result = await (await engine()).layout(inputGraph(nodes, edges));
  return { nodes: result.children.map(flowNode), routes: edgeRoutes(result.edges) };
}


function flowNode(layout) {
  return { id: layout.id, type: "research", position: { x: layout.x, y: layout.y }, width: NODE_WIDTH, height: NODE_HEIGHT,
    measured: { width: NODE_WIDTH, height: NODE_HEIGHT }, handles: HANDLES };
}


export function edgeHandles(edge, nodeMap) {
  const source=nodeMap.get(edge.source),target=nodeMap.get(edge.target);
  if(!source||!target)return {};
  const sourceRank=KIND_ORDER.indexOf(source.kind||source.data?.kind);
  const targetRank=KIND_ORDER.indexOf(target.kind||target.data?.kind);
  const side=sourceRank===targetRank?'bottom':sourceRank<targetRank?'right':'left';
  return {sourceHandle:`source-${side}`,targetHandle:`target-${OPPOSITE[side]}`};
}
