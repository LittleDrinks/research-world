import { displayLabel, formatTime, shortId } from "../../utils";
import { fmtDuration } from "./format";

export function JobsView({ jobs }) {
  if (!jobs.length) return <p className="act-empty">暂无任务记录。</p>;
  return <div className="jobs-table"><table><thead><tr><th>智能体</th><th>尝试</th><th>代际</th><th>状态</th><th>开始时间</th><th>耗时</th></tr></thead><tbody>{jobs.map((job) => <tr key={job.id}><td>{job.actor}</td><td><code>{shortId(job.id)}</code></td><td><code>{shortId(job.generation_id)}</code></td><td>{displayLabel(job.status)}</td><td>{formatTime(job.created_at)}</td><td>{fmtDuration(job.created_at, job.completed_at)}</td></tr>)}</tbody></table></div>;
}
