async function decode(response) {
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const error = new Error(body?.detail || `请求失败（${response.status}）`);
    error.code = body?.code;
    throw error;
  }
  return body;
}


const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const enc = encodeURIComponent;

export const getBootstrap = (projectId) => fetch(`/api/v1/bootstrap${projectId ? `?project_id=${enc(projectId)}` : ""}`).then(decode);
export const deleteProject = (id) => fetch(`/api/v1/projects/${enc(id)}`, {method:"DELETE"}).then(decode);
export const createProject = (body) => fetch("/api/v1/projects", json("POST", body)).then(decode);
export const projectExportUrl = (projectId) => `/api/v1/projects/${enc(projectId)}/export`;
export const getLocalMap = (projectId, query) => fetch(`/api/v1/projects/${enc(projectId)}/local-map`, json("POST", query)).then(decode);
export const artifactUrl = (projectId, artifactId, download = false) => `/api/v1/projects/${enc(projectId)}/artifacts/${enc(artifactId)}${download ? "?download=true" : ""}`;
export const deleteRecord = (projectId, recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}`, { method: "DELETE" }).then(decode);
export const deleteRelation = (projectId, relationId) => fetch(`/api/v1/projects/${enc(projectId)}/relations/${enc(relationId)}`, { method: "DELETE" }).then(decode);
export const listAgents = () => fetch("/api/v1/agents").then(decode);
export const recordImpact = (projectId, recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}/impact`).then(decode);
