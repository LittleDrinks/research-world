import { Copy, RotateCcw, Save, Trash2 } from "lucide-react";
import { TABS } from "./seed";
import { IconButton, Status } from "./shared";
import { DiagnosticsPanel, ModelPanel, ProfilePanel } from "./ProfilePanels";
import { CapabilityPanel } from "./CapabilityPanel";
import { RuntimePanel } from "./RuntimePanel";

export function AgentWorkspace({ state }) {
  if (!state.profile) return <main className="arp-workspace arp-no-profile">没有 Profile</main>;
  return <main className={`arp-workspace ${state.dirty ? "is-dirty" : ""}`}><WorkspaceHeader state={state} /><TabBar state={state} /><div className="arp-content"><ActivePanel state={state} /></div><SaveBar state={state} /></main>;
}

function WorkspaceHeader({ state }) {
  const text = state.readiness.status === "ready" ? "ready" : `${state.readiness.issues.length} 项阻塞`;
  const modified = state.dirty ? "unsaved" : state.profile.modified;
  return <header className="arp-workspace-header"><div><span>Profile · {state.profile.id}</span><h1>{state.profile.name}</h1><p>Preset: {state.profile.preset} · modified {modified}</p></div><div className="arp-header-actions"><Status value={state.readiness.status} text={text} /><IconButton label="复制 Agent" onClick={state.copyAgent}><Copy size={16} /></IconButton><IconButton label="删除 Agent" onClick={() => state.setDeleteOpen(true)}><Trash2 size={16} /></IconButton></div></header>;
}

function TabBar({ state }) {
  return <nav className="arp-tabs" aria-label="Agent 设置">{TABS.map(([id, label]) => <button key={id} className={state.activeTab === id ? "active" : ""} onClick={() => state.setActiveTab(id)}>{label}</button>)}</nav>;
}

function ActivePanel({ state }) {
  if (state.activeTab === "runtime") return <RuntimePanel state={state} />;
  if (state.activeTab === "model") return <ModelPanel state={state} />;
  if (state.activeTab === "skills") return <CapabilityPanel state={state} type="skills" />;
  if (state.activeTab === "tools") return <CapabilityPanel state={state} type="tools" />;
  if (state.activeTab === "diagnostics") return <DiagnosticsPanel state={state} />;
  return <ProfilePanel state={state} />;
}

function SaveBar({ state }) {
  if (!state.dirty) return null;
  const blocked = state.readiness.status !== "ready";
  return <footer className="arp-savebar"><span>{blocked ? state.readiness.issues[0]?.message : "AgentSpec snapshot ready"}</span><div><button onClick={state.cancel}><RotateCcw size={15} />取消</button><button className="primary" disabled={blocked} onClick={state.save}><Save size={15} />保存 Profile</button></div></footer>;
}
