import { Settings } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EmptyState } from "../components/bits";
import { useWorld } from "../context/WorldContext";
import { formatDate } from "../utils/labels";
import "../settings.css";


export function SettingsPage() {
  const { data, projectId } = useWorld();
  const project = data.projects.find((item) => item.id === projectId);
  if (!project) return <EmptyState icon={Settings} title="未选择项目" />;
  return <section className="settings-page"><h1>项目设置</h1>
    <dl className="settings-record">
      <div><dt>名称</dt><dd>{project.name}</dd></div>
      <div><dt>研究问题</dt><dd>{project.question}</dd></div>
      <div><dt>项目 ID</dt><dd className="mono">{project.id}</dd></div>
      <div><dt>创建时间</dt><dd>{formatDate(project.created_at)}</dd></div>
    </dl>
    <ExitProject /></section>;
}


function ExitProject() {
  const navigate = useNavigate();
  return <button className="button secondary" onClick={() => navigate("/projects")}>切换项目</button>;
}
