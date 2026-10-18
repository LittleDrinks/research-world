import { Position } from "@xyflow/react";
import { layoutComponents } from "./packComponents.js";


export const NODE_WIDTH = 280;
export const NODE_HEIGHT = 128;
const KIND_ORDER = ["question", "source", "direction", "experiment"];
const OPPOSITE = { top: "bottom", right: "left", bottom: "top", left: "right" };
function dimensions(node) {
  return node.kind === 'joint' ? {width:112,height:64} : {width:NODE_WIDTH,height:NODE_HEIGHT};
}
function handlePoints(node) {
  const {width,height} = dimensions(node);
  return [[Position.Top,width/2,0],[Position.Right,width,height/2],[Position.Bottom,width/2,height],[Position.Left,0,height/2]];
}
const OPTIONS = { "elk.algorithm": "layered", "elk.direction": "RIGHT", "elk.edgeRouting": "ORTHOGONAL",
  "elk.partitioning.activate": "false", "elk.separateConnectedComponents": "true",
  "elk.spacing.componentComponent": "100",
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
  return handlePoints(node).map(([side,x,y])=>({id:`${node.id}:${side}`,x,y,width:0,height:0,
    layoutOptions:{'elk.port.side':sides[side]}}));
}

function inputGraph(nodes, edges, aspectRatio) {
  const nodeMap=new Map(nodes.map(node=>[node.id,node]));
  return {id:'research-graph',layoutOptions:{...OPTIONS,'elk.aspectRatio':String(aspectRatio)},
    children:nodes.map(node=>({id:node.id,...dimensions(node),ports:ports(node),
      layoutOptions:{'elk.portConstraints':'FIXED_POS'}})),
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


export async function layoutGraph(nodes, edges, aspectRatio = 1.3) {
  if (!nodes.length) return { nodes: [], routes: new Map() };
  const result = await layoutComponents(await engine(), inputGraph(nodes, edges, aspectRatio), nodes, edges, aspectRatio);
  return { nodes: result.children.map(child => flowNode(child, nodes.find(node => node.id === child.id))), routes: edgeRoutes(result.edges) };
}


function flowNode(layout, node) {
  const size = dimensions(node);
  const handles = ['target','source'].flatMap(type=>handlePoints(node).map(([position,x,y])=>
    ({id:`${type}-${position}`,type,position,x,y,width:1,height:1})));
  return {id:layout.id,type:node.kind==='joint'?'joint':'research',position:{x:layout.x,y:layout.y},
    ...size,measured:size,handles};
}

export function edgeHandles(edge, nodeMap) {
  if (edge.polarity === 'joint') return {sourceHandle:'source-right',targetHandle:'target-left'};
  const source=nodeMap.get(edge.source),target=nodeMap.get(edge.target);
  if(!source||!target)return {};
  const sourceRank=KIND_ORDER.indexOf(source.kind||source.data?.kind);
  const targetRank=KIND_ORDER.indexOf(target.kind||target.data?.kind);
  const side=sourceRank===targetRank?'bottom':sourceRank<targetRank?'right':'left';
  return {sourceHandle:`source-${side}`,targetHandle:`target-${OPPOSITE[side]}`};
}
