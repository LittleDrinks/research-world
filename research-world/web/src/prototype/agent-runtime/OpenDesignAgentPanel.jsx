import { Bot, Check, ChevronDown, ChevronRight, Download, Plus, RefreshCw, Search, Terminal, X } from "lucide-react";
import { useState } from "react";
import { GROUP_LABELS, PROVIDERS, RUNTIMES } from "./seed";
import { Status, TestButton } from "./shared";

export function OpenDesignAgentPanel({ state }) {
  const [channel, setChannel] = useState("cli");
  return <main className="od-workspace"><header className="od-title"><Bot size={22} /><div><h1>{state.draft.name || "新建 Agent"}</h1><code>{state.draft.id}</code></div></header>
    <section className="od-panel"><ChannelTabs channel={channel} setChannel={setChannel} />
      {channel === "cli" ? <CliCatalog state={state} /> : <ProviderCatalog state={state} />}
      <CapabilityCatalog state={state} /><AgentInstructions state={state} />
      <footer className="od-save"><span>原型设置只保存在当前页面</span><button className="od-primary" onClick={state.create}><Check size={16} />保存 Agent</button></footer>
    </section></main>;
}

function ChannelTabs({ channel, setChannel }) {
  return <div className="od-segment" role="tablist"><button className={channel === "cli" ? "active" : ""} onClick={() => setChannel("cli")}>本机 CLI</button>
    <button className={channel === "api" ? "active" : ""} onClick={() => setChannel("api")}>API 提供商</button></div>;
}

function CliCatalog({ state }) {
  const ready = RUNTIMES.filter((item) => item.status !== "missing");
  const missing = RUNTIMES.filter((item) => item.status === "missing");
  return <section className="od-catalog"><CatalogHeader state={state} count={ready.length} />
    <div className="od-runtime-list">{ready.map((item) => <RuntimeCard key={item.id} item={item} state={state} />)}</div>
    <Collapsible title={`可安装 (${missing.length})`} items={missing} state={state} />
  </section>;
}

function CatalogHeader({ state, count }) {
  const scanning = state.scan.status === "scanning";
  return <header className="od-catalog-head"><div><p>选择用来运行 Agent 的 CLI。模型与推理强度由 CLI 提供。</p><h2>你的 CLI ({count})</h2></div>
    <button className="od-pill" disabled={scanning} onClick={state.rescan}><RefreshCw className={scanning ? "spinning" : ""} size={15} />{scanning ? "扫描中" : "重新扫描"}</button></header>;
}

function RuntimeCard({ item, state }) {
  const selected = state.draft.channel === "cli" && state.draft.runtimeId === item.id;
  return <article className={`od-runtime ${selected ? "selected" : ""}`}><button className="od-runtime-summary" onClick={() => state.selectRuntime(item)} disabled={item.status !== "ready"}>
    <RuntimeMark item={item} /><RuntimeCopy item={item} /><Status status={item.status} label={runtimeLabel(item)} />
    {selected ? <ChevronDown size={18} /> : <ChevronRight size={18} />}</button>{selected && <RuntimeOptions item={item} state={state} />}</article>;
}

function RuntimeCopy({ item }) {
  return <div className="od-runtime-copy"><h3>{item.name}<span> · {item.vendor}</span></h3><p>{item.version}</p><small>{item.path}</small></div>;
}

function RuntimeMark({ item }) {
  return <span className={`od-runtime-mark ${item.id}`}>{item.id === "codex" ? "C" : item.id === "kimi" ? "K" : <Terminal size={20} />}</span>;
}

function RuntimeOptions({ item, state }) {
  return <div className="od-runtime-options"><label><span>模型 <em>来自 CLI 的实时列表</em></span><select value={state.draft.model} onChange={(event) => state.patch({ model: event.target.value })}>
    {item.models.map((model) => <option key={model}>{model}</option>)}</select></label><label><span>推理强度</span><select value={state.draft.effort} onChange={(event) => state.patch({ effort: event.target.value })}>
      {item.efforts.map((effort) => <option key={effort}>{effort}</option>)}</select></label><TestButton id={`runtime:${item.id}`} state={state} label="测试" /></div>;
}

