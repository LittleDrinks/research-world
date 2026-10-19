import {ChatMarkdown} from '../chat/ChatMarkdown';
import {LabelBadge} from './Labels';

const authors={user:'用户',system:'系统',experiment:'计算任务'};

export function ResearchTimeline({changes,projectId,onVersion}){
  return <div className="research-timeline" aria-label="讨论与变更时间线">{changes.map(change=>change.kind==='comment'?
    <article className="timeline-comment" key={change.id}><header><b>{authors[change.author]||change.author}</b><time>{new Date(change.created_at).toLocaleString()}</time><button className="text-link" onClick={()=>onVersion(change.reference_revision)}>引用 r{change.reference_revision}</button></header><ChatMarkdown projectId={projectId}>{change.comment}</ChatMarkdown></article>:
    <div className="timeline-event" key={change.id}><span className="event-dot"/><div><span>{authors[change.author]||change.author} {eventText(change)}</span><LabelDelta change={change}/><time>{new Date(change.created_at).toLocaleString()}</time>
      {change.kind==='revise'?<details><summary>查看正文差异 · r{change.before.revision} → r{change.revision}</summary><div className="record-diff"><div><b>修改前</b><pre>{change.before.content.text}</pre></div><div><b>修改后</b><pre>{change.after.content.text}</pre></div></div><p>{change.reason}</p><button className="text-link" onClick={()=>onVersion(change.revision)}>查看 r{change.revision}</button></details>:<details><summary>变更原因</summary><p>{change.reason}</p></details>}</div></div>)}</div>;
}

function eventText(change){
  return {revise:'修改了正文',labels:'调整了标签',attachment:'添加了研究产物'}[change.kind]||'更新了记录';
}

function LabelDelta({change}){
  if(change.kind!=='labels')return null;
  const before=change.before.labels,after=change.after.labels;
  const added=after.filter(a=>!before.some(b=>b.id===a.id&&b.name===a.name&&b.color===a.color));
  const removed=before.filter(a=>!after.some(b=>b.id===a.id&&b.name===a.name&&b.color===a.color));
  return <span className="label-delta">{removed.map(l=><del key={l.id}><LabelBadge label={l}/></del>)}{added.map(l=><LabelBadge key={l.id} label={l}/>)}</span>;
}
