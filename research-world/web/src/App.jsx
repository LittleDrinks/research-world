import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { useWorld } from "./context/WorldContext";


const MapPage = lazy(() => import("./pages/MapPage").then((value) => ({ default: value.MapPage })));
const ChatPage = lazy(() => import("./pages/ChatPage").then((value) => ({ default: value.ChatPage })));
const TracesPage = lazy(() => import("./pages/TracesPage").then((value) => ({ default: value.TracesPage })));
const AgentsPage = lazy(() => import("./pages/AgentsPage").then((value) => ({ default: value.AgentsPage })));
const SettingsPage = lazy(() => import("./pages/SettingsPage").then((value) => ({ default: value.SettingsPage })));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then((value) => ({ default: value.ProjectsPage })));
const AgentRuntimePrototype = lazy(() => import("./prototype/agent-runtime/AgentRuntimePrototype").then((value) => ({ default: value.AgentRuntimePrototype })));


function View({ component: Component }) {
  return <Suspense fallback={<div className="page-loading">正在载入...</div>}><Component /></Suspense>;
}


function ProjectRequired() {
  const { loading, projectId } = useWorld();
  if (loading) return <div className="page-loading">正在载入项目...</div>;
  return projectId ? <AppShell /> : <Navigate to="/projects" replace />;
}


export function App() {
  return <Routes>
    <Route index element={<Navigate to="/projects" replace />} />
    <Route path="projects" element={<View component={ProjectsPage} />} />
    <Route path="prototype/agent-runtime" element={<View component={AgentRuntimePrototype} />} />
    <Route element={<ProjectRequired />}>
      <Route path="map" element={<View component={MapPage} />} />
      <Route path="chat" element={<View component={ChatPage} />} />
      <Route path="chat/:threadId" element={<View component={ChatPage} />} />
      <Route path="traces" element={<View component={TracesPage} />} />
      <Route path="traces/:runId" element={<View component={TracesPage} />} />
      <Route path="agents" element={<View component={AgentsPage} />} />
      <Route path="agents/:agentId" element={<View component={AgentsPage} />} />
      <Route path="settings" element={<View component={SettingsPage} />} />
    </Route>
    <Route path="*" element={<Navigate to="/projects" replace />} />
  </Routes>;
}
