import {useState} from 'react';
import {useWorld} from '../context/WorldContext';
import {Modal} from './Modal';

export function DeleteProjectDialog({project,onClose}){
  const {removeProject}=useWorld();
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const close=()=>{if(!busy){setError('');onClose();}};
  const confirm=async()=>{
    setBusy(true);setError('');
    try{await removeProject(project.id);onClose();}catch(error){setError(error.message);}finally{setBusy(false);}
  };
  return <Modal title="删除项目" open={Boolean(project)} onClose={close}>
    <p>确定永久删除「{project?.name}」？</p>
    <p>该项目的研究图谱、附件、对话、工作轨迹和工作目录将被删除，无法恢复。</p>
    {error&&<p role="alert">{error}</p>}
    <div className="form-actions"><button className="button secondary" disabled={busy} onClick={close}>取消</button><button className="button primary" disabled={busy} onClick={confirm}>{busy?'正在删除…':'永久删除'}</button></div>
  </Modal>;
}
