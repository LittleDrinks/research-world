import { Bot, Check, FileText, LoaderCircle, ShieldAlert, Sparkles, Wrench, X } from "lucide-react";
import { IconButton, Status } from "./shared";

export function DraftDialog({ state }) {
  if (!state.draft) return null;
  return <div className="arp-overlay"><section className="arp-dialog" role="dialog" aria-modal="true" aria-label="新建 Agent 草稿"><DialogHeader title="新建 Agent 草稿" close={() => state.setDraft(null)} />{state.draft.step === "choose" && <DraftChoices state={state} />}{state.draft.step === "describe" && <DescribeDraft state={state} />}{state.draft.step === "confirm" && <ConfirmDraft state={state} />}</section></div>;
}

function DraftChoices({ state }) {
  const options = [["preset", FileText, "Preset", "从受控参数生成草稿"], ["blank", Bot, "空白", "从最小 AgentSpec 开始"], ["orchestrator", Sparkles, "描述目标", "生成待确认字段与理由"]];
  return <div className="arp-draft-choices">{options.map(([id, Icon, name, detail]) => <button key={id} onClick={() => state.chooseDraft(id)}><Icon size={20} /><b>{name}</b><span>{detail}</span></button>)}</div>;
}

function DescribeDraft({ state }) {
  return <div className="arp-dialog-body"><label className="arp-field"><span>研究目标</span><textarea rows="6" value={state.draft.goal} onChange={(event) => state.patchDraft({ goal: event.target.value })} placeholder="例如：检索官方一手来源并形成可复核竞品矩阵" /></label><p className="arp-dialog-note">Prototype 使用固定草稿演示；此按钮不调用模型、Tool、prepare 或业务 API。</p><DialogFooter cancel={() => state.setDraft(null)} confirm={state.generateDraft} confirmText="生成待确认草稿" disabled={!state.draft.goal.trim()} /></div>;
}

function ConfirmDraft({ state }) {
  return <div className="arp-dialog-body"><div className="arp-draft-source"><Status value="found" text={draftLabel(state.draft.mode)} /><span>未保存 · 未 prepare · 未启动</span></div><label className="arp-field"><span>名称</span><input value={state.draft.name} onChange={(event) => state.patchDraft({ name: event.target.value })} /></label><DraftSummary mode={state.draft.mode} /><DialogFooter cancel={() => state.setDraft(null)} confirm={state.confirmDraft} confirmText="确认创建 Profile" /></div>;
}

function DraftSummary({ mode }) {
  return <div className="arp-draft-summary"><div><b>Runtime</b><code>codex</code><small>{mode === "orchestrator" ? "理由：支持非交互、streaming 与 workspace" : "来自默认草稿"}</small></div><div><b>Model</b><code>gpt-5.6-sol</code><small>未决：endpoint secret 仍需 readiness 检查</small></div><div><b>Capabilities</b><code>source-research · read_skill · browser.opencli</code><small>OpenCLI 作为 Tool，不参与 CLI readiness</small></div></div>;
}

export function PrepareDrawer({ state }) {
  if (!state.prepare) return null;
  return <div className="arp-drawer-backdrop"><aside className="arp-drawer" role="dialog" aria-modal="true" aria-label="准备计划"><DialogHeader title="显式准备计划" close={() => state.setPrepare(null)} /><PrepareImpact /><div className="arp-prepare-steps">{state.prepare.steps.map((step) => <PrepareStep key={step.name} step={step} />)}</div><PrepareFooter state={state} /></aside></div>;
}

function PrepareImpact() {
  return <div className="arp-prepare-impact"><ShieldAlert size={18} /><div><b>docs.openai · configure adapter</b><span>来源：Runtime catalog revision 7f2c</span><span>影响：1 个托管配置文件、官方 endpoint 网络访问、无 shell、无 secret 回显</span><span>回滚：删除该 revision 的托管配置</span></div></div>;
}

function PrepareStep({ step }) {
  const Icon = step.state === "running" ? LoaderCircle : step.state === "succeeded" ? Check : Wrench;
  return <div><Icon className={step.state === "running" ? "spinning" : ""} size={16} /><span><b>{step.name}</b><small>{step.detail}</small></span><Status value={step.state === "succeeded" ? "ready" : "found"} text={step.state} /></div>;
}

function PrepareFooter({ state }) {
  if (state.prepare.state === "done") return <footer><span>日志已脱敏 · Prototype 未改动宿主</span><button className="primary" onClick={() => state.setPrepare(null)}>完成</button></footer>;
  return <footer><button onClick={() => state.setPrepare(null)}>取消</button><button className="primary" disabled={state.prepare.state === "running"} onClick={state.runPrepare}>确认并执行</button></footer>;
}

export function DeleteDialog({ state }) {
  if (!state.deleteOpen) return null;
  return <div className="arp-overlay"><section className="arp-dialog arp-delete" role="dialog" aria-modal="true"><DialogHeader title="删除 Agent" close={() => state.setDeleteOpen(false)} /><div className="arp-dialog-body"><p>此 Profile 被 2 个 Pipeline 和 1 个 Thread 引用。Prototype 只删除页面内存，不删除 Trace。</p><DialogFooter cancel={() => state.setDeleteOpen(false)} confirm={state.deleteAgent} confirmText="确认删除" danger /></div></section></div>;
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
