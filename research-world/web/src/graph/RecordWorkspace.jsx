import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {artifactViewUrl,changeRecord,getRecordRevision,listChanges} from '../api';
import {RecordContent} from './RecordContent';
import {ResearchTimeline} from './ResearchTimeline';
import {LabelBadge} from './Labels';
import {ChatMarkdown} from '../chat/ChatMarkdown';

export function RecordWorkspace({node}){
  const {projectId}=useWorld(),[changes,setChanges]=useState([]),[past,setPast]=useState(null),[error,setError]=useState(''),[edit,setEdit]=useState(null);
  useEffect(()=>{let active=true;listChanges(projectId,node.id).then(v=>{if(active)setChanges(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[projectId,node.id,node.revision]);
  const version=async revision=>{try{setPast(await getRecordRevision(projectId,node.id,revision));setError('');}catch(e){setError(e.message);}};
  return <section className="record-workspace"><article className="issue-description"><header><b>研究记录</b><div className="record-version"><span>{past?`固定版本 r${past.revision}`:`r${node.revision}`}</span><button className="text-link" onClick={()=>version(1)}>初始版本</button>{past?<button className="text-link" onClick={()=>setPast(null)}>返回当前</button>:<button className="text-link" onClick={()=>setEdit({revision:node.revision,content:node.content})}>编辑正文</button>}</div></header>
    {error&&<p role="alert">{error}</p>}{past&&<FixedRecord record={past} projectId={projectId}/>}<RecordContent content={(past||node).content}/></article>
    <ResearchTimeline changes={changes} projectId={projectId} onVersion={version}/>
    <RecordDiscussion key={past?.revision||'current'} node={node} revision={past?.revision||node.revision} projectId={projectId}/>
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
  const [text,setText]=useState(draft.content.text||''),[preview,setPreview]=useState(false);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');const fields=Object.fromEntries(new FormData(event.currentTarget));
    try{await changeRecord(projectId,node.id,{...fields,kind:'revise',base_revision:draft.revision});onClose();}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <Modal title="修订研究正文" open onClose={busy?()=>{}:onClose}><form className="record-edit-form" onSubmit={submit}>
    <p className="muted">基于 r{draft.revision}</p><label>标题<input name="title" required maxLength={200} defaultValue={draft.content.title||''}/></label>
    <PreviewTabs preview={preview} setPreview={setPreview}/><label hidden={preview}>正文（Markdown）<textarea aria-label="正文（Markdown）" name="text" required maxLength={20000} value={text} onChange={e=>setText(e.target.value)} rows={10}/></label>
    {preview&&<div className="markdown-preview"><ChatMarkdown projectId={projectId}>{text}</ChatMarkdown></div>}
    <label>修订原因<input name="reason" required maxLength={500} placeholder="依据什么修改？仍有哪些未验证项？"/></label>
    {error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy||!text.trim()}>保存修订</button>
  </form></Modal>;
}

function RecordDiscussion({node,revision,projectId}){
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [reference]=useState(revision),[text,setText]=useState(''),[preview,setPreview]=useState(false);
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');const form=event.currentTarget,comment=new FormData(form).get('comment');
    try{await changeRecord(projectId,node.id,{kind:'comment',base_revision:node.revision,reference_revision:reference,reason:'补充研究讨论',comment});setText('');setPreview(false);}catch(e){setError(e.message);}finally{setBusy(false);}};
  return <div className="record-discussion"><form onSubmit={submit}><h3>发表评论</h3><PreviewTabs preview={preview} setPreview={setPreview}/>
    <label hidden={preview}>评论 · 引用 r{reference}<textarea aria-label="评论正文" name="comment" value={text} onChange={e=>setText(e.target.value)} required maxLength={4000} placeholder="补充证据、提出问题…"/></label>
      {preview&&<div className="markdown-preview"><ChatMarkdown projectId={projectId}>{text||'尚未输入评论。'}</ChatMarkdown></div>}
      {error&&<p role="alert">{error}</p>}<button className="button secondary" disabled={busy||!text.trim()}>发表评论</button></form></div>;
}

function PreviewTabs({preview,setPreview}){
  return <div className="markdown-tabs"><button type="button" aria-pressed={!preview} onClick={()=>setPreview(false)}>编写</button><button type="button" aria-pressed={preview} onClick={()=>setPreview(true)}>预览</button></div>;
}
