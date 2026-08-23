import { AgentRail, CapabilityTable, CapabilityToolbar, DraftSummary, IdentityEditor, ModelFields, PrototypeHeader, ProviderInventory, RuntimeInventory, ScanHeader } from "./shared";

export function VariantA({ state }) {
  return <div className="ar-variant ar-a"><PrototypeHeader state={state} section="清单优先" />
    <div className="ar-a-body"><AgentRail state={state} /><main className="ar-a-main">
      <section className="ar-flat-section"><header className="ar-title"><span className="ar-eyebrow">AGENT 草稿</span><h1>配置执行环境与本地能力</h1></header><IdentityEditor state={state} /></section>
      <section className="ar-flat-section"><ScanHeader state={state} /><RuntimeInventory state={state} /><ModelFields state={state} /><ProviderInventory state={state} /></section>
      <section className="ar-flat-section"><header className="ar-section-head"><div><span className="ar-eyebrow">本地能力</span><h2>Skills / Tools / MCP</h2><p>展示扫描来源、路径与可用状态</p></div></header>
        <CapabilityToolbar state={state} /><CapabilityTable state={state} /></section></main><DraftSummary state={state} full /></div></div>;
}
