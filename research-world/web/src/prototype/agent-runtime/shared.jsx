import { Check, CircleAlert, CircleDashed, CircleDot, Clock3, Copy, X } from "lucide-react";

const ICONS = { ready: Check, found: CircleDot, "auth-required": CircleAlert, missing: CircleDashed, error: CircleAlert, unsupported: CircleDashed, blocked: CircleAlert, unknown: CircleDot, "setup-required": Clock3, unavailable: CircleDashed };

export function Status({ value, text }) {
  const Icon = ICONS[value] || CircleDot;
  return <span className={`arp-status is-${value}`}><Icon size={12} />{text || value}</span>;
}

export function IconButton({ label, children, ...props }) {
  return <button className="arp-icon-button" title={label} aria-label={label} {...props}>{children}</button>;
}

export function Field({ label, hint, children }) {
  return <label className="arp-field"><span>{label}{hint && <small>{hint}</small>}</span>{children}</label>;
}

export function CopyValue({ children, label = "复制" }) {
  const copy = () => navigator.clipboard?.writeText(String(children));
  return <div className="arp-copy-value"><code>{children}</code><IconButton label={label} onClick={copy}><Copy size={14} /></IconButton></div>;
}

export function Notice({ state }) {
  if (!state.notice) return null;
  return <div className="arp-notice" role="status"><span>{state.notice}</span><IconButton label="关闭" onClick={() => state.setNotice("")}><X size={15} /></IconButton></div>;
}

export function EmptyState({ title, detail, action }) {
  return <div className="arp-empty"><CircleDashed size={22} /><b>{title}</b><span>{detail}</span>{action}</div>;
}
