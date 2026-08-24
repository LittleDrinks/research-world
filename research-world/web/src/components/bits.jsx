import { statusTone } from "../utils/labels";


export function StatusPill({ status, label }) {
  return <i className={`status-pill ${statusTone(status)}`}>{label || status}</i>;
}


export function EmptyState({ icon: Icon, title, hint, children }) {
  return <div className="empty-state">{Icon && <Icon size={26} />}<h2>{title}</h2>{hint && <p>{hint}</p>}{children}</div>;
}
