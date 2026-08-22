import { Bot, RefreshCw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { getCatalog, saveAgent } from "../api";
import { EmptyState } from "../components/bits";
import { CapabilityPicker } from "../components/agents/CapabilityPicker";
import { useWorld } from "../context/WorldContext";
import { REASONING_EFFORTS } from "../utils/labels";
import "../agents.css";


export function AgentsPage() {
  const { agentId } = useParams();
  const { data, loading } = useWorld();
  if (loading) return <div className="page-loading">正在载入 Agent...</div>;
  if (!agentId && data.agents.length) return <Navigate to={`/agents/${encodeURIComponent(data.agents[0].id)}`} replace />;
  if (!agentId) return <EmptyState icon={Bot} title="暂无 Agent" hint="Agent 定义来自服务端 agents 目录。" />;
  const agent = data.agents.find((item) => item.id === agentId);
  if (!agent) return <EmptyState icon={Bot} title="Agent 不存在" />;
  return <AgentEditor key={agent.id} agent={agent} />;
}


function useCatalog(projectId) {
  const [catalog, setCatalog] = useState(null);
  const [failed, setFailed] = useState("");
  const [epoch, setEpoch] = useState(0);
  const { setError } = useWorld();
  useEffect(() => {
    let stale = false;
    setCatalog(null); setFailed("");
    getCatalog(projectId).then((value) => {
      if (!stale) { setCatalog(value); setError(""); }
    }).catch((error) => {
      if (!stale) { setFailed(error.message); setError(error.message); }
    });
    return () => { stale = true; };
  }, [projectId, epoch]);
  return { catalog, failed, retry: () => setEpoch((value) => value + 1) };
}


function useAgentForm(agent) {
  const { projectId, refresh, setError } = useWorld();
  const catalogState = useCatalog(projectId);
  const [form, setForm] = useState(() => normalize(agent));
  const [state, setState] = useState("");
  const patch = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const patchOption = (key, value) => setForm((current) => ({ ...current, options: { ...current.options, [key]: value } }));
  const save = async () => {
    setState("saving");
    try { await saveAgent(agent.id, form); await refresh(projectId); setState("saved"); }
    catch (error) { setError(error.message); setState(""); }
  };
  return { ...catalogState, form, patch, patchOption, state, save };
}


function AgentEditor({ agent }) {
  const { catalog, failed, retry, form, patch, patchOption, state, save } = useAgentForm(agent);
  const issue = catalogIssue(form, catalog);
  return <section className="agents-page"><div className="agent-form">
    <header className="agent-form-header"><h1>{form.name || form.id}</h1><span className="mono">{form.id}</span></header>
    {failed ? <CatalogFailure message={failed} retry={retry} />
      : !catalog ? <p className="record-empty">正在载入 runtime catalog...</p>
      : <CatalogFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} />}</div>
    <footer className="agent-form-footer"><span>{issue || (state === "saved" ? "已保存" : state === "saving" ? "保存中..." : "")}</span>
      <button className="button primary" disabled={!catalog || Boolean(issue) || state === "saving"} onClick={save}><Save size={15} />保存</button></footer></section>;
}


function CatalogFailure({ message, retry }) {
  return <div className="catalog-failure"><div><b>Runtime 目录载入失败</b><span>{message}</span></div>
    <button className="button secondary" onClick={retry}><RefreshCw size={15} />重试识别</button></div>;
}


function catalogIssue(form, catalog) {
  if (!catalog) return "";
  const runtime = catalog.runtimes.find((item) => item.id === form.runtime);
  if (!runtime?.available) return "Runtime 当前不可用";
  const model = catalog.models.some((item) => item.runtime === form.runtime && item.id === form.model);
  if (!model) return "模型与 Runtime 不匹配";
  const missing = missingCapabilities(form, catalog);
  return missing.length ? `能力未被 Runtime 识别：${missing.join("、")}` : "";
}


function missingCapabilities(form, catalog) {
  const groups = [[form.skills, catalog.skills], [form.tools, catalog.tools], [form.mcp_servers, catalog.mcp_servers]];
  return groups.flatMap(([selected, options]) => {
    const known = new Set(options.map((item) => item.id));
    return selected.filter((id) => !known.has(id));
  });
}


function CatalogFields({ form, patch, patchOption, catalog }) {
  return <>
    <IdentityFields form={form} patch={patch} />
    <RuntimeFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} />
    <CapabilityPicker label="Skills" options={catalog.skills} selected={form.skills} onChange={(value) => patch("skills", value)} />
    <CapabilityPicker label="工具" options={catalog.tools.map((tool) => ({ ...tool, description: tool.name }))} selected={form.tools} onChange={(value) => patch("tools", value)} />
    <CapabilityPicker label="MCP 服务器" options={catalog.mcp_servers.map((server) => ({ ...server, name: server.id, description: server.transport }))} selected={form.mcp_servers} onChange={(value) => patch("mcp_servers", value)} />
    <label className="field"><span>指令</span><textarea rows={6} value={form.instructions} onChange={(event) => patch("instructions", event.target.value)} /></label>
    <AdvancedFields form={form} patchOption={patchOption} /></>;
}


function normalize(agent) {
  return { skills: [], tools: [], mcp_servers: [], options: {}, ...agent,
    options: { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 8, token_budget: 120000, ...(agent.options || {}) } };
}


function IdentityFields({ form, patch }) {
  return <label className="field"><span>名称</span><input value={form.name || ""} onChange={(event) => patch("name", event.target.value)} /></label>;
}


function RuntimeFields({ form, patch, patchOption, catalog }) {
  const models = catalog.models.filter((model) => model.runtime === form.runtime);
  const known = models.some((model) => model.id === form.model);
  const chooseRuntime = (event) => {
    patch("runtime", event.target.value);
    const first = catalog.models.find((model) => model.runtime === event.target.value);
    if (first) patch("model", first.id);
  };
  return <div className="agent-grid">
    <label className="field"><span>Runtime</span><select value={form.runtime} onChange={chooseRuntime}>
      {catalog.runtimes.map((runtime) => <option key={runtime.id} value={runtime.id} disabled={!runtime.available}>
        {runtime.name}{runtime.available ? "" : "（不可用）"}{runtime.version ? ` · ${runtime.version}` : ""}</option>)}</select></label>
    <label className="field"><span>模型</span><select value={form.model} onChange={(event) => patch("model", event.target.value)}>
      {!known && <option value={form.model}>{form.model}（不在 catalog）</option>}
      {models.map((model) => <option key={model.id} value={model.id}>{model.id}</option>)}</select></label>
    <label className="field"><span>推理强度</span><select value={form.options.reasoning_effort} onChange={(event) => patchOption("reasoning_effort", event.target.value)}>
      {REASONING_EFFORTS.map((effort) => <option key={effort} value={effort}>{effort}</option>)}</select></label></div>;
}


function AdvancedFields({ form, patchOption }) {
  return <details className="agent-advanced"><summary>高级设置</summary><div className="agent-grid">
    <label className="field"><span>Sandbox</span><select value={form.options.sandbox} onChange={(event) => patchOption("sandbox", event.target.value)}>
      {["read-only", "workspace-write"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
    <label className="field"><span>最大轮次</span><input type="number" min="1" value={form.options.max_rounds}
      onChange={(event) => patchOption("max_rounds", Number(event.target.value))} /></label>
    <label className="field"><span>Token 预算</span><input type="number" min="1000" value={form.options.token_budget}
      onChange={(event) => patchOption("token_budget", Number(event.target.value))} /></label></div></details>;
}
