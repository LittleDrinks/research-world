import {
  Activity, AlertTriangle, Archive, ArrowLeft, Box, Braces, CheckCircle2, ChevronDown, ChevronRight,
  CircleDot, Clock3, Copy, Filter, GitBranch, Menu, MessageSquareText,
  PanelRightOpen, Pause, Search, ShieldAlert, TerminalSquare, X, Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  FALLBACK_CONTENT, STATUS_LABEL, TRACE_CONTENT, TRACE_RELATIONS, TRACE_ROWS, TRACE_RUNS, TRACE_SUMMARY,
} from "./trace-seed";
import "./trace-page-prototype.css";

const TYPE_ICON = { stage: GitBranch, step: Zap, session: Activity, turn: MessageSquareText, response: Braces, tool: TerminalSquare };
const SCENES = ["running", "completed", "failed", "paused", "cancelled", "empty", "loading"];
const TABS = ["overview", "input", "output", "diff", "artifact", "raw"];
const TAB_LABEL = { overview: "概览", input: "输入", output: "输出", diff: "Diff", artifact: "Artifact", raw: "原始" };

function sceneRows(scene) {
  if (scene === "completed") return TRACE_ROWS.map((row) => ({ ...row, status: "completed", duration: row.duration === "--" ? "18s" : row.duration }));
  if (scene === "failed") return TRACE_ROWS.map((row) => row.id === "tool-search" || row.id === "session-b" || row.id === "stage-execute" ? { ...row, status: "failed", duration: "2m 11s" } : row);
  if (scene === "paused") return TRACE_ROWS.map((row) => row.status === "running" ? { ...row, status: "paused", duration: "已暂停" } : row);
  if (scene === "cancelled") return TRACE_ROWS.map((row) => row.id === "session-b" || row.id === "tool-search" ? { ...row, status: "cancelled", duration: "2m 04s" } : row.id === "stage-execute" ? { ...row, status: "paused" } : row);
  return TRACE_ROWS;
}

function ancestors(rows, matches) {
  const byId = new Map(rows.map((row) => [row.id, row]));
  const visible = new Set(matches);
  matches.forEach((id) => { let row = byId.get(id); while (row?.parent) { visible.add(row.parent); row = byId.get(row.parent); } });
  return visible;
}

function filteredRows(rows, query, type, errorsOnly) {
  const term = query.trim().toLowerCase();
  const matching = rows.filter((row) => (!term || `${row.label} ${row.meta} ${row.id}`.toLowerCase().includes(term))
    && (type === "all" || row.type === type) && (!errorsOnly || row.status === "failed"));
  if (!term && type === "all" && !errorsOnly) return rows;
  const visible = ancestors(rows, matching.map((row) => row.id));
  return rows.filter((row) => visible.has(row.id));
}

function visibleByFold(rows, expanded) {
  const byId = new Map(rows.map((row) => [row.id, row]));
  return rows.filter((row) => { let parent = row.parent; while (parent) { if (!expanded.has(parent)) return false; parent = byId.get(parent)?.parent; } return true; });
}

