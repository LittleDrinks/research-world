import {useState} from 'react';
import {changeRecord,recordUrl} from '../api';
import {useWorld} from '../context/WorldContext';
import {Modal} from '../components/Modal';

export const CLOSE_REASONS={completed:'已完成',not_planned:'不再推进',duplicate:'重复'};
export function RecordStatus({node}){
  const {projectId}=useWorld(),[open,setOpen]=useState(false),closed=node.content.status==='closed';
  return <div className="record-status"><span className={closed?'closed':'opened'}>{closed?`Closed · ${CLOSE_REASONS[node.content.close_reason]}`:'Open'}</span>
    {node.content.duplicate_of&&<a href={recordUrl(projectId,node.content.duplicate_of)}>查看保留节点</a>}
    <button className="button secondary" onClick={()=>setOpen(true)}>{closed?'重新打开':'关闭节点'}</button>
    {open&&<StatusDialog node={node} closed={closed} projectId={projectId} onClose={()=>setOpen(false)}/>}
  </div>;
}

function StatusDialog({node,closed,projectId,onClose}){
  const [reason,setReason]=useState('not_planned'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const submit=async e=>{e.preventDefault();const fields=Object.fromEntries(new FormData(e.currentTarget));setBusy(true);try{await changeRecord(projectId,node.id,{...fields,kind:'status',base_revision:node.revision,status:closed?'open':'closed'});onClose();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <Modal open title={closed?'重新打开研究节点':'关闭研究节点'} onClose={onClose}><form className="label-form" onSubmit={submit}>
    {!closed&&<label>关闭原因<select name="close_reason" value={reason} onChange={e=>setReason(e.target.value)}>{Object.entries(CLOSE_REASONS).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>}
    {!closed&&reason==='duplicate'&&<label>保留节点 ID<input name="duplicate_of" required placeholder="record:…"/></label>}
    <label>决定依据<textarea name="reason" required maxLength={500} rows={3}/></label>{error&&<p role="alert">{error}</p>}
    <button className="button primary" disabled={busy}>确认{closed?'重新打开':'关闭'}</button>
  </form></Modal>;
}
