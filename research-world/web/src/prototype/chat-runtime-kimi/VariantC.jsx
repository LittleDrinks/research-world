// 变体 C — 项目级科研日志，不以 Thread 或 Agent 为边界。
import { NotebookText } from "lucide-react";
import { ACTIVITY } from "./seed";

export function VariantC({ state }) {
  return <div className="crt-c"><LogRail project={state.project} /><ProjectLog project={state.project} /></div>;
}

function LogRail({ project }) {
  return <aside className="crt-c-rail"><header><b>{project.name}</b></header>
    <button className="crt-c-activity-entry on"><NotebookText size={14} /><span><b>科研日志</b><small>项目记录</small></span></button>
    <nav><button className="on"><b>今天</b><small>6 条记录</small></button>
      <button><b>昨天</b><small>12 条记录</small></button></nav>
  </aside>;
}

function ProjectLog({ project }) {
  return <main className="crt-c-main"><header className="crt-c-activity-head"><h1>科研日志</h1><span>{project.name}</span></header>
    <ol className="crt-timeline">{ACTIVITY.map((item) => <li className="crt-entry fact" key={item.id}>
      <time>{item.time}</time><i /><div className="crt-entry-body"><p className="crt-fact"><b>{item.kind}</b>{item.text}<span>{item.ref}</span></p></div>
    </li>)}</ol>
  </main>;
}
