import { Play } from "lucide-react";
import { useState } from "react";
import { startRun } from "../../api";
import { useWorld } from "../../context/WorldContext";
import { nodeText, shortId } from "../../utils/labels";


export function LaunchControl({ thread }) {
  const { data, projectId, refresh, setError } = useWorld();
  const pinned = thread.nodes;
  const [pipelineId, setPipelineId] = useState("");
  const [nodeId, setNodeId] = useState("");
  const effectivePipeline = data.pipelines.some((item) => item.id === pipelineId) ? pipelineId : data.pipelines[0]?.id || "";
  const effectiveNode = pinned.some((node) => node.id === nodeId) ? nodeId : pinned[0]?.id || "";
  const launch = async () => {
    setBusy(true);
    try { await startRun(projectId, { node_id: effectiveNode, pipeline_id: effectivePipeline, payload: { thread_id: thread.id } }); await refresh(projectId); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  };
  const [busy, setBusy] = useState(false);
  if (!data.pipelines.length) return null;
  return <div className="launch-control">
    <select aria-label="选择流程" value={effectivePipeline} onChange={(event) => setPipelineId(event.target.value)}>
      {data.pipelines.map((pipeline) => <option key={pipeline.id} value={pipeline.id}>{pipeline.name || pipeline.id}</option>)}</select>
    <select aria-label="作用节点" value={effectiveNode} onChange={(event) => setNodeId(event.target.value)} disabled={!pinned.length}>
      {pinned.map((node) => <option key={node.id} value={node.id}>{shortId(node.id)} · {nodeText(node)}</option>)}
      {!pinned.length && <option value="">先钉入节点</option>}</select>
    <button className="button secondary" disabled={busy || !effectiveNode || !effectivePipeline} onClick={launch}><Play size={14} />启动流程</button></div>;
}
