import { Bot, Check, CircleAlert, FileText, LoaderCircle, ShieldAlert, Sparkles, Wrench, X } from "lucide-react";
import { DraftAgentSpec } from "./DraftAgentSpec";
import { IconButton, Status } from "./shared";

export function DraftDialog({ state }) {
  if (!state.draft) return null;
  const confirm = state.draft.step === "confirm";
  return <div className="arp-overlay"><section className={"arp-dialog" + (confirm ? " arp-draft-dialog" : "")} role="dialog" aria-modal="true" aria-label="新建 Agent 草稿"><DialogHeader title="新建 Agent 草稿" close={() => state.setDraft(null)} />{state.draft.step === "choose" && <DraftChoices state={state} />}{state.draft.step === "describe" && <DescribeDraft state={state} />}{confirm && <ConfirmDraft state={state} />}</section></div>;
}

function DraftChoices({ state }) {
  const options = [["preset", FileText, "Preset", "从 #41 受控参数生成草稿"], ["blank", Bot, "空白", "不预填 runtime、model 或能力"], ["orchestrator", Sparkles, "描述目标", "消费 #41 待确认草稿"]];
  return <div className="arp-draft-choices">{options.map(([id, Icon, name, detail]) => <button key={id} onClick={() => state.chooseDraft(id)}><Icon size={20} /><b>{name}</b><span>{detail}</span></button>)}</div>;
}

function DescribeDraft({ state }) {
  return <div className="arp-dialog-body"><label className="arp-field"><span>研究目标</span><textarea aria-label="研究目标" rows="6" value={state.draft.goal} onChange={(event) => state.patchDraft({ goal: event.target.value })} placeholder="例如：检索官方一手来源并形成可复核竞品矩阵" /></label><p className="arp-dialog-note">固定 fixture 消费 #41 contract；不调用模型、Tool、prepare 或业务 API。</p><DialogFooter cancel={() => state.setDraft(null)} confirm={state.generateDraft} confirmText="生成待确认草稿" disabled={!state.draft.goal.trim()} /></div>;
}

function ConfirmDraft({ state }) {
  const blocked = state.draftReadiness.status !== "ready";
  return <><div className="arp-draft-source"><Status value={blocked ? "blocked" : "ready"} text={draftLabel(state.draft.mode)} /><span>未保存 · 未 prepare · 未启动</span></div><DraftAgentSpec state={state} /><DialogFooter cancel={() => state.setDraft(null)} confirm={state.confirmDraft} confirmText="确认创建 Profile" disabled={blocked} /></>;
}

export function PrepareDrawer({ state }) {
  if (!state.prepare) return null;
  return <div className="arp-drawer-backdrop"><aside className="arp-drawer" role="dialog" aria-modal="true" aria-label="CLI 准备计划"><DialogHeader title="CLI-only prepare" close={() => state.setPrepare(null)} /><PrepareImpact prepare={state.prepare} /><PrepareProgress prepare={state.prepare} /><PrepareFooter state={state} /></aside></div>;
}

function PrepareImpact({ prepare }) {
  return <div className="arp-prepare-impact"><ShieldAlert size={18} /><div><b>{prepare.target.name} · {prepare.target.realm}</b><span>来源：{prepare.target.source} · version {prepare.target.version || "unresolved"}</span><span>影响：受控 CLI installation、官方来源网络访问、无 secret 回显</span><span>Tool provision 由 #43 负责</span></div></div>;
}

function PrepareProgress({ prepare }) {
  return <div className="arp-prepare-body"><div className="arp-prepare-state"><Status value={prepare.state} /><b>{prepare.state}</b></div><div className="arp-prepare-steps">{prepare.steps.map((step) => <PrepareStep key={step.name} step={step} />)}</div><PrepareLogs logs={prepare.logs} /></div>;
}

function PrepareStep({ step }) {
  const Icon = step.state === "running" ? LoaderCircle : step.state === "succeeded" ? Check : step.state === "failed" ? CircleAlert : Wrench;
  return <div><Icon className={step.state === "running" ? "spinning" : ""} size={16} /><span><b>{step.name}</b><small>{step.detail}</small></span><Status value={step.state} /></div>;
}

function PrepareLogs({ logs }) {
  return <section className="arp-prepare-log" aria-label="Prepare 日志"><h3>保留日志</h3>{logs.map((item, index) => <code key={index}>{String(index + 1).padStart(2, "0")} · {item}</code>)}</section>;
}

function PrepareFooter({ state }) {
  const current = state.prepare.state;
  if (current === "plan") return <footer><button onClick={state.cancelPrepare}>取消计划</button><button className="primary" onClick={state.advancePrepare}>继续确认</button></footer>;
  if (current === "confirm") return <ConfirmFooter state={state} />;
  if (current === "running") return <footer><span>执行中；取消会保留现有日志</span><button onClick={state.cancelPrepare}>取消执行</button></footer>;
  if (["failed", "cancelled"].includes(current)) return <footer><button onClick={() => state.setPrepare(null)}>关闭</button><button className="primary" onClick={state.retryPrepare}>Retry</button></footer>;
  return <footer><span>日志已脱敏并保留</span><button className="primary" onClick={() => state.setPrepare(null)}>完成</button></footer>;
}

function ConfirmFooter({ state }) {
  return <footer className="arp-confirm-footer"><label>Fixture result<select aria-label="Prepare 结果" value={state.prepare.outcome} onChange={(event) => state.setPrepare((current) => ({ ...current, outcome: event.target.value }))}><option value="succeeded">succeeded</option><option value="failed">failed</option></select></label><button onClick={state.cancelPrepare}>取消</button><button className="primary" onClick={state.runPrepare}>确认并执行</button></footer>;
}

export function DeleteDialog({ state }) {
  if (!state.deleteOpen) return null;
  return <div className="arp-overlay"><section className="arp-dialog arp-delete" role="dialog" aria-modal="true" aria-label="删除 Agent"><DialogHeader title="删除 Agent" close={() => state.setDeleteOpen(false)} /><div className="arp-dialog-body"><p>{state.profile.name} 被 2 个 Pipeline 和 1 个 Thread 引用。Prototype 只删除页面内存，不删除 Trace。</p><DialogFooter cancel={() => state.setDeleteOpen(false)} confirm={state.deleteAgent} confirmText="确认删除" danger /></div></section></div>;
}

function DialogHeader({ title, close }) {
  return <header className="arp-dialog-header"><h2>{title}</h2><IconButton label="关闭" onClick={close}><X size={17} /></IconButton></header>;
}

function DialogFooter({ cancel, confirm, confirmText, disabled, danger }) {
  return <footer className="arp-dialog-footer"><button onClick={cancel}>取消</button><button className={danger ? "danger" : "primary"} disabled={disabled} onClick={confirm}>{confirmText}</button></footer>;
}

function draftLabel(mode) {
  if (mode === "orchestrator") return "orchestrator draft";
  return mode === "preset" ? "Preset draft" : "Blank draft";
}
