import {nanoid} from 'nanoid';
import {useCallback,useEffect,useRef,useState} from 'react';
import {sessionDetail,sendMessage,turnUrl,cancelTurn} from '../sessionApi';

export function useSession(projectId,sessionId,onError) {
  const [detail,setDetail]=useState(null),[events,setEvents]=useState([]);
  const [sending,setSending]=useState(false),[connection,setConnection]=useState('idle');
  const generation=useRef(0);
  const load=useCallback(async()=>{
    const version=generation.current;
    const value=await sessionDetail(projectId,sessionId);
    if(version===generation.current)setDetail(value);
  },[projectId,sessionId]);
  useDetailPolling(sessionId,load,setDetail,setEvents,generation,onError);
  const active=detail?.run.turns.find(t=>t.status==='running');
  useTurnStream(projectId,sessionId,active?.id,setEvents,setConnection,load,onError);
  const send=async(content)=>{setSending(true);try{await sendMessage(projectId,sessionId,content,nanoid());await load();}finally{setSending(false);}};
  const cancel=async()=>{try{await cancelTurn(projectId,sessionId,active.id);await load();}catch(e){onError(e.message);}};
  return {detail,events,sending,active,connection,send,cancel};
}

function useDetailPolling(sessionId,load,setDetail,setEvents,generation,onError){
  useEffect(()=>{
    generation.current+=1;setDetail(null);setEvents([]);
    if(!sessionId)return;
    load().catch(e=>onError(e.message));
    const timer=setInterval(()=>load().catch(e=>onError(e.message)),2000);
    return()=>{generation.current+=1;clearInterval(timer);};
  },[sessionId,load]);
}

function useTurnStream(projectId,sessionId,turnId,setEvents,setConnection,load,onError){
  useEffect(()=>{
    if(!turnId){setConnection('idle');return;}
    setEvents([]);setConnection('connecting');
    const stream=new EventSource(`${turnUrl(projectId,sessionId,turnId)}/events`);
    stream.onopen=()=>setConnection('live');
    for(const type of ['delta','reasoning','tool','child_result','turn_start','turn_end'])
      stream.addEventListener(type,e=>receiveEvent(e,stream,setEvents,load,onError));
    stream.onerror=()=>{setConnection('reconnecting');load().catch(e=>onError(e.message));};
    return()=>stream.close();
  },[projectId,sessionId,turnId,load]);
}

function receiveEvent(event,stream,setEvents,load,onError){
  const value=JSON.parse(event.data);
  setEvents(previous=>previous.some(e=>e.seq===value.seq)?previous:[...previous,value]);
  if(value.type==='turn_end'){stream.close();load().catch(e=>onError(e.message));}
}
