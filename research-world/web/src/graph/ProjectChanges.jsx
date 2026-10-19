import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {listChanges} from '../api';
import {ChangeHistory} from './ChangeHistory';

export function ProjectChanges({onSelect}){
  const [open,setOpen]=useState(false);
  return <><button className="button secondary" onClick={()=>setOpen(true)}>Changes</button>
    {open&&<ChangeDialog onClose={()=>setOpen(false)} onSelect={id=>{setOpen(false);onSelect(id);}}/>}</>;
}

function ChangeDialog({onClose,onSelect}){
  const {projectId}=useWorld(),[changes,setChanges]=useState([]),[error,setError]=useState('');
  useEffect(()=>{let active=true;listChanges(projectId).then(v=>{if(active)setChanges(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[projectId]);
  return <Modal title="项目 Changes" open wide onClose={onClose}><p className="muted">每次修改与讨论都保留目标、理由和版本。标签不触发流程阶段。</p>
    {error&&<p role="alert">{error}</p>}<ChangeHistory changes={changes} projectId={projectId} onSelect={onSelect}/></Modal>;
}
