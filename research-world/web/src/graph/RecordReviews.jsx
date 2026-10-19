import {useEffect,useState} from 'react';
import {artifactViewUrl,listRecordReviews,reviewAction} from '../api';
import './reviews.css';

const states={queued:'等待启动',running:'复核中',completed:'复核完成',failed:'复核中断',cancelling:'正在取消',cancelled:'已取消'};

export function RecordReviews({projectId,recordId}){
  const [tasks,setTasks]=useState([]),[error,setError]=useState('');
  useEffect(()=>{let active=true;const load=()=>listRecordReviews(projectId,recordId).then(v=>{if(active){setTasks(v);setError('');}}).catch(e=>{if(active)setError(e.message);});load();const timer=setInterval(load,2000);return()=>{active=false;clearInterval(timer);};},[projectId,recordId]);
  return <div className="record-reviews" aria-label="独立复核任务">{error&&<p role="alert">{error}</p>}
    {tasks.map(task=><ReviewTask key={task.id} task={task} projectId={projectId}/>)}
  </div>;
}

function ReviewTask({task,projectId}){
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const act=async action=>{setBusy(true);setError('');try{await reviewAction(projectId,task.id,action);}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <article className="review-task" data-status={task.status}><header><b>{states[task.status]}</b><span>针对 r{task.revision}</span></header>
    <p>{task.agent_name} · {task.model}</p>
    {task.input_changed&&<p className="review-stale">正文或输入附件已变化，本次复核尚未覆盖当前修改。</p>}
    {task.error&&<p>{task.error}</p>}{error&&<p role="alert">{error}</p>}
    <div className="review-links">{task.run_id&&<a href={`/chat/${task.session_id}`} target="_blank" rel="noreferrer">执行过程 ↗</a>}
      {task.target_id&&<a href={artifactViewUrl(projectId,task.target_id)} target="_blank" rel="noreferrer">被审快照 ↗</a>}
      {task.report_id&&<a href={artifactViewUrl(projectId,task.report_id)} target="_blank" rel="noreferrer">阅读报告 ↗</a>}
      {task.status==='failed'&&<button disabled={busy} onClick={()=>act('retry')}>重试复核</button>}
      {['queued','running','failed'].includes(task.status)&&<button disabled={busy} onClick={()=>act('cancel')}>取消任务</button>}
    </div>
  </article>;
}