function Collapsible({ title, items, state }) {
  return <details className="od-collapsible"><summary><ChevronRight size={15} />{title}</summary><div>{items.map((item) => <article key={item.id} className="od-install-row">
    <RuntimeMark item={item} /><div><b>{item.name}</b><small>{item.vendor}</small></div><button className="od-pill" onClick={() => state.setNotice(`安装命令：${item.install}`)}><Download size={14} />安装</button></article>)}</div></details>;
}

function ProviderCatalog({ state }) {
  return <section className="od-catalog"><header className="od-catalog-head"><div><p>凭证由 Runtime 读取，不写入 Agent。</p><h2>API 提供商 ({PROVIDERS.length})</h2></div></header>
    <div className="od-runtime-list">{PROVIDERS.map((item) => <ProviderCard key={item.id} item={item} state={state} />)}</div></section>;
}

function ProviderCard({ item, state }) {
  const selected = state.draft.channel === "api" && state.draft.providerId === item.id;
  return <article className={`od-runtime ${selected ? "selected" : ""}`}><button className="od-runtime-summary" disabled={item.status !== "ready"} onClick={() => state.selectProvider(item)}>
    <span className="od-runtime-mark api">API</span><div className="od-runtime-copy"><h3>{item.name}</h3><p>{item.endpoint}</p></div><Status status={item.status} label={item.auth} />
    {selected ? <ChevronDown size={18} /> : <ChevronRight size={18} />}</button>{selected && <RuntimeOptions item={item} state={state} />}</article>;
}

function CapabilityCatalog({ state }) {
  return <section className="od-capabilities"><header><div><h2>本地能力</h2><p>从配置文件和工作区识别，选择只决定是否挂载。</p></div></header>
    {Object.entries(GROUP_LABELS).map(([type, label]) => <CapabilitySection key={type} type={type} label={label} state={state} />)}</section>;
}

function CapabilitySection({ type, label, state }) {
  const [open, setOpen] = useState(type === "skills");
  const [adding, setAdding] = useState(false);
  const items = state.inventory[type];
  const canAdd = type !== "mcp";
  const beginAdd = (event) => { event.preventDefault(); setOpen(true); setAdding(true); };
  return <details className="od-cap-section" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}><summary><ChevronRight size={15} /><b>{label}</b><span>{items.length} 个已识别</span>
    {canAdd && <button className="od-add-source" onClick={beginAdd}><Plus size={14} />添加来源</button>}</summary>
    <div className="od-cap-body"><label className="od-search"><Search size={15} /><input value={state.query} onChange={(event) => state.setQuery(event.target.value)} placeholder={`搜索 ${label}`} /></label>
      {adding && <AddSourceForm type={type} state={state} close={() => setAdding(false)} />}
      {items.map((item) => <CapabilityRow key={item.id} item={item} type={type} state={state} />)}</div></details>;
}

function AddSourceForm({ type, state, close }) {
  const [path, setPath] = useState("");
  const submit = (event) => { event.preventDefault(); state.addCapability(type, path); close(); };
  const placeholder = type === "skills" ? "Skill 目录，例如 /workspace/.agents/skills/my-skill" : "工具清单或可执行文件路径";
  return <form className="od-add-form" onSubmit={submit}><input autoFocus value={path} onChange={(event) => setPath(event.target.value)} placeholder={placeholder} />
    <button type="submit" disabled={!path.trim()}>识别并添加</button><button type="button" onClick={close} aria-label="取消"><X size={15} /></button></form>;
}

function CapabilityRow({ item, type, state }) {
  const checked = state.draft.selected[type].includes(item.id);
  return <label className={`od-cap-row ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked} onChange={() => state.toggle(type, item.id)} />
    <span><b>{item.name}</b><small>{item.detail}</small><code>{item.path}</code></span><em>{item.source}</em><Status status={item.status} label="已识别" /></label>;
}

function AgentInstructions({ state }) {
  return <section className="od-instructions"><label><span>名称</span><input value={state.draft.name} onChange={(event) => state.patch({ name: event.target.value })} /></label>
    <label><span>指令</span><textarea rows="5" value={state.draft.instructions} onChange={(event) => state.patch({ instructions: event.target.value })} /></label></section>;
}

function runtimeLabel(item) {
  if (item.status === "ready") return item.auth;
  if (item.status === "adapter") return "已发现，未接入";
  return "未安装";
}
