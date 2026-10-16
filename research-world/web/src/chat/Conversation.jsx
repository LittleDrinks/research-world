import ReactMarkdown from 'react-markdown';
import {mergeEvents,timeline} from './timeline';

const TOOL_NAMES={graph:'查询研究地图',record:'保存研究方向',connect:'连接证据',artifact:'保存研究产物',literature:'检索文献',delegate:'委派独立 Agent',read:'读取文件',write:'写入文件',edit:'编辑文件',bash:'执行命令'};

export function Conversation({detail,events,active,connection,sending}){
  return <div className="pi-messages"><div className="pi-transcript">
    {detail.session.messages.map(message=>{
      const turn=detail.run.turns.find(t=>t.message_id===message.id);
      const live=turn?.id===active?.id;
      const ordered=mergeEvents(turn?.events||[],live?events.filter(e=>e.turn_id===turn.id):[]);
      return <Message key={message.id} message={message} turn={turn} events={ordered} active={live} connection={connection}/>;
    })}
    {sending&&!active&&<p className="pi-status" role="status">正在发送…</p>}
  </div></div>;
}

function Message({message,turn,events,active,connection}){
  const parts=timeline(events);
  const answer=parts.some(part=>part.type==='text')?'':message.assistant_response;
  return <article data-turn-id={turn?.id}><div className="pi-user"><span className="pi-role">你</span><ReactMarkdown>{message.content}</ReactMarkdown></div>
    {(parts.length>0||answer)&&<div className="pi-assistant"><span className="pi-role">研究助手</span>
      {parts.map(part=><Part key={`${part.type}:${part.id}`} part={part} status={turn?.status}/>)}
      {answer&&<ReactMarkdown>{answer}</ReactMarkdown>}
    </div>}
    {active&&<p className="pi-status" role="status"><span className="pi-spinner"/>{statusText(events,connection)}</p>}
    {turn?.status==='error'&&<p className="pi-failure" role="alert">本轮执行失败，请查看轨迹中的错误后重试。</p>}
    {turn?.status==='cancelled'&&<p className="pi-status">已取消本轮工作。</p>}
  </article>;
}

function Part({part,status}){
  if(part.type==='tool')return <ToolCall tool={part.tool} status={status}/>;
  if(part.type==='child')return <div className="pi-child"><b>独立 Agent 的结果</b><ReactMarkdown>{part.result_text||part.status}</ReactMarkdown></div>;
  return <div className="pi-text"><ReactMarkdown>{part.text}</ReactMarkdown></div>;
}

function ToolCall({tool,status}){
  const stopped=status&&status!=='running';
  const label=tool.is_error?'失败':tool.phase==='completed'?'完成':stopped?'已中断':'进行中';
  const output=tool.result??tool.partial_result;
  return <details className="pi-tool" data-tool-id={tool.id} open={label==='进行中'||label==='失败'}>
    <summary><b>{TOOL_NAMES[tool.name]||tool.name}</b><code>{tool.arguments?.path||tool.arguments?.command||''}</code><span>{label}</span></summary>
    {tool.arguments&&<div><small>输入</small><pre>{JSON.stringify(tool.arguments,null,2)}</pre></div>}
    {output!==undefined&&<div><small>结果</small><pre>{toolOutput(output)}</pre></div>}
  </details>;
}

function toolOutput(value){
  if(typeof value==='string')return value;
  if(Array.isArray(value?.content))return value.content.map(item=>item.type==='text'?item.text:'[图片]').join('\n');
  return JSON.stringify(value,null,2);
}

function statusText(events,connection){
  if(connection==='reconnecting')return '连接中断，正在恢复；研究任务仍在运行…';
  const pending=timeline(events).filter(p=>p.type==='tool'&&p.tool.phase!=='completed');
  if(pending.length)return `${TOOL_NAMES[pending.at(-1).tool.name]||'正在调用工具'}…`;
  if(events.at(-1)?.type==='reasoning')return '正在思考…';
  return events.some(e=>e.type==='delta')?'正在回复…':'正在思考…';
}
