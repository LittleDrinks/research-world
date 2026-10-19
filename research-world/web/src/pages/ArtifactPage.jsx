import {useEffect,useState} from 'react';
import {useParams} from 'react-router-dom';
import {artifactUrl,artifactViewUrl,getArtifactReading} from '../api';
import {ArtifactText} from '../artifacts/ArtifactText';
import {DocumentBody} from '../artifacts/DocumentBody';
import '../artifacts/artifacts.css';

export function ArtifactPage(){
  const {projectId,artifactId}=useParams(),[view,setView]=useState(null),[error,setError]=useState('');
  useEffect(()=>{
    let current=true;setView(null);setError('');
    getArtifactReading(projectId,artifactId).then(v=>{if(current)setView(v);}).catch(e=>{if(current)setError(e.message);});
    return()=>{current=false;};
  },[projectId,artifactId]);
  return <main className="artifact-page" tabIndex={0} aria-label="研究产物阅读"><nav><a href="/projects">研究世界</a><span> / 研究产物</span></nav>
    {error?<p role="alert">{error}</p>:view?<ArtifactContent view={view} projectId={projectId}/>:<p role="status">正在读取产物…</p>}
  </main>;
}

function ArtifactContent({view,projectId}){
  const structured=view.kind==='document';
  return <article className="artifact-paper"><header><p className="eyebrow">{structured?view.schema.title:'研究资料'}</p>
    <h1>{structured?view.data.title:view.name||'产物预览'}</h1><ArtifactActions view={view} projectId={projectId}/></header>
    {structured?<><DocumentContext view={view} projectId={projectId}/><DocumentBody data={view.data} projectId={projectId}/></>:
      <ArtifactText key={view.artifact.id} view={view} projectId={projectId}/>}
    <details className="document-provenance"><summary>版本与校验信息</summary><p>产物：{view.artifact.id}</p>
      {structured&&<><p>正文 {view.reading_chars} / {view.schema['x-max-reading-chars']} 字符；结构已校验。</p>
        <a href={artifactViewUrl(projectId,view.schema_id)}>查看固定模板版本</a><p>结构校验不判定科学结论。</p></>}
    </details>
  </article>;
}

function ArtifactActions({view,projectId}){
  const raw=artifactUrl(projectId,view.artifact.id);
  return <div className="artifact-actions"><a className="button secondary" href={raw+'?download=true'}>下载原件</a>
    {view.kind==='document'&&<a className="button secondary" href={raw+'/markdown'}>导出 Markdown</a>}</div>;
}

function DocumentContext({view,projectId}){
  return <div className="document-context"><span>被审对象：{view.target?.content?.title||'对象已不可用'}</span>
    <a href={artifactViewUrl(projectId,view.data.target_artifact_id)} target="_blank" rel="noreferrer">查看被审原件</a>
  </div>;
}
