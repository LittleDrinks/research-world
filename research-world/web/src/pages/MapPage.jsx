import { Map as MapIcon, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { deleteRecord, deleteRelation, getLocalMap } from "../api";
import { useWorld } from "../context/WorldContext";
import { GraphView } from "../graph/GraphView";
import { Inspector } from "../graph/Inspector";
import "../map.css";


const LOCAL_MAP_LIMIT = 50;
const EMPTY_MAP = { records: [], relations: [], artifacts: [] };


export function MapPage() {
  const { data, loading, setError } = useWorld();
  if (loading) return <div className="page-loading">正在载入研究世界...</div>;
  return <MapContent data={data} setError={setError} />;
}


function MapContent({ data, setError }) {
  const [params, setParams] = useSearchParams();
  const [localMap, setLocalMap] = useState(EMPTY_MAP);
  const project = data.projects.find((item) => item.id === data.active_project_id);
  const { text, recordId } = mapQuery(params, project);
  const load = useLocalMap(data.active_project_id, text, recordId, setLocalMap, setError, setParams);
  const removeRecord = useCallback((id) => removeMapItem(deleteRecord, data.active_project_id, id, text, load, setParams, setError), [data.active_project_id, text, load, setParams, setError]);
  const removeRelation = useCallback((id) => removeMapItem(deleteRelation, data.active_project_id, id, text, load, setParams, setError), [data.active_project_id, text, load, setParams, setError]);

  useEffect(() => {
    load().catch(() => {});
    const timer = window.setInterval(() => load().catch(() => {}), 1000);
    return () => window.clearInterval(timer);
  }, [load]);

  return <section className="map-page">
    <MapToolbar count={localMap.records.length} relationCount={localMap.relations.length}
      text={text} setParams={setParams} />
    <MapView localMap={localMap} selectedId={recordId} onSelect={(id) => selectRecord(setParams, id)} onDeleteRecord={removeRecord} onDeleteRelation={removeRelation} />
  </section>;
}


function mapQuery(params, project) {
  return { text: params.get("text") || project?.question || "", recordId: params.get("node") || "" };
}


function useLocalMap(projectId, text, recordId, setMap, setError, setParams) {
  return useCallback(async (requested = { text, recordId }) => {
    if (!projectId) return;
    const query = requested.recordId ? { record_id: requested.recordId, limit: LOCAL_MAP_LIMIT } : { text: requested.text, limit: LOCAL_MAP_LIMIT };
    try { setMap(normalizeLocalMap(await getLocalMap(projectId, query))); setError(""); }
    catch (error) { if (requested.recordId) setParams(text ? { text } : {}); else setError(error.message); throw error; }
  }, [projectId, text, recordId, setMap, setError, setParams]);
}


async function removeMapItem(remove, projectId, id, text, reload, setParams, setError) {
  try { await remove(projectId, id); await reload({ text, recordId: "" }); setParams(text ? { text } : {}); }
  catch (error) { setError(error.message); throw error; }
}


function selectRecord(setParams, id) {
  setParams((current) => { const next = new URLSearchParams(current); next.set("node", id); return next; });
}


function normalizeLocalMap(value) {
  return { records: value.records.map(mapRecord), relations: value.relations.map(mapRelation), artifacts: value.artifacts };
}


function mapRecord({ id, type: kind, content, artifact_ids }) {
  return { id, kind, content, artifact_ids };
}


function mapRelation({ id, source_id: source, target_id: target, type: polarity }) {
  return { id, source, target, polarity };
}


function MapToolbar({ count, relationCount, text, setParams }) {
  const [draft, setDraft] = useState(text);
  useEffect(() => setDraft(text), [text]);
  const search = (event) => {
    event.preventDefault();
    const value = draft.trim() || text;
    setParams(value ? { text: value } : {});
  };
  return <header className="map-toolbar"><div><b><MapIcon size={17} />研究地图</b>
    <span>{count} 个记录 · {relationCount} 条关系</span></div>
    <form className="map-search" onSubmit={search}>
      <input aria-label="检索局部地图" name="text" type="search" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="检索记录" />
      <button className="icon-button" type="submit" aria-label="检索" title="检索"><Search size={16} /></button>
    </form>
  </header>;
}


function MapView({ localMap, selectedId, onSelect, onDeleteRecord, onDeleteRelation }) {
  const edges = localMap.relations;
  const nodeIds = new Set(localMap.records.map((record) => record.id));
  const visibleEdges = edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  const selected = localMap.records.find((record) => record.id === selectedId) || localMap.records[0];
  return <div className="map-workspace"><div className="graph-canvas">
    <GraphView nodes={localMap.records} edges={visibleEdges} selectedId={selected?.id} onSelect={onSelect} />
  </div><Inspector node={selected} nodes={localMap.records} edges={edges} artifacts={localMap.artifacts} onSelect={onSelect} onDeleteRecord={onDeleteRecord} onDeleteRelation={onDeleteRelation} />
  </div>;
}
