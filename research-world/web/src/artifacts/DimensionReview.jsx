import {EvidenceLinks} from './DocumentBody';

const states={unverified:'未核验',not_applicable:'不适用'};
const execution={executed:'有执行证据',not_executed:'未执行',unverified:'执行未核验',not_applicable:'无执行事项'};

export function DimensionReview({data,projectId,schema}){
  const scored=data.dimensions.filter(d=>d.result==='scored');
  return <section className="dimension-review" aria-label="六维评价"><header><h2>六维评价</h2>
    <span>{scored.length===6?`${scored.reduce((n,d)=>n+d.score,0)} / 12`:`已评 ${scored.length} / 6 维`}</span></header>
    <div className="dimension-overview" aria-label="六维评分概览">{data.dimensions.map(d=><div key={d.id}><span>{d.title}</span><strong>{d.result==='scored'?`${d.score} / 2`:states[d.result]}</strong></div>)}</div>
    <div className="execution-evidence"><b>{execution[data.execution.status]}</b><p>{data.execution.reason}</p>
      <EvidenceLinks items={data.execution.evidence} projectId={projectId}/></div>
    {data.dimensions.map((d,i)=><Dimension key={d.id} item={d} projectId={projectId} anchors={schema.properties.dimensions.prefixItems[i]['x-score-anchors']}/>)}
  </section>;
}

function Dimension({item,projectId,anchors}){
  return <article className={`dimension-item dimension-${item.result}`}><header><h3>{item.title}</h3>
    <strong>{item.result==='scored'?`${item.score} / 2`:states[item.result]}</strong></header>
    <p>{item.reason}</p>{item.improvement&&<p className="dimension-improvement"><b>下一步：</b>{item.improvement}</p>}
    <EvidenceLinks items={item.evidence} projectId={projectId}/>
    <details><summary>评分判据</summary><ol start="0">{anchors.map(a=><li key={a}>{a}</li>)}</ol></details>
  </article>;
}
