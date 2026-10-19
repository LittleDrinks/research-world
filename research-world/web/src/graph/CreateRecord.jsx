import {useState} from 'react';
import {createRecord,preflightRecord,recordUrl} from '../api';
import {useWorld} from '../context/WorldContext';
import {Modal} from '../components/Modal';

export function CreateRecord({seed}){
  const [open,setOpen]=useState(false);
  return <><button className="button secondary" onClick={()=>setOpen(true)}>{seed?'提出相关方向':'新建节点'}</button>{open&&<CreationDialog seed={seed} onClose={()=>setOpen(false)}/>}</>;
}

function CreationDialog({seed,onClose}){
  const {projectId}=useWorld(),[kind,setKind]=useState('direction'),[check,setCheck]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[created,setCreated]=useState(null);
  const submit=async e=>{e.preventDefault();const form=new FormData(e.currentTarget),content={title:form.get('title'),text:form.get('text')};if(kind==='source')content.canonical_url=form.get('canonical_url');const body={type:kind,content};setBusy(true);setError('');
    try{if(!check){const result=await preflightRecord(projectId,body);if(result.matches.length){setCheck(result);return;}}else body.duplicate_resolution={reason:form.get('reason'),draft_hash:check.draft_hash,matches:Object.fromEntries(check.matches.map(m=>[m.id,m.revision]))};setCreated(await createRecord(projectId,body));}catch(e){if(e.detail?.matches)setCheck(e.detail);setError(e.message);}finally{setBusy(false);}};
  return <Modal title="创建研究节点" open wide onClose={onClose}>{created?<p>已创建：<a href={recordUrl(projectId,created.id)}>{created.content.title}</a></p>:<form className="label-form" onSubmit={submit}>
    <label>类型<select value={kind} onChange={e=>{setKind(e.target.value);setCheck(null);}}>{[['direction','方向'],['question','问题'],['source','来源'],['experiment','实验']].map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
    <label>标题<input name="title" required maxLength={200} defaultValue={seed?.title||''} onChange={()=>setCheck(null)}/></label>
    {kind==='source'&&<label>规范链接<input name="canonical_url" type="url" required placeholder="https://doi.org/…" onChange={()=>setCheck(null)}/></label>}
    <label>正文（Markdown）<textarea name="text" required rows={5} maxLength={20000} defaultValue={seed?.text||''} onChange={()=>setCheck(null)}/></label>
    {check&&<DuplicateNotice check={check} projectId={projectId}/>}{check&&<label>仍然创建的理由<input name="reason" required maxLength={500} placeholder="新增了什么条件、解释或预测？"/></label>}
    {error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy}>{busy?'检查中…':check?'说明差异并创建':'检查并创建'}</button>
  </form>}</Modal>;
}

function DuplicateNotice({check,projectId}){
  return <section className="creation-warning" role="status"><b>发现可能重复的节点</b><p>{check.method}</p>{check.matches.map(m=><article key={m.id}>
    <a href={recordUrl(projectId,m.id)} target="_blank" rel="noreferrer">{m.title} · r{m.revision}</a><p>{m.reason} · 文本相似度 {m.score.toFixed(3)}</p><p>{m.text}</p><a href={recordUrl(projectId,m.id)} target="_blank" rel="noreferrer">打开已有节点补充</a>
  </article>)}</section>;
}
