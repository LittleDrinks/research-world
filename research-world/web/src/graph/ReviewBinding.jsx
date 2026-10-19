import {useEffect,useState} from 'react';
import {artifactViewUrl,getArtifactTemplates,listAgents,listReviewRules,saveReviewRule} from '../api';
import './reviews.css';

export function ReviewBinding({projectId,label,onClose}){
  const [options,setOptions]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[saved,setSaved]=useState(false);
  useEffect(()=>{let active=true;Promise.all([listAgents(),getArtifactTemplates(projectId),listReviewRules(projectId)]).then(([agents,schemas,rules])=>{if(active)setOptions({agents,schemas,rule:rules.find(r=>r.label_id===label.id)});}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[projectId,label.id]);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');setSaved(false);const values=new FormData(event.currentTarget);
    try{await saveReviewRule(projectId,label.id,{agent_id:values.get('agent_id'),schema_id:values.get('schema_id'),enabled:values.has('enabled')});setSaved(true);}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <section className="review-binding"><h3>添加「{label.name}」时启动独立复核</h3>
    {options&&<BindingForm options={options} projectId={projectId} submit={submit} busy={busy}/>}
    {error&&<p role="alert">{error}</p>}{saved&&<p role="status">绑定已保存。仅在此后新增标签时触发。</p>}
    <button className="text-link" onClick={onClose}>收起自动复核设置</button>
  </section>;
}

function BindingForm({options,projectId,submit,busy}){
  const {agents,schemas,rule}=options;
  return <form className="label-form" onSubmit={submit}>
    <label>复核 Agent<select name="agent_id" defaultValue={rule?.config.agent.id||'research-assistant'}>{agents.map(a=><option key={a.id} value={a.id}>{a.name} · {a.model}</option>)}</select></label>
    <label>报告模板<select name="schema_id" defaultValue={rule?.config.schema_id||schemas[0]?.id}>{schemas.map(s=><option key={s.id} value={s.id}>{s.title} · {s.max_reading_chars} 字符</option>)}</select></label>
    <div>{schemas.map(s=><a key={s.id} href={artifactViewUrl(projectId,s.id)} target="_blank" rel="noreferrer">查看{s.title}模板 ↗</a>)}</div>
    <label className="review-enable"><input type="checkbox" name="enabled" defaultChecked={rule?.enabled||false}/>启用：新增标签后自动调用模型</label>
    <p className="muted">保存时固定 Agent 配置。独立会话读取被审正文和附件，报告完成后回复到原记录。已有标签不会补跑。</p>
    <button className="button primary" disabled={busy||!agents.length||!schemas.length}>保存复核绑定</button>
  </form>;
}

export function ReviewTriggerNotice({rules,labels,selected,previous}){
  const pending=rules.filter(rule=>rule.enabled&&selected.includes(rule.label_id)&&!previous.includes(rule.label_id));
  if(!pending.length)return null;
  return <div className="review-trigger" role="note"><b>保存后将启动独立复核</b>{pending.map(rule=><p key={rule.id}>
    {labels.find(label=>label.id===rule.label_id)?.name} → {rule.config.agent.name} · {rule.config.agent.model}
  </p>)}<small>固定当前正文与附件，结果回到本记录。同一输入已有任务时不重复启动。</small></div>;
}
