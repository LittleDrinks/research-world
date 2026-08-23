import { Bot, Check, ChevronRight, CircleAlert, CircleDot, FlaskConical, Plus, Wrench } from "lucide-react";

export function AgentRail({ state }) {
  return <aside className="ar-agent-rail"><header><span>AGENTS</span><button className="ar-add-agent" title="新建 Agent" onClick={state.beginNew}><Plus size={20} /></button></header>
    <button className="active"><Bot size={17} /><span><b>{state.draft.name || "New Agent"}</b><small>{state.draft.id}</small></span><ChevronRight size={17} /></button>
    {state.agents.map((agent) => <button key={agent.id}><Bot size={17} /><span><b>{agent.name}</b><small>{agent.id}</small></span></button>)}</aside>;
}

export function TestButton({ id, state, label }) {
  const status = state.tests[id];
  return <button className="od-test" disabled={status === "testing"} onClick={() => state.test(id)}>
    {status === "passed" ? <Check size={15} /> : <FlaskConical className={status === "testing" ? "spinning" : ""} size={15} />}
    {status === "passed" ? "通过" : status === "testing" ? "测试中" : label}</button>;
}

export function Status({ status, label }) {
  const Icon = status === "ready" ? Check : status === "missing" ? CircleAlert : CircleDot;
  return <span className={`ar-status ${status}`}><Icon size={12} />{label}</span>;
}

export function Notice({ state }) {
  if (!state.notice) return null;
  return <div className="ar-notice" role="status"><Wrench size={16} /><pre>{state.notice}</pre><button onClick={() => state.setNotice("")} aria-label="关闭">×</button></div>;
}

export function StatePeek({ state }) {
  const visible = { agent: state.draft, scan: state.scan, tests: state.tests, memoryAgents: state.agents };
  return <details className="ar-state"><summary>Prototype state</summary><pre>{JSON.stringify(visible, null, 2)}</pre></details>;
}
