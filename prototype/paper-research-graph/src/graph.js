export const kinds=['question','decision','investigation','evidence','claim'];
export const kindLabel={question:'问题',decision:'决策',investigation:'研究行动',evidence:'证据',claim:'主张'};
export const stateLabel={supported:'已支持',refuted:'已推翻',accepted:'已采纳',completed:'已完成',supporting:'支持',contradicting:'反证',qualifying:'限定',inconclusive:'未定'};
export const categories=['formal-proof','benchmark','numerical-simulation','observation','wet-lab','human-clinical'];
export const categoryLabel={'formal-proof':'形式证明','benchmark':'科学 Benchmark','numerical-simulation':'数值模拟','observation':'科学观测','wet-lab':'湿实验','human-clinical':'临床 / 人类数据'};
export const displayTitle=text=>text.replaceAll('$','');
const columnX={question:0,decision:300,investigation:600,evidence:900,claim:1200};
export function visiblePaper(paper,showInferred){
  const nodes=paper.nodes.filter(node=>showInferred||node.provenance==='explicit');
  const ids=new Set(nodes.map(node=>node.id));
  return {...paper,nodes,edges:paper.edges.filter(edge=>ids.has(edge.from)&&ids.has(edge.to)&&(showInferred||edge.provenance==='explicit'))};
}
export function flowNodes(paper,onSelect){
  return paper.nodes.map(node=>({id:node.id,type:'kernel',position:{x:columnX[node.kind],y:paper.nodes.filter(item=>item.kind===node.kind).findIndex(item=>item.id===node.id)*154},data:{node,onSelect}}));
}
export function flowEdges(paper){
  return paper.edges.map((edge,index)=>({id:`${edge.from}-${edge.to}-${index}`,source:edge.from,target:edge.to,label:edge.relation,animated:edge.relation==='refutes',className:edge.provenance,markerEnd:{type:'arrowclosed'}}));
}
export function connectedEdges(paper,nodeId){return paper.edges.filter(edge=>edge.from===nodeId||edge.to===nodeId);}
export function relatedNodes(paper,nodeId){
  const ids=new Set(connectedEdges(paper,nodeId).flatMap(edge=>[edge.from,edge.to]));
  return paper.nodes.filter(node=>ids.has(node.id)&&node.id!==nodeId);
}
