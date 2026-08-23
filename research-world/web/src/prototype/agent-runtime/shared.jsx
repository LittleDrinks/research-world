import { Bot, Check, ChevronRight, CircleAlert, CircleDot, Eye, FlaskConical, Plus, RefreshCw, Search, Terminal, Wrench } from "lucide-react";
import { ThemeButton } from "../../components/ThemeButton";
import { GROUP_LABELS, PROVIDERS, RUNTIMES } from "./seed";

export function PrototypeHeader({ state, section = "Agent 配置" }) {
  return <header className="ar-topbar"><div className="ar-brand"><span>&gt;_</span><b>Research World</b><em>原型</em></div>
    <nav><span>地图</span><span>对话</span><strong>Agent</strong><span>设置</span></nav>
    <div className="ar-top-actions"><small>{section}</small><ThemeButton /><button className="ar-button primary" onClick={state.beginNew}><Plus size={15} />新建 Agent</button></div></header>;
}

export function ScanHeader({ state, title = "自动识别的 Runtime / CLI" }) {
  const running = state.scan.status === "scanning";
  return <header className="ar-section-head"><div><span className="ar-eyebrow">本地识别</span><h2>{title}</h2>
    <p>{running ? "正在检查 PATH、认证与 Adapter..." : `${state.scan.count} 项 · ${state.scan.label}`}</p></div>
    <button className="ar-button secondary" disabled={running} onClick={state.rescan}><RefreshCw className={running ? "spinning" : ""} size={15} />重新扫描</button></header>;
}

export function RuntimeInventory({ state, compact = false }) {
  return <div className={`ar-runtime-list ${compact ? "compact" : ""}`}>{RUNTIMES.map((item) =>
    <RuntimeRow key={item.id} item={item} state={state} />)}</div>;
}

function RuntimeRow({ item, state }) {
  const selected = state.draft.channel === "cli" && state.draft.runtimeId === item.id;
  return <article className={`ar-runtime-row ${selected ? "selected" : ""}`}><RuntimeIdentity item={item} />
    <div className="ar-runtime-meta"><code>{item.path}</code><span>{item.version}</span></div>
    <Status status={item.status} label={item.auth} /><RuntimeActions item={item} state={state} selected={selected} /></article>;
}

export function RuntimeIdentity({ item }) {
  return <div className="ar-runtime-id"><span><Terminal size={17} /></span><div><b>{item.name}</b><small>{item.vendor}</small></div></div>;
}

function RuntimeActions({ item, state, selected }) {
  if (item.status === "ready") return <div className="ar-row-actions"><TestButton id={`runtime:${item.id}`} state={state} label="测试" />
    <button className="ar-button secondary" disabled={selected} onClick={() => state.selectRuntime(item)}>{selected ? <Check size={14} /> : null}{selected ? "已选择" : "选择"}</button></div>;
  const text = item.status === "missing" ? "安装" : "接入说明";
  const message = item.install ? `安装命令：${item.install}` : `${item.name} 已在机器上发现，但 catalog 尚无 Adapter。`;
  return <button className="ar-button secondary" onClick={() => state.setNotice(message)}>{text}</button>;
}

export function ProviderInventory({ state, title = "API Provider" }) {
  return <section className="ar-provider"><header><div><span className="ar-eyebrow">API</span><h3>{title}</h3></div><small>与本地 CLI 分开识别</small></header>
    {PROVIDERS.map((item) => <ProviderRow key={item.id} item={item} state={state} />)}</section>;
}

function ProviderRow({ item, state }) {
  const selected = state.draft.channel === "api" && state.draft.providerId === item.id;
  return <div className={`ar-provider-row ${selected ? "selected" : ""}`}><div><b>{item.name}</b><code>{item.endpoint}</code></div>
    <Status status={item.status} label={item.auth} /><button className="ar-button secondary" disabled={selected || item.status !== "ready"}
      onClick={() => state.selectProvider(item)}>{selected ? "已选择" : item.status === "ready" ? "选择" : "未接入"}</button></div>;
}

export function ModelFields({ state, condensed = false }) {
  const source = state.draft.channel === "cli" ? state.runtime : state.provider;
  return <div className={`ar-model-fields ${condensed ? "condensed" : ""}`}><label><span>模型 · 来自 {source.name}</span><select value={state.draft.model}
    onChange={(event) => state.patch({ model: event.target.value })}>{source.models.map((model) => <option key={model}>{model}</option>)}</select></label>
    <label><span>推理强度 · Runtime 支持</span><select value={state.draft.effort} onChange={(event) => state.patch({ effort: event.target.value })}>
      {source.efforts.map((effort) => <option key={effort}>{effort}</option>)}</select></label></div>;
}

export function IdentityEditor({ state, long = false }) {
  return <div className={`ar-identity ${long ? "long" : ""}`}><label><span>Agent 名称</span><input value={state.draft.name}
    onChange={(event) => state.patch({ name: event.target.value })} /></label><label><span>系统指令</span><textarea rows={long ? 5 : 3}
      value={state.draft.instructions} onChange={(event) => state.patch({ instructions: event.target.value })} /></label></div>;
}

