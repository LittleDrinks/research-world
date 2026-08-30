import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { getBootstrap, listAgents } from "../api";

const EMPTY = { projects: [], nodes: [], edges: [], runs: [], pipelines: [], threads: [], slots: [], agents: [] };
const LAST_PROJECT_KEY = "rw.active_project";
const WorldContext = createContext(null);

function useWorldState() {
  const [data, setData] = useState(EMPTY);
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  return { data, setData, projectId, setProjectId, loading, setLoading, error, setError };
}

function useRefresh(state, desiredProject) {
  return useCallback(async (nextId = state.projectId) => {
    if (desiredProject.current && nextId && nextId !== desiredProject.current) return;
    try {
      const [result, agents] = await Promise.all([getBootstrap(nextId), listAgents()]);
      if (desiredProject.current && result.active_project_id !== desiredProject.current) {
        throw new Error("项目切换响应不匹配");
      }
      desiredProject.current = result.active_project_id || "";
      if (result.active_project_id) localStorage.setItem(LAST_PROJECT_KEY, result.active_project_id);
      state.setData({ ...EMPTY, ...result, agents });
      state.setProjectId(result.active_project_id || "");
      state.setError("");
      return result;
    } catch (error) { state.setError(error.message); throw error; }
    finally { state.setLoading(false); }
  }, [state.projectId]);
}

export function WorldProvider({ children }) {
  const state = useWorldState();
  const desiredProject = useRef("");
  const refresh = useRefresh(state, desiredProject);
  useEffect(() => { refresh(localStorage.getItem(LAST_PROJECT_KEY) || "").catch(() => {}); }, []);
  useEffect(() => {
    const timer = setInterval(() => refresh(state.projectId).catch(() => {}), 5000);
    return () => clearInterval(timer);
  }, [state.projectId, refresh]);
  const streamState = state.loading ? "syncing" : "live";
  const selectProject = useCallback(async (id) => {
    const previous = state.projectId;
    desiredProject.current = id;
    state.setLoading(true);
    try { return await refresh(id); }
    catch (error) { desiredProject.current = previous; throw error; }
  }, [refresh, state.projectId]);
  const value = useMemo(() => ({ ...state, refresh, selectProject, streamState }), [state.data, state.projectId, state.loading, state.error, streamState, refresh, selectProject]);
  return <WorldContext.Provider value={value}>{children}</WorldContext.Provider>;
}

export function useWorld() {
  const value = useContext(WorldContext);
  if (!value) throw new Error("useWorld requires WorldProvider");
  return value;
}
