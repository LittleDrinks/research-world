import {useEffect,useState} from 'react';
import {ArtifactDownload} from '../components/map/ArtifactDownload';
import {getArtifactReading} from '../api';
import {ArtifactText} from '../artifacts/ArtifactText';
import {DocumentBody} from '../artifacts/DocumentBody';

export function RecordAssets({node,artifacts}){
  const [selected,setSelected]=useState(null),byId=new Map(artifacts.map(a=>[a.id,a]));
  const names=new Map((Array.isArray(node.content.attachments)?node.content.attachments:[]).filter(a=>a&&typeof a==='object').map(a=>[a.id,a.name]));
  const items=node.artifact_ids.map(id=>byId.get(id)).filter(Boolean);
  if(!items.length)return null;
  return <section className="inspector-section record-assets"><h2>研究产物</h2>{items.map(a=><div key={a.id} className="record-asset"><b>{names.get(a.id)||assetName(a)}</b><div><button className="text-link" onClick={()=>setSelected(selected===a.id?null:a.id)}>{selected===a.id?'收起预览':'预览'}</button><ArtifactDownload artifact={a}/></div>
    {selected===a.id&&<AssetPreview key={a.id} artifact={a}/>}</div>)}</section>;
}

function AssetPreview({artifact}){
  const [view,setView]=useState(null),[error,setError]=useState('');
  useEffect(()=>{let active=true;getArtifactReading(artifact.project_id,artifact.id).then(v=>{if(active)setView(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[artifact.id]);
  return <div className="asset-preview">{error?<p role="alert">{error}</p>:!view?<p>正在读取…</p>:view.kind==='document'?<DocumentBody data={view.data} projectId={artifact.project_id}/>:<ArtifactText view={view} projectId={artifact.project_id}/>}</div>;
}

function assetName(artifact){
  return artifact.media_type==='text/markdown'?'研究报告':artifact.media_type.startsWith('image/')?'结果图':artifact.media_type.includes('python')?'计算代码':artifact.media_type==='application/json'?'结果数据':'研究文件';
}
