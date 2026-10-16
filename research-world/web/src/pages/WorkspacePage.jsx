import {useEffect,useState} from 'react';
import {ExternalLink,FlaskConical,RefreshCw} from 'lucide-react';
import {getWorkspace,startWorkspace,stopWorkspace} from '../api';
import {useWorld} from '../context/WorldContext';
import '../workspace.css';

const LABELS={not_started:'尚未启动',created:'正在准备',running:'正在启动',ready:'可使用',exited:'已停止',dead:'启动失败',unhealthy:'健康检查失败',restarting:'正在重启',paused:'已暂停'};

export function WorkspacePage(){
  const {projectId,data}=useWorld();
  const project=data.projects.find(p=>p.id===projectId);
  return project?<Workspace key={projectId} project={project} />:<p>请选择项目。</p>;
}

function useWorkspace(id){
  const [state,setState]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{let current=true;getWorkspace(id).then(v=>{if(current)setState(v);}).catch(e=>{if(current)setError(e.message);});return()=>{current=false;};},[id]);
  const action=async(fn)=>{setBusy(true);setError('');try{setState(await fn(id));}catch(e){setError(e.message);}finally{setBusy(false);}};
  return {state,busy,error,action};
}

function Workspace({project}){
  const {state,busy,error,action}=useWorkspace(project.id);
  return <section className="workspace-page"><header><FlaskConical/><div><h1>实验工作区</h1><p>{project.name} · 文件、Python 与 Pi 共用一个环境</p></div></header>
    <div className="workspace-card"><div className="workspace-status"><strong>{busy?'正在处理…':LABELS[state?.status]||'正在读取状态…'}</strong>{state?.model&&<span>Pi 默认模型：{state.model}</span>}</div>
      {error&&<p role="alert" className="workspace-error">{error}</p>}
      <div className="form-actions"><WorkspaceActions state={state} busy={busy} action={action}/></div>
      <p className="muted">停止工作区会结束其中的程序，文件和 Pi 会话会保留。删除项目会同时删除工作区资料。</p></div>
    <WorkspaceGuide/>
  </section>;
}

function WorkspaceActions({state,busy,action}){
  const running=['ready','running','restarting','paused','unhealthy'].includes(state?.status);
  return <>{state?.status==='ready'&&<a className="button primary" href={state.url} target="_blank" rel="noreferrer"><ExternalLink size={16}/>打开 JupyterLab</a>}
    {!running&&<button className="button primary" disabled={busy||!state} onClick={()=>action(startWorkspace)}>启动工作区</button>}
    {running&&<button className="button secondary" disabled={busy} onClick={()=>action(stopWorkspace)}>停止工作区</button>}
    <button className="button secondary" disabled={busy} onClick={()=>action(getWorkspace)}><RefreshCw size={16}/>刷新状态</button></>;
}

function WorkspaceGuide(){
  return <div className="workspace-card"><h2>人和 Agent 使用同一份文件</h2><ol>
    <li>打开 JupyterLab，在文件列表创建或上传脚本、数据和 Notebook。</li>
    <li>点击「+」→ Terminal，在终端输入 <code>pi</code>，让 Agent 读取、编辑和运行工作区里的文件。</li>
    <li>你也可以直接编辑文件，在另一个终端执行 <code>python hello.py</code>，或选择 Notebook 的 Python (Research World) 内核。</li>
    </ol><p>工作目录：<code>/workspace</code>。文件、终端和 Notebook 使用同一套 Python；Pi 使用原生会话与文件工具。</p>
    <p className="muted">这里的 Pi 会话独立于「对话」页面。工作文件可修改，重要结果请另存为研究产物。</p></div>;
}
