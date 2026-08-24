import { Download, FlaskConical, Folder, ShieldCheck } from "lucide-react";
import { ENDPOINTS } from "./seed";
import { CopyValue, Field, Status } from "./shared";

export function ProfilePanel({ state }) {
  return <div className="arp-panel-stack"><IdentitySection state={state} /><WorkspaceSection state={state} /></div>;
}

function IdentitySection({ state }) {
  return <Section title="身份" detail="Profile 是独立 AgentSpec snapshot；Preset 只记录来源。"><div className="arp-form-grid"><Field label="名称"><input aria-label="Profile 名称" value={state.profile.name} onChange={(event) => state.patchProfile({ name: event.target.value })} /></Field><Field label="Stable id" hint="保存后不可变"><CopyValue>{state.profile.id}</CopyValue></Field></div><Field label="Instructions"><textarea aria-label="Profile Instructions" rows="6" value={state.profile.instructions} onChange={(event) => state.patchProfile({ instructions: event.target.value })} /></Field></Section>;
}

function WorkspaceSection({ state }) {
  return <Section title="Workspace 与权限" detail="保存 policy，不把个人宿主路径写入 Profile。"><div className="arp-form-grid"><Field label="Workspace policy"><select aria-label="Workspace policy" value={state.profile.workspace} onChange={(event) => state.patchProfile({ workspace: event.target.value })}><option>Project workspace</option><option>Isolated worktree</option><option>Read-only workspace</option></select></Field><Field label="Sandbox"><select aria-label="Sandbox" value={state.profile.sandbox} onChange={(event) => state.patchProfile({ sandbox: event.target.value })}><option value="workspace-write">workspace-write</option><option value="read-only">read-only</option></select></Field></div><div className="arp-inline-note"><Folder size={15} /><span>Resolved at launch</span><code>/workspace/projects/q89/source-researcher-with-a-long-derived-directory</code></div></Section>;
}

export function ModelPanel({ state }) {
  return <div className="arp-panel-stack"><Section title="Endpoint 与模型" detail="Runtime、Endpoint 和 model 独立选择；secret 未决会阻止 ready。"><div className="arp-form-grid"><EndpointField state={state} /><Field label="Model"><textarea aria-label="Model" rows="2" spellCheck="false" value={state.profile.model} onChange={(event) => state.patchProfile({ model: event.target.value })} /></Field><Field label="Reasoning"><Reasoning value={state.profile.reasoning} patch={state.patchProfile} /></Field><Field label="Service tier"><select aria-label="Service tier" defaultValue="auto"><option>auto</option><option>priority</option></select></Field></div></Section><SecretSection state={state} /></div>;
}

function EndpointField({ state }) {
  return <Field label="Endpoint"><select aria-label="Endpoint" value={state.profile.endpoint} onChange={(event) => state.patchProfile({ endpoint: event.target.value })}>{ENDPOINTS.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}</select></Field>;
}

export function Reasoning({ value, patch }) {
  return <select aria-label="Reasoning" value={value} onChange={(event) => patch({ reasoning: event.target.value })}><option value="">未选择</option><option>medium</option><option>high</option><option>xhigh</option></select>;
}

function SecretSection({ state }) {
  const endpoint = ENDPOINTS.find((item) => item.id === state.profile.endpoint);
  const status = endpoint?.secret || "unknown";
  return <Section title="环境变量与 Secret" detail="只显示 provider、scope 和状态；值永不进入页面或诊断。"><div className="arp-definition-list"><div><ShieldCheck size={15} /><code>{state.profile.endpoint || "endpoint unresolved"}</code><span>Runtime-managed</span><Status value={status} /></div><div><ShieldCheck size={15} /><code>Kimi config</code><span>valid != authenticated</span><Status value="unknown" /></div></div><button onClick={() => state.setNotice("只刷新 secret 状态；未读取值。")}><FlaskConical size={15} />检查状态</button></Section>;
}

export function DiagnosticsPanel({ state }) {
  return <div className="arp-panel-stack"><ReadinessSection state={state} /><DiagnosticActions state={state} /><EnvironmentSection /></div>;
}

function ReadinessSection({ state }) {
  return <Section title="Readiness" detail="六组状态独立投影；unknown 不会显示为 ready。"><div className="arp-readiness">{state.readiness.groups.map((item) => <div key={item.name}><Status value={item.status} /><span><b>{item.name}</b><small>{item.detail}</small></span></div>)}</div>{state.readiness.issues.length > 0 && <div className="arp-alert" role="alert">{state.readiness.issues.map((item) => <div key={item.code}><code>{item.code}</code><span>{item.message}</span></div>)}</div>}</Section>;
}

function DiagnosticActions({ state }) {
  const summary = `runtime=${state.profile.runtime} realm=${state.profile.realm} readiness=${state.readiness.status} issues=${state.readiness.issues.map((item) => item.code).join(",") || "none"}`;
  return <Section title="诊断摘要" detail="稳定 reason code、检查时间与脱敏事实可复制；不包含 stdout、stderr、env value 或 token。"><CopyValue label="复制脱敏诊断">{summary}</CopyValue><div className="arp-actions"><button onClick={state.refresh}><FlaskConical size={15} />重新检查</button><button onClick={() => state.setNotice("已导出脱敏诊断 JSON。")}><Download size={15} />导出 JSON</button></div></Section>;
}

function EnvironmentSection() {
  return <Section title="Execution realms" detail="WSL、Windows 与 container 独立判定；跨 realm 发现不能成为当前 ready。"><div className="arp-definition-list"><div><span className="arp-realm">WSL</span><code>wsl:ubuntu</code><span>launch realm</span><Status value="ready" /></div><div><span className="arp-realm">WIN</span><code>windows:host</code><span>inventory only</span><Status value="found" /></div><div><span className="arp-realm">CTR</span><code>container:runtime</code><span>probe timeout</span><Status value="error" /></div></div></Section>;
}

export function Section({ title, detail, children }) {
  return <section className="arp-section"><header><h2>{title}</h2><p>{detail}</p></header>{children}</section>;
}
