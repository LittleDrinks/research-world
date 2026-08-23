import { Bot, Plus, RefreshCw, Save, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { getCatalog, registerConnector, saveAgent } from "../api";
import { EmptyState } from "../components/bits";
import { CapabilityPicker } from "../components/agents/CapabilityPicker";
import { useWorld } from "../context/WorldContext";
import { REASONING_EFFORTS } from "../utils/labels";
import "../agents.css";

const AGENT_EFFORTS = [...REASONING_EFFORTS, "xhigh"];
const AGENT_SANDBOXES = ["read-only", "workspace-write"];


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
    try { await saveAgent(agent.id, agentPayload(form)); await refresh(projectId); setState("saved"); }
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
      : <CatalogFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} retry={retry} />}</div>
    <footer className="agent-form-footer"><span>{issue || (state === "saved" ? "已保存" : state === "saving" ? "保存中..." : "")}</span>
      <button className="button primary" disabled={!catalog || Boolean(issue) || state === "saving"} onClick={save}><Save size={15} />保存</button></footer></section>;
}


function CatalogFailure({ message, retry }) {
  return <div className="catalog-failure"><div><b>Runtime 目录载入失败</b><span>{message}</span></div>
    <button className="button secondary" onClick={retry}><RefreshCw size={15} />重试识别</button></div>;
}


function catalogIssue(form, catalog) {
  if (!catalog) return "";
  const invalid = formIssue(form);
  if (invalid) return invalid;
  const endpoint = catalog.endpoints.find((item) => item.id === form.endpoint);
  if (!endpoint?.available) return "Endpoint 当前不可用";
  const model = catalog.models.some((item) => item.endpoint === form.endpoint && item.id === form.model);
  if (!model) return "模型与 Endpoint 不匹配";
  const missing = missingCapabilities(form, catalog);
  return missing.length ? `能力未被 Runtime 识别：${missing.join("、")}` : "";
}


function formIssue(form) {
  if (!form.name?.trim()) return "名称不能为空";
  if (!form.instructions?.trim()) return "指令不能为空";
  if (!AGENT_EFFORTS.includes(form.options.reasoning_effort)) return "推理强度不受支持";
  if (!AGENT_SANDBOXES.includes(form.options.sandbox)) return "Sandbox 不受支持";
  const rounds = form.options.max_rounds;
  if (!Number.isInteger(rounds) || rounds < 1 || rounds > 64) return "最大轮次必须是 1 到 64 的整数";
  const budget = form.options.token_budget;
  return Number.isInteger(budget) && budget >= 1 ? "" : "Token 预算必须是正整数";
}


function missingCapabilities(form, catalog) {
  const groups = [[form.skills, catalog.skills], [form.tools, catalog.tools], [form.connectors, catalog.connectors]];
  return groups.flatMap(([selected, options]) => {
    const known = new Set(options.filter((item) => item.available !== false).map((item) => item.id));
    return selected.filter((id) => !known.has(id));
  });
}


function CatalogFields({ form, patch, patchOption, catalog, retry }) {
  return <>
    <IdentityFields form={form} patch={patch} />
    <EndpointFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} />
    <CapabilityPicker label="Skills" options={catalog.skills} selected={form.skills} onChange={(value) => patch("skills", value)} />
    <CapabilityPicker label="工具" options={catalog.tools.map((tool) => ({ ...tool, description: tool.name }))} selected={form.tools} onChange={(value) => patch("tools", value)} />
    <ConnectorField form={form} patch={patch} catalog={catalog} retry={retry} />
    <label className="field"><span>指令</span><textarea required rows={6} value={form.instructions} onChange={(event) => patch("instructions", event.target.value)} /></label>
    <AdvancedFields form={form} patchOption={patchOption} /></>;
}


function normalize(agent) {
  return { skills: [], tools: [], connectors: [], options: {}, ...agent,
    options: { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 8, token_budget: 120000, ...(agent.options || {}) } };
}


function IdentityFields({ form, patch }) {
  return <label className="field"><span>名称</span><input required value={form.name || ""} onChange={(event) => patch("name", event.target.value)} /></label>;
}


function EndpointFields({ form, patch, patchOption, catalog }) {
  const models = catalog.models.filter((model) => model.endpoint === form.endpoint);
  const known = models.some((model) => model.id === form.model);
  const chooseEndpoint = (event) => {
    patch("endpoint", event.target.value);
    const first = catalog.models.find((model) => model.endpoint === event.target.value);
    if (first) patch("model", first.id);
  };
  return <div className="agent-grid">
    <label className="field"><span>Endpoint</span><select value={form.endpoint} onChange={chooseEndpoint}>
      {catalog.endpoints.map((endpoint) => <option key={endpoint.id} value={endpoint.id} disabled={!endpoint.available}>
        {endpoint.name}{endpoint.available ? "" : "（不可用）"}</option>)}</select></label>
    <label className="field"><span>模型</span><select value={form.model} onChange={(event) => patch("model", event.target.value)}>
      {!known && <option value={form.model}>{form.model}（不在 catalog）</option>}
      {models.map((model) => <option key={model.id} value={model.id}>{model.id}</option>)}</select></label>
    <label className="field"><span>推理强度</span><select value={form.options.reasoning_effort} onChange={(event) => patchOption("reasoning_effort", event.target.value)}>
      {AGENT_EFFORTS.map((effort) => <option key={effort} value={effort}>{effort}</option>)}</select></label></div>;
}


