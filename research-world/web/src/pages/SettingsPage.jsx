import { Download, Settings } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { projectExportUrl, setProjectAuto } from "../api";
import { EmptyState } from "../components/bits";
import { useWorld } from "../context/WorldContext";
import { formatDate } from "../utils/labels";
import "../settings.css";


export function SettingsPage() {
  const { data, projectId, refresh, setError } = useWorld();
  const project = data.projects.find((item) => item.id === projectId);
  if (!project) return <EmptyState icon={Settings} title="未选择项目" />;
  return <section className="settings-page"><h1>项目设置</h1>
    <dl className="settings-record">
      <div><dt>名称</dt><dd>{project.title || project.name}</dd></div>
      <div><dt>研究问题</dt><dd>{project.question}</dd></div>
      <div><dt>工作区</dt><dd className="mono">{project.root}</dd></div>
      <div><dt>创建时间</dt><dd>{formatDate(project.created_at)}</dd></div>
      <div><dt>规模</dt><dd>{project.node_count} 节点 · {project.run_count} 运行</dd></div>
    </dl>
    <AutoToggle project={project} refresh={refresh} setError={setError} />
    <a className="button secondary settings-export" href={projectExportUrl(project.id)}><Download size={16} />下载研究包</a>
    <ExitProject /></section>;
}


function AutoToggle({ project, refresh, setError }) {
  const toggle = async () => {
    try { await setProjectAuto(project.id, !project.auto); await refresh(project.id); }
    catch (error) { setError(error.message); }
  };
  return <label className="auto-toggle settings-auto"><input type="checkbox" checked={Boolean(project.auto)} onChange={toggle} />
    <span>Auto 模式：运行获批后自动推进，无需人工逐步确认</span></label>;
}


function ExitProject() {
  const navigate = useNavigate();
  return <button className="button secondary" onClick={() => navigate("/projects")}>切换项目</button>;
}
