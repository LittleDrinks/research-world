import '../settings.css';
import {useEffect,useState} from 'react';
import {useParams} from 'react-router-dom';
import {sessionDetail,turnUrl} from '../sessionApi';
import {useWorld} from '../context/WorldContext';

export function TracesPage(){
  const {runId:sessionId}=useParams(),{projectId,setError}=useWorld();
  const [detail,setDetail]=useState(null),[events,setEvents]=useState([]);
  useEffect(()=>{setEvents([]);setDetail(null);if(sessionId)sessionDetail(projectId,sessionId).then(setDetail).catch(e=>setError(e.message));},[sessionId,projectId]);
  async function inspect(turn){try{const response=await fetch(`${turnUrl(projectId,sessionId,turn.id)}/events`);if(!response.ok)throw new Error('无法读取轨迹');const text=await response.text();setEvents(text.split('\n').filter(l=>l.startsWith('data: ')).map(l=>JSON.parse(l.slice(6))));}catch(e){setError(e.message);}}
  return <section className="settings-page"><h1>工作轨迹</h1>{detail?<><p>{detail.session.title} · {detail.run.agent_snapshot.model}</p>{detail.run.turns.map(t=><button className="button secondary" key={t.id} onClick={()=>inspect(t)} disabled={t.status==='running'}>{t.status} · {t.id.slice(0,10)}</button>)}{events.map(e=><details key={e.seq}><summary>{e.seq} · {e.type}</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(e.data,null,2)}</pre></details>)}</>:<p>从侧栏选择一个对话查看轨迹。</p>}</section>;
}
