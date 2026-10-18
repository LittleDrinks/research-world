import { ArrowRight, FolderOpen, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { NewProjectDialog } from "../components/NewProjectDialog";
import { ErrorToast } from "../components/AppShell";
import { DeleteProjectDialog } from "../components/DeleteProjectDialog";
import { ThemeButton } from "../components/ThemeButton";
import { useWorld } from "../context/WorldContext";
import { useProjectWorkspaces } from "../context/useProjectWorkspaces";
import { ProjectWorkspace } from "../components/ProjectWorkspace";
import "../projects.css";


export function ProjectsPage() {
  const { data, loading, projectId, selectProject } = useWorld();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [deleting,setDeleting]=useState(null);
  const [query, setQuery] = useState("");
  const workspaces=useProjectWorkspaces();
  const filtered=data.projects.filter(p=>`${p.name} ${p.question}`.toLowerCase().includes(query.toLowerCase()));
  const enter = async (id) => {
    try { await selectProject(id); navigate("/map"); }
    catch {}
  };
  return <section className="projects-page"><ProjectBar onNew={() => setOpen(true)} /><ErrorToast /><main><label className="project-search">搜索研究项目<input type="search" aria-label="搜索研究项目" value={query} onChange={event=>setQuery(event.target.value)} placeholder="输入 q049、问题关键词…" /></label>
    {workspaces.error&&<p role="alert" className="workspace-stop-error">{workspaces.error}</p>}
    {loading ? <div className="projects-loading">正在载入项目...</div> : <ProjectList projects={filtered} activeId={projectId} onOpen={enter} onDelete={setDeleting} onNew={() => setOpen(true)} workspaces={workspaces} />}</main>
    <DeleteProjectDialog project={deleting} onClose={()=>setDeleting(null)} />
    <NewProjectDialog open={open} onClose={() => setOpen(false)} /></section>;
}


function ProjectBar({ onNew }) {
  return <header className="projects-bar"><div className="projects-brand"><span className="mono">&gt;_</span><div><b>Research World</b><small>选择研究项目</small></div></div>
    <div><ThemeButton /><button className="button primary" onClick={onNew}><Plus size={16} />新建项目</button></div></header>;
}


function ProjectList({ projects, activeId, onOpen, onNew, onDelete, workspaces }) {
  if (!projects.length) return <section className="projects-empty"><FolderOpen size={28} /><h2>暂无研究项目</h2><button className="button primary" onClick={onNew}><Plus size={16} />新建项目</button></section>;
  return <div className="project-list">{projects.map(project=><div className={`project-row ${project.id===activeId?"active":""}`} key={project.id}>
    <button className="project-open" onClick={()=>onOpen(project.id)}>
      <span className="project-name"><b>{project.title || project.name}</b><small>{project.question}</small></span>
      <span className="project-counts"><b>{project.node_count}</b> 节点</span>
      <time>{formatDate(project.created_at)}</time><ArrowRight size={18} />
    </button><ProjectWorkspace project={project} workspaces={workspaces}/><button className="icon-button project-delete" aria-label={`删除项目 ${project.name}`} title="删除项目" onClick={()=>onDelete(project)}><Trash2 size={18}/></button>
  </div>)}</div>;
}


function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
}
