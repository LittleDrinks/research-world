import {ChatMarkdown} from './ChatMarkdown';
import {splitThinking} from './thinking';

export function Thinking({text,projectId}) {
  return <details className="pi-thinking"><summary>思考过程</summary>
    <div className="thinking-body"><ChatMarkdown projectId={projectId}>{text}</ChatMarkdown></div>
  </details>;
}

export function AssistantMarkdown({children='',projectId}) {
  return splitThinking(children).parts.map((part,index)=>part.type==='thinking'
    ? <Thinking key={index} text={part.text} projectId={projectId}/>
    : <ChatMarkdown key={index} projectId={projectId}>{part.text}</ChatMarkdown>);
}
