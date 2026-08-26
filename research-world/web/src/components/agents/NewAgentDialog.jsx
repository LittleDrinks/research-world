import { useEffect, useState } from "react";
import { createAgent, getCatalog } from "../../api";
import { useWorld } from "../../context/WorldContext";
import { agentCatalogIssue, blockedTools, newAgentPayload, toolStatus } from "../../utils/agents";
import { FormActions } from "../Field";
import { Modal } from "../Modal";
import { AgentDraftEditor } from "./AgentDraftEditor";

const EMPTY = { id: "", name: "", instructions: "" };


function useCatalog(open) {
  const { projectId, setError } = useWorld();
  const [catalog, setCatalog] = useState(null);
  useEffect(() => {
    if (!open) return;
    setCatalog(null);
    getCatalog(projectId).then(setCatalog).catch((error) => setError(error.message));
  }, [open, projectId]);
  return catalog;
}


export function NewAgentDialog({ open, onClose, done, preset }) {
  const [spec, setSpec] = useState(null);
  const catalog = useCatalog(open);
  const { busy, submit } = useCreateAgent(spec, onClose, done);
  useEffect(() => {
    if (open && catalog) setSpec(initialSpec(preset, catalog));
  }, [open, preset, catalog]);
  const blocked = spec ? blockedTools(spec.tools, preset?.tools || [], catalog.tools) : [];
  const issue = spec && catalog ? agentCatalogIssue(spec, catalog) : "";
  return <Modal wide title={preset ? `应用 Preset：${preset.name}` : "新建 Agent"} open={open} onClose={onClose}>
    <AgentDialogForm preset={preset} spec={spec} catalog={catalog} blocked={blocked} issue={issue}
      busy={busy} submit={submit} setSpec={setSpec} onClose={onClose} /></Modal>;
}


function AgentDialogForm({ preset, spec, catalog, blocked, issue, busy, submit, setSpec, onClose }) {
  return <form onSubmit={submit} className="form-stack">
    {preset && <p className="preset-reason">{preset.description}</p>}
    {blocked.length > 0 && <p className="preset-blocked" role="alert">Tool 不可用：{blocked.map(toolStatus).join("、")}。请移除该 Tool，或配置 Runtime 后重试。</p>}
    {!blocked.length && issue && <p className="preset-blocked" role="alert">{issue}</p>}
    {spec && <AgentDraftEditor spec={spec} catalog={catalog} onChange={setSpec} />}
    <FormActions onCancel={onClose} submitting={busy || !spec} disabled={blocked.length > 0 || Boolean(issue)}
      submitLabel="创建 Agent" /></form>;
}


function useCreateAgent(spec, onClose, done) {
  const { projectId, setError } = useWorld();
  const [busy, setBusy] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setBusy(true);
    try { const agent = await createAgent(spec, projectId); onClose(); done(agent); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return { busy, submit };
}


function initialSpec(preset, catalog) {
  const form = preset ? preset.spec : EMPTY;
  const capabilities = { skills: form.skills || [], tools: form.tools || [] };
  const value = newAgentPayload(form, catalog, capabilities);
  return { ...value, options: { ...value.options, ...(form.options || {}) } };
}
