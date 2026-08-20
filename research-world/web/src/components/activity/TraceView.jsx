import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { formatTime } from "../../utils";
import { Badge } from "./bits";
import { argSummary, fmtMs, fmtTokens, messageText, oneLine, roleLabel } from "./format";
import { parseRecord } from "./trace";

export function TraceView({ wire }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const rows = useMemo(() => traceRows(wire), [wire]);
  const visible = useMemo(() => rows.filter((row) => JSON.stringify(row.record).toLowerCase().includes(query.toLowerCase())), [rows, query]);
  const current = rows.find((row) => row.key === selected);
  return <div>
    <label className="wire-search"><Search size={16} /><input aria-label="搜索轨迹" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索轨迹" /></label>
    <div className="trace-view">
      <div className="trace-list">
        {visible.map((row, index) => <TraceRow key={row.key} row={row} index={index} selected={selected === row.key} onSelect={() => setSelected(row.key)} />)}
        {!visible.length && <p className="act-empty">没有匹配的轨迹记录。</p>}
      </div>
      <TraceInspector row={current?.record} previous={current && rows[rows.indexOf(current) - 1]?.record} />
    </div>
  </div>;
}

function traceRows(wire) {
  return (wire || []).flatMap((attempt) => (attempt.content?.trace || []).flatMap((trace) => {
    const records = trace.jsonl.split("\n").filter(Boolean).map(parseRecord).filter(Boolean);
    return records.sort((a, b) => (a.turn_index - b.turn_index) || (a.event_index - b.event_index))
      .map((record) => ({ key: `${attempt.attempt_id}:${trace.name}:${record.event_index}`, record }));
  }));
}

function rowRole(record) {
  return record.capture_type === "llm_call" ? "runtime" : record.role || "trace";
}

function rowSummary(record) {
  if (record.capture_type === "llm_call") return oneLine(messageText(record.payload?.response?.content), 140) || "LLM 调用";
  if (record.role === "tool") return (record.tool_names || []).map((name, index) => `${name} ${argSummary(record.tool_arguments?.[index])}`).join(" · ") || "工具结果";
  return oneLine(record.text || record.error || "（无文本）", 140);
}

function rowMeta(record) {
  const response = record.payload?.response || {};
  const usage = response.usage || {};
  const parts = [];
  if (record.capture_type === "llm_call") parts.push(record.payload?.model_name || record.model_name);
  if (response.finish_reason || record.finish_reason) parts.push(response.finish_reason || record.finish_reason);
  if (usage.total_tokens) parts.push(`${fmtTokens(usage.total_tokens)} tokens`);
  return parts.filter(Boolean).join(" · ");
}

function TraceRow({ row, index, selected, onSelect }) {
  const role = rowRole(row.record);
  return <button className={`trace-row ${selected ? "selected" : ""}`} onClick={onSelect}>
    <span className="act-idx">{index + 1}</span>
    <Badge kind={role}>{roleLabel(role)}</Badge>
    <span className="act-line" title={rowSummary(row.record)}>{rowSummary(row.record)}</span>
    <span className="trace-meta">{rowMeta(row.record)}</span>
    <time>{formatTime(row.record.timestamp, false)}</time>
  </button>;
}

const TABS = [["summary", "Summary"], ["preview", "Preview"], ["raw", "Raw"]];

function TraceInspector({ row, previous }) {
  const [tab, setTab] = useState("summary");
  useEffect(() => setTab("summary"), [row]);
  if (!row) return <aside className="inspector trace-inspector"><div className="inspector-empty">点击左侧的记录行查看详情，LLM 调用行可查看请求。</div></aside>;
  if (row.capture_type !== "llm_call") {
    return <aside className="inspector trace-inspector"><div className="inspector-scroll">
      <span className="eyebrow">{roleLabel(rowRole(row))}</span>
      <h2>{rowSummary(row)}</h2>
      <p className="muted">{formatTime(row.timestamp)}</p>
      <section className="inspector-section"><h3>原始数据</h3><pre className="chat-json">{JSON.stringify(row, null, 2)}</pre></section>
    </div></aside>;
  }
  return <aside className="inspector trace-inspector"><div className="inspector-scroll">
    <span className="eyebrow">LLM 请求</span>
    <h2>{row.payload?.model_name || row.model_name || "模型调用"}</h2>
    <div className="segmented trace-tabs">{TABS.map(([id, label]) => <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{label}</button>)}</div>
    {tab === "summary" && <SummaryTab row={row} previous={previous} />}
    {tab === "preview" && <PreviewTab payload={row.payload || {}} />}
    {tab === "raw" && <pre className="chat-json trace-raw">{JSON.stringify(row, null, 2)}</pre>}
  </div></aside>;
}

function SummaryTab({ row, previous }) {
  const response = row.payload?.response || {};
  const usage = response.usage || {};
  const gap = previous?.timestamp && row.timestamp ? fmtMs(Math.max(0, new Date(row.timestamp) - new Date(previous.timestamp))) : "-";
  const facts = [
    ["模型", row.payload?.model_name || row.model_name || "-"],
    ["finish_reason", response.finish_reason || row.finish_reason || "-"],
    ["Prompt tokens", fmtTokens(usage.prompt_tokens)],
    ["Completion tokens", fmtTokens(usage.completion_tokens)],
    ["Total tokens", fmtTokens(usage.total_tokens)],
    ["Reasoning", response.reasoning_content ? "有" : "无"],
    ["时间", formatTime(row.timestamp)],
    ["与上一条间隔", gap],
  ];
  return <section className="inspector-section inspector-facts"><dl>{facts.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></section>;
}

function PreviewTab({ payload }) {
  const messages = payload.request_messages || [];
  const response = messageText(payload.response?.content);
  return <section className="inspector-section">
    <div className="act-msgs trace-preview">
      {messages.map((message, index) => <div className="act-msg" key={index}>
        <header><Badge kind={message.role}>{roleLabel(message.role)}</Badge></header>
        <p className="act-msg-text">{oneLine(messageText(message.content), 400) || "（无文本）"}</p>
      </div>)}
      {response && <div className="act-msg"><header><Badge kind="assistant">{roleLabel("assistant")} · 回复</Badge></header><p className="act-msg-text">{oneLine(response, 800)}</p></div>}
      {!messages.length && !response && <p className="act-empty">没有可预览的消息。</p>}
    </div>
  </section>;
}
