import {createContext,useContext,useEffect,useState} from 'react';
import {LoaderCircle,RefreshCw} from 'lucide-react';
import '../workspace.css';

const WorkspaceContext=createContext(null);

export function WorkspaceProvider({projectId,children}){
  const [state,setState]=useState({status:'starting'}),[attempt,setAttempt]=useState(0);
  useEffect(()=>connectWorkspace(projectId,setState),[projectId,attempt]);
  return <WorkspaceContext.Provider value={{state,retry:()=>setAttempt(n=>n+1)}}>{children}</WorkspaceContext.Provider>;
}

function connectWorkspace(projectId,setState){
  const url=new URL(`/api/v1/projects/${encodeURIComponent(projectId)}/workspace/presence`,location.href);
  url.protocol=location.protocol==='https:'?'wss:':'ws:';
  let socket;
  const open=()=>{setState({status:'starting'});socket=subscribe(url,setState);};
  const close=()=>{socket.onmessage=null;socket.onclose=null;socket.close();};
  const restore=event=>{if(event.persisted)open();};
  open();window.addEventListener('pagehide',close);window.addEventListener('pageshow',restore);
  return()=>{close();window.removeEventListener('pagehide',close);window.removeEventListener('pageshow',restore);};
}

function subscribe(url,setState){
  const socket=new WebSocket(url);
  socket.onmessage=event=>setState(JSON.parse(event.data));
  socket.onclose=()=>setState(state=>state.status==='error'?state:{status:'error',detail:'工作区连接已断开，请重试'});
  return socket;
}

export const useWorkspace=()=>useContext(WorkspaceContext);

export function WorkspaceReady({children}){
  const {state,retry}=useWorkspace();
  if(state.status==='ready')return children;
  const failed=state.status==='error';
  return <section className="workspace-loading" aria-busy={!failed}>
    {!failed&&<LoaderCircle className="workspace-spinner" size={36} aria-hidden="true"/>}
    <h1>{failed?'工作区暂时不可用':'正在启动项目工作区'}</h1>
    <p role={failed?'alert':'status'}>{failed?state.detail:'正在准备文件和运行环境，首次启动可能需要一点时间…'}</p>
    {failed&&<button className="button primary" onClick={retry}><RefreshCw size={16}/>重试</button>}
    <p className="muted">离开项目后自动停止，已保存的文件会保留。</p>
  </section>;
}
