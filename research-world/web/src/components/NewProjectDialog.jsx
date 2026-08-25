import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProject } from "../api";
import { useWorld } from "../context/WorldContext";
import { Field, FormActions } from "./Field";
import { Modal } from "./Modal";

const EMPTY = { name: "", title: "", question: "" };

export function NewProjectDialog({ open, onClose }) {
  const { selectProject, setError } = useWorld();
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const submit = async (event) => {
    event.preventDefault(); setSubmitting(true);
    try {
      const result = await createProject(form);
      if (!result?.id) throw new Error("创建项目响应缺少 id");
      setForm(EMPTY); onClose();
      await selectProject(result.id); navigate("/map");
    } catch (error) { setError(error.message); }
    finally { setSubmitting(false); }
  };
  return <Modal title="新建研究项目" open={open} onClose={onClose}><form onSubmit={submit} className="form-stack">
    <Field label="项目名称"><input required value={form.name} onChange={update("name")} autoFocus /></Field>
    <Field label="问题标题"><input required value={form.title} onChange={update("title")} /></Field>
    <Field label="研究问题"><textarea required rows="5" value={form.question} onChange={update("question")} /></Field>
    <FormActions onCancel={onClose} submitting={submitting} submitLabel="创建项目" />
  </form></Modal>;
}
