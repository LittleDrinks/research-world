import { BookOpen, CircleHelp, Compass, FlaskConical, LoaderCircle, X } from "lucide-react";
import { Handle, Position } from "@xyflow/react";
import { nodeTitle } from "./nodeText";


const ICONS = { question: CircleHelp, source: BookOpen, direction: Compass, experiment: FlaskConical };
const LABELS = { question: "问题", source: "来源", direction: "方向", experiment: "实验" };
const POSITIONS = [["top", Position.Top], ["right", Position.Right], ["bottom", Position.Bottom], ["left", Position.Left]];


function Handles({ type }) {
  return POSITIONS.map(([side, position]) => <Handle key={side} className="hidden-handle" id={`${type}-${side}`} type={type} position={position} isConnectable={false} />);
}


function statusBadge(data) {
  if (data.working) return { className: "state-running", label: "运行中" };
  if (data.life_state === "ghost") return { className: "state-muted", label: "已驳回" };
  if (data.life_state === "pending") return { className: "", label: "待审查" };
  if (data.direction_status === "supported") return { className: "state-success", label: "已支持" };
  if (data.direction_status === "refuted") return { className: "state-failed", label: "已反驳" };
  if (data.direction_status === "proposed") return { className: "state-warning", label: "待验证" };
  return { className: "state-success", label: "已入图" };
}


export function ResearchNode({ data, selected }) {
  const Icon = ICONS[data.kind] || Compass;
  const title = nodeTitle(data.payload);
  const badge = statusBadge(data);
  return <article className={`research-node kind-${data.kind} life-${data.life_state} ${data.working ? "is-working" : ""} ${data.justCompleted ? "just-completed" : ""} ${selected ? "selected" : ""}`}>
    <Handles type="target" />
    <header><span className="node-kind-icon" role="img" aria-label={`${LABELS[data.kind]}图标`}><Icon size={19} /></span>
      <div><span>{LABELS[data.kind]}</span><h3>{title}</h3></div>
      <span className={`node-status-badge ${badge.className}`}>{badge.label}</span></header>
    <footer><div className="node-meta"><span>{String(data.id || "").slice(0, 12)}</span></div>
      {Boolean(data.working) && <LoaderCircle className="spin" size={14} />}{data.life_state === "ghost" && <X size={13} />}</footer>
    <Handles type="source" />
  </article>;
}
