import { shortId } from "../../utils";
import { Badge, Fold } from "./bits";
import { argSummary, messageText, roleLabel } from "./format";

export function ContextView({ items }) {
  if (!items.length) return <p className="act-empty">暂无上下文记录。</p>;
  return <div className="act-context">{items.map((item) => <AttemptContext key={item.attempt_id} item={item} />)}</div>;
}

function AttemptContext({ item }) {
  const messages = item.content?.messages || [];
  return <details open className="act-block"><summary><b>{item.actor}</b><span>{messages.length} 条消息</span><code>{shortId(item.attempt_id)}</code></summary>
    <div className="act-msgs">
      {messages.map((message, index) => <MessageCard key={index} message={message} />)}
      {!messages.length && <InputFold input={item.content?.input} />}
    </div></details>;
}

function InputFold({ input }) {
  if (!input) return <p className="act-empty">暂无消息记录。</p>;
  const text = JSON.stringify(input, null, 2);
  return <Fold meta={`输入 · ${text.length} 字符`}>{text}</Fold>;
}

function MessageCard({ message }) {
  const text = messageText(message.content);
  const thinking = messageText(message.reasoning_content);
  const calls = message.tool_calls || [];
  return <div className={`act-msg ${message.role}`}>
    <header><Badge kind={message.role}>{roleLabel(message.role)}</Badge>{thinking ? <Badge kind="think">思考</Badge> : null}{calls.length ? <Badge kind="muted">{calls.length} 次工具调用</Badge> : null}</header>
    {thinking ? <Fold meta={`思考 · ${thinking.length} 字符`}>{thinking}</Fold> : null}
    <BodyText role={message.role} text={text} />
    {calls.map((call, index) => <CallChip key={call.id || index} call={call} />)}
  </div>;
}

function BodyText({ role, text }) {
  if (!text) return null;
  if (role === "tool") return <Fold meta={`工具结果 · ${text.length} 字符`}>{text}</Fold>;
  if (role === "system" || text.length > 320) return <Fold meta={`${roleLabel(role)}内容 · ${text.length} 字符`}>{text}</Fold>;
  return <p className="act-msg-text">{text}</p>;
}

function CallChip({ call }) {
  const name = call.function?.name || call.name || "tool";
  return <div className="act-call"><Badge kind="call">CALL</Badge><code className="act-chip">{name} {argSummary(call.function?.arguments ?? call.arguments, 140)}</code><span className="act-call-id">{shortId(call.id)}</span></div>;
}
