import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { deleteProject, getBootstrap, listAgents } from "../api";

const EMPTY = { sessions: [], projects: [], nodes: [], edges: [], runs: [], pipelines: [], threads: [], slots: [], agents: [] };
const LAST_PROJECT_KEY = "rw.active_project";
const WorldContext = createContext(null);

function useWorldState() {
  const [data, setData] = useState(EMPTY);
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  return { data, setData, projectId, setProjectId, loading, setLoading, error, setError };
}

function useRefresh(state, desiredProject, requests) {
  return useCallback(async (nextId = state.projectId) => {
    if (desiredProject.current && nextId && nextId !== desiredProject.current) return;
    const request=++requests.current;
    try {
      const [result, agents] = await Promise.all([getBootstrap(nextId), listAgents()]);
      if(request!==requests.current)return;
      if (desiredProject.current && result.active_project_id !== desiredProject.current) {
        throw new Error("项目切换响应不匹配");
      }
      desiredProject.current = result.active_project_id || "";
      saveSelection(result.active_project_id);
      state.setData({ ...EMPTY, ...result, agents });
      state.setProjectId(result.active_project_id || "");
      state.setError(""); return result;
    } catch (error) { if(request===requests.current)state.setError(error.message); throw error; }
    finally { state.setLoading(false); }
  }, [state.projectId]);
}

export function WorldProvider({ children }) {
  const state = useWorldState();
  const desiredProject = useRef("");
  const requests=useRef(0);
  const refresh = useRefresh(state, desiredProject, requests);
  const removeProject=useProjectDeletion(state,desiredProject,refresh);
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
  const value = useMemo(() => ({ ...state, refresh, selectProject, removeProject, streamState }), [state.data, state.projectId, state.loading, state.error, streamState, refresh, selectProject, removeProject]);
  return <WorldContext.Provider value={value}>{children}</WorldContext.Provider>;
}

export function useWorld() {
  const value = useContext(WorldContext);
  if (!value) throw new Error("useWorld requires WorldProvider");
  return value;
}


function useProjectDeletion(state,desiredProject,refresh){
  return useCallback(async(id)=>{
    await deleteProject(id);
    if(desiredProject.current===id){
      desiredProject.current="";
      localStorage.removeItem(LAST_PROJECT_KEY);
      state.setProjectId("");
    }
    state.setData(data=>({...data,projects:data.projects.filter(p=>p.id!==id)}));
    await refresh(desiredProject.current);
  },[refresh]);
}

function saveSelection(id){
  if(id)localStorage.setItem(LAST_PROJECT_KEY,id);
  else localStorage.removeItem(LAST_PROJECT_KEY);
}
