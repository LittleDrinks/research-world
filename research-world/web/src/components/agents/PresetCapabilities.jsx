import { AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";


export function PresetCapabilities({ preset }) {
  const items = recommendations(preset);
  if (!items.length) return null;
  return <ul className="preset-capabilities">{items.map((item) =>
    <li key={`${item.kind}:${item.id}`}><span><b>{item.id}</b><em data-status={item.status}>（{state(item)}）</em>
      <small>{item.kind}</small></span><p>{item.recommendation || item.description}</p></li>)}</ul>;
}


export function CapabilityAlert({ tools = [], skills = [] }) {
  const items = [...tools.map((item) => ({ ...item, kind: "Tool" })),
    ...skills.map((item) => ({ ...item, kind: "Skill" }))];
  if (!items.length) return null;
  return <div className="capability-alert" role="alert"><AlertTriangle size={16} />
    <p>{items.map((item) => `${item.kind} 不可用：${item.id}（${state(item)}）`).join("；")}</p>
    <Link className="button secondary" to="/agents#tool-catalog">Tool Catalog</Link></div>;
}


export function recommendations(preset) {
  return [
    ...(preset?.skills || []).map((item) => ({ ...item, kind: "Skill" })),
    ...(preset?.tools || []).map((item) => ({ ...item, kind: "Tool" })),
  ];
}


function state(item) {
  return [item.status || "ready", item.reason].filter(Boolean).join(" / ");
}
