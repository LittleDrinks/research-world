import {useEffect,useState} from 'react';
import {useParams} from 'react-router-dom';
import {getRecord,getLocalMap,projectMapUrl} from '../api';
import {RecordWorkspace} from '../graph/RecordWorkspace';
import {RecordLabels} from '../graph/Labels';
import {RecordAssets} from '../graph/RecordAssets';
import {KIND_LABELS} from '../utils/labels';
import '../graph/changes.css';
import {RecordStatus} from '../graph/RecordStatus';
import {RecordDocument,SourceIdentity} from '../graph/RecordDocument';
import {CreateRecord} from '../graph/CreateRecord';

export function RecordPage(){
  const {projectId,recordId}=useParams(),[node,setNode]=useState(null),[artifacts,setArtifacts]=useState([]),[error,setError]=useState('');
  useEffect(()=>{let active=true;const load=async()=>{try{const [record,map]=await Promise.all([getRecord(projectId,recordId),getLocalMap(projectId,{record_id:recordId})]);if(active){setNode({...record,kind:record.type});setArtifacts(map.artifacts);}}catch(e){if(active)setError(e.message);}};load();const timer=setInterval(load,2000);return()=>{active=false;clearInterval(timer);};},[projectId,recordId]);
  if(error)return <p role="alert">{error}</p>;
  if(!node)return <p role="status">正在读取研究记录…</p>;
  return <main className="research-record-page"><nav><a href={projectMapUrl(projectId)+'?node='+encodeURIComponent(recordId)}>返回研究地图</a><span>{KIND_LABELS[node.kind]}</span></nav>
    <header><h1>{node.content.title}</h1><SourceIdentity node={node}/><RecordStatus node={node}/><RecordLabels key={`labels:${node.id}`} node={node}/></header>
    <RecordDocument node={node}/><CreateRecord seed={node.content}/><div className="research-record-columns"><RecordWorkspace key={`workspace:${node.id}`} node={node}/><aside><RecordAssets node={node} artifacts={artifacts}/></aside></div>
  </main>;
}
