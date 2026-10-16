import { Check, X } from "lucide-react";
import { useState } from "react";
import { resolveAdmission } from "../api";
import { useWorld } from "../context/WorldContext";


export function AdmissionControl({ node }) {
  const { projectId, refresh } = useWorld();
  const [state, setState] = useState({ mode: "", reason: "", busy: false, message: "", error: "" });
  const decide = async (decision) => submitDecision(decision, node, projectId, state, setState, refresh);
  if (state.message) return <p className="admission-success" role="status">{state.message}</p>;
  if (node?.kind !== "source" || node.life_state !== "pending") return null;
  return <section className="admission-control" aria-label="Source Admission">
    {state.mode === "reject" ? <RejectForm state={state} setState={setState} onSubmit={() => decide("reject")} />
      : <DecisionButtons busy={state.busy} onApprove={() => decide("approve")} onReject={() => setState({ ...state, mode: "reject", error: "" })} />}
    {state.error && <p className="admission-error" role="alert">{state.error}</p>}
  </section>;
}


async function submitDecision(decision, node, projectId, state, setState, refresh) {
  const reason = state.reason.trim();
  if (decision === "reject" && !reason) return setState({ ...state, error: "请输入驳回理由" });
  setState({ ...state, busy: true, error: "" });
  try {
    await resolveAdmission(projectId, node.id, { decision, ...(reason ? { reason } : {}) });
    setState({ ...state, busy: false, message: decision === "approve" ? "Admission 已通过" : "Admission 已驳回", error: "" });
    await refresh(projectId);
  } catch (error) { setState({ ...state, busy: false, error: error.message }); }
}


function DecisionButtons({ busy, onApprove, onReject }) {
  return <div className="admission-actions">
    <button className="button primary" disabled={busy} onClick={onApprove}><Check size={15} />{busy ? "处理中..." : "通过"}</button>
    <button className="button secondary" disabled={busy} onClick={onReject}><X size={15} />驳回</button>
  </div>;
}


function RejectForm({ state, setState, onSubmit }) {
  const change = (event) => setState({ ...state, reason: event.target.value, error: "" });
  const submit = (event) => { event.preventDefault(); onSubmit(); };
  return <form className="admission-reject" onSubmit={submit}>
    <label><span>驳回理由</span><textarea required rows="3" value={state.reason} disabled={state.busy} onChange={change} /></label>
    <div className="admission-actions"><button className="button primary" disabled={state.busy || !state.reason.trim()} type="submit">{state.busy ? "处理中..." : "确认驳回"}</button>
      <button className="button secondary" disabled={state.busy} type="button" onClick={() => setState({ ...state, mode: "", error: "" })}>取消</button></div>
  </form>;
}
