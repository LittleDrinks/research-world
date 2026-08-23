import { Sparkles } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { createAgent, draftAgent, getCatalog } from "../../api";
import { AgentDraftEditor } from "../agents/AgentDraftEditor";
import { useWorld } from "../../context/WorldContext";
import { usePopoverDismiss } from "./usePopoverDismiss";


export function ProfileDraftButton({ onDraft }) {
  const { catalog, busy, toggle, choose, close } = usePresetMenu(onDraft);
  const root = useRef(null);
  const trigger = useRef(null);
  usePopoverDismiss(Boolean(catalog), root, trigger, close);
  return <div className="profile-draft-launcher" ref={root}>
    <button ref={trigger} type="button" className="composer-tool" aria-expanded={Boolean(catalog)} disabled={busy} onClick={toggle}>
      <Sparkles size={13} />起草 Agent</button>
    {catalog && <PresetMenu presets={catalog.presets || []} busy={busy} onChoose={choose} />}</div>;
}


function usePresetMenu(onDraft) {
  const { projectId, setError } = useWorld();
  const [catalog, setCatalog] = useState(null);
  const [busy, setBusy] = useState(false);
  const close = useCallback(() => setCatalog(null), []);
  const toggle = async () => {
    if (catalog) return close();
    try { setCatalog(await getCatalog(projectId)); }
    catch (error) { setError(error.message); }
  };
  const choose = async (presetId) => {
    setBusy(true);
    try { onDraft({ ...await draftAgent(projectId, presetId), catalog }); close(); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return { catalog, busy, toggle, choose, close };
}


function PresetMenu({ presets, busy, onChoose }) {
  if (!presets.length) return <div className="preset-menu"><p className="record-empty">Runtime 未提供 Preset</p></div>;
  return <div className="preset-menu" role="menu">{presets.map((preset) =>
    <button type="button" role="menuitem" key={preset.id} disabled={busy} onClick={() => onChoose(preset.id)}>
      <b>{preset.name}</b><span className="mono">{preset.id}</span></button>)}</div>;
}


export function ProfileDraftCard({ draft, onCancel }) {
  const { projectId } = useWorld();
  const [spec, setSpec] = useState(() => cloneSpec(draft.spec));
  const { busy, error, created, confirm } = useDraftConfirm(spec, projectId);
  const blocked = blockedIssues(draft, spec);
  if (created) return <DraftCreated agent={created} />;
  return <div className="profile-draft" role="region" aria-label="Agent 草稿">
    <header className="draft-header"><Sparkles size={15} /><div><b>Agent 草稿</b><p className="preset-reason">{draft.reason}</p></div></header>
    <AgentDraftEditor spec={spec} catalog={draft.catalog} onChange={setSpec} />
    {blocked.length > 0 && <p className="preset-blocked" role="alert">{blocked.join("；")}</p>}
    {error && <p className="preset-blocked" role="alert">{error}</p>}
    <DraftActions busy={busy} blocked={blocked} onConfirm={confirm} onCancel={onCancel} /></div>;
}


function useDraftConfirm(spec, projectId) {
  const { refresh } = useWorld();
  const [state, setState] = useState({ busy: false, error: "", created: null });
  const confirm = async () => {
    setState({ busy: true, error: "", created: null });
    try {
      const agent = await createAgent(draftPayload(spec), projectId);
      await refresh(projectId);
      setState({ busy: false, error: "", created: agent });
    } catch (failure) { setState({ busy: false, error: failure.message, created: null }); }
  };
  return { ...state, confirm };
}


function draftPayload(spec) {
  return { ...spec, name: spec.name.trim(), instructions: spec.instructions.trim(),
    skills: [...spec.skills], tools: [...spec.tools], options: { ...spec.options } };
}


function cloneSpec(spec) {
  return { ...spec, skills: [...spec.skills], tools: [...spec.tools], options: { ...spec.options } };
}


function blockedIssues(draft, spec) {
  const status = new Map(draft.catalog.tools.map((tool) => [tool.id, tool.status || "ready"]));
  const server = draft.issues.filter((issue) => !issue.startsWith("tool unavailable:"));
  return spec.tools.filter((id) => (status.get(id) || "missing") !== "ready")
    .map((id) => `Tool 不可用：${id}（${status.get(id) || "missing"}）`).concat(server);
}


function DraftActions({ busy, blocked, onConfirm, onCancel }) {
  return <div className="draft-actions">
    <button type="button" className="button primary" disabled={busy || blocked.length > 0} onClick={onConfirm}>
      {busy ? "创建中..." : "确认创建"}</button>
    <button type="button" className="button secondary" disabled={busy} onClick={onCancel}>取消</button></div>;
}


function DraftCreated({ agent }) {
  return <div className="profile-draft draft-created" role="status">
    <p>Agent <b>{agent.name}</b>（<span className="mono">{agent.id}</span>）已创建。</p>
    <Link className="button primary" to={`/agents/${encodeURIComponent(agent.id)}`}>打开 Agent 设置</Link></div>;
}
