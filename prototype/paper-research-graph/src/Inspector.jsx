import { ExternalLink,X } from 'lucide-react';
import { connectedEdges,kindLabel,relatedNodes,stateLabel } from './graph';
export default function Inspector({paper,node,onClose}){
  if(!node)return <aside className="inspector empty"><span>选择节点查看原文依据</span></aside>;
  const edges=connectedEdges(paper,node.id),related=relatedNodes(paper,node.id);
  return <aside className="inspector"><header><span className={`kind-chip kind-${node.kind}`}>{kindLabel[node.kind]}</span><button title="关闭检查器" onClick={onClose}><X size={17}/></button></header>
    <h2>{node.title}</h2><p>{node.body}</p>{node.metric&&<div className="metric">{node.metric}</div>}
    <dl><dt>状态</dt><dd>{stateLabel[node.state]||'—'}</dd><dt>来源性质</dt><dd className={node.provenance}>{node.provenance}</dd><dt>原文定位</dt><dd>{node.locator}</dd></dl>
    <a href={paper.paper.sourceUrl} target="_blank" rel="noreferrer">打开论文原文 <ExternalLink size={15}/></a>
    <h3>关系</h3><ul>{edges.map((edge,index)=><li key={index}><b>{edge.relation}</b><span>{edge.provenance}</span></li>)}</ul>
    <h3>相邻节点</h3><ul>{related.map(item=><li key={item.id}>{item.title}</li>)}</ul>
  </aside>;
}
