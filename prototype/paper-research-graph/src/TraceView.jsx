import { kindLabel,stateLabel } from './graph';
function Relations({paper,node}){
  const outgoing=paper.edges.filter(edge=>edge.from===node.id);
  return <div className="trace-relations">{outgoing.map((edge,index)=><span className={edge.provenance} key={`${edge.to}-${index}`}>{edge.relation} → {paper.nodes.find(item=>item.id===edge.to)?.title}</span>)}</div>;
}
export default function TraceView({paper,onSelect}){
  return <section className="trace-view"><div className="trace-line"/>{paper.nodes.map((node,index)=><article key={node.id} className={`trace-item side-${index%2}`}>
    <button className={`trace-node kind-${node.kind}`} onClick={()=>onSelect(node)}><span>{kindLabel[node.kind]} · {node.provenance}</span><strong>{node.title}</strong><p>{node.body}</p><small>{node.metric||stateLabel[node.state]||''}</small></button>
    <Relations paper={paper} node={node}/>
  </article>)}</section>;
}
