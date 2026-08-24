import {
  Activity, AlertTriangle, ArrowLeft, Box, Braces, CheckCircle2, ChevronDown, ChevronRight,
  CircleDot, Clock3, Copy, Filter, GitBranch, Menu, MessageSquareText,
  PanelRightOpen, Search, TerminalSquare, X, Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  FALLBACK_CONTENT, SOURCE_LABEL, STATUS_LABEL, TRACE_CONTENT, TRACE_RELATIONS, TRACE_ROWS, TRACE_RUNS, TRACE_SUMMARY, TRACE_THREADS,
} from "./trace-seed";
import "./trace-page-prototype.css";

const TYPE_ICON = { stage: GitBranch, step: Zap, session: Activity, turn: MessageSquareText, response: Braces, tool: TerminalSquare };
const SCENES = ["running", "completed", "failed", "cancelled", "empty", "loading"];
const TABS = ["overview", "input", "output", "diff", "artifact", "raw"];
const TAB_LABEL = { overview: "概览", input: "输入", output: "输出", diff: "Diff", artifact: "Artifact", raw: "原始" };
const MAX_LINES = 200;
const MAX_CONTENT = 256 * 1024;

function sceneRows(scene) {
  if (scene === "completed") return TRACE_ROWS.map((row) => ({ ...row, status: "completed", duration: row.duration === "--" ? "18s" : row.duration }));
  if (scene === "failed") return TRACE_ROWS.map((row) => ["tool-search", "turn-execute", "session-b", "step-2", "stage-execute"].includes(row.id) ? { ...row, status: "failed", duration: "2m 11s" } : row);
  if (scene === "cancelled") return cancelledRows();
  return TRACE_ROWS;
}

