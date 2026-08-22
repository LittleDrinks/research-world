import { SendHorizontal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { searchNodes } from "../../api";
import { useWorld } from "../../context/WorldContext";
import { KIND_LABELS, nodeText } from "../../utils/labels";


export function mentionQuery(draft) {
  const match = draft.match(/(?:^|\s)@([^\s@]*)$/);
  return match ? match[1] : null;
}


export function insertMention(draft, nodeId) {
  return draft.replace(/(?:^|\s)@([^\s@]*)$/, (value) => `${value.startsWith(" ") ? " " : ""}@${nodeId} `);
}


function useMentionChoices(query, pinnedIds) {
  const { data, projectId } = useWorld();
  const [choices, setChoices] = useState([]);
  const request = useRef(0);
  useEffect(() => {
    if (query === null) { setChoices([]); return undefined; }
    const token = ++request.current;
    const show = (rows) => request.current === token && setChoices(rows.filter((row) => !pinnedIds.includes(row.id)).slice(0, 5));
    if (!query) { show(data.nodes.map((node) => ({ id: node.id, kind: node.kind, title: nodeText(node) }))); return undefined; }
    searchNodes(projectId, query)
      .then((rows) => show(rows.map((row) => ({ id: row.id, kind: row.kind, title: row.summary }))))
      .catch(() => {});
    return () => {};
  }, [query, projectId]);
  return choices;
}


function usePinning(onPin) {
  const [pinning, setPinning] = useState(false);
  const pin = async (nodeId) => {
    setPinning(true);
    try { return await onPin(nodeId); } finally { setPinning(false); }
  };
  return { pinning, pin };
}


export function Composer({ pinnedNodes, onSend, onPin, sending }) {
  const [draft, setDraft] = useState("");
  const { pinning, pin } = usePinning(onPin);
  const query = mentionQuery(draft);
  const choices = useMentionChoices(query, pinnedNodes.map((node) => node.id));
  const submit = async () => { const text = draft.trim(); if (!text || sending || pinning) return; if (await onSend(text)) setDraft(""); };
  const choose = async (node) => { if (await pin(node.id)) setDraft(insertMention(draft, node.id)); };
  const keyDown = (event) => {
    const composing = event.isComposing || event.nativeEvent?.isComposing || event.keyCode === 229;
    if (event.key === "Enter" && !event.shiftKey && !composing) { event.preventDefault(); submit(); }
  };
  return <div className="composer-wrap">
    {choices.length > 0 && <div className="mention-menu">{choices.map((node) =>
      <button key={node.id} onClick={() => choose(node)}><i className={`kind-dot kind-${node.kind}`} /><b className="mono">@{node.id}</b><span>{KIND_LABELS[node.kind]} · {node.title}</span></button>)}</div>}
    <div className="composer"><textarea aria-label="消息" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown}
      placeholder="发消息，输入 @ 引用节点" rows={3} />
      <button className="icon-button send-button" aria-label="发送" title={pinning ? "正在钉入节点" : "发送"} disabled={sending || pinning || !draft.trim()} onClick={submit}><SendHorizontal size={18} /></button></div></div>;
}
