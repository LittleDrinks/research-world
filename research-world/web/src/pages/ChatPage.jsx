import {useEffect,useRef,useState} from 'react';
import {useNavigate,useParams} from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {createSession,sessionDetail,sendMessage,turnUrl,cancelTurn} from '../sessionApi';
import {useWorld} from '../context/WorldContext';
import '../chat.css';

export function ChatPage() {
  const {threadId:sessionId}=useParams();
  const {projectId,data,refresh,setError}=useWorld();
  const navigate=useNavigate();
  const [detail,setDetail]=useState(null),[draft,setDraft]=useState(''),[events,setEvents]=useState([]),[busy,setBusy]=useState(false);
  const [agent,setAgent]=useState('research-assistant');
  const source=useRef(null);
  const load=()=>sessionDetail(projectId,sessionId).then(setDetail);
  useEffect(()=>{setDetail(null);setEvents([]);if(sessionId)load().catch(e=>setError(e.message));return()=>source.current?.close();},[sessionId,projectId]);
  const active=detail?.run.turns.find(t=>t.status==='running');
  useEffect(()=>{if(active)watch(active.id);},[active?.id]);
  async function create(){try{const s=await createSession(projectId,agent);await refresh();navigate(`/chat/${s.id}`);}catch(e){setError(e.message);}}
  function watch(turn){source.current?.close();setEvents([]);const stream=new EventSource(`${turnUrl(projectId,sessionId,turn)}/events`);source.current=stream;
    for(const kind of ['delta','tool','tool_call','tool_result','child_result','turn_start','turn_end','reasoning']) stream.addEventListener(kind,e=>{const value=JSON.parse(e.data);setEvents(v=>v.some(x=>x.seq===value.seq)?v:[...v,value]);if(kind==='turn_end'){stream.close();setBusy(false);load().catch(e=>setError(e.message));refresh();}});
    stream.onerror=()=>{stream.close();setBusy(false);load().catch(e=>setError(e.message));};
  }
  async function send(event){event.preventDefault();if(!draft.trim())return;setBusy(true);try{const result=await sendMessage(projectId,sessionId,draft,crypto.randomUUID());setDraft('');await load();watch(result.turn.id);}catch(e){setBusy(false);setError(e.message);}}
  return <section className="pi-chat"><header><h1>{detail?.session.title||'研究对话'}</h1><select aria-label="启动 Agent" value={agent} onChange={e=>setAgent(e.target.value)}>{data.agents.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select><button className="button secondary" onClick={create}>新建对话</button></header>
    {detail?<><Conversation detail={detail} events={events}/><form className="pi-composer" onSubmit={send}><textarea aria-label="研究消息" value={draft} onChange={e=>setDraft(e.target.value)} placeholder="输入研究问题；可要求独立审查并保存方向到研究地图"/><button className="button primary" disabled={busy||Boolean(active)||!draft.trim()}>发送</button>{active&&<button type="button" onClick={()=>cancelTurn(projectId,sessionId,active.id).then(load)}>取消</button>}</form></>:<p>选择 Agent，点击“新建对话”开始研究。</p>}</section>;
}

function Conversation({detail,events}) {
  const streaming=events.filter(e=>e.type==='delta').map(e=>e.data.text||'').join('');
  const ended=events.some(e=>e.type==='turn_end');
  return <div className="pi-messages">{detail.session.messages.map(message=>{
    const turn=detail.run.turns.find(t=>t.message_id===message.id);
    return <article key={message.id}><div className="pi-user"><ReactMarkdown>{message.content}</ReactMarkdown></div>
      {message.assistant_response&&<ReactMarkdown>{message.assistant_response}</ReactMarkdown>}
      {turn?.status==='error'&&<p role="alert">本轮执行失败。可在轨迹中查看详情后重试。</p>}</article>;
  })}{streaming&&!ended&&<ReactMarkdown>{streaming}</ReactMarkdown>}
    {events.length>0&&<details><summary>本轮工作过程 · {events.length} 条事件</summary>{events.filter(e=>!['delta','reasoning'].includes(e.type)).map(e=><pre key={e.seq}>{JSON.stringify(e,null,2)}</pre>)}</details>}
  </div>;
}
