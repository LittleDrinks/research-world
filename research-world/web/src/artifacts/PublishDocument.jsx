import {useEffect,useState} from 'react';
import {Modal} from '../components/Modal';
import {useWorld} from '../context/WorldContext';
import {captureArtifact,getArtifactTemplates} from '../api';
import './artifacts.css';

export function PublishDocument({node}){
  const [open,setOpen]=useState(false);
  return <><button className="button secondary" onClick={()=>setOpen(true)}>发布审计报告</button>
    {open&&<PublishDialog key={node.id} node={node} onClose={()=>setOpen(false)}/>}</>;
}

function PublishDialog({node,onClose}){
  const {projectId}=useWorld(),state=usePublisher(projectId,node);
  return <Modal title="发布结构化报告" open onClose={state.busy?()=>{}:onClose}>
    <div className="publish-document"><p>报告将关联到「{node.content.title}」。已有资料保持原样。</p>
      <TemplateFields node={node} state={state}/><DocumentInput state={state}/>
      {state.error&&<div role="alert"><p>{state.error.message}</p><ul>{state.error.errors?.map((e,i)=><li key={i}>{e.path}：{e.message}</li>)}</ul></div>}
      {state.valid&&<p role="status">结构、篇幅与证据引用校验通过。</p>}
      {state.saved?<a className="button primary" href={state.saved.view_url} target="_blank" rel="noreferrer">阅读已发布报告</a>:
        <div className="form-actions"><button className="button secondary" disabled={state.busy||!state.template} onClick={()=>state.submit('validate')}>校验</button>
          <button className="button primary" disabled={state.busy||!state.template} onClick={()=>state.submit('capture')}>{state.busy?'处理中…':'校验并发布'}</button></div>}
    </div>
  </Modal>;
}

function TemplateFields({node,state}){
  return <><label>报告模板<select value={state.template?.id||''} onChange={e=>state.change('schemaId',e.target.value)}>
    {state.templates.map(t=><option key={t.id} value={t.id}>{t.title}</option>)}</select></label>
    <label>被审原件<select value={state.target} onChange={e=>state.change('target',e.target.value)}>
      <option value="">选择该对象已关联的产物</option>{node.artifact_ids.map(id=><option key={id} value={id}>{attachmentName(node,id)}</option>)}
    </select></label><button className="button secondary" disabled={!state.template||!state.target} onClick={state.download}>下载填写示例</button>
    <p className="muted">正文最多 {state.template?.max_reading_chars||'—'} 字符。超长日志和推导请作为独立附件引用。</p></>;
}

function attachmentName(node,id){
  return node.content.attachments?.find(a=>a.id===id)?.name||id;
}

function DocumentInput({state}){
  return <><label>报告文件来源<select value={state.mode} onChange={e=>state.change('mode',e.target.value)}>
    <option value="upload">上传 JSON 文件</option><option value="workspace">实验工作区文件</option></select></label>
    {state.mode==='workspace'?<label>工作区相对路径<input value={state.path} placeholder="reports/audit.json" onChange={e=>state.change('path',e.target.value)}/></label>:
      <label>选择已填写的报告<input type="file" accept=".json,application/json" onChange={e=>state.change('file',e.target.files[0]||null)}/></label>}
  </>;
}

function usePublisher(projectId,node){
  const [templates,setTemplates]=useState([]),[values,setValues]=useState({schemaId:'',target:node.artifact_ids[0]||'',mode:'upload',path:'',file:null});
  const [busy,setBusy]=useState(false),[error,setError]=useState(null),[valid,setValid]=useState(false),[saved,setSaved]=useState(null);
  useEffect(()=>{let current=true;getArtifactTemplates(projectId).then(v=>{if(current)setTemplates(v);}).catch(e=>{if(current)setError(e);});return()=>{current=false;};},[projectId]);
  const template=templates.find(t=>t.id===values.schemaId)||templates[0];
  const change=(key,value)=>{setValues(v=>({...v,[key]:value}));setValid(false);setSaved(null);setError(null);};
  const submit=async operation=>{
    setBusy(true);setError(null);setValid(false);
    try{const body=await publicationBody(values,template,node.id,operation);const result=await captureArtifact(projectId,body);operation==='validate'?setValid(true):setSaved(result);}
    catch(e){setError(e);}finally{setBusy(false);}
  };
  return {...values,templates,template,busy,error,valid,saved,change,submit,download:()=>downloadExample(template,values.target)};
}

async function publicationBody(values,template,recordId,operation){
  const body={schema_id:template.id,record_id:recordId,target_artifact_id:values.target,operation};
  if(values.mode==='workspace')return {...body,path:values.path};
  if(!values.file)throw Error('请选择填写后的 JSON 文件');
  if(values.file.size>4*1024*1024)throw Error('文件超过 4 MiB');
  const data=JSON.parse(await values.file.text());
  if(data.target_artifact_id!==values.target)throw Error('文件中的被审原件与所选原件不同，请核对版本');
  return {...body,content:JSON.stringify(data)};
}

function downloadExample(template,target){
  const data={...template.example,target_artifact_id:target};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download='audit-report.json';anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