function useTraceModel() {
  const [scene, setScene] = useState("running");
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [selected, setSelected] = useState("tool-write");
  const [expanded, setExpanded] = useState(new Set(TRACE_ROWS.map((row) => row.id)));
  const [railOpen, setRailOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const rows = useMemo(() => filteredRows(sceneRows(scene), query, type, errorsOnly), [scene, query, type, errorsOnly]);
  return { scene, setScene, query, setQuery, type, setType, errorsOnly, setErrorsOnly, selected, setSelected, expanded, setExpanded, railOpen, setRailOpen, inspectorOpen, setInspectorOpen, rows };
}

export function TracePagePrototype() {
  const model = useTraceModel();
  const [activeRun, setActiveRun] = useState(TRACE_RUNS[1]);
  const context = traceContext();
  const chooseRun = (run) => { setActiveRun(run); model.setScene(run.status); model.setRailOpen(false); };
  return <div className={`tp-shell ${model.railOpen ? "tp-rail-open" : ""}`}>
    <RunRail active={activeRun} choose={chooseRun} close={() => model.setRailOpen(false)} context={context} />
    <main className="tp-main"><MobileBar open={() => model.setRailOpen(true)} run={activeRun} />
      <TraceWorkspace model={model} run={activeRun} context={context} /></main>
    <TraceInspector model={model} />
  </div>;
}

function traceContext() {
  const params = new URLSearchParams(window.location.search);
  return { project: params.get("project_id") || "project:q49", thread: params.get("thread_id") || "thread:orbital", from: params.get("from") || "/chat/thread:orbital" };
}

function RunRail({ active, choose, close, context }) {
  const [status, setStatus] = useState("all");
  const rows = TRACE_RUNS.filter((run) => status === "all" || run.status === status);
  return <aside className="tp-run-rail"><header><div><small>{context.project} · {TRACE_RUNS.length} RUNS</small><b>{context.thread}</b></div><button onClick={close} aria-label="关闭运行列表"><X size={18} /></button></header>
    <label className="tp-rail-search"><Search size={14} /><span className="sr-only">筛选状态</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">全部状态</option><option value="running">运行中</option><option value="failed">失败</option><option value="completed">已完成</option></select></label>
    <div className="tp-run-list">{rows.map((run) => <RunItem key={run.id} run={run} active={active.id === run.id} choose={choose} />)}</div>
    <footer><span><CircleDot size={12} />5 秒前更新</span><button title="暂停列表更新"><Pause size={14} /></button></footer>
  </aside>;
}

function RunItem({ run, active, choose }) {
  return <button className={`tp-run-item ${active ? "active" : ""}`} onClick={() => choose(run)}>
    <StatusMark status={run.status} /><span><b>{run.name}</b><code>{run.id} · node {run.node}</code></span>
    <small>{STATUS_LABEL[run.status]}<time>{run.time}</time></small>
  </button>;
}

function MobileBar({ open, run }) {
  return <header className="tp-mobile-bar"><button onClick={open} aria-label="打开运行列表"><Menu size={19} /></button><span><b>{run.name}</b><code>{run.id}</code></span><StatusMark status={run.status} /></header>;
}

function TraceWorkspace({ model, run, context }) {
  if (model.scene === "empty" || model.scene === "loading") return <TraceState scene={model.scene} model={model} />;
  const rows = visibleByFold(model.rows, model.expanded);
  return <section className="tp-workspace"><RunHeader model={model} run={run} context={context} />
    <SummaryBand scene={model.scene} /><RelationStrip run={run} /><TraceOverview rows={model.rows} scene={model.scene} />
    <TraceToolbar model={model} /><div className="tp-tree" role="tree">{rows.map((row) => <TraceRow key={row.id} row={row} model={model} />)}</div>
    {!rows.length && <div className="tp-filter-empty"><Search size={24} /><b>无匹配事件</b><button onClick={() => { model.setQuery(""); model.setType("all"); model.setErrorsOnly(false); }}>清除筛选</button></div>}
  </section>;
}

function TraceState({ scene, model }) {
  const loading = scene === "loading";
  return <section className={`tp-state-screen ${loading ? "loading" : ""}`}><Activity size={28} /><h1>{loading ? "正在载入 Trace" : "暂无运行"}</h1>
    <p>{loading ? "" : "Pipeline run 创建后显示在此处"}</p><button onClick={() => model.setScene("running")}>{loading ? "返回运行态" : "查看运行态"}</button></section>;
}

function RunHeader({ model, run, context }) {
  const status = model.scene === "cancelled" ? "paused" : model.scene;
  return <><header className="tp-run-header"><div className="tp-heading"><span>{context.project} / {context.thread} / Trace</span><h1>{run.name} <code>run:{run.id}</code></h1><p>node:{run.node} · lineage:8f3d · 当前 execute</p></div>
    <div className="tp-header-actions"><a className="tp-back-chat" href={context.from}><ArrowLeft size={15} />返回对话</a><SceneSelect model={model} /><CopyButton value={`run:${run.id}`} /><StatusBadge status={status} /></div></header>
    {model.scene === "failed" && <ErrorBanner />}{model.scene === "cancelled" && <CancelBanner />}</>;
}

function SceneSelect({ model }) {
  return <label className="tp-scene"><span className="sr-only">Prototype 状态</span><select value={model.scene} onChange={(event) => model.setScene(event.target.value)}>
    {SCENES.map((scene) => <option key={scene} value={scene}>{scene === "cancelled" ? "Turn cancelled" : scene}</option>)}</select></label>;
}

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);
  const copy = () => navigator.clipboard?.writeText(value).then(() => { setCopied(true); window.setTimeout(() => setCopied(false), 1200); });
  return <button className="tp-icon-button" onClick={copy} title="复制完整 Run ID">{copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}</button>;
}

