import { Activity, Bot, LogOut, Map, Menu, MessagesSquare, Settings, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useWorld } from "../context/WorldContext";
import { RecordList } from "./RecordList";


export const MODULES = [
  ["/map", "地图", Map],
  ["/chat", "对话", MessagesSquare],
  ["/traces", "轨迹", Activity],
  ["/agents", "Agent", Bot],
  ["/settings", "设置", Settings],
];


export function moduleOf(pathname) {
  const match = MODULES.find(([to]) => pathname.startsWith(to));
  return match?.[0] || "/map";
}


function Brand() {
  return <div className="brand"><div className="brand-mark" aria-hidden="true">&gt;_</div>
    <div><b>“强国有我”思政案例库</b><span>研究世界 · 工作台</span></div></div>;
}


function ModuleNav({ close }) {
  return <nav className="module-nav">{MODULES.map(([to, label, Icon]) =>
    <NavLink key={to} to={to} onClick={close} end={false}><Icon size={17} /><span>{label}</span></NavLink>)}</nav>;
}


function ProjectDock({ close }) {
  return <footer className="project-dock">
    <NavLink to="/projects" onClick={close} className="icon-button dock-icon" aria-label="切换项目" title="切换项目"><LogOut size={17} /></NavLink>
    <NavLink to="/settings" onClick={close} className="icon-button dock-icon" aria-label="项目设置" title="项目设置"><Settings size={17} /></NavLink>
  </footer>;
}


function Sidebar({ open, close }) {
  const { pathname } = useLocation();
  return <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
    <button className="icon-button sidebar-close" onClick={close} title="关闭导航"><X size={19} /></button>
    <Brand /><ModuleNav close={close} /><RecordList module={moduleOf(pathname)} close={close} /><ProjectDock close={close} /></aside>;
}


function MobileBar({ openNav }) {
  const { data, projectId } = useWorld();
  const project = data.projects.find((item) => item.id === projectId);
  return <header className="mobile-bar"><button className="icon-button" onClick={openNav} title="打开导航" aria-label="打开导航"><Menu size={19} /></button>
    <b>{project?.title || project?.name}</b></header>;
}


export function ErrorToast() {
  const { error, setError } = useWorld();
  if (!error) return null;
  return <div className="error-toast" role="alert"><span>{error}</span><button className="icon-button" onClick={() => setError("")} title="关闭提示"><X size={18} /></button></div>;
}


export function AppShell() {
  const [navOpen, setNavOpen] = useState(false);
  const close = () => setNavOpen(false);
  return <div className="app-shell"><Sidebar open={navOpen} close={close} />
    {navOpen && <div className="sidebar-mask" onClick={close} />}
    <div className="app-main"><ErrorToast /><MobileBar openNav={() => setNavOpen(true)} />
      <main className="page-host"><Outlet /></main></div></div>;
}
