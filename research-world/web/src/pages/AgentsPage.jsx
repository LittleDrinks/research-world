import { Bot, RefreshCw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { getCatalog, saveAgent } from "../api";
import { EmptyState } from "../components/bits";
import { CapabilityPicker } from "../components/agents/CapabilityPicker";
import { NewAgentDialog } from "../components/agents/NewAgentDialog";
import { PresetCapabilities } from "../components/agents/PresetCapabilities";
import { useWorld } from "../context/WorldContext";
import { AGENT_OPTION_DEFAULTS, blockedSkills, blockedTools, toolStatus } from "../utils/agents";
import { REASONING_EFFORTS } from "../utils/labels";
import "../agents.css";

const AGENT_EFFORTS = [...REASONING_EFFORTS, "xhigh"];
const AGENT_SANDBOXES = ["read-only", "workspace-write"];


export function AgentsPage() {
  const { agentId } = useParams();
  const { hash } = useLocation();
  const { data, loading } = useWorld();
  if (loading) return <div className="page-loading">正在载入 Agent...</div>;
  if (!agentId && data.agents.length) return <Navigate to={`/agents/${encodeURIComponent(data.agents[0].id)}${hash}`} replace />;
  if (!agentId) return <EmptyState icon={Bot} title="暂无 Agent" hint="点击侧栏 + 新建 Agent。" />;
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
    try { await saveAgent(agent.id, projectId, agentPayload(form)); await refresh(projectId); setState("saved"); }
    catch (error) { setError(error.message); setState(""); }
  };
  return { ...catalogState, form, patch, patchOption, state, save };
}


function AgentEditor({ agent }) {
  const { projectId, refresh } = useWorld();
  const navigate = useNavigate();
  const [preset, setPreset] = useState(null);
  const { catalog, failed, retry, form, patch, patchOption, state, save } = useAgentForm(agent);
  const issue = catalogIssue(form, catalog);
  const created = async (value) => { await refresh(projectId); navigate(`/agents/${encodeURIComponent(value.id)}`); };
  return <section className="agents-page"><div className="agent-form">
    <PresetPanel catalog={catalog} onApply={setPreset} />
    <header className="agent-form-header"><h1>{form.name || form.id}</h1><span className="mono">{form.id}</span></header>
    {failed ? <CatalogFailure message={failed} retry={retry} />
      : !catalog ? <p className="record-empty">正在载入 runtime catalog...</p>
      : <CatalogFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} />}</div>
    <footer className="agent-form-footer">{issue ? <span role="alert">{issue}</span>
      : <span>{state === "saved" ? "已保存" : state === "saving" ? "保存中..." : ""}</span>}
      <button className="button primary" disabled={!catalog || Boolean(issue) || state === "saving"} onClick={save}><Save size={15} />保存</button></footer>
    <NewAgentDialog open={Boolean(preset)} preset={preset} onClose={() => setPreset(null)} done={created} /></section>;
}


function PresetPanel({ catalog, onApply }) {
  const presets = catalog?.presets || [];
  if (!presets.length) return null;
  return <section className="preset-panel" aria-label="Profile Presets"><h2>Profile Presets</h2>
    {presets.map((preset) => <PresetRow key={preset.id} preset={preset} onApply={() => onApply(preset)} />)}</section>;
}


function PresetRow({ preset, onApply }) {
  return <div className="preset-row"><div className="preset-info"><b>{preset.name}</b><span className="mono">{preset.id}</span>
    <p>{preset.description}</p><PresetCapabilities preset={preset} /></div>
    <button className="button secondary" onClick={onApply}>应用为草稿</button></div>;
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
  return capabilityIssue(form, catalog);
}


function capabilityIssue(form, catalog) {
  const presetTools = catalog.presets.flatMap((preset) => preset.tools);
  const presetSkills = catalog.presets.flatMap((preset) => preset.skills || []);
  const tools = blockedTools(form.tools, presetTools, catalog.tools);
  const skills = blockedSkills(form.skills, presetSkills, catalog.skills);
  const blocked = [...skills, ...tools];
  const unknown = blocked.filter((item) => item.status === "missing").map((item) => item.id);
  const unavailable = blocked.filter((item) => item.status !== "missing");
  const issues = unknown.length ? [`能力未被 Runtime 识别：${unknown.join("、")}`] : [];
  if (unavailable.length) issues.push(`能力不可用：${unavailable.map(toolStatus).join("、")}`);
  return issues.join("；");
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


function availableCapability(item) {
  return item.available !== false && (!item.status || item.status === "ready");
}


function CatalogFields({ form, patch, patchOption, catalog }) {
  return <>
    <IdentityFields form={form} patch={patch} />
    <EndpointFields form={form} patch={patch} patchOption={patchOption} catalog={catalog} />
    <CapabilityPicker label="Skills" options={catalog.skills} selected={form.skills} onChange={(value) => patch("skills", value)} />
    <CapabilityPicker id="tool-catalog" label="工具" options={catalog.tools.map(toolOption)} selected={form.tools} onChange={(value) => patch("tools", value)} />
    <label className="field"><span>指令</span><textarea required rows={6} value={form.instructions} onChange={(event) => patch("instructions", event.target.value)} /></label>
    <AdvancedFields form={form} patchOption={patchOption} /></>;
}


function normalize(agent) {
  return { skills: [], tools: [], options: {}, ...agent,
    options: { ...AGENT_OPTION_DEFAULTS, ...(agent.options || {}) } };
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


function toolOption(tool) {
  return { ...tool, description: tool.description || tool.name,
    available: availableCapability(tool) };
}


function agentPayload(form) {
  return { id: form.id, name: form.name.trim(), endpoint: form.endpoint, model: form.model,
    instructions: form.instructions.trim(), skills: [...form.skills], tools: [...form.tools],
    options: optionPayload(form.options) };
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
