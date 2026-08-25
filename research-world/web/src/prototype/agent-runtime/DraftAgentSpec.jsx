import { ENDPOINTS, RUNTIMES, SKILLS, TOOLS } from "./seed";
import { Field, Status } from "./shared";
import { Reasoning, Section } from "./ProfilePanels";
import { runtimeKey } from "./runtimeKey";

export function DraftAgentSpec({ state }) {
  const draft = state.draft;
  return <div className="arp-draft-editor"><Identity state={state} draft={draft} /><Execution state={state} draft={draft} /><Capabilities state={state} draft={draft} /><DraftDecision state={state} /></div>;
}

function Identity({ state, draft }) {
  return <Section title="AgentSpec" detail="所有字段在保存前保持可编辑。"><div className="arp-form-grid"><Field label="Stable id"><input aria-label="Draft Stable id" value={draft.id} onChange={(event) => state.patchDraft({ id: event.target.value })} /></Field><Field label="名称"><input aria-label="Draft 名称" value={draft.name} onChange={(event) => state.patchDraft({ name: event.target.value })} /></Field></div><Field label="Instructions"><textarea aria-label="Draft Instructions" rows="4" value={draft.instructions} onChange={(event) => state.patchDraft({ instructions: event.target.value })} /></Field></Section>;
}

function Execution({ state, draft }) {
  return <Section title="Execution" detail="Runtime、realm、Endpoint 与 model 分别保存；reasoning 由 Adapter capability 决定。"><div className="arp-form-grid"><RuntimeField state={state} draft={draft} /><RealmField state={state} draft={draft} /><EndpointField state={state} draft={draft} /><Field label="Model"><textarea aria-label="Draft Model" rows="2" value={draft.model} onChange={(event) => state.patchDraft({ model: event.target.value })} /></Field><Field label="Reasoning"><Reasoning value={draft.reasoning} patch={state.patchDraft} /></Field><SandboxField state={state} draft={draft} /><WorkspaceField state={state} draft={draft} /></div></Section>;
}

function RuntimeField({ state, draft }) {
  const change = (event) => selectRuntime(state, event.target.value);
  const value = draft.runtime && draft.realm ? runtimeKey(draft.runtime, draft.realm) : "";
  return <Field label="Runtime"><select aria-label="Draft Runtime" value={value} onChange={change}><option value="">未选择</option>{RUNTIMES.map((item) => <option key={runtimeKey(item.id, item.realm)} value={runtimeKey(item.id, item.realm)}>{item.name} · {item.realm} · {item.status}</option>)}</select></Field>;
}

function selectRuntime(state, key) {
  const runtime = RUNTIMES.find((item) => runtimeKey(item.id, item.realm) === key);
  state.patchDraft({ runtime: runtime?.id || "", realm: runtime?.realm || "" });
}

function RealmField({ state, draft }) {
  return <Field label="Realm"><input aria-label="Draft Realm" value={draft.realm} onChange={(event) => state.patchDraft({ realm: event.target.value })} placeholder="wsl:ubuntu" /></Field>;
}

function EndpointField({ state, draft }) {
  return <Field label="Endpoint"><select aria-label="Draft Endpoint" value={draft.endpoint} onChange={(event) => state.patchDraft({ endpoint: event.target.value })}><option value="">未选择</option>{ENDPOINTS.map((item) => <option key={item.id} value={item.id}>{item.name} · secret {item.secret}</option>)}</select></Field>;
}

function SandboxField({ state, draft }) {
  return <Field label="Sandbox"><select aria-label="Draft Sandbox" value={draft.sandbox} onChange={(event) => state.patchDraft({ sandbox: event.target.value })}><option value="">未选择</option><option value="read-only">read-only</option><option value="workspace-write">workspace-write</option></select></Field>;
}

function WorkspaceField({ state, draft }) {
  return <Field label="Workspace"><select aria-label="Draft Workspace" value={draft.workspace} onChange={(event) => state.patchDraft({ workspace: event.target.value })}><option value="">未选择</option><option>Project workspace</option><option>Isolated worktree</option><option>Read-only workspace</option></select></Field>;
}

function Capabilities({ state, draft }) {
  return <Section title="Skills、Tools 与 MCP" detail="MCP 是 Tool adapter source；AgentSpec 不保存独立 MCP 数组。"><CapabilityGroup title="Skills" type="skills" items={SKILLS} selected={draft.skills} state={state} /><CapabilityGroup title="Tools · MCP source" type="tools" items={TOOLS} selected={draft.tools} state={state} /></Section>;
}

function CapabilityGroup({ title, type, items, selected, state }) {
  return <fieldset className="arp-draft-capabilities"><legend>{title}</legend>{items.map((item) => <label key={item.id}><input aria-label={"Draft " + item.name} type="checkbox" checked={selected.includes(item.id)} onChange={() => state.toggleDraftCapability(type, item.id)} /><span><b>{item.name}</b><small>{item.source || item.scope} · {item.description}</small></span><Status value={item.status} /></label>)}</fieldset>;
}

function DraftDecision({ state }) {
  return <Section title="推荐与未决" detail="推荐理由不覆盖 readiness；所有 unresolved 解决后才可保存。"><div className="arp-rationale">{state.draft.rationale.map((item) => <p key={item}>{item}</p>)}</div>{state.draftReadiness.issues.length ? <div className="arp-alert" role="alert">{state.draftReadiness.issues.map((item) => <div key={item.code + ":" + item.message}><code>{item.code}</code><span>{item.message}</span></div>)}</div> : <div className="arp-ready-line"><Status value="ready" /><span>AgentSpec 草稿可以保存</span></div>}</Section>;
}
