import { Download, Eye, FileText, Save } from "lucide-react";
import { useState } from "react";
import { publishThreadReport, saveThreadReport } from "../../api";
import { traceReportKey } from "./reportState";


const stageLabels = { projection: "读取投影", citation_validation: "引用校验", rendering: "生成", output_validation: "最终校验", persistence: "发布" };


export function ReportCard({ threadId, title, reports = [], onRefresh, requests }) {
  const [state, setState] = useState(emptyState());
  const scope = `report-card:${threadId}`;
  const publish = () => publishReport(threadId, title, setState, onRefresh, requests, scope);
  return <section className="report-workflow" aria-label="报告发布"><ReportHeader onPublish={publish} />
    <ReportProgress state={state} setState={setState} onRetry={publish} onRefresh={onRefresh} requests={requests} scope={scope} />
    <ReportHistory threadId={threadId} reports={reports} />
  </section>;
}


export function ReportMessage({ threadId, result, title, onPublished, onRefresh, requests }) {
  const [state, setState] = useState(resultState(result));
  const scope = traceReportKey(result);
  const retry = () => retryReport(threadId, result.title || title, state, setState, onRefresh, requests, scope, result, onPublished);
  return <article className="message assistant report-message"><span>助手</span><section className="report-workflow">
    <ReportMessageHeader failed={state.error !== null} />
    <ReportProgress state={state} setState={setState} onRetry={retry} onRefresh={onRefresh} requests={requests} scope={scope} />
  </section></article>;
}


export function PublicationMessage({ publication }) {
  return <article className="message assistant report-message"><span>助手</span><section className="report-workflow">
    <ReportMessageHeader failed={false} /><PublishedRecord publication={publication} />
  </section></article>;
}


export function ReportProgressMessage({ update }) {
  return <article className="message assistant report-message" role="status"><span>助手</span>
    <section className="report-workflow"><header><FileText size={16} /><b>{update?.title || "正在生成报告"}</b></header></section></article>;
}


function emptyState() {
  return { stages: [], result: null, error: null, saved: null, refresh: null };
}


function resultState(result) {
  const value = { ...emptyState(), stages: result.stages || [] };
  return result.status === "published" ? { ...value, result } : { ...value, error: result.assessment?.gaps || [] };
}


async function publishReport(threadId, title, setState, onRefresh, requests, scope) {
  const request = requests.next(scope);
  setState(emptyState());
  try {
    const result = await publishThreadReport(threadId, { title });
    if (!requests.latest(request)) return;
    setState(resultState(result));
    if (result.status === "published") await refreshQuietly(onRefresh, setState, requests, request);
  } catch (error) {
    if (requests.latest(request)) setState({ ...emptyState(), error: [failureGap(error)] });
  }
}


async function retryReport(threadId, title, previous, setState, onRefresh, requests, scope, source, onPublished) {
  const request = requests.next(scope);
  try {
    const result = await publishThreadReport(threadId, { title });
    if (!requests.latest(request)) return;
    setState(resultState(result));
    if (result.status !== "published") return;
    onPublished?.(source, result);
    await refreshQuietly(onRefresh, setState, requests, request);
  } catch (error) {
    if (requests.latest(request)) setState({ ...previous, error: [failureGap(error)] });
  }
}


async function refreshQuietly(onRefresh, setState, requests, request) {
  try {
    const refreshed = await onRefresh?.(request);
    if (refreshed !== false && requests.latest(request)) return;
  } catch {
    if (requests.latest(request)) setState((value) => ({ ...value, refresh: "failed" }));
  }
}


function failureGap(error) {
  return { code: error.code || "request_failed", path: "request", value: null };
}


function ReportHeader({ onPublish }) {
  return <header><FileText size={16} /><b>可信报告</b><button className="button secondary" onClick={onPublish}>生成报告</button></header>;
}


function ReportMessageHeader({ failed }) {
  return <header><FileText size={16} /><b>{failed ? "报告发布失败" : "报告已发布"}</b></header>;
}