function ErrorBanner() {
  return <button className="tp-error-banner" onClick={() => document.getElementById("tool-search")?.scrollIntoView({ block: "center" })}><AlertTriangle size={16} /><b>graph_query 失败</b><span>Connection closed</span><ChevronRight size={16} /></button>;
}

function CancelBanner() {
  return <div className="tp-cancel-banner"><Pause size={15} /><b>Turn 已取消</b><span>Run cancelled 状态未记录 · 待 Kernel API</span></div>;
}

function SummaryBand({ scene }) {
  const summary = scene === "cancelled" ? TRACE_SUMMARY.map((item) => item.label === "进度" ? { ...item, value: "Turn cancelled", note: "Run 待 API" } : item) : TRACE_SUMMARY;
  return <section className="tp-summary" aria-label="运行摘要">{summary.map((item) => <div key={item.label}><span>{item.label}</span><b>{item.value}</b><small>{item.note}</small></div>)}</section>;
}

function RelationStrip({ run }) {
  const relations = TRACE_RELATIONS.map((item) => item.label === "Node" ? { ...item, value: run.node } : item);
  return <nav className="tp-relations" aria-label="关联记录">{relations.map((item) => <button key={item.label}><span>{item.label}</span><b className={item.tone}>{item.value}</b><ChevronRight size={13} /></button>)}</nav>;
}

function TraceOverview({ rows, scene }) {
  return <section className="tp-overview"><header><span><Clock3 size={14} />OVERVIEW</span><b>{scene === "running" ? "LIVE · 06:42" : "06:42"}</b></header>
    <div className="tp-overview-scale"><span>00:00</span><span>02:00</span><span>04:00</span><span>06:00</span></div>
    <div className="tp-lanes">{rows.filter((row) => ["stage", "session"].includes(row.type)).slice(0, 6).map((row) => <OverviewLane key={row.id} row={row} />)}<i className="tp-now" /></div>
  </section>;
}

function OverviewLane({ row }) {
  return <div className="tp-lane"><span>{row.type === "stage" ? row.label : `↳ ${row.label}`}</span><i className={row.status} style={{ left: `${row.start}%`, width: `${row.width}%` }} /></div>;
}

function TraceToolbar({ model }) {
  const expandAll = () => model.setExpanded(new Set(TRACE_ROWS.map((row) => row.id)));
  return <div className="tp-toolbar"><label className="tp-search"><Search size={15} /><input value={model.query} onChange={(event) => model.setQuery(event.target.value)} placeholder="搜索事件、Tool、ID" /></label>
    <label className="tp-select"><Filter size={14} /><select value={model.type} onChange={(event) => model.setType(event.target.value)}><option value="all">全部类型</option><option value="session">Session</option><option value="tool">Tool</option><option value="response">Response</option></select></label>
    <label className="tp-errors"><input type="checkbox" checked={model.errorsOnly} onChange={(event) => model.setErrorsOnly(event.target.checked)} />仅异常</label>
    <div className="tp-fold"><button onClick={() => model.setExpanded(new Set())}>折叠</button><button onClick={expandAll}>展开</button></div>
  </div>;
}

