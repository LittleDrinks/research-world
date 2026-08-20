import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { displayLabel, formatTime, shortId } from "../../utils";
import { pairedEvents } from "../../utils/pairing";
import { Badge } from "./bits";
import { oneLine } from "./format";

export function WireView({ events }) {
  const [query, setQuery] = useState("");
  const visible = useMemo(() => pairedEvents(events).filter((event) => JSON.stringify(event).toLowerCase().includes(query.toLowerCase())), [events, query]);
  return <div>
    <label className="wire-search"><Search size={16} /><input aria-label="搜索事件" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索事件" /></label>
    <div className="act-wire">{visible.map((event, index) => <WireRow key={event.event_id} event={event} index={index} />)}{!visible.length && <p className="act-empty">没有匹配的事件。</p>}</div>
  </div>;
}

function WireRow({ event, index }) {
  return <details className="act-wire-row"><summary>
    <span className="act-idx">{index + 1}</span>
    <time>{formatTime(event.time, false)}</time>
    <Badge kind={wireKind(event)}>{event.pair ? "工具调用 / 结果" : displayLabel(event.type)}</Badge>
    <span className="act-line" title={eventSummary(event)}>{oneLine(eventSummary(event), 160)}</span>
    <code>{shortId(event.attempt_id || event.entity.id)}</code>
  </summary><pre>{JSON.stringify(event, null, 2)}</pre></details>;
}

function wireKind(event) {
  if (event.payload?.error || event.type.includes("fail")) return "error";
  if (event.type.startsWith("tool")) return "tool";
  if (event.type.startsWith("attempt")) return "turn";
  return "muted";
}

function eventSummary(event) {
  const result = event.pair?.payload.error || event.pair?.payload.result;
  return event.payload.message || event.payload.error || readable(result) || Object.values(event.payload).filter((value) => typeof value === "string").join(" · ") || `${event.entity.type} ${shortId(event.entity.id)}`;
}

function readable(value) {
  return typeof value === "string" ? value : value ? JSON.stringify(value) : "";
}
