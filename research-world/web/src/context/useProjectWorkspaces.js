import {useCallback,useEffect,useRef,useState} from 'react';
import {getWorkspaces,stopWorkspace} from '../api';

export function useProjectWorkspaces(){
  const [states,setStates]=useState(null),[error,setError]=useState('');
  const [pending,setPending]=useState({}),[errors,setErrors]=useState({});
  const requests=useRef(0);
  const refresh=useCallback(async()=>{
    const request=++requests.current;
    try{const values=await getWorkspaces();if(request===requests.current){setStates(values);setError('');}}
    catch{if(request===requests.current)setError('工作区状态暂不可用');}
  },[]);
  useEffect(()=>poll(refresh,requests),[refresh]);
  const stop=async(id)=>{
    if(pending[id])return;
    setPending(values=>({...values,[id]:true}));setErrors(values=>({...values,[id]:''}));
    try{await stopWorkspace(id);await refresh();}catch(error){setErrors(values=>({...values,[id]:error.message}));}
    finally{setPending(values=>({...values,[id]:false}));}
  };
  return {states,error,pending,errors,stop};
}

function poll(refresh,requests){
  let active=true,timer;
  const update=async()=>{await refresh();if(active)timer=setTimeout(update,5000);};
  update();
  return()=>{active=false;requests.current++;clearTimeout(timer);};
}
