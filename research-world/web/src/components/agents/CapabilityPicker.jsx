import { X } from "lucide-react";
import { useState } from "react";


export function CapabilityPicker({ label, options, selected, onChange }) {
  const [query, setQuery] = useState("");
  const available = options.filter((item) => item.available !== false && !selected.includes(item.id) && matches(item, query));
  const add = (id) => { onChange([...selected, id]); setQuery(""); };
  return <section className="capability-picker"><h2>{label}</h2>
    {selected.length > 0 && <div className="capability-chips">{selected.map((id) => {
      const item = options.find((option) => option.id === id);
      const missing = !item || item.available === false;
      return <span className={`capability-chip ${missing ? "missing" : ""}`} key={id}><b>{item?.name || id}</b>
        <small>{capabilityState(item, id)}</small>
        <button type="button" aria-label={`移除 ${item?.name || id}`} onClick={() => onChange(selected.filter((value) => value !== id))}><X size={12} /></button></span>;
    })}</div>}
    <input aria-label={`搜索${label}`} placeholder={`搜索${label}...`} value={query} onChange={(event) => setQuery(event.target.value)} />
    <div className="capability-options">{available.map((item) => <button type="button" key={item.id} onClick={() => add(item.id)}>
      <b>{item.name || item.id}</b>{item.description && <span>{item.description}</span>}<small>{[item.id, item.source].filter(Boolean).join(" · ")}</small></button>)}
      {!available.length && <p className="record-empty">无匹配项</p>}</div></section>;
}


function capabilityState(item, id) {
  if (!item) return `${id} · 未识别`;
  if (item.status === "setup_required") return `${id} · 需要配置`;
  if (item.available === false) return `${id} · 不可用`;
  return item.source || item.id;
}


function matches(item, query) {
  if (!query) return true;
  const text = `${item.id} ${item.name || ""} ${item.description || ""} ${item.source || ""}`.toLowerCase();
  return text.includes(query.toLowerCase());
}
