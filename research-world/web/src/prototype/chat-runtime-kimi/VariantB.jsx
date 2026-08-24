// 变体 B — 单工作区上下文切换: 无常驻侧栏, 顶部 select 切 Thread, segmented 切 对话/研究活动, Inspector 为模态。
import { ACTIVITY } from "./seed";
import { ActivityList, Composer, InspectorModal, PinChip, PinPicker, RunCard } from "./shared";

export function VariantB({ state }) {
  return <div className="crt-b">
    <WorkspaceBar state={state} />
    {state.view === "activity" ? <ActivityPane /> : <ChatPane state={state} />}
    {state.inspector && <InspectorModal state={state} />}
  </div>;
}

function WorkspaceBar({ state }) {
  return <header className="crt-b-bar">
    <span className="crt-b-crumb">{state.project.name}</span>
    <select className="crt-b-thread-select" value={state.threadId} aria-label="切换 Thread"
      onChange={(event) => { state.setThreadId(event.target.value); state.setView("chat"); }}>
      {state.threads.map((thread) => <option key={thread.id} value={thread.id}>{thread.id} · {thread.title}</option>)}
    </select>
    <nav className="crt-b-segmented">
      <button className={state.view === "chat" ? "on" : ""} onClick={() => state.setView("chat")}>对话</button>
      <button className={state.view === "activity" ? "on" : ""} onClick={() => state.setView("activity")}>研究活动</button>
    </nav>
  </header>;
}

function ChatPane({ state }) {
  const thread = state.thread;
  return <>
    <div className="crt-b-scroll"><div className="crt-b-column">
      <ContextStrip thread={thread} state={state} />
      {thread.messages.map((message) => <BMessage key={message.id} message={message} state={state} />)}
    </div></div>
    <footer className="crt-b-footer"><Composer onSend={state.send} placeholder="单工作区:描述意图,execution 由 Run 承载…" /></footer>
  </>;
}

function ContextStrip({ thread, state }) {
  return <div className="crt-b-context">
    <span>上下文</span>
    {thread.pinned.map((id) => <PinChip key={id} nodeId={id} onRemove={() => state.togglePin(id)} />)}
    <PinPicker pinned={thread.pinned} onAdd={state.togglePin} />
  </div>;
}

function BMessage({ message, state }) {
  return <article className={`crt-msg ${message.role}`}>
    <span>{message.role === "user" ? "你" : "研究助手"} · {message.time}</span>
    <p>{message.text}</p>
    {(message.runs || []).map((runId) => <RunCard key={runId} run={state.runs[runId]}
      expanded={state.openRunId === runId} onToggle={() => state.toggleRun(runId)} onOpenTrace={state.setInspectorId} />)}
  </article>;
}

function ActivityPane() {
  return <div className="crt-b-scroll"><div className="crt-b-column crt-b-activity">
    <ActivityList items={ACTIVITY} />
  </div></div>;
}
