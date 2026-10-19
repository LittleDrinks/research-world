import {useState} from 'react';
import {ChatMarkdown} from '../chat/ChatMarkdown';

export function ArtifactText({view,projectId}){
  const [raw,setRaw]=useState(false);
  if(view.kind==='text')return <pre className="artifact-raw">{view.text}</pre>;
  if(view.kind!=='markdown')return <p>此格式请下载原件查看。</p>;
  return <><div className="segmented artifact-reading-mode" role="group" aria-label="文档显示方式">
    <button type="button" className={!raw?'active':''} aria-pressed={!raw} onClick={()=>setRaw(false)}>阅读</button>
    <button type="button" className={raw?'active':''} aria-pressed={raw} onClick={()=>setRaw(true)}>原文</button>
  </div>{raw?<pre className="artifact-raw">{view.text}</pre>:
    <div className="artifact-markdown"><ChatMarkdown projectId={projectId}>{view.text}</ChatMarkdown></div>}</>;
}
