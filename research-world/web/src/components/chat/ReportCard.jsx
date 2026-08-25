import { Download, Eye, FileText, Save } from "lucide-react";
import { useState } from "react";
import { publishThreadReport, saveThreadReport } from "../../api";


const stages = ["读取投影", "引用校验", "生成", "最终校验", "发布"];


export function ReportCard({ threadId, title, reports }) {
  const [state, setState] = useState({ stage: -1, result: null, error: null, saved: null });
  const publish = () => publishReport(threadId, title, setState);
  return <section className="report-workflow" aria-label="报告发布"><ReportHeader onPublish={publish} />
    <ReportProgress state={state} onRetry={publish} setState={setState} />
    <ReportHistory threadId={threadId} reports={reports} />
  </section>;
}


async function publishReport(threadId, title, setState) {
  setState({ stage: 0, result: null, error: null, saved: null });
  try { publishResult(await publishThreadReport(threadId, { title }), setState); }
  catch (error) { publishFailure(error, setState); }
}


function publishResult(result, setState) {
  if (result.status === "failed") return setState((value) => ({ ...value, error: result.assessment.gaps }));
  setState((value) => ({ ...value, stage: result.stages.length - 1, result }));
}


function publishFailure(error, setState) {
  const gap = { code: error.code || error.message, path: "request", value: error.message };
  setState((value) => ({ ...value, error: [gap] }));
}


function ReportHeader({ onPublish }) {
  return <header><FileText size={16} /><b>可信报告</b><button className="button secondary" onClick={onPublish}>生成报告</button></header>;
}


function ReportProgress({ state, onRetry, setState }) {
  return <>{state.stage >= 0 && <ol className="report-stages">{stages.map((stage, index) => <li className={index <= state.stage ? "done" : ""} key={stage}>{stage}</li>)}</ol>}
    {state.error && <ReportFailure gaps={state.error} onRetry={onRetry} />}{state.result && <ReportResult result={state.result} saved={state.saved} onSaved={(saved) => setState((value) => ({ ...value, saved }))} />}</>;
}


function ReportFailure({ gaps, onRetry }) {
  return <div className="report-failure" role="alert"><span>{gaps.map(gapText).join("; ")}</span><button className="button secondary" onClick={onRetry}>重试</button></div>;
}


function gapText(gap) {
  return `${gap.code}: ${gap.path} = ${JSON.stringify(gap.value)}`;
}


function ReportResult({ result, saved, onSaved }) {
  const [name, setName] = useState("");
  const [error, setError] = useState(null);
  const save = async () => {
    try { onSaved(await saveThreadReport(result.publication.thread_id, { title: name, publication_id: result.publication.id })); }
    catch (failure) { setError(failure.code || failure.message); }
  };
  return <div className="report-result"><ReportDetails result={result} /><ReportLinks publication={result.publication} />
    {saved ? <p className="report-saved">已保存版本 {saved.id}</p> : <ReportSave name={name} onName={setName} onSave={save} error={error} />}</div>;
}


function ReportDetails({ result }) {
  return <dl><dt>标题</dt><dd>{result.title}</dd><dt>时间</dt><dd>{result.publication.created_at}</dd><dt>交付级别</dt><dd>{result.assessment.delivery_level}</dd><dt>引用</dt><dd>已校验</dd><dt>最低来源</dt><dd>{result.assessment.minimum_source_level}</dd></dl>;
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
