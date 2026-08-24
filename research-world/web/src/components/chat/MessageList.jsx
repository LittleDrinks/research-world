import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { shortId } from "../../utils/labels";
import { NodePeek } from "./NodePeek";


const MENTION = /@(node:[A-Za-z0-9]+)/g;


export function MessageList({ messages, streaming }) {
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, streaming]);
  return <div className="message-list">
    {!messages.length && !streaming && <p className="message-placeholder">暂无消息。直接提问，或输入 @ 引用节点作为上下文。</p>}
    {messages.map((message, index) => <Message key={index} message={message} />)}
    {streaming ? <article className="message assistant"><span>助手</span>
      <div className="markdown streaming"><ReactMarkdown>{streaming}</ReactMarkdown><i className="cursor-block" /></div></article> : null}
    <div ref={end} /></div>;
}


function Message({ message }) {
  return <article className={`message ${message.role}`}><span>{message.role === "user" ? "你" : "助手"}</span>
    {message.role === "assistant"
      ? <div className="markdown"><ReactMarkdown>{message.content}</ReactMarkdown></div>
      : <p><MentionText text={message.content} /></p>}</article>;
}


function MentionText({ text }) {
  return text.split(MENTION).map((part, index) =>
    index % 2 ? <InlineMention key={index} nodeId={part} /> : part);
}


function InlineMention({ nodeId }) {
  const [open, setOpen] = useState(false);
  return <><button className="inline-mention" onClick={() => setOpen(!open)}>@{shortId(nodeId)}</button>
    {open && <NodePeek nodeId={nodeId} />}</>;
}
