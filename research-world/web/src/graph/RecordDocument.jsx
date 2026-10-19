import {useState} from 'react';
import {recordDocumentUrl} from '../api';
import {useWorld} from '../context/WorldContext';

export function RecordDocument({node}){
  const {projectId}=useWorld(),[text,setText]=useState(''),[error,setError]=useState('');
  const load=async e=>{if(!e.currentTarget.open)return;try{const response=await fetch(recordDocumentUrl(projectId,node.id));if(!response.ok)throw Error('读取文档失败');setText(await response.text());}catch(e){setError(e.message);}};
  return <details className="record-document" onToggle={load}><summary>文档属性与 Markdown</summary><a href={recordDocumentUrl(projectId,node.id)} download={`${node.id.replace(':','-')}.md`}>下载 .md</a>{error&&<p role="alert">{error}</p>}<pre>{text}</pre></details>;
}

export function SourceIdentity({node}){
  const c=node.content;if(node.kind!=='source'||!c.canonical_url)return null;
  let u;try{u=new URL(c.canonical_url);}catch{return null;}if(!['https:','http:'].includes(u.protocol))return null;
  return <div className="source-identity"><a href={u.href} target="_blank" rel="noreferrer">{c.doi?`DOI ${c.doi}`:c.canonical_url} ↗</a>
    <span>{[c.authors,c.year,c.venue].filter(Boolean).join(' · ')}</span>{c.verification&&<span>{c.verification}</span>}
  </div>;
}
