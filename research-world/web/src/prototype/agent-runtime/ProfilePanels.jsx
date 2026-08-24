import { Download, FlaskConical, Folder, ShieldCheck } from "lucide-react";
import { READINESS } from "./seed";
import { CopyValue, Field, Status } from "./shared";

export function ProfilePanel({ state }) {
  return <div className="arp-panel-stack"><Section title="身份" detail="保存为稳定 AgentSpec；Preset 只记录草稿来源。"><div className="arp-form-grid"><Field label="名称"><input value={state.profile.name} onChange={(event) => state.patchProfile({ name: event.target.value })} /></Field><Field label="Stable id" hint="保存后不可变"><CopyValue>{state.profile.id}</CopyValue></Field></div><Field label="Instructions"><textarea rows="6" value={state.profile.instructions} onChange={(event) => state.patchProfile({ instructions: event.target.value })} /></Field></Section><WorkspaceSection state={state} /></div>;
}

function WorkspaceSection({ state }) {
  return <Section title="Workspace 与权限" detail="保存 policy，不把个人宿主路径写入 Profile。"><div className="arp-form-grid"><Field label="Workspace policy"><select value={state.profile.workspace} onChange={(event) => state.patchProfile({ workspace: event.target.value })}><option>Project workspace</option><option>Isolated worktree</option><option>Read-only workspace</option></select></Field><Field label="Sandbox"><select defaultValue="workspace-write"><option>workspace-write</option><option>read-only</option></select></Field></div><div className="arp-inline-note"><Folder size={15} /><span>Resolved at launch</span><code>/workspace/projects/q89/source-researcher-with-a-long-derived-directory</code></div></Section>;
}

export function ModelPanel({ state }) {
  return <div className="arp-panel-stack"><Section title="Endpoint 与模型" detail="Runtime、Endpoint 和模型是三个选择；只有 Adapter 支持时才出现高级参数。"><div className="arp-form-grid"><Field label="Endpoint"><select value={state.profile.endpoint} onChange={(event) => state.patchProfile({ endpoint: event.target.value })}><option>openai-compatible</option><option>codex-account</option></select></Field><Field label="Model"><textarea rows="2" spellCheck="false" value={state.profile.model} onChange={(event) => state.patchProfile({ model: event.target.value })} /></Field><Field label="Reasoning"><select value={state.profile.reasoning} onChange={(event) => state.patchProfile({ reasoning: event.target.value })}><option>medium</option><option>high</option><option>xhigh</option></select></Field><Field label="Service tier"><select defaultValue="auto"><option>auto</option><option>priority</option></select></Field></div></Section><SecretSection state={state} /></div>;
}

function SecretSection({ state }) {
  const rows = [["OPENAI_API_KEY", "Repository secret", "configured"], ["ANTHROPIC_API_KEY", "User secret", "missing"], ["KIMI_AUTH", "CLI-owned", "unknown"]];
  return <Section title="环境变量与 Secret" detail="只显示名称、scope 和状态；值永不进入页面或诊断。"><div className="arp-definition-list">{rows.map(([name, scope, status]) => <div key={name}><ShieldCheck size={15} /><code>{name}</code><span>{scope}</span><Status value={status} /></div>)}</div><button onClick={() => state.setNotice("Prototype：已刷新 secret 状态，未读取值。") }><FlaskConical size={15} />检查状态</button></Section>;
}

export function DiagnosticsPanel({ state }) {
  return <div className="arp-panel-stack"><Section title="Readiness" detail="聚合状态来自六个独立模块；unknown 不会显示为 ready。"><div className="arp-readiness">{READINESS.map((item) => <div key={item.name}><Status value={item.status} /><span><b>{item.name}</b><small>{item.detail}</small></span></div>)}</div></Section><DiagnosticActions state={state} /><EnvironmentSection /></div>;
}

function DiagnosticActions({ state }) {
  return <Section title="诊断摘要" detail="稳定 reason code、最近检查时间与脱敏事实可复制；不包含 stdout、stderr、env value 或 token。"><CopyValue label="复制脱敏诊断">runtime=codex status=ready checked=2026-08-24T12:04:18Z; tools=blocked reason=setup_required</CopyValue><div className="arp-actions"><button onClick={state.refresh}><FlaskConical size={15} />重新检查</button><button onClick={() => state.setNotice("Prototype：已导出脱敏诊断 JSON。") }><Download size={15} />导出 JSON</button></div></Section>;
}

function EnvironmentSection() {
  return <Section title="Execution realms" detail="WSL、Windows 与 container 独立判定；跨 realm 发现不能成为当前 ready。"><div className="arp-definition-list"><div><span className="arp-realm">WSL</span><code>linux PATH</code><span>launch realm</span><Status value="ready" /></div><div><span className="arp-realm">WIN</span><code>Windows PATH</code><span>2 found</span><Status value="found" /></div><div><span className="arp-realm">CTR</span><code>runtime container</code><span>probe error</span><Status value="error" /></div></div></Section>;
}

export function Section({ title, detail, children }) {
  return <section className="arp-section"><header><h2>{title}</h2><p>{detail}</p></header>{children}</section>;
}