export function CapabilityToolbar({ state, tabs = true }) {
  return <div className="ar-cap-toolbar">{tabs && <div className="ar-tabs">{Object.entries(GROUP_LABELS).map(([key, label]) =>
    <button key={key} className={state.group === key ? "active" : ""} onClick={() => state.setGroup(key)}>{label}<span>{state.inventory[key].length}</span></button>)}</div>}
    <label className="ar-search"><Search size={15} /><input aria-label="搜索本地能力" placeholder="搜索名称、路径或来源" value={state.query}
      onChange={(event) => state.setQuery(event.target.value)} /></label></div>;
}

export function CapabilityTable({ state, group = state.group, all = false }) {
  const groups = all ? Object.keys(GROUP_LABELS) : [group];
  return <div className="ar-cap-groups">{groups.map((key) => <CapabilityGroup key={key} type={key} items={state.inventory[key]} state={state} showTitle={all} />)}</div>;
}

function CapabilityGroup({ type, items, state, showTitle }) {
  return <section className="ar-cap-group">{showTitle && <h3>{GROUP_LABELS[type]}<span>{items.length}</span></h3>}
    <div className="ar-cap-table">{items.map((item) => <CapabilityRow key={item.id} item={item} type={type} state={state} />)}
      {!items.length && <p className="ar-empty">没有匹配的本地来源</p>}</div></section>;
}

function CapabilityRow({ item, type, state }) {
  const checked = state.draft.selected[type].includes(item.id);
  return <article className={`ar-cap-row ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked}
    onChange={() => state.toggle(type, item.id)} aria-label={`选择 ${item.name}`} /><div className="ar-cap-main"><b>{item.name}</b><span>{item.detail}</span><code>{item.path}</code></div>
    <span className="ar-source">{item.source}</span><Status status={item.status} label={item.status === "ready" ? "可用" : "离线"} />
    <div className="ar-row-actions"><TestButton id={`${type}:${item.id}`} state={state} /><button className="ar-icon-button" title={`查看 ${item.name}`}
      onClick={() => state.setNotice(`${item.name}\n来源：${item.source}\n路径：${item.path}\n${item.detail}`)}><Eye size={15} /></button></div></article>;
}

export function TestButton({ id, state, label = "" }) {
  const status = state.tests[id];
  return <button className={label ? "ar-button secondary" : "ar-icon-button"} title={status === "passed" ? "测试通过" : "测试连接"}
    disabled={status === "testing"} onClick={() => state.test(id)}>{status === "passed" ? <Check size={15} /> : <FlaskConical className={status === "testing" ? "spinning" : ""} size={15} />}{label && (status === "passed" ? "通过" : status === "testing" ? "测试中" : label)}</button>;
}

export function Status({ status, label }) {
  const Icon = status === "ready" ? Check : status === "missing" ? CircleAlert : CircleDot;
  return <span className={`ar-status ${status}`}><Icon size={12} />{label}</span>;
}

export function DraftSummary({ state, full = false }) {
  const source = state.draft.channel === "cli" ? state.runtime.name : state.provider.name;
  return <aside className={`ar-summary ${full ? "full" : ""}`}><header><Bot size={18} /><div><span>当前草稿</span><h3>{state.draft.name || "未命名 Agent"}</h3></div></header>
    <dl><div><dt>执行入口</dt><dd>{source}</dd></div><div><dt>模型</dt><dd>{state.draft.model || "等待认证"}</dd></div>
      <div><dt>推理强度</dt><dd>{state.draft.effort}</dd></div><div><dt>能力</dt><dd>{selectedCount(state)} 项</dd></div></dl>
    {full && <SelectedList state={state} />}<button className="ar-button primary wide" onClick={state.create}><Plus size={15} />创建 Agent</button>
    <small>仅保存在当前页面内存，刷新即清空</small></aside>;
}

function SelectedList({ state }) {
  return <div className="ar-selected-list">{Object.entries(state.draft.selected).map(([key, values]) =>
    <div key={key}><b>{GROUP_LABELS[key]}</b><span>{values.length ? values.join(" · ") : "未选择"}</span></div>)}</div>;
}

export function AgentRail({ state }) {
  return <aside className="ar-agent-rail"><header><span>AGENTS</span><button className="ar-icon-button" title="新建 Agent" onClick={state.beginNew}><Plus size={15} /></button></header>
    <button className="active"><Bot size={15} /><span><b>{state.draft.name}</b><small>{state.draft.id}</small></span><ChevronRight size={14} /></button>
    {state.agents.map((agent) => <button key={agent.id}><Bot size={15} /><span><b>{agent.name}</b><small>{agent.id} · {agent.runtime}</small></span></button>)}</aside>;
}

export function Notice({ state }) {
  if (!state.notice) return null;
  return <div className="ar-notice" role="status"><Wrench size={16} /><pre>{state.notice}</pre><button onClick={() => state.setNotice("")} aria-label="关闭">×</button></div>;
}

export function StatePeek({ state }) {
  const visible = { agent: state.draft, scan: state.scan, tests: state.tests, memoryAgents: state.agents };
  return <details className="ar-state"><summary>STATE</summary><pre>{JSON.stringify(visible, null, 2)}</pre></details>;
}

function selectedCount(state) {
  return Object.values(state.draft.selected).reduce((sum, items) => sum + items.length, 0);
}
