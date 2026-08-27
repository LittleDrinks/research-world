import { ArrowRight, FolderOpen, Plus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { NewProjectDialog } from "../components/NewProjectDialog";
import { ErrorToast } from "../components/AppShell";
import { ThemeButton } from "../components/ThemeButton";
import { useWorld } from "../context/WorldContext";
import "../projects.css";


export function ProjectsPage() {
  const { data, loading, projectId, selectProject } = useWorld();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const enter = async (id) => {
    try { await selectProject(id); navigate("/map"); }
    catch {}
  };
  return <section className="projects-page"><ProjectBar onNew={() => setOpen(true)} /><ErrorToast /><main>
    {loading ? <div className="projects-loading">正在载入项目...</div> : <ProjectList projects={data.projects} activeId={projectId} onOpen={enter} onNew={() => setOpen(true)} />}</main>
    <NewProjectDialog open={open} onClose={() => setOpen(false)} /></section>;
}


function ProjectBar({ onNew }) {
  return <header className="projects-bar"><div className="projects-brand"><span className="mono">&gt;_</span><div><b>Research World</b><small>选择研究项目</small></div></div>
    <div><ThemeButton /><button className="button primary" onClick={onNew}><Plus size={16} />新建项目</button></div></header>;
}


function ProjectList({ projects, activeId, onOpen, onNew }) {
  if (!projects.length) return <section className="projects-empty"><FolderOpen size={28} /><h2>暂无研究项目</h2><button className="button primary" onClick={onNew}><Plus size={16} />新建项目</button></section>;
  return <div className="project-list">{projects.map((project) => <button className={project.id === activeId ? "active" : ""} onClick={() => onOpen(project.id)} key={project.id}>
    <span className="project-name"><b>{project.title || project.name}</b><small>{project.question}</small></span>
    <span className="project-counts"><b>{project.node_count}</b> 节点{project.active_run_count > 0 && <> · <b>{project.active_run_count}</b> 运行中</>}</span>
    <time>{formatDate(project.created_at)}</time><ArrowRight size={18} /></button>)}</div>;
}


function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
}
