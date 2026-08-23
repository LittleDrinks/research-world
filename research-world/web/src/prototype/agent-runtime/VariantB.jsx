import { Check, CircleDot, Terminal } from "lucide-react";
import { CAPABILITIES, GROUP_LABELS, PROVIDERS, RUNTIMES } from "./seed";
import { CapabilityTable, CapabilityToolbar, DraftSummary, IdentityEditor, ModelFields, PrototypeHeader, RuntimeIdentity, ScanHeader, Status, TestButton } from "./shared";

export function VariantB({ state }) {
  return <div className="ar-variant ar-b"><PrototypeHeader state={state} section="引导式配置" />
    <div className="ar-b-body"><StepRail state={state} /><main className="ar-flow"><FlowIntro />
      <FlowStep number="01" title="命名 Agent" hint="先定义职责，再选择执行入口"><IdentityEditor state={state} long /></FlowStep>
      <FlowStep number="02" title="选择执行入口" hint="CLI 与 API Provider 是并列入口"><ScanHeader state={state} title="CLI 自动识别" />
        <RuntimeTiles state={state} /><ProviderTiles state={state} /><ModelFields state={state} /></FlowStep>
      <FlowStep number="03" title="装配本地能力" hint="每项都保留识别来源与状态"><CapabilityToolbar state={state} tabs={false} />
        <CapabilityTable state={state} all /></FlowStep></main><DraftSummary state={state} full /></div></div>;
}

function FlowIntro() {
  return <header className="ar-flow-intro"><span className="ar-eyebrow">新建 AGENT</span><h1>从可执行环境开始配置 Agent</h1><p>运行时决定模型与推理强度，本地识别结果决定可挂载的 Skills、Tools 和 MCP。</p></header>;
}

function FlowStep({ number, title, hint, children }) {
  return <section className="ar-flow-step"><header><span>{number}</span><div><h2>{title}</h2><p>{hint}</p></div></header><div>{children}</div></section>;
}

function StepRail({ state }) {
  const selected = Object.values(state.draft.selected).reduce((sum, items) => sum + items.length, 0);
  return <aside className="ar-step-rail"><span>配置步骤</span><ol><li className="done"><Check size={14} /><b>身份</b><small>{state.draft.name || "未命名"}</small></li>
    <li className="active"><CircleDot size={14} /><b>Runtime</b><small>{state.draft.channel === "cli" ? state.runtime.name : state.provider.name}</small></li>
    <li><CircleDot size={14} /><b>能力</b><small>{selected} 项已选</small></li></ol></aside>;
}

function RuntimeTiles({ state }) {
  return <div className="ar-runtime-tiles">{RUNTIMES.map((item) => <RuntimeTile key={item.id} item={item} state={state} />)}</div>;
}

function RuntimeTile({ item, state }) {
  const selected = state.draft.channel === "cli" && state.draft.runtimeId === item.id;
  return <article className={`${selected ? "selected" : ""} ${item.status !== "ready" ? "muted" : ""}`}><header><RuntimeIdentity item={item} /><Status status={item.status} label={item.status === "ready" ? "已识别可用" : item.status === "adapter" ? "等待 Adapter" : "未安装"} /></header>
    <code>{item.path}</code><p>{item.status === "ready" ? `${item.models.length} 个模型 · ${item.auth}` : item.install || item.auth}</p>
    <footer>{item.status === "ready" && <TestButton id={`runtime:${item.id}`} state={state} label="测试" />}<button className="ar-button secondary" disabled={selected || item.status !== "ready"}
      onClick={() => state.selectRuntime(item)}>{selected ? "当前入口" : item.status === "ready" ? "使用此 CLI" : "尚不可选"}</button></footer></article>;
}

function ProviderTiles({ state }) {
  return <div className="ar-provider-tiles"><header><Terminal size={15} /><b>或者使用 API Provider</b><span>不依赖本地 CLI</span></header>{PROVIDERS.map((item) => {
    const selected = state.draft.channel === "api" && state.draft.providerId === item.id;
    return <button key={item.id} disabled={item.status !== "ready"} className={selected ? "selected" : ""} onClick={() => state.selectProvider(item)}>
      <span><b>{item.name}</b><small>{item.endpoint}</small></span><Status status={item.status} label={item.auth} /></button>;
  })}</div>;
}
