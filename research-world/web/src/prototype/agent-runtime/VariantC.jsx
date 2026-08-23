import { Boxes, Cable, FolderSearch, Layers3, Terminal } from "lucide-react";
import { GROUP_LABELS, PROVIDERS, RUNTIMES } from "./seed";
import { CapabilityTable, CapabilityToolbar, DraftSummary, IdentityEditor, ModelFields, PrototypeHeader, Status, TestButton } from "./shared";

export function VariantC({ state }) {
  return <div className="ar-variant ar-c"><PrototypeHeader state={state} section="能力目录" />
    <div className="ar-c-body"><SourceNavigator state={state} /><main className="ar-console"><ConsoleHeader state={state} />
      <section className="ar-console-runtimes"><RuntimeMatrix state={state} /><ProviderMatrix state={state} /></section>
      <section className="ar-console-caps"><CapabilityToolbar state={state} tabs={false} /><CapabilityTable state={state} all /></section></main>
      <aside className="ar-config-panel"><header><span className="ar-eyebrow">AGENT 草稿</span><h2>执行清单</h2></header><IdentityEditor state={state} />
        <ModelFields state={state} condensed /><DraftSummary state={state} full /></aside></div></div>;
}

function ConsoleHeader({ state }) {
  return <header className="ar-console-header"><div><span className="ar-eyebrow">识别结果</span><h1>本地来源与执行入口</h1><p>把可运行、已发现未接入、期望支持放在同一清单中比较。</p></div>
    <button className="ar-button secondary" onClick={state.rescan}><FolderSearch size={15} />重新扫描</button></header>;
}

function SourceNavigator({ state }) {
  return <aside className="ar-source-nav"><header><Layers3 size={16} /><b>来源</b><small>{state.scan.count}</small></header><SourceButton active icon={Terminal} label="Runtime / CLI" count={RUNTIMES.length} />
    <SourceButton icon={Cable} label="API Provider" count={PROVIDERS.length} />{Object.entries(GROUP_LABELS).map(([key, label]) =>
      <SourceButton key={key} icon={Boxes} label={label} count={state.inventory[key].length} />)}
    <footer><span className={`ar-scan-dot ${state.scan.status}`} />{state.scan.status === "scanning" ? "扫描中" : `上次扫描：${state.scan.label}`}</footer></aside>;
}

function SourceButton({ icon: Icon, label, count, active }) {
  return <button className={active ? "active" : ""}><Icon size={15} /><span>{label}</span><small>{count}</small></button>;
}

function RuntimeMatrix({ state }) {
  return <section className="ar-matrix"><header><h2>Runtime / CLI</h2><span>安装与 Adapter 状态分离</span></header>
    <div className="ar-matrix-head"><span>名称</span><span>路径 / 版本</span><span>状态</span><span>模型</span><span>操作</span></div>
    {RUNTIMES.map((item) => <RuntimeMatrixRow key={item.id} item={item} state={state} />)}</section>;
}

function RuntimeMatrixRow({ item, state }) {
  const selected = state.draft.channel === "cli" && state.draft.runtimeId === item.id;
  return <div className={`ar-matrix-row ${selected ? "selected" : ""}`}><b>{item.name}<small>{item.vendor}</small></b><code>{item.path}<small>{item.version}</small></code>
    <Status status={item.status} label={item.status === "ready" ? item.auth : item.status === "adapter" ? "未接 Adapter" : "未安装"} />
    <span>{item.models.join(", ") || "由 Adapter 识别"}</span><div>{item.status === "ready" && <TestButton id={`runtime:${item.id}`} state={state} />}
      <button className="ar-button secondary" disabled={selected || item.status !== "ready"}
      onClick={() => state.selectRuntime(item)}>{selected ? "已选" : "选择"}</button></div></div>;
}

function ProviderMatrix({ state }) {
  return <section className="ar-matrix ar-provider-matrix"><header><h2>API Provider</h2><span>独立认证与模型来源</span></header>{PROVIDERS.map((item) => {
    const selected = state.draft.channel === "api" && state.draft.providerId === item.id;
    return <div className={`ar-provider-line ${selected ? "selected" : ""}`} key={item.id}><b>{item.name}</b><code>{item.endpoint}</code>
      <Status status={item.status} label={item.auth} /><button className="ar-button secondary" disabled={selected || item.status !== "ready"}
        onClick={() => state.selectProvider(item)}>{selected ? "已选" : "选择"}</button></div>;
  })}</section>;
}
