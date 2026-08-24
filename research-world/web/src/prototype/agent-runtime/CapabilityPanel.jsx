import { ExternalLink, Search } from "lucide-react";
import { SKILLS, TOOLS } from "./seed";
import { CopyValue, EmptyState, Status } from "./shared";
import { Section } from "./ProfilePanels";

export function CapabilityPanel({ state, type }) {
  const items = filterItems(type === "skills" ? SKILLS : TOOLS, state.catalogQuery);
  const title = type === "skills" ? "Skill catalog" : "Tool catalog · MCP sources";
  const detail = type === "skills" ? "Profile 保存 stable Skill id；完整描述和 path 保持可读。" : "MCP 是 Tool Adapter 来源；OpenCLI 只作为 browser Tool。";
  return <Section title={title} detail={detail}><CatalogSearch state={state} type={type} />{items.length ? <div className="arp-cap-list">{items.map((item) => <CapabilityRow key={item.id} item={item} type={type} state={state} />)}</div> : <EmptyState title="没有匹配项" detail="搜索同时覆盖名称、id、描述、来源与 path。" />}</Section>;
}

function CatalogSearch({ state, type }) {
  return <div className="arp-catalog-toolbar"><label><Search size={15} /><input aria-label={`搜索 ${type}`} value={state.catalogQuery} onChange={(event) => state.setCatalogQuery(event.target.value)} placeholder="搜索名称、描述、来源或路径" /></label><span>{type === "skills" ? SKILLS.length : TOOLS.length} discovered</span></div>;
}

function CapabilityRow({ item, type, state }) {
  const selected = state.profile[type].includes(item.id);
  return <article className={selected ? "selected" : ""}><label><input aria-label={`选择 ${item.name}`} type="checkbox" checked={selected} onChange={() => state.toggleCapability(type, item.id)} /><span><b>{item.name}</b><code>{item.id}</code></span></label><Status value={item.status} /><p>{item.description}</p>{type === "skills" ? <SkillFacts item={item} /> : <ToolFacts item={item} />}{item.status !== "ready" && <button onClick={() => state.setNotice("Tool provision 由 #43 Tool Catalog 负责；未触发 CLI prepare。") }><ExternalLink size={14} />前往 Tool Catalog</button>}</article>;
}

function SkillFacts({ item }) {
  return <div className="arp-cap-facts"><span>scope · {item.scope}</span><CopyValue>{item.path}</CopyValue></div>;
}

function ToolFacts({ item }) {
  return <div className="arp-cap-facts"><span>source · {item.source}</span><CopyValue>runtime://tools/{item.id}</CopyValue></div>;
}

function filterItems(items, query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return items;
  return items.filter((item) => Object.values(item).join(" ").toLowerCase().includes(needle));
}
