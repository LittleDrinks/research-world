import {useEffect,useState} from 'react';
import {ArtifactDownload} from '../components/map/ArtifactDownload';
import {getArtifactReading} from '../api';
import {ArtifactText} from '../artifacts/ArtifactText';
import {DocumentBody} from '../artifacts/DocumentBody';

const documentType='application/vnd.research-world.document+json';

export function RecordAssets({node,artifacts}){
  const byId=new Map(artifacts.map(a=>[a.id,a]));
  const names=new Map((Array.isArray(node.content.attachments)?node.content.attachments:[]).filter(a=>a&&typeof a==='object').map(a=>[a.id,a.name]));
  const items=node.artifact_ids.map(id=>byId.get(id)).filter(Boolean);
  const reports=items.filter(a=>a.media_type===documentType),files=items.filter(a=>a.media_type!==documentType);
  if(!items.length)return null;
  return <section className="inspector-section record-assets">
    {reports.length>0&&<><h2>六维审计</h2>{reports.map(a=><Asset key={a.id} artifact={a} name={names.get(a.id)||'审计结果'} expanded/>)}</>}
    {files.length>0&&<><h2>证据附件</h2>{files.map(a=><Asset key={a.id} artifact={a} name={names.get(a.id)||assetName(a)}/>)}</>}
  </section>;
}

function Asset({artifact,name,expanded=false}){
  const [open,setOpen]=useState(expanded);
  return <div className="record-asset"><b>{name}</b><div><button className="text-link" onClick={()=>setOpen(!open)}>{open?'收起预览':'预览'}</button><ArtifactDownload artifact={artifact}/></div>
    {open&&<AssetPreview artifact={artifact}/>}</div>;
}

function AssetPreview({artifact}){
  const [view,setView]=useState(null),[error,setError]=useState('');
  useEffect(()=>{let active=true;getArtifactReading(artifact.project_id,artifact.id).then(v=>{if(active)setView(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[artifact.id]);
  return <div className="asset-preview">{error?<p role="alert">{error}</p>:!view?<p>正在读取…</p>:view.kind==='document'?<DocumentBody schema={view.schema} data={view.data} projectId={artifact.project_id}/>:<ArtifactText view={view} projectId={artifact.project_id}/>}</div>;
}

function assetName(artifact){
  return artifact.media_type==='text/markdown'?'文档附件':artifact.media_type.startsWith('image/')?'结果图':artifact.media_type.includes('python')?'计算代码':artifact.media_type==='application/json'?'结果数据':'研究文件';
}
