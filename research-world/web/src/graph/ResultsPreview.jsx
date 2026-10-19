import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {artifactViewUrl,recordUrl,getLocalMap} from '../api';
import {useWorld} from '../context/WorldContext';

export function ResultsPreview(){
  const [open,setOpen]=useState(false),{projectId}=useWorld();
  const [map,setMap]=useState({records:[],artifacts:[]}),[error,setError]=useState('');
  useEffect(()=>{let active=true;if(open)getLocalMap(projectId,{limit:1000}).then(v=>{if(active)setMap(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[open,projectId]);
  const records=map.records.filter(r=>r.type!=='source'&&r.artifact_ids.length);
  const names=new Map(map.artifacts.map(a=>[a.id,a.media_type]));
  return <><button className="button secondary" onClick={()=>setOpen(true)}>成果预览</button>{open&&<Modal title="研究成果" open wide onClose={()=>setOpen(false)}>{error&&<p role="alert">{error}</p>}<div className="results-list">{records.map(r=><article key={r.id}><h3><a href={recordUrl(projectId,r.id)} target="_blank" rel="noreferrer">{r.content.title}</a></h3><div>{r.artifact_ids.map(id=><a key={id} href={artifactViewUrl(projectId,id)} target="_blank" rel="noreferrer">{r.content.attachments?.find(a=>a.id===id)?.name||names.get(id)}</a>)}</div></article>)}{!records.length&&<p>暂无产物。</p>}</div></Modal>}</>;
}
