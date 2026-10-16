import '../settings.css';
import {useEffect, useState} from 'react';
import {useParams} from 'react-router-dom';
import {agents, catalog, saveAgent} from '../sessionApi';
import {useWorld} from '../context/WorldContext';
import '../agents.css';

export function AgentsPage() {
  const {agentId} = useParams();
  const {refresh, setError} = useWorld();
  const [values,setValues] = useState([]), [options,setOptions] = useState(null), [draft,setDraft] = useState(null);
  useEffect(() => {Promise.all([agents(),catalog()]).then(([a,c]) => {
    setValues(a);setOptions(c);setDraft(a.find(v=>v.id===agentId)||a[0]);
  }).catch(e=>setError(e.message));},[agentId]);
  async function save(event) {
    event.preventDefault();
    try {const value=await saveAgent(draft);setDraft(value);setValues(await agents());await refresh();setError('');}
    catch(e){setError(e.message);}
  }
  if(!draft||!options) return <p>正在载入 Pi 配置…</p>;
  return <section className="settings-page"><h1>Agent · Pi</h1>
    <select aria-label="选择 Agent" value={values.some(v=>v.id===draft.id)?draft.id:''} onChange={e=>setDraft(values.find(v=>v.id===e.target.value))}>{values.map(v=><option key={v.id} value={v.id}>{v.name}</option>)}</select>
    <button className="button secondary" onClick={()=>setDraft({...draft,id:`agent-${Date.now()}`,name:'新研究 Agent'})}>复制为新 Agent</button>
    <AgentForm draft={draft} patch={(key,value)=>setDraft({...draft,[key]:value})} options={options} save={save}/></section>;
}

function AgentForm({draft,patch,options,save}) {
  return <form className="form-stack" onSubmit={save}>
    <label className="field">名称<input required value={draft.name} onChange={e=>patch('name',e.target.value)}/></label>
    <label className="field">模型<select value={draft.model} onChange={e=>patch('model',e.target.value)}>{options.models.map(m=><option key={m}>{m}</option>)}</select></label>
    <label className="field">思考级别<select value={draft.thinking} onChange={e=>patch('thinking',e.target.value)}>{['off','minimal','low','medium','high','xhigh','max'].map(v=><option key={v}>{v}</option>)}</select></label>
    <label className="field">指令<textarea rows={8} required value={draft.instructions} onChange={e=>patch('instructions',e.target.value)}/></label>
    <p>工作区已内置：Agent 可直接读写、编辑和运行项目文件，与 JupyterLab 共享。</p>
    <Choices title="Tools" values={Object.entries(options.tools).filter(([id])=>id!=='workspace')} selected={draft.tools} onChange={v=>patch('tools',v)}/>
    <Choices title="Skills" values={options.skills.map(v=>[v,v])} selected={draft.skills} onChange={v=>patch('skills',v)}/>
    <p>保存后新建对话生效；已有对话保留启动时的配置。</p><button className="button primary">保存 Agent</button>
  </form>;
}

function Choices({title,values,selected,onChange}) {
  return <fieldset className="pi-capabilities"><legend>{title}</legend><div>{values.map(([id,label])=><label style={{display:'block'}} key={id}>
    <input type="checkbox" checked={selected.includes(id)} onChange={e=>onChange(e.target.checked?[...selected,id]:selected.filter(v=>v!==id))}/>{label}
  </label>)}</div></fieldset>;
}
