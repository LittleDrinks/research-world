import { useMemo,useState } from 'react';
import { kindLabel,stateLabel } from './graph';
function EvidenceItem({node,onSelect}){return <button className={`evidence-row state-${node.state}`} onClick={()=>onSelect(node)}><span>{node.title}</span><b>{node.metric||stateLabel[node.state]}</b></button>}
export default function ClaimView({paper,onSelect}){
  const claims=useMemo(()=>paper.nodes.filter(node=>node.kind==='claim'),[paper]);
  const [claimId,setClaimId]=useState(claims[0]?.id);
  const claim=claims.find(node=>node.id===claimId)||claims[0];
  const evidence=paper.nodes.filter(node=>node.kind==='evidence');
  const work=paper.nodes.filter(node=>['investigation','decision'].includes(node.kind));
  return <section className="claim-view">
    <nav className="claim-rail">{claims.map(item=><button className={item.id===claim?.id?'active':''} key={item.id} onClick={()=>{setClaimId(item.id);onSelect(item)}}><span>{kindLabel.claim}</span>{item.title}</button>)}</nav>
    <div className="claim-focus"><span className="eyebrow">{claim?.provenance}</span><h2>{claim?.title||paper.thesis}</h2><p>{claim?.body||paper.thesis}</p><div className="claim-state">{stateLabel[claim?.state]||'论文主结论'}</div></div>
    <div className="evidence-stack"><h3>证据</h3>{evidence.map(node=><EvidenceItem key={node.id} node={node} onSelect={onSelect}/>)}</div>
    <div className="work-strip"><h3>研究行动与决策</h3>{work.map(node=><button key={node.id} onClick={()=>onSelect(node)}><i className={`dot kind-${node.kind}`}/><span>{node.title}</span><small>{stateLabel[node.state]}</small></button>)}</div>
  </section>;
}
