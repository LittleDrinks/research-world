import { Copy, MoreHorizontal, Save, Trash2 } from "lucide-react";
import { TABS } from "./seed";
import { IconButton, Status } from "./shared";
import { DiagnosticsPanel, ModelPanel, ProfilePanel } from "./ProfilePanels";
import { CapabilityPanel } from "./CapabilityPanel";
import { RuntimePanel } from "./RuntimePanel";

export function AgentWorkspace({ state }) {
  return <main className="arp-workspace"><WorkspaceHeader state={state} /><TabBar state={state} /><div className="arp-content"><ActivePanel state={state} /></div><SaveBar state={state} /></main>;
}

function WorkspaceHeader({ state }) {
  return <header className="arp-workspace-header"><div><span>Profile · {state.profile.id}</span><h1>{state.profile.name}</h1><p>Preset: source-researcher · modified 12 min ago</p></div><div className="arp-header-actions"><Status value="blocked" text="1 项阻塞" /><IconButton label="复制 Agent"><Copy size={16} /></IconButton><IconButton label="删除 Agent" onClick={() => state.setDeleteOpen(true)}><Trash2 size={16} /></IconButton><IconButton label="更多操作"><MoreHorizontal size={16} /></IconButton></div></header>;
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
  return <footer className="arp-savebar"><span>Prototype fixture · 保存不写入生产数据</span><div><button>取消更改</button><button className="primary" onClick={state.save}><Save size={15} />保存 Profile</button></div></footer>;
}
