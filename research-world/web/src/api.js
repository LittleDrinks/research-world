async function decode(response) {
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = body?.detail;
    const error = new Error(typeof detail==='string'?detail:detail?.message || `请求失败（${response.status}）`);
    error.errors = detail?.errors || [];
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
export const artifactViewUrl = (projectId, artifactId) => `/projects/${enc(projectId)}/artifacts/${enc(artifactId)}`;
export const getArtifactReading = (projectId, artifactId) => fetch(artifactUrl(projectId,artifactId)+'/reading').then(decode);
export const getArtifactTemplates = projectId => fetch(`/api/v1/projects/${enc(projectId)}/artifact-templates`).then(decode);
export const captureArtifact = (projectId, body) => fetch(`/api/v1/projects/${enc(projectId)}/artifacts`,json('POST',body)).then(decode);
export const listLabels = projectId => fetch(`/api/v1/projects/${enc(projectId)}/labels`).then(decode);
export const saveLabel = (projectId,body,id) => fetch(`/api/v1/projects/${enc(projectId)}/labels${id?'/'+enc(id):''}`,json(id?'PUT':'POST',body)).then(decode);
export const removeLabel = (projectId,id) => fetch(`/api/v1/projects/${enc(projectId)}/labels/${enc(id)}`,{method:'DELETE'}).then(decode);
export const listReviewRules = projectId => fetch(`/api/v1/projects/${enc(projectId)}/review-rules`).then(decode);
export const saveReviewRule = (projectId,labelId,body) => fetch(`/api/v1/projects/${enc(projectId)}/review-rules/${enc(labelId)}`,json('PUT',body)).then(decode);
export const listRecordReviews = (projectId,recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}/reviews`).then(decode);
export const reviewAction = (projectId,id,action) => fetch(`/api/v1/projects/${enc(projectId)}/reviews/${enc(id)}/${action}`,{method:'POST'}).then(decode);
export const listChanges = (projectId,recordId) => fetch(`/api/v1/projects/${enc(projectId)}/changes${recordId?'?record_id='+enc(recordId):''}`).then(decode);
export const changeRecord = (projectId,recordId,body) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}/changes`,json('POST',body)).then(decode);
export const getRecordRevision = (projectId,recordId,revision) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}/revisions/${revision}`).then(decode);
export const getRecord = (projectId,recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}`).then(decode);
export const recordUrl = (projectId,recordId) => `/projects/${enc(projectId)}/records/${enc(recordId)}`;
export const projectMapUrl = projectId => `/projects/${enc(projectId)}/map`;
export const selectCandidates = (projectId,body) => fetch(`/api/v1/projects/${enc(projectId)}/candidate-selection`,json('POST',body)).then(decode);
export const deleteRecord = (projectId, recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}`, { method: "DELETE" }).then(decode);
export const deleteRelation = (projectId, relationId) => fetch(`/api/v1/projects/${enc(projectId)}/relations/${enc(relationId)}`, { method: "DELETE" }).then(decode);
export const listAgents = () => fetch("/api/v1/agents").then(decode);
export const recordImpact = (projectId, recordId) => fetch(`/api/v1/projects/${enc(projectId)}/records/${enc(recordId)}/impact`).then(decode);

export const getWorkspace = id => fetch(`/api/v1/projects/${enc(id)}/workspace`).then(decode);
export const startWorkspace = id => fetch(`/api/v1/projects/${enc(id)}/workspace`,{method:'POST'}).then(decode);
export const stopWorkspace = id => fetch(`/api/v1/projects/${enc(id)}/workspace/stop`,{method:'POST'}).then(decode);
export const getWorkspaces = () => fetch('/api/v1/workspaces').then(decode);
