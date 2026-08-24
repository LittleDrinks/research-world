import { Bot, Download, FileUp, Plus, Search } from "lucide-react";
import { IconButton, Status } from "./shared";

export function AgentRail({ state }) {
  return <aside className="arp-rail"><RailHeader state={state} /><RailSearch state={state} /><div className="arp-agent-list">
    {state.visibleAgents.map((agent) => <AgentRow key={agent.id} agent={agent} state={state} />)}
  </div><RailFooter state={state} /></aside>;
}

function RailHeader({ state }) {
  return <header><div><span>Agent Profiles</span><b>{state.agents.length}</b></div><IconButton label="新建 Agent" onClick={state.beginDraft}><Plus size={17} /></IconButton></header>;
}

function RailSearch({ state }) {
  return <label className="arp-rail-search"><Search size={14} /><input aria-label="搜索 Agent" value={state.agentQuery} onChange={(event) => state.setAgentQuery(event.target.value)} placeholder="搜索名称、Runtime、模型" /></label>;
}

function AgentRow({ agent, state }) {
  const active = agent.id === state.selectedId;
  return <button className={active ? "active" : ""} onClick={() => state.setSelectedId(agent.id)}><Bot size={16} /><span><b>{agent.name}</b><code>{agent.id}</code><small>{agent.runtime} · {agent.model}</small></span><Status value={agent.status} /></button>;
}

function RailFooter({ state }) {
  return <footer><button onClick={() => state.setNotice("Prototype：已打开 AgentSpec 文件选择器。") }><FileUp size={14} />导入</button><button onClick={() => state.setNotice("Prototype：已生成脱敏 AgentSpec 导出。") }><Download size={14} />导出</button></footer>;
}