function TraceRow({ row, model }) {
  const Icon = TYPE_ICON[row.type] || CircleDot;
  const expandable = TRACE_ROWS.some((item) => item.parent === row.id);
  const open = model.expanded.has(row.id);
  const select = () => { model.setSelected(row.id); model.setInspectorOpen(true); };
  const toggle = (event) => { event.stopPropagation(); model.setExpanded((value) => { const next = new Set(value); next.has(row.id) ? next.delete(row.id) : next.add(row.id); return next; }); };
  return <button id={row.id} role="treeitem" aria-selected={model.selected === row.id} className={`tp-row ${model.selected === row.id ? "selected" : ""}`} style={{ "--depth": row.depth }} onClick={select}>
    <span className="tp-branch">{expandable ? <span onClick={toggle}>{open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</span> : <i />}</span><Icon className="tp-type-icon" size={15} />
    <span className="tp-row-copy"><b>{row.label}</b><small>{row.type.toUpperCase()} · {row.meta}</small></span><StatusBadge status={row.status} compact />
    <time>{row.duration}</time><code>{row.tokens}</code><PanelRightOpen className="tp-open-inspector" size={15} />
  </button>;
}

function TraceInspector({ model }) {
  const [tab, setTab] = useState("output");
  const content = TRACE_CONTENT[model.selected] || FALLBACK_CONTENT;
  return <aside className={`tp-inspector ${model.inspectorOpen ? "open" : ""}`}><header><div><span>INSPECTOR</span><b>{content.title}</b><small>{content.subtitle}</small></div><button onClick={() => model.setInspectorOpen(false)} aria-label="关闭检查器"><X size={18} /></button></header>
    <div className="tp-inspector-meta"><span><ShieldAlert size={13} />脱敏标记：未记录</span><CopyButton value={JSON.stringify(content, null, 2)} /></div>
    <nav>{TABS.map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{TAB_LABEL[item]}</button>)}</nav>
    <div className="tp-inspector-body"><InspectorContent tab={tab} content={content} /></div>
  </aside>;
}

function InspectorContent({ tab, content }) {
  if (tab === "overview") return <OverviewContent content={content} />;
  if (tab === "input") return <JsonBlock value={content.input} />;
  if (tab === "output") return <OutputContent content={content} />;
  if (tab === "diff") return <DiffContent lines={content.diff} />;
  if (tab === "artifact") return <ArtifactContent artifact={content.artifact} />;
  return <JsonBlock value={content} />;
}

function OverviewContent({ content }) {
  return <dl className="tp-inspector-grid"><div><dt>Status</dt><dd>completed</dd></div><div><dt>Duration</dt><dd>52s</dd></div><div><dt>Token</dt><dd>--</dd></div><div><dt>Cost</dt><dd>未记录</dd></div><div><dt>Parent</dt><dd>session-b</dd></div><div><dt>Event</dt><dd>{content.title}</dd></div></dl>;
}

function JsonBlock({ value }) {
  return <pre className="tp-code"><code>{JSON.stringify(value, null, 2)}</code></pre>;
}

function OutputContent({ content }) {
  return <><section className="tp-terminal"><header><TerminalSquare size={13} />stdout</header><pre>{content.output}</pre></section><article className="tp-markdown"><ReactMarkdown>{content.markdown}</ReactMarkdown></article></>;
}

function DiffContent({ lines }) {
  return <pre className="tp-diff">{lines.map((line, index) => <span key={`${line}-${index}`} className={line.startsWith("+") ? "add" : line.startsWith("-") ? "remove" : "hunk"}><i>{index + 1}</i>{line}</span>)}</pre>;
}

function ArtifactContent({ artifact }) {
  return <section className="tp-artifact"><Box size={22} /><span><b>Immutable Artifact</b><code>{artifact.id}</code></span><dl><dt>Media type</dt><dd>{artifact.media_type}</dd><dt>Size</dt><dd>{artifact.size}</dd><dt>Admission</dt><dd>{artifact.admission}</dd></dl><button><Archive size={15} />打开 Artifact</button></section>;
}

function StatusMark({ status }) {
  return <i className={`tp-status-mark ${status}`} aria-label={STATUS_LABEL[status] || status} />;
}

function StatusBadge({ status, compact }) {
  return <span className={`tp-status-badge ${status} ${compact ? "compact" : ""}`}><StatusMark status={status} />{STATUS_LABEL[status] || status}</span>;
}
