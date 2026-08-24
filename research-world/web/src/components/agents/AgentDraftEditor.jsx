import { CapabilityPicker } from "./CapabilityPicker";
import "../../agents.css";

const EFFORTS = ["low", "medium", "high"];
const SANDBOXES = ["read-only", "workspace-write"];


export function AgentDraftEditor({ spec, catalog, onChange }) {
  const patch = (key, value) => onChange({ ...spec, [key]: value });
  const patchOption = (key, value) => patch("options", { ...spec.options, [key]: value });
  return <div className="agent-draft-editor">
    <IdentityFields spec={spec} patch={patch} />
    <RuntimeFields spec={spec} catalog={catalog} onChange={onChange} patch={patch} patchOption={patchOption} />
    <CapabilityFields spec={spec} catalog={catalog} patch={patch} />
    <label className="field"><span>指令</span><textarea required rows={4} value={spec.instructions} onChange={(event) => patch("instructions", event.target.value)} /></label>
    <OptionFields spec={spec} patchOption={patchOption} />
  </div>;
}


function IdentityFields({ spec, patch }) {
  return <div className="agent-grid draft-identity">
    <label className="field"><span>ID</span><input required pattern="[a-z0-9-]+" value={spec.id} onChange={(event) => patch("id", event.target.value)} />
      <small>小写字母、数字、连字符，创建后不可改</small></label>
    <label className="field"><span>名称</span><input required value={spec.name} onChange={(event) => patch("name", event.target.value)} /></label>
  </div>;
}


function RuntimeFields({ spec, catalog, onChange, patch, patchOption }) {
  const models = catalog.models.filter((item) => item.endpoint === spec.endpoint);
  const chooseEndpoint = (event) => {
    const endpoint = event.target.value;
    const model = catalog.models.find((item) => item.endpoint === endpoint);
    onChange({ ...spec, endpoint, model: model?.id || "" });
  };
  return <div className="agent-grid">
    <label className="field"><span>Endpoint</span><select value={spec.endpoint} onChange={chooseEndpoint}>{catalog.endpoints.map(endpointOption)}</select></label>
    <label className="field"><span>模型</span><select value={spec.model} onChange={(event) => patch("model", event.target.value)}>{models.map(modelOption)}</select></label>
    <label className="field"><span>推理强度</span><select value={spec.options.reasoning_effort} onChange={(event) => patchOption("reasoning_effort", event.target.value)}>{EFFORTS.map(option)}</select></label>
  </div>;
}


function CapabilityFields({ spec, catalog, patch }) {
  return <>
    <CapabilityPicker label="Skills" options={catalog.skills} selected={spec.skills} onChange={(value) => patch("skills", value)} />
    <CapabilityPicker label="工具" options={catalog.tools.map(toolOption)} selected={spec.tools} onChange={(value) => patch("tools", value)} />
  </>;
}


function OptionFields({ spec, patchOption }) {
  return <details className="agent-advanced"><summary>权限与限制</summary><div className="agent-grid">
    <label className="field"><span>Sandbox</span><select value={spec.options.sandbox} onChange={(event) => patchOption("sandbox", event.target.value)}>{SANDBOXES.map(option)}</select></label>
    <NumberField label="最大轮次" value={spec.options.max_rounds} min={1} max={64} change={(value) => patchOption("max_rounds", value)} />
    <NumberField label="Token 预算" value={spec.options.token_budget} min={1000} max={2000000} change={(value) => patchOption("token_budget", value)} />
  </div></details>;
}


function NumberField({ label, value, min, max, change }) {
  return <label className="field"><span>{label}</span><input type="number" min={min} max={max} step="1" value={value}
    onChange={(event) => change(Number(event.target.value))} /></label>;
}


function endpointOption(item) {
  return <option key={item.id} value={item.id} disabled={!item.available}>{item.name}{item.available ? "" : "（不可用）"}</option>;
}


function modelOption(item) {
  return <option key={item.id} value={item.id}>{item.id}</option>;
}


function option(value) {
  return <option key={value} value={value}>{value}</option>;
}


function toolOption(item) {
  return { ...item, available: item.status === "ready" };
}