function ConnectorField({ form, patch, catalog, retry }) {
  const [adding, setAdding] = useState(false);
  const options = catalog.connectors.map(connectorOption);
  return <section className="connector-field"><header><span>Connectors</span>
    <button className="button secondary" onClick={() => setAdding(!adding)}>
      {adding ? <X size={14} /> : <Plus size={14} />}{adding ? "取消" : "添加"}</button></header>
    {adding && <ConnectorForm done={(connector) => {
      patch("connectors", [...new Set([...form.connectors, connector.id])]);
      setAdding(false); retry();
    }} />}
    <CapabilityPicker label="已识别 Connector" options={options} selected={form.connectors}
      onChange={(value) => patch("connectors", value)} /></section>;
}


function connectorOption(item) {
  const summary = [item.transport, item.source].filter(Boolean).join(" · ");
  return { id: item.id, name: item.name, description: item.description || summary,
    source: item.source, available: item.available };
}


function ConnectorForm({ done }) {
  const { setError } = useWorld();
  const [form, setForm] = useState({ id: "", name: "", transport: "stdio", location: "", args: "", credentialKey: "", credentialEnv: "" });
  const [busy, setBusy] = useState(false);
  const patch = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => {
    event.preventDefault(); setBusy(true);
    try { const connector = await registerConnector(connectorPayload(form)); setError(""); done(connector); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return <form className="connector-form" onSubmit={submit}><ConnectorInputs form={form} patch={patch} />
    <button className="button primary" disabled={busy} type="submit"><Plus size={14} />注册 Connector</button></form>;
}


function ConnectorInputs({ form, patch }) {
  return <><div className="agent-grid">
    <label className="field"><span>ID</span><input required pattern="[A-Za-z][A-Za-z0-9_-]*" value={form.id} onChange={(event) => patch("id", event.target.value)} /></label>
    <label className="field"><span>名称</span><input required value={form.name} onChange={(event) => patch("name", event.target.value)} /></label>
    <label className="field"><span>Transport</span><select value={form.transport} onChange={(event) => patch("transport", event.target.value)}><option value="stdio">stdio</option><option value="http">HTTP</option><option value="sse">SSE</option></select></label></div>
    <label className="field"><span>{form.transport === "stdio" ? "命令" : "URL"}</span><input required value={form.location} onChange={(event) => patch("location", event.target.value)} /></label>
    {form.transport === "stdio" && <label className="field"><span>参数</span><textarea rows={3} value={form.args} onChange={(event) => patch("args", event.target.value)} /></label>}
    <CredentialInputs form={form} patch={patch} />
  </>;
}


function CredentialInputs({ form, patch }) {
  const stdio = form.transport === "stdio";
  const required = Boolean(form.credentialKey || form.credentialEnv);
  return <div className="connector-credential">
    <label className="field"><span>{stdio ? "进程 Env key" : "Header 名"}</span><input required={required}
      pattern={stdio ? "[A-Za-z_][A-Za-z0-9_]*" : undefined} value={form.credentialKey}
      onChange={(event) => patch("credentialKey", event.target.value)} /></label>
    <label className="field"><span>来源环境变量</span><input required={required} pattern="[A-Za-z_][A-Za-z0-9_]*"
      value={form.credentialEnv} onChange={(event) => patch("credentialEnv", event.target.value)} /></label></div>;
}


function connectorPayload(form) {
  const base = { id: form.id.trim(), name: form.name.trim(), transport: form.transport };
  const args = form.args.split("\n").map((value) => value.trim()).filter(Boolean);
  const field = form.transport === "stdio" ? "env" : "headers";
  const credential = credentialPayload(form, field);
  if (form.transport === "stdio") return { ...base, command: form.location.trim(), args, ...credential };
  return { ...base, url: form.location.trim(), ...credential };
}


function credentialPayload(form, field) {
  const key = form.credentialKey.trim();
  const env = form.credentialEnv.trim();
  return key && env ? { [field]: { [key]: `\${${env}}` } } : {};
}


function agentPayload(form) {
  return { id: form.id, name: form.name.trim(), endpoint: form.endpoint, model: form.model,
    instructions: form.instructions.trim(), skills: [...form.skills], tools: [...form.tools],
    connectors: [...form.connectors], options: optionPayload(form.options) };
}


function optionPayload(options) {
  return { reasoning_effort: options.reasoning_effort, sandbox: options.sandbox,
    max_rounds: options.max_rounds, token_budget: options.token_budget };
}


function AdvancedFields({ form, patchOption }) {
  return <details className="agent-advanced"><summary>高级设置</summary><div className="agent-grid">
    <label className="field"><span>Sandbox</span><select value={form.options.sandbox} onChange={(event) => patchOption("sandbox", event.target.value)}>
      {AGENT_SANDBOXES.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
    <label className="field"><span>最大轮次</span><input type="number" min="1" max="64" step="1" value={form.options.max_rounds}
      onChange={(event) => patchOption("max_rounds", Number(event.target.value))} /></label>
    <label className="field"><span>Token 预算</span><input type="number" min="1" step="1" value={form.options.token_budget}
      onChange={(event) => patchOption("token_budget", Number(event.target.value))} /></label></div></details>;
}
