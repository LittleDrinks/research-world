import { useEffect, useState } from "react";
import { createAgent, getCatalog } from "../../api";
import { useWorld } from "../../context/WorldContext";
import { newAgentPayload } from "../../utils/agents";
import { Field, FormActions } from "../Field";
import { Modal } from "../Modal";

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


export function NewAgentDialog({ open, onClose, done }) {
  const { setError } = useWorld();
  const [form, setForm] = useState(EMPTY);
  const catalog = useCatalog(open);
  const [busy, setBusy] = useState(false);
  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const submit = async (event) => {
    event.preventDefault(); setBusy(true);
    try { const agent = await createAgent(newAgentPayload(form, catalog)); setForm(EMPTY); onClose(); done(agent); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  return <Modal title="新建 Agent" open={open} onClose={onClose}><form onSubmit={submit} className="form-stack">
    <AgentFields form={form} update={update} />
    <FormActions onCancel={onClose} submitting={busy || !catalog} submitLabel="创建 Agent" /></form></Modal>;
}


function AgentFields({ form, update }) {
  return <><Field label="ID" hint="小写字母、数字、连字符，创建后不可改"><input required pattern="[a-z0-9-]+" value={form.id} onChange={update("id")} autoFocus /></Field>
    <Field label="名称"><input required value={form.name} onChange={update("name")} /></Field>
    <Field label="指令"><textarea required rows={4} value={form.instructions} onChange={update("instructions")} /></Field></>;
}
