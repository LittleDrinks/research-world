import {useEffect,useState} from 'react';
import {useParams,useSearchParams} from 'react-router-dom';
import {getWorkspace,startWorkspace} from '../api';
import {useWorld} from '../context/WorldContext';
import {editorUrl,filePath} from '../chat/workspaceLinks';
import '../workspace.css';

export function WorkspaceFilePage(){
  const {projectId:active,loading}=useWorld(),{'*':path}=useParams(),[query]=useSearchParams();
  const projectId=query.get('project')||active;
  const [error,setError]=useState(''),[attempt,setAttempt]=useState(0);
  useEffect(()=>{
    if(loading)return;
    let current=true;setError('');
    openFile(projectId,path).then(url=>{if(current)window.location.replace(url);}).catch(e=>{if(current)setError(e.message);});
    return()=>{current=false;};
  },[projectId,path,loading,attempt]);
  return <section className="workspace-page"><h1>打开工作区文件</h1><p>{path}</p>
    {error?<><p role="alert">{error}</p><button className="button secondary" onClick={()=>setAttempt(n=>n+1)}>重试</button><a className="button secondary" href="/workspace">返回工作区</a></>:<p role="status">正在准备工作区并打开编辑器…</p>}
  </section>;
}

async function openFile(projectId,path){
  filePath(path);
  if(!projectId)throw Error('请先选择文件所属的项目');
  let state=await getWorkspace(projectId);
  if(state.status!=='ready')state=await startWorkspace(projectId);
  if(state.status!=='ready')throw Error('工作区尚未就绪，请稍后重试');
  return editorUrl(state.url,path);
}
