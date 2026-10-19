import {ChatMarkdown} from '../chat/ChatMarkdown';
import {useWorld} from '../context/WorldContext';

export function RecordContent({content}){
  const {projectId}=useWorld();
  const extra=Object.entries(content).filter(([key])=>!['title','text','attachments','origin','note'].includes(key));
  return <section className="inspector-section node-body"><ChatMarkdown projectId={projectId}>{String(content.text||'')}</ChatMarkdown>
    {extra.length>0&&<details className="node-details"><summary>来源与记录信息</summary><dl className="node-record">{extra.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{typeof value==='string'?value:JSON.stringify(value)}</dd></div>)}</dl></details>}
  </section>;
}
