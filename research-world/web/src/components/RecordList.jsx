import {Trash2} from 'lucide-react';
import {useNavigate,useParams} from 'react-router-dom';
import {useState} from 'react';
import {useWorld} from '../context/WorldContext';
import {deleteSession} from '../sessionApi';
import {Modal} from './Modal';

export function RecordList({module,close}) {
  const {data,projectId,refresh,setError}=useWorld(),navigate=useNavigate(),params=useParams();
  const [pending,setPending]=useState(null),[busy,setBusy]=useState(false);
  const sessions=module==='/chat'||module==='/traces';
  const values=sessions?data.sessions:module==='/agents'?data.agents:[];
  const remove=async()=>{setBusy(true);try{await deleteSession(projectId,pending.id);if([params.threadId,params.runId].includes(pending.id))navigate(module);setPending(null);await refresh();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <section className="record-list"><div className="record-items">{values.map(value=><div className="session-row" key={value.id}>
    <button className="record-item" title={value.title||value.name} onClick={()=>{navigate(`${module}/${value.id}`);close();}}><span>{value.title||value.name}</span></button>
    {sessions&&<button className="icon-button session-delete" aria-label={`删除对话 ${value.title}`} onClick={()=>setPending(value)}><Trash2 size={15}/></button>}
  </div>)}</div><Modal title="删除对话" open={Boolean(pending)} onClose={()=>!busy&&setPending(null)}><p>删除“{pending?.title}”？正在运行的任务将停止，研究图谱和历史轨迹保留。</p><div className="form-actions"><button className="button secondary" disabled={busy} onClick={()=>setPending(null)}>取消</button><button className="button primary" disabled={busy} onClick={remove}>确认删除</button></div></Modal></section>;
}
