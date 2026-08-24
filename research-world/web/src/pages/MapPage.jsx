import { Focus, Map as MapIcon, Network, ScrollText } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { setProjectAuto, startRun } from "../api";
import { journalEntries } from "../components/journal";
import { useWorld } from "../context/WorldContext";
import { GraphView } from "../graph/GraphView";
import { Inspector } from "../graph/Inspector";
import { formatTime, shortId } from "../utils/labels";
import "../map.css";


export function MapPage() {
  const { data, loading, refresh, setError } = useWorld();
  const [params, setParams] = useSearchParams();
  const view = params.get("view") === "journal" ? "journal" : "map";
  if (loading) return <div className="page-loading">正在载入研究世界...</div>;
  const setView = (next) => setParams(next === "journal" ? { view: "journal" } : {});
  return <section className="map-page">
    <MapToolbar data={data} view={view} setView={setView} refresh={refresh} setError={setError} />
    {view === "journal" ? <Journal entries={journalEntries(data.nodes, data.runs)} /> : <MapView data={data} />}</section>;
}


function MapToolbar({ data, view, setView, refresh, setError }) {
  const project = data.projects.find((item) => item.id === data.active_project_id);
  const active = data.runs.filter((item) => ["queued", "running", "waiting_human"].includes(item.status)).length;
  const toggle = async () => {
    try { await setProjectAuto(project.id, !project.auto); await refresh(project.id); }
    catch (error) { setError(error.message); }
  };
  return <header className="map-toolbar"><div><b>{view === "journal" ? "科研日志" : "研究地图"}</b>
      <span>{data.nodes.length} 个节点 · {data.edges.length} 条关系 · {active} 个运行中</span></div>
    <div className="map-tools"><label className="auto-toggle"><input type="checkbox" checked={Boolean(project?.auto)} onChange={toggle} /><span>Auto</span></label>
      <div className="segmented" aria-label="地图视图">
        <button className={view === "map" ? "active" : ""} onClick={() => setView("map")}><MapIcon size={16} /><span>地图</span></button>
        <button className={view === "journal" ? "active" : ""} onClick={() => setView("journal")}><ScrollText size={16} /><span>科研日志</span></button></div></div></header>;
}


function Journal({ entries }) {
  if (!entries.length) return <p className="journal-empty">暂无科研日志</p>;
  return <ol className="journal">{entries.map((entry, index) => <li key={index}>
    <time className="mono">{formatTime(entry.time)}</time><i className={`kind-dot ${entry.tone}`} /><p>{entry.text}</p><span className="mono journal-ref">{shortId(entry.ref)}</span></li>)}</ol>;
}


function useSelectedNode(data, params, setParams) {
  const rootId = data.nodes.find((node) => node.kind === "question")?.id || "";
  const [selectedId, setSelectedId] = useState(params.get("node") || rootId);
  useEffect(() => { const id = params.get("node"); if (id && data.nodes.some((node) => node.id === id)) setSelectedId(id); }, [params, data.nodes]);
  const select = (id) => { setSelectedId(id); setParams(id ? { node: id } : {}); };
  return { selected: data.nodes.find((node) => node.id === selectedId) || data.nodes[0], select };
}


function useStartRun(projectId) {
  const { refresh, setError } = useWorld();
  const navigate = useNavigate();
  return (node, pipelineId) => startRun(projectId, { node_id: node.id, pipeline_id: pipelineId })
    .then((run) => refresh(projectId).then(() => navigate(`/traces/${encodeURIComponent(run.id)}`)))
    .catch((error) => setError(error.message));
}


function MapView({ data }) {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [overview, setOverview] = useState(true);
  const { selected, select } = useSelectedNode(data, params, setParams);
  const newIds = useNewNodes(data.nodes);
  const active = activeRun(data.runs, selected?.id);
  const relations = useMemo(() => graphEdges(data.nodes, data.edges), [data.nodes, data.edges]);
  const busyIds = useMemo(() => busyNodeIds(data.runs), [data.runs]);
  const graph = useMemo(() => overview ? { nodes: data.nodes, edges: relations }
    : branch(data.nodes, relations, selected?.id), [data.nodes, relations, overview, selected?.id]);
  const start = useStartRun(data.active_project_id);
  return <div className="map-workspace"><div className="graph-canvas">
      <GraphView nodes={graph.nodes} edges={graph.edges} selectedId={selected?.id} onSelect={select} newIds={newIds} busyIds={busyIds} />
      <ScopeToggle overview={overview} setOverview={setOverview} /></div>
    <Inspector node={selected} nodes={data.nodes} edges={data.edges} run={active} onSelect={select} onStart={start}
      onOpen={(run) => navigate(`/traces/${encodeURIComponent(run.id)}`)} /></div>;
}


function ScopeToggle({ overview, setOverview }) {
  return <div className="segmented map-scope" aria-label="地图范围">
    <button className={!overview ? "active" : ""} onClick={() => setOverview(false)} title="节点上下文"><Focus size={15} /></button>
    <button className={overview ? "active" : ""} onClick={() => setOverview(true)} title="全局结构"><Network size={15} /></button></div>;
}


function busyNodeIds(runs) {
  const ids = new Set();
  runs.filter((item) => ["queued", "running", "waiting_human"].includes(item.status)).forEach((item) => {
    ids.add(item.node_id);
    if (item.payload?.experiment_id) ids.add(item.payload.experiment_id);
  });
  return ids;
}


function activeRun(runs, nodeId) {
  const active = runs.filter((item) => ["queued", "running", "waiting_human"].includes(item.status));
  return active.find((item) => item.payload?.experiment_id === nodeId) || active.find((item) => item.node_id === nodeId);
}


function branch(nodes, edges, focusId) {
  const ids = new Set([focusId]);
  edges.filter((edge) => edge.source === focusId || edge.target === focusId)
    .forEach((edge) => { ids.add(edge.source); ids.add(edge.target); });
  return { nodes: nodes.filter((node) => ids.has(node.id)),
    edges: edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target)) };
}


function graphEdges(nodes, edges) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const evidencePairs = new Set(edges.map((edge) => pairKey(edge.source, edge.target)));
  const lineage = nodes.filter((node) => node.parent_id && byId.has(node.parent_id))
    .filter((node) => !evidencePairs.has(pairKey(node.parent_id, node.id)))
    .map((node) => ({ source: node.parent_id, target: node.id, polarity: "lineage" }));
  return [...lineage, ...edges];
}


function pairKey(left, right) {
  return [left, right].sort().join(":");
}


function useNewNodes(nodes) {
  const known = useRef(new Map());
  const [newIds, setNewIds] = useState(new Set());
  useEffect(() => {
    const next = new Map(nodes.map((node) => [node.id, node.life_state]));
    const admitted = nodes.filter((node) => node.life_state === "admitted" && known.current.get(node.id) === "pending").map((node) => node.id);
    known.current = next;
    if (!admitted.length) return undefined;
    setNewIds(new Set(admitted));
    const timer = setTimeout(() => setNewIds(new Set()), 1800);
    return () => clearTimeout(timer);
  }, [nodes]);
  return newIds;
}