function cancelledRows() {
  const completed = new Set(["step-2", "session-b", "tool-search"]);
  return TRACE_ROWS.map((row) => {
    if (row.id === "turn-execute") return { ...row, status: "cancelled", duration: "2m 04s" };
    return completed.has(row.id) ? { ...row, status: "completed", duration: "2m 04s" } : row;
  });
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

function useTraceModel(initialScene) {
  const [scene, setSceneValue] = useState(initialScene);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [selected, setSelected] = useState(null);
  const [expanded, setExpanded] = useState(new Set(TRACE_ROWS.map((row) => row.id)));
  const [railOpen, setRailOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const rows = useMemo(() => filteredRows(sceneRows(scene), query, type, errorsOnly), [scene, query, type, errorsOnly]);
  const setScene = (next) => { setSceneValue(next); setSelected(null); setInspectorOpen(false); };
  return { scene, setScene, query, setQuery, type, setType, errorsOnly, setErrorsOnly, selected, setSelected, expanded, setExpanded, railOpen, setRailOpen, inspectorOpen, setInspectorOpen, rows };
}

export function TracePagePrototype() {
  const context = useMemo(traceContext, []);
  const model = useTraceModel(context.run?.status || "empty");
  const [activeRun, setActiveRun] = useState(context.run);
  const chooseRun = (run) => { setActiveRun(run); model.setScene(run.status); model.setRailOpen(false); };
  const stateOnly = ["empty", "loading"].includes(model.scene);
  return <div className={`tp-shell ${model.railOpen ? "tp-rail-open" : ""} ${stateOnly ? "tp-state-only" : ""}`}>
    <RunRail active={activeRun} choose={chooseRun} close={() => model.setRailOpen(false)} context={context} />
    <main className="tp-main"><MobileBar open={() => model.setRailOpen(true)} run={activeRun} />
      <TraceWorkspace model={model} run={activeRun} context={context} /></main>
    {!stateOnly && <TraceInspector model={model} />}
  </div>;
}

function validId(value, prefix) {
  return new RegExp(`^${prefix}:[A-Za-z0-9_-]{1,64}$`).test(value || "") ? value : "";
}

function validProject(value, notices) {
  if (value === "project:q49") return value;
  notices.push("project_id 无效或不可访问，已回退到 /projects");
  return "";
}

function validThread(value, project, notices) {
  if (!value) return "";
  const thread = validId(value, "thread");
  if (TRACE_THREADS.some((item) => item.id === thread && item.project === project)) return thread;
  notices.push("thread_id 不属于当前 Project，已移除 Thread scope");
  return "";
}

function scopedRuns(project, thread) {
  return TRACE_RUNS.filter((run) => run.project === project && (!thread || run.thread === thread));
}

function selectRun(raw, runs, notices) {
  const fallback = runs.find((run) => run.status === "running") || runs[0] || null;
  if (!raw) return fallback;
  if (!/^fixture:run-[A-Za-z0-9_-]{1,64}$/.test(raw)) notices.push("run_id 非法，已回退到 scope 内默认 run");
  else if (!TRACE_RUNS.some((run) => run.id === raw)) notices.push("run_id 不存在，已回退到 scope 内默认 run");
  else if (!runs.some((run) => run.id === raw)) notices.push("run_id 不属于当前 Project/Thread，已回退到 scope 内默认 run");
  else return runs.find((run) => run.id === raw);
  return fallback;
}

function safeReturn(raw, project, thread) {
  const fallback = thread ? `/chat/${encodeURIComponent(thread)}` : project ? "/map" : "/projects";
  if (!raw || !project) return fallback;
  let url;
  try { url = new URL(raw, window.location.origin); } catch { return fallback; }
  if (url.origin !== window.location.origin || url.hash) return fallback;
  if (url.pathname === "/projects" && !url.search) return "/projects";
  if (validMapReturn(url)) return `${url.pathname}${url.search}`;
  return validChatReturn(url, thread) ? `/chat/${encodeURIComponent(thread)}` : fallback;
}

function validMapReturn(url) {
  return url.pathname === "/map" && !url.search;
}

function validChatReturn(url, thread) {
  if (!thread || url.search || !url.pathname.startsWith("/chat/")) return false;
  try { return decodeURIComponent(url.pathname.slice(6)) === thread; } catch { return false; }
}

function traceContext() {
  const params = new URLSearchParams(window.location.search);
  const notices = [];
  const project = validProject(params.get("project_id"), notices);
  const thread = validThread(params.get("thread_id"), project, notices);
  const runs = scopedRuns(project, thread);
  const run = selectRun(params.get("run_id"), runs, notices);
  const from = safeReturn(params.get("from"), project, thread);
  const origin = from === "/projects" ? "Project" : from.startsWith("/map") ? "Graph" : "Chat";
  return { project, thread, runs, run, notices, from, origin };
}

function RunRail({ active, choose, close, context }) {
  const [status, setStatus] = useState("all");
  const rows = context.runs.filter((run) => status === "all" || run.status === status);
  return <aside className="tp-run-rail"><header><div><small>{context.project || "Project 无效"} · {context.runs.length} FIXTURES</small><b>{context.thread || "Project scope"}</b></div><button onClick={close} aria-label="关闭运行列表"><X size={18} /></button></header>
    <label className="tp-rail-search"><Search size={14} /><span className="sr-only">筛选状态</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">全部状态</option><option value="running">运行中</option><option value="failed">失败</option><option value="completed">已完成</option></select></label>
    <div className="tp-run-list">{rows.map((run) => <RunItem key={run.id} run={run} active={active?.id === run.id} choose={choose} />)}</div>
    <footer><SourceTag source="existing" /><span>静态 fixture</span></footer>
  </aside>;
}

function RunItem({ run, active, choose }) {
  return <button className={`tp-run-item ${active ? "active" : ""}`} onClick={() => choose(run)}>
    <StatusMark status={run.status} /><span><b>{run.name}</b><code>{run.id}</code><SourceTag source={run.source} /></span>
    <small>{STATUS_LABEL[run.status]}<time>{run.time}</time></small>
  </button>;
}

function MobileBar({ open, run }) {
  return <header className="tp-mobile-bar"><button onClick={open} aria-label="打开运行列表"><Menu size={19} /></button><span><b>{run?.name || "Trace"}</b><code>{run?.id || "无可见 run"}</code></span>{run && <StatusMark status={run.status} />}</header>;
}

function TraceWorkspace({ model, run, context }) {
  if (["empty", "loading"].includes(model.scene)) return <TraceState scene={model.scene} model={model} context={context} />;
  const rows = visibleByFold(model.rows, model.expanded);
  return <section className="tp-workspace"><RunHeader model={model} run={run} context={context} />
    <SourceLegend /><SummaryBand scene={model.scene} /><RelationStrip /><TraceOverview rows={model.rows} scene={model.scene} />
    <TraceToolbar model={model} /><div className="tp-tree" role="tree">{rows.map((row) => <TraceRow key={row.id} row={row} model={model} />)}</div>
    {!rows.length && <div className="tp-filter-empty"><Search size={24} /><b>无匹配事件</b><button onClick={() => { model.setQuery(""); model.setType("all"); model.setErrorsOnly(false); }}>清除筛选</button></div>}
  </section>;
}

function TraceState({ scene, model, context }) {
  const loading = scene === "loading";
  return <section className={`tp-state-screen ${loading ? "loading" : ""}`}><Activity size={28} /><h1>{loading ? "正在载入 Trace" : "暂无运行"}</h1>
    <p>{context.notices[0] || (loading ? "旧 inspector 已隔离" : "Pipeline run 创建后显示在此处")}</p><a href={context.from}><ArrowLeft size={14} />返回 {context.origin}</a>
    {context.run && <button onClick={() => model.setScene("running")}>查看 running fixture</button>}</section>;
}

function RunHeader({ model, run, context }) {
  const status = model.scene === "cancelled" ? "paused" : model.scene;
  return <><header className="tp-run-header"><div className="tp-heading"><span>{context.project || "无有效 Project"} / {context.thread || "Project scope"} / Trace</span><h1>{run.name} <code>{run.id}</code> <SourceTag source="existing" /></h1><p><button className="tp-node-disabled" disabled>Node：当前 Compose 无可达节点</button> <SourceTag source="missing" /> · 当前 execute <SourceTag source="derived" /></p></div>
    <div className="tp-header-actions"><a className="tp-back-chat" href={context.from}><ArrowLeft size={15} />返回 {context.origin}</a><SceneSelect model={model} /><CopyButton value={run.id} title="复制完整 fixture ID" /><StatusBadge status={status} /></div></header>
    <ContextNotices notices={context.notices} />{model.scene === "failed" && <ErrorBanner model={model} />}{model.scene === "cancelled" && <CancelBanner />}</>;
}

function ContextNotices({ notices }) {
  if (!notices.length) return null;
  return <div className="tp-context-banner" role="status"><AlertTriangle size={15} /><span>{notices.join("；")}</span></div>;
}

function SourceLegend() {
  return <div className="tp-source-legend"><span>字段来源</span>{Object.keys(SOURCE_LABEL).map((source) => <SourceTag key={source} source={source} />)}</div>;
}

function SourceTag({ source }) {
  return <small className={`tp-source ${source}`} data-source={source}>{SOURCE_LABEL[source]}</small>;
}

function SceneSelect({ model }) {
  return <label className="tp-scene"><span className="sr-only">Prototype 状态</span><select value={model.scene} onChange={(event) => model.setScene(event.target.value)}>
    {SCENES.map((scene) => <option key={scene} value={scene}>{scene === "completed" ? "complete" : scene}</option>)}</select></label>;
}

function CopyButton({ value, title = "复制可见内容" }) {
  const [copied, setCopied] = useState(false);
  const copy = () => navigator.clipboard?.writeText(value).then(() => { setCopied(true); window.setTimeout(() => setCopied(false), 1200); });
  return <button className="tp-icon-button" onClick={copy} title={title} aria-label={title}>{copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}</button>;
}

function jumpToError(model) {
  model.setQuery(""); model.setType("all"); model.setErrorsOnly(false);
  model.setExpanded(new Set(TRACE_ROWS.map((row) => row.id)));
  model.setSelected("tool-search"); model.setInspectorOpen(true);
  requestAnimationFrame(() => document.getElementById("tool-search")?.scrollIntoView({ block: "center" }));
}

function ErrorBanner({ model }) {
  return <button className="tp-error-banner" onClick={() => jumpToError(model)}><AlertTriangle size={16} /><b>graph_query 失败</b><SourceTag source="existing" /><ChevronRight size={16} /></button>;
}

function CancelBanner() {
  return <div className="tp-cancel-banner"><b>Turn 2 已取消</b><SourceTag source="existing" /><span>Run cancelled：待 API/不可用</span><SourceTag source="missing" /></div>;
}

function SummaryBand({ scene }) {
  const summary = scene === "cancelled" ? TRACE_SUMMARY.map((item) => item.label === "进度" ? { ...item, value: "Turn cancelled", note: "Run 状态不可用" } : item) : TRACE_SUMMARY;
  return <section className="tp-summary" aria-label="运行摘要">{summary.map((item) => <div key={item.label}><span>{item.label}</span><b>{item.value}</b><small>{item.note}</small><SourceTag source={item.source} /></div>)}</section>;
}

function RelationStrip() {
  return <nav className="tp-relations" aria-label="关联记录">{TRACE_RELATIONS.map((item) => item.href
    ? <a key={item.label} href={item.href}><Relation item={item} /></a>
    : <button key={item.label} disabled title={item.source === "missing" ? "待 API/不可用" : "无独立路由"}><Relation item={item} /></button>)}</nav>;
}

function Relation({ item }) {
  return <><span>{item.label}</span><b>{item.value}</b><SourceTag source={item.source} />{item.href && <ChevronRight size={13} />}</>;
}

function TraceOverview({ rows, scene }) {
  return <section className="tp-overview"><header><span><Clock3 size={14} />OVERVIEW <SourceTag source="derived" /></span><b>{scene === "running" ? "LIVE · 06:42" : "06:42"}</b></header>
    <div className="tp-overview-scale"><span>00:00</span><span>02:00</span><span>04:00</span><span>06:00</span></div>
    <div className="tp-lanes">{rows.filter((row) => ["stage", "session"].includes(row.type)).slice(0, 6).map((row) => <OverviewLane key={row.id} row={row} />)}<i className="tp-now" /></div>
  </section>;
}

function OverviewLane({ row }) {
  return <div className="tp-lane"><span>{row.type === "stage" ? row.label : `↳ ${row.label}`}</span><i className={row.status} style={{ left: `${row.start}%`, width: `${row.width}%` }} /></div>;
}

function TraceToolbar({ model }) {
  const expandAll = () => model.setExpanded(new Set(TRACE_ROWS.map((row) => row.id)));
  return <div className="tp-toolbar"><label className="tp-search"><Search size={15} /><input value={model.query} onChange={(event) => model.setQuery(event.target.value)} placeholder="搜索已加载 fixture" /></label>
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
    <span className="tp-row-copy"><b>{row.label}</b><small>{row.type.toUpperCase()} · {row.meta}</small><SourceTag source={row.source} /></span><StatusBadge status={row.status} compact />
    <time>{row.duration}</time><code>{row.tokens}</code><PanelRightOpen className="tp-open-inspector" size={15} />
  </button>;
}

function TraceInspector({ model }) {
  const [tab, setTab] = useState("output");
  const rows = sceneRows(model.scene);
  const row = rows.find((item) => item.id === model.selected);
  if (!row) return <EmptyInspector open={model.inspectorOpen} close={() => model.setInspectorOpen(false)} />;
  const content = contentForRow(row);
  const session = sessionForRow(row, rows);
  return <aside className={`tp-inspector ${model.inspectorOpen ? "open" : ""}`}><header><div><span>INSPECTOR</span><b>{content.title}</b><small>{content.subtitle}</small></div><button onClick={() => model.setInspectorOpen(false)} aria-label="关闭检查器"><X size={18} /></button></header>
    <div className="tp-inspector-meta"><SourceTag source={content.source} /><span>脱敏 provenance</span><SourceTag source="missing" /></div>
    <nav>{TABS.map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{TAB_LABEL[item]}</button>)}</nav>
    <div className="tp-inspector-body"><InspectorContent tab={tab} content={content} row={row} session={session} /></div>
  </aside>;
}

function EmptyInspector({ open, close }) {
  return <aside className={`tp-inspector tp-inspector-empty ${open ? "open" : ""}`}><header><div><span>INSPECTOR</span><b>选择事件</b><small>未选择任何 row</small></div><button onClick={close} aria-label="关闭检查器"><X size={18} /></button></header><div className="tp-unavailable"><PanelRightOpen size={20} /><span>从因果树选择事件</span></div></aside>;
}

function contentForRow(row) {
  const content = TRACE_CONTENT[row.id] || FALLBACK_CONTENT;
  return { ...content, title: TRACE_CONTENT[row.id]?.title || row.label, subtitle: `${row.type} · ${row.status} · fixture` };
}

function sessionForRow(row, rows) {
  const byId = new Map(rows.map((item) => [item.id, item]));
  let current = row;
  while (current && current.type !== "session") current = byId.get(current.parent);
  return current?.id || "待 API/不可用";
}

function InspectorContent({ tab, content, row, session }) {
  if (tab === "overview") return <OverviewContent row={row} session={session} />;
  if (tab === "input") return <JsonBlock field={content.input} />;
  if (tab === "output") return <OutputContent field={content.output} />;
  if (tab === "diff") return <MissingContent label="normalized diff" />;
  if (tab === "artifact") return <ArtifactContent />;
  return <JsonBlock field={{ source: "existing", value: content }} />;
}

function OverviewContent({ row, session }) {
  const sessionSource = session === "待 API/不可用" ? "missing" : "derived";
  return <dl className="tp-inspector-grid"><InspectorField label="Status" value={row.status} source="existing" /><InspectorField label="Duration" value={row.duration} source="derived" /><InspectorField label="Session" value={session} source={sessionSource} /><InspectorField label="Parent" value={row.parent || "无"} source={row.parent ? "existing" : "missing"} /><InspectorField label="Event type" value={row.type} source="existing" /><InspectorField label="Event id" value={row.id} source="existing" /></dl>;
}

function InspectorField({ label, value, source }) {
  return <div><dt>{label}</dt><dd>{value}</dd><SourceTag source={source} /></div>;
}

function JsonBlock({ field }) {
  const [expanded, setExpanded] = useState(false);
  const lines = JSON.stringify(field.value, null, 2).split("\n");
  const visible = expanded ? lines : lines.slice(0, MAX_LINES);
  return <section className="tp-bounded"><header><SourceTag source={field.source} /><span>{lines.length} 行</span><CopyButton value={visible.join("\n")} /></header><pre className="tp-code"><code>{visible.join("\n")}</code></pre>
    {lines.length > MAX_LINES && <button className="tp-content-toggle" onClick={() => setExpanded(!expanded)}>{expanded ? "折叠到 200 行" : `展开全部 ${lines.length} 行`}</button>}</section>;
}

function OutputContent({ field }) {
  const bytes = new TextEncoder().encode(field.value).length;
  const visible = field.value.slice(0, MAX_CONTENT);
  return <section className="tp-bounded"><header><SourceTag source={field.source} /><span>{bytes} bytes</span><CopyButton value={visible} /></header><section className="tp-terminal"><header><TerminalSquare size={13} />stdout</header><pre>{visible}</pre></section>
    {bytes > MAX_CONTENT && <div className="tp-truncated" role="status">已显示 256 KiB；其余 {bytes - MAX_CONTENT} bytes 已截断。Artifact：待 API/不可用 <SourceTag source="missing" /></div>}</section>;
}

function MissingContent({ label }) {
  return <section className="tp-unavailable"><AlertTriangle size={20} /><b>{label}</b><span>待 API/不可用</span><SourceTag source="missing" /></section>;
}

function ArtifactContent() {
  return <section className="tp-artifact"><Box size={22} /><span><b>Artifact metadata/read</b><code>待 API/不可用</code><SourceTag source="missing" /></span><button disabled title="待 API/不可用">打开 Artifact</button></section>;
}

function StatusMark({ status }) {
  return <i className={`tp-status-mark ${status}`} aria-label={STATUS_LABEL[status] || status} />;
}

function StatusBadge({ status, compact }) {
  return <span className={`tp-status-badge ${status} ${compact ? "compact" : ""}`}><StatusMark status={status} />{STATUS_LABEL[status] || status}</span>;
}
