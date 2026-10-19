const enc = encodeURIComponent;
async function request(path, method = 'GET', body) {
  const response = await fetch(`/api/v1${path}`, {method,
    headers: body ? {'Content-Type':'application/json'} : {}, body: body ? JSON.stringify(body) : undefined});
  if(response.status===204)return null;
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : JSON.stringify(value.detail || value));
  return value;
}
export const catalog = () => request('/runtime/catalog');
export const agents = () => request('/agents');
export const saveAgent = value => request(`/agents/${enc(value.id)}`, 'PUT', value);
export const deleteAgent = id => request(`/agents/${enc(id)}`, 'DELETE');
const sessions = project => `/projects/${enc(project)}/sessions`;
export const createSession = (project, agent, content, messageId) => request(sessions(project), 'POST', {agent_id:agent,content,message_id:messageId});
export const sessionDetail = (project, session) => request(`${sessions(project)}/${enc(session)}`);
export const sendMessage = (project, session, content, messageId) => request(`${sessions(project)}/${enc(session)}/messages`, 'POST', {content, message_id:messageId});
export const turnUrl = (project, session, turn) => `/api/v1${sessions(project)}/${enc(session)}/turns/${enc(turn)}`;
export const cancelTurn = (project, session, turn) => request(`${sessions(project)}/${enc(session)}/turns/${enc(turn)}/cancel`, 'POST');

export const deleteSession = (project,session) => fetch(`/api/v1${sessions(project)}/${enc(session)}`,{method:"DELETE"}).then(async response=>{if(!response.ok)throw new Error("删除对话失败");});
