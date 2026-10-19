import {useState} from 'react';
import {Trash2} from 'lucide-react';
import {Modal} from './Modal';
import {deleteAgent} from '../sessionApi';

export function DeleteAgent({agent,saved,onDeleted}){
  const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const disabled=!saved||agent.id==='research-assistant';
  const remove=async()=>{setBusy(true);setError('');try{await deleteAgent(agent.id);await onDeleted();setOpen(false);}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <><button className="button secondary agent-delete" disabled={disabled} title={!saved?'请先保存配置':disabled?'内置研究助手不能删除':'删除此配置'} onClick={()=>setOpen(true)}><Trash2 size={15}/>删除配置</button>
    <Modal title="删除 Agent 配置" open={open} onClose={()=>!busy&&setOpen(false)}><p>删除「{agent.name}」？已有会话保留启动时的配置和历史记录。</p>
      {error&&<p role="alert">{error}</p>}<div className="form-actions"><button className="button secondary" disabled={busy} onClick={()=>setOpen(false)}>取消</button><button className="button primary" disabled={busy} onClick={remove}>{busy?'删除中…':'确认删除配置'}</button></div>
    </Modal></>;
}
