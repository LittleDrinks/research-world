import ReactMarkdown from 'react-markdown';

const TOOL_NAMES={graph:'查询研究地图',record:'保存研究方向',connect:'连接证据',artifact:'保存研究产物',literature:'检索文献',delegate:'委派独立 Agent'};

export function Conversation({detail,events,active,connection,sending}){
  return <div className="pi-messages"><div className="pi-transcript">
    {detail.session.messages.map(message=>{
      const turn=detail.run.turns.find(t=>t.message_id===message.id);
      const live=turn?.id===active?.id;
      return <Message key={message.id} message={message} turn={turn} events={live?events:(turn?.events||[])} active={live} connection={connection}/>;
    })}
    {sending&&!active&&<p className="pi-status" role="status">正在发送…</p>}
  </div></div>;
}

function Message({message,turn,events,active,connection}){
  const streaming=active?events.filter(e=>e.type==='delta').map(e=>e.data.text||'').join(''):'';
  const answer=message.assistant_response||streaming;
  return <article data-turn-id={turn?.id}><div className="pi-user"><span className="pi-role">你</span><ReactMarkdown>{message.content}</ReactMarkdown></div>
    {answer&&<div className="pi-assistant"><span className="pi-role">研究助手</span><ReactMarkdown>{answer}</ReactMarkdown></div>}
    {active&&<p className="pi-status" role="status"><span className="pi-spinner"/>{statusText(events,connection)}</p>}
    {turn?.status==='error'&&<p className="pi-failure" role="alert">本轮执行失败，请查看轨迹中的错误后重试。</p>}
    {turn?.status==='cancelled'&&<p className="pi-status">已取消本轮工作。</p>}
    <WorkSteps events={events}/>
  </article>;
}

function statusText(events,connection){
  if(connection==='reconnecting')return '连接中断，正在恢复；研究任务仍在运行…';
  const tool=events.filter(e=>e.type==='tool').at(-1);
  if(tool?.data.phase==='started')return `${TOOL_NAMES[tool.data.name]||'正在调用工具'}…`;
  if(events.at(-1)?.type==='reasoning')return '正在思考…';
  return events.some(e=>e.type==='delta')?'正在回复…':'正在思考…';
}

function WorkSteps({events}){
  const tools=new Map();
  for(const event of events.filter(e=>e.type==='tool'))tools.set(event.data.id,{...tools.get(event.data.id),...event.data});
  const children=events.filter(e=>e.type==='child_result');
  if(!tools.size&&!children.length)return null;
  return <details className="pi-work"><summary>工作过程 · {tools.size} 次工具调用{children.length?` · ${children.length} 个子 Agent`:''}</summary>
    {[...tools.values()].map(tool=><div key={tool.id}><b>{TOOL_NAMES[tool.name]||tool.name}</b><span> · {tool.is_error?'失败':tool.phase==='completed'?'完成':'进行中'}</span></div>)}
    {children.map(child=><div key={child.seq}><b>独立 Agent 的结果</b><ReactMarkdown>{child.data.result_text||child.data.status}</ReactMarkdown></div>)}
  </details>;
}
