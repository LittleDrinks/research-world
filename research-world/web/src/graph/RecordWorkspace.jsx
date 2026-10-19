import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {artifactViewUrl,changeRecord,getRecordRevision,listChanges} from '../api';
import {RecordContent} from './RecordContent';
import {ChangeHistory} from './ChangeHistory';
import {LabelBadge} from './Labels';
import {ChatMarkdown} from '../chat/ChatMarkdown';

export function RecordWorkspace({node}){
  const {projectId}=useWorld(),[mode,setMode]=useState('body'),[changes,setChanges]=useState([]),[past,setPast]=useState(null),[error,setError]=useState(''),[edit,setEdit]=useState(null);
  useEffect(()=>{let active=true;listChanges(projectId,node.id).then(v=>{if(active)setChanges(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[projectId,node.id,node.revision]);
  const version=async revision=>{try{setPast(await getRecordRevision(projectId,node.id,revision));setMode('body');setError('');}catch(e){setError(e.message);}};
  return <section className="record-workspace"><div className="record-workspace-tabs">{[['body','正文'],['discussion','讨论'],['changes','Changes']].map(([key,title])=><button key={key} aria-pressed={mode===key} onClick={()=>setMode(key)}>{title}</button>)}</div>
    <div className="record-version"><span>{past?`正在阅读固定版本 r${past.revision}`:`当前版本 r${node.revision}`}</span><button className="text-link" onClick={()=>version(1)}>初始版本</button>{past?<button className="text-link" onClick={()=>setPast(null)}>返回当前</button>:<button className="text-link" onClick={()=>setEdit({revision:node.revision,content:node.content})}>编辑正文</button>}</div>
    {error&&<p role="alert">{error}</p>}{mode==='body'&&<>{past&&<FixedRecord record={past} projectId={projectId}/>}<RecordContent content={(past||node).content}/></>}
    {mode==='changes'&&<ChangeHistory changes={changes} projectId={projectId} onVersion={version}/>}
    {mode==='discussion'&&<RecordDiscussion key={past?.revision||'current'} node={node} revision={past?.revision||node.revision} changes={changes} projectId={projectId}/>}
    {edit&&<EditRecord node={node} draft={edit} projectId={projectId} onClose={()=>setEdit(null)}/>}
  </section>;
}

function FixedRecord({record,projectId}){
  return <div className="fixed-record"><b>{record.content.title}</b><div>{record.labels.map(l=><LabelBadge key={l.id} label={l}/>)}</div>
    <details><summary>{record.artifact_ids.length} 个版本内附件</summary>{record.artifact_ids.map(id=><p key={id}><a href={artifactViewUrl(projectId,id)} target="_blank" rel="noreferrer">{record.content.attachments?.find(a=>a.id===id)?.name||id}</a></p>)}</details>
  </div>;
}

function EditRecord({node,draft,projectId,onClose}){
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');const fields=Object.fromEntries(new FormData(event.currentTarget));
    try{await changeRecord(projectId,node.id,{...fields,kind:'revise',base_revision:draft.revision});onClose();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <Modal title="修订研究正文" open onClose={busy?()=>{}:onClose}><form className="record-edit-form" onSubmit={submit}>
    <p className="muted">基于 r{draft.revision}。保存后生成新版本，旧内容和证据仍可回读。</p><label>标题<input name="title" required maxLength={200} defaultValue={draft.content.title||''}/></label>
    <label>正文（Markdown）<textarea aria-label="正文（Markdown）" name="text" required maxLength={20000} defaultValue={draft.content.text||''} rows={10}/></label>
    <label>修订原因<input name="reason" required maxLength={500} placeholder="依据什么修改？仍有哪些未验证项？"/></label>
    {error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy}>保存修订</button>
  </form></Modal>;
}

function RecordDiscussion({node,revision,changes,projectId}){
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [reference]=useState(revision);
  const comments=changes.filter(c=>c.kind==='comment');
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');const form=event.currentTarget,comment=new FormData(form).get('comment');
    try{await changeRecord(projectId,node.id,{kind:'comment',base_revision:node.revision,reference_revision:reference,reason:'补充研究讨论',comment});form.reset();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <div className="record-discussion">{comments.map(c=><article key={c.id}><p className="change-meta">{c.author} · 引用 r{c.reference_revision}</p><ChatMarkdown projectId={projectId}>{c.comment}</ChatMarkdown></article>)}
    <form onSubmit={submit}><label>评论 · 引用 r{reference}<textarea name="comment" required maxLength={4000} placeholder="补充证据、提出疑点或澄清假设…"/></label>
      {error&&<p role="alert">{error}</p>}<button className="button secondary" disabled={busy}>发表评论</button></form></div>;
}