function ReportProgress({ state, setState, onRetry, onRefresh, requests, scope }) {
  return <>{state.stages.length > 0 && <ReportStages rows={state.stages} />}
    {state.error && <ReportFailure gaps={state.error} onRetry={onRetry} />}
    {state.result && <ReportResult result={state.result} saved={state.saved} onSaved={(saved) => setState((value) => ({ ...value, saved }))} onRefresh={onRefresh} requests={requests} scope={scope} />}
    {state.refresh === "failed" && <p role="status">报告已发布，刷新失败。</p>}</>;
}


function ReportStages({ rows }) {
  const actual = rows.filter((row) => stageLabels[row.name] && ["completed", "failed"].includes(row.status));
  return <ol className="report-stages">{actual.map((row) => <li className={row.status} key={row.name}>{stageLabels[row.name]}</li>)}</ol>;
}


function ReportFailure({ gaps, onRetry }) {
  return <div className="report-failure" role="alert"><span>{gaps.map(gapText).join("; ")}</span><button className="button secondary" onClick={onRetry}>重试</button></div>;
}


function gapText(gap) {
  return `${gap.code}: ${gap.path} = ${JSON.stringify(safeGapValue(gap.value))}`;
}


function safeGapValue(value) {
  return value === null || ["number", "boolean"].includes(typeof value) ? value : null;
}


function ReportResult({ result, saved, onSaved, onRefresh, requests, scope }) {
  const [name, setName] = useState("");
  const [error, setError] = useState(null);
  const save = () => saveReport(result, name, onSaved, onRefresh, setError, requests, scope);
  return <div className="report-result"><ReportDetails result={result} /><ReportLinks publication={result.publication} />
    {saved ? <p className="report-saved">已保存版本 {saved.id}</p> : <ReportSave name={name} onName={setName} onSave={save} error={error} />}</div>;
}


async function saveReport(result, name, onSaved, onRefresh, setError, requests, scope) {
  const request = requests.next(scope);
  try {
    const saved = await saveThreadReport(result.publication.thread_id, { title: name, publication_id: result.publication.id });
    if (!requests.latest(request)) return;
    onSaved(saved);
    try { await onRefresh?.(request); } catch {}
    if (!requests.latest(request)) return;
  } catch (failure) { if (requests.latest(request)) setError(failure.code || "request_failed"); }
}


function ReportDetails({ result }) {
  return <dl><dt>标题</dt><dd>{result.title}</dd><dt>时间</dt><dd>{result.publication.created_at}</dd><dt>交付级别</dt><dd>{result.assessment.delivery_level}</dd><dt>引用</dt><dd>已校验</dd><dt>最低来源</dt><dd>{result.assessment.minimum_source_level}</dd></dl>;
}


function PublishedRecord({ publication }) {
  return <div className="report-result"><dl><dt>标题</dt><dd>{publication.title}</dd><dt>时间</dt><dd>{publication.created_at}</dd></dl><ReportLinks publication={publication} /></div>;
}


function ReportLinks({ publication }) {
  const root = `/api/v1/threads/${encodeURIComponent(publication.thread_id)}/report/${encodeURIComponent(publication.id)}/content`;
  return <><iframe title="报告预览" sandbox="" src={root} /><div className="report-actions"><a className="button secondary" href={`${root}?download=true`} download><Download size={14} />下载 HTML</a><a className="button secondary" href={root} target="_blank" rel="noreferrer"><Eye size={14} />预览</a></div></>;
}


function ReportSave({ name, onName, onSave, error }) {
  return <div className="report-save"><input aria-label="报告名称" value={name} onChange={(event) => onName(event.target.value)} placeholder="命名此版本" /><button className="button secondary" disabled={!name.trim()} onClick={onSave}><Save size={14} />保存</button>{error && <span role="alert">{error}</span>}</div>;
}


function ReportHistory({ threadId, reports }) {
  if (!reports.length) return null;
  return <ul className="report-history">{reports.map((report) => <li key={report.id}><span>{report.title}</span><ReportHistoryLinks threadId={threadId} report={report} /></li>)}</ul>;
}


function ReportHistoryLinks({ threadId, report }) {
  const root = `/api/v1/threads/${encodeURIComponent(threadId)}/report/${encodeURIComponent(report.publication_id)}/content`;
  return <span><a href={root} target="_blank" rel="noreferrer">预览</a><a href={`${root}?download=true`} download>下载</a></span>;
}
