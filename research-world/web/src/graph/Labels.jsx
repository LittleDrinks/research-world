import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {changeRecord,listLabels,saveLabel,removeLabel} from '../api';
import './changes.css';

export function LabelBadge({label}){
  return <span className="research-label" style={{'--label-color':label.color}} title={label.description||label.name}>{label.name}</span>;
}

export function LabelManager(){
  const [open,setOpen]=useState(false);
  return <><button className="button secondary" onClick={()=>setOpen(true)}>管理标签</button>
    {open&&<LabelDialog onClose={()=>setOpen(false)}/>}</>;
}

function LabelDialog({onClose}){
  const {projectId}=useWorld(),[labels,setLabels]=useState([]),[editing,setEditing]=useState(null),[error,setError]=useState(''),[pending,setPending]=useState(null);
  const refresh=()=>listLabels(projectId).then(setLabels);
  useEffect(()=>{refresh().catch(e=>setError(e.message));},[projectId]);
  const remove=async()=>{try{await removeLabel(projectId,pending.id);setPending(null);await refresh();}catch(e){setError(e.message);}};
  return <Modal title="项目标签" open onClose={onClose}><p className="muted">名称和颜色由你定义。标签可以并存，用来表达研究动作与关注点。</p>
    {error&&<p role="alert">{error}</p>}<ul className="label-manager-list">{labels.map(label=><li key={label.id}>
      <div><LabelBadge label={label}/><p>{label.description}</p></div><button onClick={()=>{setEditing(label);setPending(null);}}>编辑</button><button onClick={()=>setPending(label)}>删除</button></li>)}</ul>
    {pending&&<div className="label-delete"><p>删除「{pending.name}」会移除当前关联，历史版本保留。</p><button onClick={remove}>确认删除标签</button><button onClick={()=>setPending(null)}>取消</button></div>}
    <LabelForm key={editing?.id||'new'} label={editing} onCancel={()=>setEditing(null)} onSave={async body=>{await saveLabel(projectId,body,editing?.id);setEditing(null);await refresh();}}/>
  </Modal>;
}

function LabelForm({label,onSave,onCancel}){
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');const form=event.currentTarget,values=Object.fromEntries(new FormData(form));
    try{await onSave(values);form.reset();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <form className="label-form" onSubmit={submit}><h3>{label?'编辑标签':'新建标签'}</h3>
    <label>标签名称<input name="name" required maxLength={40} defaultValue={label?.name||''}/></label>
    <label>标签颜色<input name="color" type="color" defaultValue={label?.color||'#4c78a8'}/></label>
    <label>标签说明<textarea aria-label="标签说明" name="description" maxLength={300} defaultValue={label?.description||''}/></label>
    {error&&<p role="alert">{error}</p>}<div className="form-actions"><button className="button primary" disabled={busy}>{label?'保存标签':'创建标签'}</button>{label&&<button type="button" onClick={onCancel}>取消编辑</button>}</div>
  </form>;
}

export function RecordLabels({node}){
  const [open,setOpen]=useState(false);
  return <section className="record-labels"><div className="record-label-badges">{node.labels?.map(label=><LabelBadge key={label.id} label={label}/>)}</div>
    <button className="text-link" onClick={()=>setOpen(true)}>设置标签</button>
    {open&&<AssignLabels node={node} onClose={()=>setOpen(false)}/>}</section>;
}

function AssignLabels({node,onClose}){
  const {projectId}=useWorld(),[labels,setLabels]=useState([]),[ids,setIds]=useState(node.labels.map(l=>l.id)),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [base]=useState(node.revision);
  useEffect(()=>{listLabels(projectId).then(setLabels).catch(e=>setError(e.message));},[projectId]);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');try{await changeRecord(projectId,node.id,{kind:'labels',base_revision:base,reason:new FormData(event.currentTarget).get('reason'),label_ids:ids});onClose();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <Modal title="设置研究标签" open onClose={busy?()=>{}:onClose}><form onSubmit={submit} className="label-form">
    <p className="muted">基于 r{base} · 不同标签可同时使用。</p><div className="label-options">{labels.map(label=><label key={label.id}>
      <input type="checkbox" checked={ids.includes(label.id)} onChange={e=>setIds(e.target.checked?[...ids,label.id]:ids.filter(id=>id!==label.id))}/><LabelBadge label={label}/><small>{label.description}</small></label>)}</div>
    {!labels.length&&<p>尚无标签，请先在地图工具栏创建。</p>}<label>变更原因<input name="reason" required maxLength={500} placeholder="为什么添加或移除这些标签？"/></label>
    {error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy}>保存标签关联</button>
  </form></Modal>;
}
