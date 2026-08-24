async function decode(response) {
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(body?.detail || `请求失败（${response.status}）`);
  return body;
}


const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const enc = encodeURIComponent;


export const getBootstrap = (projectId) => fetch(`/api/v1/bootstrap${projectId ? `?project_id=${enc(projectId)}` : ""}`).then(decode);
export const createProject = (body) => fetch("/api/v1/projects", json("POST", body)).then(decode);
export const setProjectAuto = (projectId, auto) => fetch(`/api/v1/projects/${enc(projectId)}`, json("PATCH", { auto })).then(decode);

export const listThreads = (projectId) => fetch(`/api/v1/projects/${enc(projectId)}/threads`).then(decode);
export const createThread = (projectId, body) => fetch(`/api/v1/projects/${enc(projectId)}/threads`, json("POST", body)).then(decode);
export const getThread = (threadId) => fetch(`/api/v1/threads/${enc(threadId)}`).then(decode);
export const restartThread = (threadId) => fetch(`/api/v1/threads/${enc(threadId)}/restart`, { method: "POST" }).then(decode);
export const pinNode = (threadId, nodeId) => fetch(`/api/v1/threads/${enc(threadId)}/nodes`, json("POST", { node_id: nodeId })).then(decode);

export async function sendPrompt(threadId, message, onEvent) {
  const response = await fetch(`/api/v1/threads/${enc(threadId)}/prompts`, json("POST", { message }));
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try { detail = JSON.parse(text)?.detail || text; } catch { /* 错误体非 JSON */ }
    throw new Error(detail || `请求失败（${response.status}）`);
  }
  await readSse(response.body, onEvent);
}


async function readSse(stream, onEvent) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop();
    frames.forEach((frame) => emitFrame(frame, onEvent));
  }
}


function emitFrame(frame, onEvent) {
  const lines = frame.split("\n");
  const event = lines.find((line) => line.startsWith("event: "))?.slice(7);
  const data = lines.find((line) => line.startsWith("data: "))?.slice(6);
  if (event && data) onEvent(event, JSON.parse(data));
}

export const searchNodes = (projectId, query) => fetch("/api/v1/tools/graph-query", json("POST", { arguments: { action: "search", project_id: projectId, query } })).then(decode);
export const getNode = (nodeId) => fetch(`/api/v1/nodes/${enc(nodeId)}`).then(decode);
export const resolveAdmission = (projectId, nodeId, body) => fetch(`/api/v1/projects/${enc(projectId)}/nodes/${enc(nodeId)}/admission`, json("POST", body)).then(decode);

export const getCatalog = (projectId) => fetch(`/api/v1/runtime/catalog?project_id=${enc(projectId)}`).then(decode);
export const getSession = (sessionId) => fetch(`/api/v1/runtime/sessions/${enc(sessionId)}`).then(decode);

export const listAgents = () => fetch("/api/v1/agents").then(decode);
export const createAgent = (body, projectId) => fetch(`/api/v1/agents?project_id=${enc(projectId)}`, json("POST", body)).then(decode);
export const draftAgent = (projectId, presetId) => fetch(`/api/v1/projects/${enc(projectId)}/agent-drafts`, json("POST", { preset_id: presetId })).then(decode);
export const saveAgent = (agentId, projectId, body) => fetch(`/api/v1/agents/${enc(agentId)}?project_id=${enc(projectId)}`, json("PUT", body)).then(decode);

export const listRuns = (projectId) => fetch(`/api/v1/projects/${enc(projectId)}/runs`).then(decode);
export const startRun = (projectId, body) => fetch(`/api/v1/projects/${enc(projectId)}/runs`, json("POST", body)).then(decode);
export const confirmRun = (runId) => fetch(`/api/v1/runs/${enc(runId)}/confirm`, { method: "POST" }).then(decode);
export const resolveRun = (runId, body) => fetch(`/api/v1/runs/${enc(runId)}/resolve`, json("POST", body)).then(decode);
