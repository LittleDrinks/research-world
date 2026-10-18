import {Circle,LoaderCircle,Square} from 'lucide-react';

const LABELS={ready:'运行中',running:'启动中',created:'启动中',restarting:'重启中',paused:'已暂停',unhealthy:'运行异常',dead:'已终止',exited:'已停止',not_started:'未启动',loading:'读取中',unknown:'状态不可用'};
const STOPPABLE=['ready','running','created','restarting','paused','unhealthy'];

export function ProjectWorkspace({project,workspaces}){
  const {states,error,pending,errors,stop}=workspaces;
  const status=error?'unknown':states?.[project.id]||'loading';
  const busy=Boolean(pending[project.id]);
  return <div className="project-workspace">
    <span className="workspace-state" data-state={status} role="status"><Circle size={8}/>{busy?'正在停止…':LABELS[status]||'状态不可用'}</span>
    {STOPPABLE.includes(status)&&<button className="button secondary workspace-stop" disabled={busy} onClick={()=>stop(project.id)}
      aria-label={`停止 ${project.name} 工作区`} title="结束工作区中的程序，保留已保存的文件">
      {busy?<LoaderCircle size={12} className="workspace-spinner"/>:<Square size={12}/>}停止工作区</button>}
    {errors[project.id]&&<span className="workspace-stop-error" role="alert">{errors[project.id]}</span>}
  </div>;
}
