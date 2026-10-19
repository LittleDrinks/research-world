import {ChatMarkdown} from '../chat/ChatMarkdown';
import {LabelBadge} from './Labels';

const kinds={revise:'正文修订',comment:'评论',labels:'标签变更',attachment:'附件追加'};

export function ChangeHistory({changes,projectId,onVersion,onSelect}){
  if(!changes.length)return <p className="muted">还没有变更。编辑正文、评论或贴标后，记录会保留在这里。</p>;
  return <div className="record-changes">{[...changes].reverse().map(change=><article key={change.id} className="record-change">
    <header><b>{kinds[change.kind]||change.kind}</b>{onVersion?<button className="text-link" onClick={()=>onVersion(change.revision)}>r{change.revision}</button>:<span>r{change.revision}</span>}</header>
    {onSelect&&<button className="text-link" onClick={()=>onSelect(change.record_id)}>{change.after.content.title||change.record_id}</button>}
    <p className="change-meta">{change.author} · {new Date(change.created_at).toLocaleString()}</p><p>{change.reason}</p>
    {change.comment&&<ChatMarkdown projectId={projectId}>{change.comment}</ChatMarkdown>}
    <details><summary>查看变更 · r{change.before.revision} → r{change.after.revision}</summary><ChangeDifference change={change}/></details>
  </article>)}</div>;
}

function ChangeDifference({change}){
  if(change.kind==='revise')return <div className="record-diff"><div><b>修改前</b><h4>{change.before.content.title}</h4><pre>{change.before.content.text}</pre></div><div><b>修改后</b><h4>{change.after.content.title}</h4><pre>{change.after.content.text}</pre></div></div>;
  if(change.kind==='labels')return <div className="record-diff"><div><b>修改前</b>{change.before.labels.map(l=><LabelBadge key={l.id} label={l}/>)}</div><div><b>修改后</b>{change.after.labels.map(l=><LabelBadge key={l.id} label={l}/>)}</div></div>;
  if(change.kind==='attachment')return <p className="mono">{change.after.artifact_ids.filter(id=>!change.before.artifact_ids.includes(id)).join('\n')}</p>;
  return <p className="muted">评论固定引用 r{change.reference_revision}，正文保持原样。</p>;
}
