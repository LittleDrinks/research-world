import { useMemo } from "react";
import { formatTime, shortId } from "../../utils";
import { Badge, Fold } from "./bits";
import { argSummary, fmtDuration, fmtMs, fmtTokens, oneLine, roleLabel } from "./format";
import { traceTurns, turnStats } from "./trace";

export function Overview({ events, jobs, wire }) {
  const turnsByAttempt = useMemo(() => new Map(wire.map((item) => [item.attempt_id, traceTurns(item)])), [wire]);
  const stats = overviewStats(events, jobs, turnsByAttempt);
  const generations = [...new Set(jobs.map((job) => job.generation_id).filter(Boolean))];
  return <div>
    <div className="act-stats">{stats.map(([label, value]) => <div className="act-stat" key={label}><span>{label}</span><b>{value}</b></div>)}</div>
    {generations.map((generation, index) => <Generation key={generation} index={index} jobs={jobs.filter((job) => job.generation_id === generation)} turnsByAttempt={turnsByAttempt} />)}
    {!generations.length && <p className="act-empty">暂无执行记录。</p>}
  </div>;
}

function overviewStats(events, jobs, turnsByAttempt) {
  const turns = [...turnsByAttempt.values()].flat();
  const tokens = turns.reduce((sum, turn) => sum + turnStats(turn).tokens, 0);
  const errors = turns.reduce((sum, turn) => sum + turnStats(turn).errors, 0) + events.filter((event) => event.payload?.error).length;
  const times = events.map((event) => new Date(event.time).getTime()).filter(Number.isFinite);
  const span = times.length ? fmtMs(Math.max(...times) - Math.min(...times)) : "-";
  return [["代际", new Set(jobs.map((job) => job.generation_id)).size], ["尝试", jobs.length], ["总 Tokens", fmtTokens(tokens)], ["错误", errors], ["总耗时", span]];
}

function Generation({ index, jobs, turnsByAttempt }) {
  return <details open className="act-block"><summary><b>代际 {index + 1}</b><span>{jobs.length} 次尝试</span><code>{shortId(jobs[0]?.generation_id)}</code></summary>
    <div className="act-attempts">{jobs.map((job) => <Attempt key={job.id} job={job} turns={turnsByAttempt.get(job.id) || []} />)}</div></details>;
}

function Attempt({ job, turns }) {
  const tokens = turns.reduce((sum, turn) => sum + turnStats(turn).tokens, 0);
  return <details open className="act-block act-attempt"><summary><i className={`state-dot ${job.status}`} /><b>{job.actor}</b><span>{turns.length} 轮</span><span>{fmtTokens(tokens)} tokens</span><span>{fmtDuration(job.created_at, job.completed_at)}</span><code>{shortId(job.id)}</code></summary>
    <div className="act-turns">{turns.map((turn, index) => <Turn key={turn.key} turn={turn} index={index} />)}{!turns.length && <p className="act-empty">暂无轨迹记录。</p>}</div></details>;
}

function Turn({ turn, index }) {
  const stats = turnStats(turn);
  const meta = `${turn.records.length} 步 · ${fmtTokens(stats.tokens)} tokens${stats.errors ? ` · ${stats.errors} 错误` : ""}${stats.wait ? ` · 等待 ${fmtMs(stats.wait)}` : ""}`;
  return <details className="act-turn"><summary><Badge kind="turn">第 {index + 1} 轮</Badge><span>{meta}</span></summary>
    <ol className="act-steps">{turn.records.map((record) => <Step key={record.event_index} record={record} />)}</ol></details>;
}

function Step({ record }) {
  const role = record.role || record.capture_type || "trace";
  const text = record.text || record.error || record.termination || "（无文本）";
  return <li className="act-step">
    <Badge kind={role}>{roleLabel(role)}</Badge>
    <div className="act-step-main">
      <StepText role={role} text={text} />
      <ToolChips names={record.tool_names} args={record.tool_arguments} />
      {record.error && record.text ? <span className="act-error">{oneLine(record.error)}</span> : null}
    </div>
    <time>{formatTime(record.timestamp, false)}</time>
  </li>;
}

function StepText({ role, text }) {
  if (role === "system") return <Fold meta={`系统提示词 · ${text.length} 字符`}>{text}</Fold>;
  if (text.length > 240) return <Fold meta={`${text.length} 字符`}>{text}</Fold>;
  return <span className="act-line" title={text}>{oneLine(text)}</span>;
}

function ToolChips({ names = [], args = [] }) {
  if (!names.length) return null;
  return <div className="act-chips">{names.map((name, index) => <code className="act-chip" key={`${name}:${index}`}>{name} {argSummary(args[index])}</code>)}</div>;
}
