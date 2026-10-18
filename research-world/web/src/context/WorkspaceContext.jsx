import {createContext,useContext,useEffect,useState} from 'react';
import {LoaderCircle,RefreshCw} from 'lucide-react';
import {getWorkspace,startWorkspace} from '../api';
import '../workspace.css';

const WorkspaceContext=createContext(null);

export function WorkspaceProvider({projectId,children}){
  const [state,setState]=useState({status:'checking'}),[attempt,setAttempt]=useState(0);
  useEffect(()=>watchWorkspace(projectId,setState),[projectId,attempt]);
  return <WorkspaceContext.Provider value={{state,retry:()=>setAttempt(n=>n+1)}}>{children}</WorkspaceContext.Provider>;
}

function watchWorkspace(projectId,setState){
  let active=true,timer;
  const update=async(start=false)=>{
    try{
      let state=await getWorkspace(projectId);
      if(start&&active&&state.status!=='ready'){
        setState({status:'starting'});state=await startWorkspace(projectId);
      }
      if(active)setState(state);
    }catch(error){if(active)setState({status:'error',detail:error.message});}
    if(active)timer=setTimeout(()=>update(),5000);
  };
  setState({status:'checking'});update(true);
  return()=>{active=false;clearTimeout(timer);};
}

export const useWorkspace=()=>useContext(WorkspaceContext);

export function WorkspaceReady({children}){
  const {state,retry}=useWorkspace();
  if(state.status==='ready')return children;
  const stopped=['exited','not_started'].includes(state.status);
  const failed=['error','dead','unhealthy','paused'].includes(state.status);
  const busy=!stopped&&!failed;
  const title=stopped?'工作区已停止':failed?'工作区暂时不可用':state.status==='checking'?'正在连接项目工作区':'正在启动项目工作区';
  return <section className="workspace-loading" aria-busy={busy}>
    {busy&&<LoaderCircle className="workspace-spinner" size={36} aria-hidden="true"/>}
    <h1>{title}</h1>
    <p role={failed?'alert':'status'}>{failed?(state.detail||'请在项目列表检查状态后重试'):stopped?'已保存的文件仍然保留，需要时可重新启动。':'正在准备文件和运行环境，请稍候…'}</p>
    {!busy&&<button className="button primary" onClick={retry}><RefreshCw size={16}/>{stopped?'重新启动':'重试'}</button>}
    <p className="muted">工作区启动后保持运行，可在项目列表中手动停止。</p>
  </section>;
}
