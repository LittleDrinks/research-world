import { RefreshCw, Search, Terminal, Wrench } from "lucide-react";
import { RUNTIMES } from "./seed";
import { CopyValue, EmptyState, Status } from "./shared";
import { runtimeKey } from "./runtimeKey";

export function RuntimePanel({ state }) {
  return <div className="arp-panel-stack"><section className="arp-section arp-runtime-section"><RuntimeHeader state={state} /><RuntimeBody state={state} /></section><RuntimeSemantics /></div>;
}

function RuntimeHeader({ state }) {
  const refreshing = state.inventoryState === "refreshing";
  return <header className="arp-runtime-header"><div><h2>Agent CLI inventory</h2><p>只读 fixture；发现不等于安装，就绪不等于启用。</p></div><div className="arp-runtime-actions"><ScenarioSwitch state={state} /><button disabled={refreshing} onClick={state.refresh}><RefreshCw className={refreshing ? "spinning" : ""} size={15} />{refreshing ? "Refreshing" : "刷新"}</button></div></header>;
}

function ScenarioSwitch({ state }) {
  const modes = [["content", "内容"], ["loading", "Loading"], ["empty", "Empty"]];
  return <div className="arp-scenario" aria-label="Inventory 场景">{modes.map(([id, label]) => <button key={id} aria-pressed={state.inventoryState === id} onClick={() => state.setInventoryState(id)}>{label}</button>)}</div>;
}

function RuntimeBody({ state }) {
  if (state.inventoryState === "loading") return <LoadingRows />;
  if (state.inventoryState === "empty") return <EmptyState title="没有 CLI candidates" detail="Catalog 为空；刷新不会安装任何产品。" action={<button onClick={state.refresh}><RefreshCw size={15} />手动刷新</button>} />;
  if (state.inventoryState === "refreshing") return <><div className="arp-refreshing"><RefreshCw className="spinning" size={15} />正在隔离探测 {RUNTIMES.length} 个 candidates；当前缓存保持可读</div><RuntimeList state={state} /></>;
  return <RuntimeList state={state} />;
}

function RuntimeList({ state }) {
  return <div className="arp-runtime-list">{RUNTIMES.map((item) => <RuntimeRow key={runtimeKey(item.id, item.realm)} item={item} state={state} />)}</div>;
}

function RuntimeRow({ item, state }) {
  const selected = runtimeKey(state.profile.runtime, state.profile.realm) === runtimeKey(item.id, item.realm);
  const preparable = ["missing", "error"].includes(item.status);
  return <article className={`arp-runtime-row ${selected ? "selected" : ""}`}><label className="arp-runtime-choice"><input type="radio" name="runtime" value={runtimeKey(item.id, item.realm)} checked={selected} disabled={item.status !== "ready"} onChange={() => state.patchProfile({ runtime: item.id, realm: item.realm })} /><Terminal size={17} /><span><b>{item.name}</b><code>{item.realm} · {item.executable} · {item.version || "version unknown"}</code></span></label><Status value={item.status} /><RuntimeFacts item={item} />{preparable && <button className="arp-prepare-link" onClick={() => state.openPrepare(item)}><Wrench size={14} />CLI 准备计划</button>}</article>;
}

function RuntimeFacts({ item }) {
  return <div className="arp-runtime-facts"><span><b>Realm</b>{item.realm}</span><span><b>Source</b>{item.source}</span><span><b>Last checked</b>{item.checked}</span><span className="wide"><b>Reason</b>{item.reason}</span><div className="wide"><b>Discovery path</b><CopyValue>{item.path || "No discovery entry in this realm"}</CopyValue></div><div className="wide"><b>Resolved executable</b><CopyValue>{item.resolvedPath || "No executable resolved in this realm"}</CopyValue></div><span className="wide"><b>Capabilities</b>{item.caps.length ? item.caps.join(" · ") : "none confirmed"}</span></div>;
}

function LoadingRows() {
  return <div className="arp-loading" role="status" aria-label="Loading CLI inventory">{[1, 2, 3].map((item) => <div key={item}><i /><span /><em /></div>)}</div>;
}

function RuntimeSemantics() {
  const states = ["found", "ready", "auth-required", "missing", "error", "unsupported"];
  return <section className="arp-section"><header><h2>状态语义</h2><p>状态使用稳定枚举和 reason code；页面不从产品名推断 readiness。</p></header><div className="arp-status-legend">{states.map((item) => <Status key={item} value={item} />)}</div><div className="arp-inline-note"><Search size={15} /><span>Probe boundary</span><code>Runtime process · 2 s/step · 5 s/candidate · no shell · no model call</code></div></section>;
}
