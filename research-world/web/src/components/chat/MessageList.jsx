import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { shortId } from "../../utils/labels";
import { NodePeek } from "./NodePeek";
import { PublicationMessage, ReportMessage, ReportProgressMessage } from "./ReportCard";
import { traceReportKey } from "./reportState";


const MENTION = /@(node:[A-Za-z0-9]+)/g;


export function MessageList({ messages, streaming, reports = [], publications = [], reportProgress, replacements = {}, requests, threadId, reportTitle, onReportPublished, onReportRefresh, turns = [] }) {
  const end = useRef(null);
  const entries = chatEntries(messages, reports, publications, turns, streaming, replacements);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, entries, reportProgress, streaming]);
  return <div className="message-list">
    {!messages.length && !entries.length && !reportProgress && !streaming && <p className="message-placeholder">暂无消息。直接提问，或输入 @ 引用节点作为上下文。</p>}
    {entries.map((entry, index) => <ChatEntry key={entryKey(entry, index)} entry={entry} threadId={threadId} title={reportTitle} onPublished={onReportPublished} onRefresh={onReportRefresh} requests={requests} />)}
    {reportProgress && <ReportProgressMessage update={reportProgress} />}
    {streaming ? <article className="message assistant"><span>助手</span>
      <div className="markdown streaming"><ReactMarkdown>{streaming}</ReactMarkdown><i className="cursor-block" /></div></article> : null}
    <div ref={end} /></div>;
}


function chatEntries(messages, reports, publications, turns, streaming, replacements) {
  if (!streaming && reports.some((report) => report.turn_id) && turns.length) return turnEntries(reports, publications, turns, replacements);
  return [...messages.map((message) => ({ message })), ...reportEntries(reports, publications, new Set(), replacements)];
}


function turnEntries(reports, publications, turns, replacements) {
  const seen = new Set();
  const entries = turns.flatMap((turn) => oneTurn(turn, reports, publications, replacements, seen));
  const published = new Set(entries.map(entryPublicationId).filter(Boolean));
  return [...entries, ...reportEntries(reports.filter((report) => !seen.has(report)), publications, published, replacements)];
}


function oneTurn(turn, reports, publications, replacements, seen) {
  const result = reports.filter((report) => report.turn_id === turn.id).sort((a, b) => a.seq - b.seq);
  result.forEach((report) => seen.add(report));
  return [turnInput(turn), ...result.map((item) => reportEntry(item, publications, replacements)), turnOutput(turn)].filter(Boolean);
}


function turnInput(turn) {
  const content = turn.input?.map((item) => item.text).filter(Boolean).join("\n");
  return content ? { message: { role: "user", content } } : null;
}


function turnOutput(turn) {
  return turn.output ? { message: { role: "assistant", content: turn.output } } : null;
}


function reportEntries(reports, publications, known = new Set(), replacements = {}) {
  const entries = reports.map((report) => reportEntry(report, publications, replacements));
  entries.forEach((entry) => { const id = entryPublicationId(entry); if (id) known.add(id); });
  return [...entries, ...publications.filter((item) => !known.has(item.id)).map((publication) => ({ publication }))];
}


function reportEntry(report, publications, replacements) {
  const key = traceReportKey(report);
  const publication = publications.find((item) => item.id === replacements[key]);
  return publication ? { publication, key } : { result: report, key };
}


function entryPublicationId(entry) {
  return entry.result?.publication?.id || entry.publication?.id;
}


function entryKey(entry, index) {
  if (entry.key) return entry.key;
  if (entry.result?.publication?.id || entry.publication?.id) return entry.result?.publication?.id || entry.publication.id;
  return entry.result ? `report-${entry.result.turn_id || "untraced"}-${entry.result.seq ?? index}` : `${entry.message?.role || "message"}-${index}`;
}


function ChatEntry({ entry, threadId, title, onPublished, onRefresh, requests }) {
  if (entry.message) return <Message message={entry.message} />;
  if (entry.result) return <ReportMessage result={entry.result} threadId={threadId} title={title} onPublished={onPublished} onRefresh={onRefresh} requests={requests} />;
  return <PublicationMessage publication={entry.publication} />;
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
