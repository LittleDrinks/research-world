import { useEffect, useState } from "react";
import { getNode } from "../../api";
import { KIND_LABELS, LIFE_LABELS, nodeText } from "../../utils/labels";


export function NodePeek({ nodeId }) {
  const [node, setNode] = useState(null);
  useEffect(() => {
    let stale = false;
    getNode(nodeId).then((value) => !stale && setNode(value)).catch(() => !stale && setNode(false));
    return () => { stale = true; };
  }, [nodeId]);
  if (node === null) return <div className="node-peek">正在载入节点...</div>;
  if (node === false) return <div className="node-peek">节点不存在或已删除</div>;
  return <div className="node-peek">
    <header><i className={`kind-dot kind-${node.kind}`} /><b>{nodeText(node)}</b><span>{KIND_LABELS[node.kind]} · {LIFE_LABELS[node.life_state] || node.life_state}</span></header>
    <details><summary>完整记录</summary><pre>{JSON.stringify(node.payload, null, 2)}</pre></details></div>;
}
