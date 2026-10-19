import {useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {recordUrl,selectCandidates} from '../api';

export function CandidateSelection({records}){
  const [open,setOpen]=useState(false);
  return <><button className="button secondary" disabled={!records.length} onClick={()=>setOpen(true)}>MMR 选择阅读候选</button>{open&&<SelectionDialog records={records} onClose={()=>setOpen(false)}/>}</>;
}

function SelectionDialog({records,onClose}){
  const {projectId}=useWorld(),[result,setResult]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setBusy(true);setError('');
    try{setResult(await selectCandidates(projectId,selectionInput(records,String(form.get('query')),Number(form.get('count')),Number(form.get('weight')))));}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <Modal title="MMR 文献选择" open wide onClose={onClose}><form className="label-form" onSubmit={submit}><label>检索主题<input name="query" required defaultValue="solar system orbit gravitational dynamics integrator symplectic energy"/></label>
    <label>选择数量<input name="count" type="number" min={1} max={records.length} defaultValue={Math.min(4,records.length)}/></label><label>多样性权重<input name="weight" type="number" min={0} max={1} step={.05} defaultValue={.65}/></label>
    <p className="muted">相关性采用标题关键词命中率，相似度采用标题词集合 Jaccard。分数用于安排阅读顺序。</p><button className="button primary" disabled={busy}>{busy?'计算中…':'运行选择'}</button></form>
    {error&&<p role="alert">{error}</p>}{result&&<div className="markdown-table-scroll"><table><thead><tr><th>顺序</th><th>文献</th><th>相关性</th><th>重复性</th><th>得分</th></tr></thead><tbody>{result.steps.map((s,i)=><tr key={s.id}><td>{i+1}</td><td><a href={recordUrl(projectId,s.id)} target="_blank" rel="noreferrer">{records.find(r=>r.id===s.id)?.content.title}</a></td><td>{s.relevance.toFixed(3)}</td><td>{s.redundancy.toFixed(3)}</td><td>{s.score.toFixed(3)}</td></tr>)}</tbody></table></div>}
  </Modal>;
}

function terms(text){
  const stop=new Set(['a','an','the','of','and','for','in','to','with','on','from','by','over','as']);
  return new Set((text.toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(t=>!stop.has(t)));
}

function selectionInput(records,query,count,weight){
  const tokens=new Map(records.map(r=>[r.id,terms(r.content.title)])),wanted=terms(query);
  const overlap=(a,b)=>[...a].filter(x=>b.has(x)).length;
  const candidates=records.map(r=>({id:r.id,title:r.content.title,relevance:wanted.size?overlap(tokens.get(r.id),wanted)/wanted.size:0}));
  const similarities=Object.fromEntries([...tokens].map(([a,x])=>[a,Object.fromEntries([...tokens].filter(([b])=>a!==b).map(([b,y])=>[b,new Set([...x,...y]).size?overlap(x,y)/new Set([...x,...y]).size:0]))]));
  return {candidates,similarities,count,diversity_weight:weight};
}
