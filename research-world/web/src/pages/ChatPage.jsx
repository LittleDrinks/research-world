import {nanoid} from 'nanoid';
import {useState} from 'react';
import {useNavigate,useParams} from 'react-router-dom';
import {createSession} from '../sessionApi';
import {useWorld} from '../context/WorldContext';
import {useSession} from '../chat/useSession';
import {Conversation} from '../chat/Conversation';
import '../chat.css';

export function ChatPage(){
  const {threadId:sessionId}=useParams(),{projectId,data,refresh,setError}=useWorld();
  const navigate=useNavigate(),[agent,setAgent]=useState('research-assistant');
  const state=useSession(projectId,sessionId,setError);
  const create=()=>navigate('/chat');
  const start=async(content)=>{const result=await createSession(projectId,agent,content,nanoid());await refresh();navigate(`/chat/${result.session.id}`);};
  return <section className="pi-chat"><header><h1>{state.detail?.session.title||'研究对话'}</h1>
    <select aria-label="启动 Agent" value={agent} onChange={e=>setAgent(e.target.value)}>{data.agents.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select>
    <button className="button secondary" onClick={create}>新建对话</button></header>
    {state.detail?<Conversation {...state}/>:<p className="pi-empty">选择 Agent，发送第一条消息开始研究。</p>}
    <Composer key={sessionId||'draft'} state={state} onError={setError} onSend={sessionId?state.send:start}/>
  </section>;
}

function Composer({state,onError,onSend}){
  const [draft,setDraft]=useState(''),[submitting,setSubmitting]=useState(false);
  const send=async(event)=>{event.preventDefault();if(!draft.trim()||submitting)return;setSubmitting(true);try{await onSend(draft);setDraft('');}catch(e){onError(e.message);}finally{setSubmitting(false);}};
  return <form className="pi-composer" onSubmit={send}>
    <textarea autoFocus onKeyDown={event=>sendShortcut(event,{...state,sending:state.sending||submitting},draft)} aria-label="研究消息" value={draft} onChange={e=>setDraft(e.target.value)} placeholder="输入研究问题；可要求独立审查并保存方向到研究地图"/>
    <div><small className="pi-shortcut">{navigator.platform.includes("Mac")?"⌘":"Ctrl"}+Enter</small><button title="Ctrl+Enter / ⌘+Enter 发送" className="button primary" disabled={submitting||state.sending||Boolean(state.active)||!draft.trim()}>发送</button>
      {state.active&&<button className="button secondary" type="button" onClick={state.cancel}>取消</button>}</div>
  </form>;
}

function sendShortcut(event,state,draft){
  if(event.key!=='Enter'||(!event.ctrlKey&&!event.metaKey)||event.nativeEvent.isComposing)return;
  event.preventDefault();
  if(!state.sending&&!state.active&&draft.trim())event.currentTarget.form.requestSubmit();
}
