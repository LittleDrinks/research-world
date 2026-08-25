import { Download, Eye, FileText, Save } from "lucide-react";
import { useState } from "react";
import { getReportProjection, publishReport, saveReport } from "../../api";

const stages = ["读取投影", "引用校验", "生成", "最终校验", "发布"];

export function ReportCard({ projectId, title }) {
  const [state, setState] = useState({ stage: -1, result: null, error: null, saved: null });
  const run = async () => {
    setState({ stage: 0, result: null, error: null, saved: null });
    try {
      const projection = await getReportProjection(projectId);
      setState((value) => ({ ...value, stage: 1 }));
      const result = await publishReport(projectId, { title, facts: projection.facts });
      if (result.status === "failed") return setState((value) => ({ ...value, error: result.assessment.gaps }));
      setState((value) => ({ ...value, stage: 4, result }));
    } catch (error) { setState((value) => ({ ...value, error: [{ code: error.message }] })); }
  };
  return <section className="report-workflow" aria-label="报告发布">
    <header><FileText size={16} /><b>可信报告</b><button className="button secondary" onClick={run}>生成报告</button></header>
    {state.stage >= 0 && <ol className="report-stages">{stages.map((stage, index) => <li className={index <= state.stage ? "done" : ""} key={stage}>{stage}</li>)}</ol>}
    {state.error && <ReportFailure gaps={state.error} onRetry={run} />}
    {state.result && <ReportResult projectId={projectId} result={state.result} saved={state.saved} onSave={(saved) => setState((value) => ({ ...value, saved }))} />}
  </section>;
}

function ReportFailure({ gaps, onRetry }) {
  return <div className="report-failure" role="alert"><span>{gaps.map((gap) => `${gap.code}${gap.path ? `: ${gap.path}` : ""}`).join("; ")}</span><button className="button secondary" onClick={onRetry}>重试</button></div>;
}

function ReportResult({ projectId, result, saved, onSave }) {
  const [name, setName] = useState("");
  const artifact = result.artifact.id;
  const url = `/api/v1/projects/${encodeURIComponent(projectId)}/report/content/${encodeURIComponent(artifact)}`;
  const save = async () => onSave(await saveReport(projectId, { title: name, artifact_id: artifact }));
  return <div className="report-result"><dl><dt>标题</dt><dd>{result.title}</dd><dt>时间</dt><dd>{result.artifact.created_at}</dd><dt>交付级别</dt><dd>{result.assessment.delivery_level}</dd><dt>引用</dt><dd>已校验</dd><dt>最低来源</dt><dd>{result.assessment.minimum_source_level}</dd></dl>
    <iframe title="报告预览" sandbox="" src={url} /><div className="report-actions"><a className="button secondary" href={`${url}?download=true`} download><Download size={14} />下载 HTML</a><a className="button secondary" href={url} target="_blank" rel="noreferrer"><Eye size={14} />预览</a></div>
    {saved ? <p className="report-saved">已保存版本 {saved.id}</p> : <div className="report-save"><input aria-label="报告名称" value={name} onChange={(event) => setName(event.target.value)} placeholder="命名此版本" /><button className="button secondary" disabled={!name.trim()} onClick={save}><Save size={14} />保存</button></div>}
  </div>;
}
