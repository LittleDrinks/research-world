// THROWAWAY
import { useEffect, useState } from "react";
import { Activity, CheckCircle2, FolderKanban, ListOrdered, Maximize2, MessageSquare, Network, Send, X } from "lucide-react";
import "./style.css";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, childrenOf, taskById } from "../seed";

const STATE = {
  待审查: "#d97706", 待验证: "#0284c7", 已支持: "#059669", 已采纳: "#7c3aed", 已入图: "#0284c7", 已锁定: "#475569",
  草稿: "#94a3b8", 已配置: "#64748b", 运行: "#059669", 排队: "#d97706", 完成: "#64748b", 失败: "#dc2626", 空闲: "#94a3b8",
};
const chipStyle = (key) => ({ background: `${STATE[key] || "#64748b"}1f`, color: STATE[key] || "#64748b" });

const dirIndex = Object.fromEntries(kimiTasks.filter((t) => t.type === "direction").map((t, i) => [t.id, i]));
const dirY = (id) => 30 + dirIndex[id] * 32;
const POS = {};
kimiTasks.forEach((t) => {
  if (t.type === "question") POS[t.id] = { x: 80, y: 334 };
  else if (t.type === "direction") POS[t.id] = { x: 430, y: dirY(t.id) };
  else if (t.type === "experiment") POS[t.id] = { x: 760, y: dirY(t.parent) + 12 };
  else POS[t.id] = { x: 980, y: dirY(t.parent) - 4 };
});
const EDGES = kimiTasks.filter((t) => t.parent).map((t) => [t.parent, t.id]);

function Graph({ selectedId, onSelect, sciOf, full = false, onOpen }) {
  const r = full ? 15 : 10;
  return (
    <svg className={full ? "v09-graph full" : "v09-graph"} viewBox="0 0 1080 680" preserveAspectRatio="xMidYMid meet">
      {EDGES.map(([a, b]) => {
        const p1 = POS[a], p2 = POS[b], mx = (p1.x + p2.x) / 2;
        const on = a === selectedId || b === selectedId;
        return <path key={a + b} className={on ? "v09-edge on" : "v09-edge"} d={`M ${p1.x} ${p1.y} C ${mx} ${p1.y}, ${mx} ${p2.y}, ${p2.x} ${p2.y}`} />;
      })}
      {kimiTasks.map((t) => {
        const p = POS[t.id], sel = t.id === selectedId, left = t.type === "review";
        return (
          <g key={t.id} className={sel ? "v09-node sel" : "v09-node"} transform={`translate(${p.x},${p.y})`}
            onClick={() => onSelect(t.id)} onDoubleClick={onOpen}>
            {sel && <circle r={r + 7} className="v09-halo" />}
            <circle r={r} fill={STATE[sciOf(t)] || "#94a3b8"} stroke="#fff" strokeWidth="2" />
            {t.executionState === "运行" && <circle r={r} className="v09-pulse" />}
            <text x={left ? -(r + 7) : r + 7} y="3.5" textAnchor={left ? "end" : "start"} className="v09-nlabel">
              {full ? `${t.id} · ${t.title}` : t.id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Detail({ id, sciOf, onApprove, onSelect }) {
  const t = taskById(id);
  if (!t) return null;
  const kids = childrenOf(id), sci = sciOf(t);
  return (
    <div className="v09-detail">
      <div className="v09-dtitle"><b className="v09-mono">{t.id}</b><span>{t.title}</span><em>{t.kind}</em></div>
      <div className="v09-chips">
        <span className="v09-chip" style={chipStyle(sci)}>{sci}</span>
        <span className="v09-chip" style={chipStyle(t.authoringState)}>{t.authoringState}</span>
        <span className="v09-chip" style={chipStyle(t.executionState)}>{t.executionState}</span>
      </div>
      <p className="v09-prompt">{t.prompt}</p>
      <p className="v09-goal">目标：{t.goal}</p>
      <div className="v09-meta">
        <div><label>Agent</label><b>{t.agent}</b></div>
        <div><label>通道</label><b>{t.channel}</b></div>
        <div><label>模型</label><b className="v09-mono">{t.model}</b></div>
        <div><label>Provider</label><b>{t.provider}</b></div>
        <div><label>工作区</label><b className="v09-mono">{t.workspace}</b></div>
        <div><label>权限</label><b>{t.permission}</b></div>
      </div>
      <div className="v09-sec">验收标准</div>
      <ul className="v09-acc">{t.acceptance.map((a) => <li key={a}>{a}</li>)}</ul>
      <div className="v09-sec">工具</div>
      <div className="v09-chips">{t.tools.map((x) => <span key={x} className="v09-chip v09-mono" style={chipStyle("已配置")}>{x}</span>)}</div>
      <div className="v09-sec">谱系 · 子节点 {kids.length}</div>
      <div className="v09-chips">
        {t.parent && <button className="v09-linkchip" onClick={() => onSelect(t.parent)}>↑ {t.parent}</button>}
        {kids.map((k) => <button key={k.id} className="v09-linkchip" onClick={() => onSelect(k.id)}>↓ {k.id} {k.title}</button>)}
        {!t.parent && kids.length === 0 && <span className="v09-dim">无关联节点</span>}
      </div>
      {sci === "待审查" && (
        <button className="v09-approve" onClick={() => onApprove(t.id)}><CheckCircle2 size={14} /> 批准 · 标记为已支持</button>
      )}
    </div>
  );
}

function Chat({ log, input, onInput, onSend, onSelect }) {
  return (
    <div className="v09-chat">
      <div className="v09-msgs">
        {log.map((m, i) => (
          <div key={i} className={`v09-msg ${m.role}`}>
            <div className="v09-bubble">
              {m.role === "orchestrator" && <div className="v09-actor">Orchestrator</div>}
              <div>{m.text}</div>
              {m.nodes && <div className="v09-chips">{m.nodes.map((n) => <button key={n} className="v09-linkchip" onClick={() => onSelect(n)}>{n}</button>)}</div>}
            </div>
          </div>
        ))}
      </div>
      <div className="v09-inputrow">
        <input value={input} onChange={(e) => onInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && onSend()} placeholder="向 Orchestrator 下达指令…" />
        <button onClick={onSend} aria-label="发送"><Send size={14} /></button>
      </div>
    </div>
  );
}

function Queue({ onSelect, selectedId, full = false }) {
  const items = kimiTasks.filter((t) => t.executionState === "运行" || t.executionState === "排队" || (full && t.executionState === "失败"));
  return (
    <div className="v09-queue">
      {items.map((t) => (
        <button key={t.id} className={t.id === selectedId ? "v09-qrow sel" : "v09-qrow"} onClick={() => onSelect(t.id)}>
          <span className="v09-dot" style={{ background: STATE[t.executionState] }} />
          <b className="v09-mono">{t.id}</b>
          <span className="v09-qtitle">{t.title}</span>
          <span className="v09-dim">{t.agent} · {t.channel}</span>
          <span className="v09-chip" style={chipStyle(t.executionState)}>{t.executionState}</span>
        </button>
      ))}
    </div>
  );
}

function ActivityList({ onSelect, full = false }) {
  return (
    <div className="v09-act">
      {kimiActivity.map((a) => (
        <div key={a.id} className="v09-arow">
          <span className="v09-time v09-mono">{a.time}</span>
          <b>{a.actor}</b>
          <span className="v09-dim">{a.action}</span>
          <button className="v09-link" onClick={() => onSelect(a.target.split(" ")[0])}>{a.target}</button>
          {full && <span className="v09-dim v09-adetail">{a.detail}</span>}
          <span className="v09-chip" style={chipStyle(a.state)}>{a.state}</span>
        </div>
      ))}
    </div>
  );
}

function Projects({ activeId, onSwitch, full = false }) {
  return (
    <div className={full ? "v09-projs full" : "v09-projs"}>
      {kimiProjects.map((p) => (
        <button key={p.id} className={p.id === activeId ? "v09-proj on" : "v09-proj"} onClick={() => onSwitch(p.id)}>
          <div className="v09-pname"><b>{p.name}</b>{p.lead && <span className="v09-badge">主项目</span>}</div>
          <div className="v09-pq">{p.question}</div>
          <div className="v09-pstats"><span>{p.nodes} 节点</span><span>{p.running} 运行</span><span>{p.pending} 待办</span><span className="v09-dim">{p.updated}</span></div>
        </button>
      ))}
    </div>
  );
}

function Tile({ area, tone, title, icon, onExpand, children }) {
  return (
    <div className={`v09-tile v09-t-${tone}`} style={{ gridArea: area }}>
      <header className="v09-tile-head">
        <span className="v09-tile-title">{icon}{title}</span>
        {onExpand && <button className="v09-iconbtn" onClick={onExpand} title="展开"><Maximize2 size={13} /></button>}
      </header>
      <div className="v09-tile-body">{children}</div>
    </div>
  );
}

const FOCUS_TITLE = { graph: "研究图谱 · 全屏", detail: "节点详情 + 对话", chat: "Orchestrator 对话", queue: "执行队列", activity: "活动流", projects: "项目列表" };

export default function V09BentoDesktop() {
  const [selectedId, setSelectedId] = useState("D-001");
  const [focus, setFocus] = useState(null);
  const [projectId, setProjectId] = useState("prime-distribution");
  const [log, setLog] = useState(kimiChat);
  const [input, setInput] = useState("");
  const [overrides, setOverrides] = useState({});

  useEffect(() => {
    if (!focus) return;
    const onKey = (e) => { if (e.key === "Escape") setFocus(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focus]);

  const sciOf = (t) => overrides[t.id] || t.scienceState;
  const sel = taskById(selectedId);
  const project = kimiProjects.find((p) => p.id === projectId);
  const counts = {
    running: kimiTasks.filter((t) => t.executionState === "运行").length,
    queued: kimiTasks.filter((t) => t.executionState === "排队").length,
    failed: kimiTasks.filter((t) => t.executionState === "失败").length,
    review: kimiTasks.filter((t) => sciOf(t) === "待审查").length,
  };
  const metrics = [
    { key: "运行", n: counts.running, area: "m1", tone: "mint", to: "queue" },
    { key: "排队", n: counts.queued, area: "m2", tone: "apricot", to: "queue" },
    { key: "待审查", n: counts.review, area: "m3", tone: "sky", to: "graph" },
    { key: "失败", n: counts.failed, area: "m4", tone: "rose", to: "queue" },
  ];

  const approve = (id) => setOverrides((o) => ({ ...o, [id]: "已支持" }));
  const send = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setLog((l) => [...l, { role: "user", text }, { role: "orchestrator", text: `已收到。围绕 ${sel.id} ${sel.title} 继续编排，进展会写入活动流。`, nodes: [sel.id] }]);
  };
  const today = new Date().toLocaleDateString("zh-CN", { month: "long", day: "numeric", weekday: "long" });

  const chatProps = { log, input, onInput: setInput, onSend: send, onSelect: setSelectedId };
  const detailProps = { id: selectedId, sciOf, onApprove: approve, onSelect: setSelectedId };

  return (
    <section className="v09-root">
      <div className="v09-grid">
        <div className="v09-tile v09-t-white" style={{ gridArea: "head" }}>
          <div className="v09-headtile">
            <div>
              <div className="v09-h1">{project.name}<span>积木桌面</span></div>
              <div className="v09-hsub">{project.question} · {today} · 更新于 {project.updated}</div>
            </div>
            <div className="v09-hstate">
              <span>已选 <b className="v09-mono">{sel.id}</b> {sel.title}</span>
              <span>子节点 {childrenOf(sel.id).length}</span>
              <span>{kimiTasks.length} 节点 · {counts.running} 运行 · {counts.review} 待审查</span>
            </div>
          </div>
        </div>
        {metrics.map((m) => (
          <button key={m.key} className={`v09-tile v09-metric v09-t-${m.tone}`} style={{ gridArea: m.area }} onClick={() => setFocus(m.to)}>
            <span className="v09-mnum" style={{ color: STATE[m.key] }}>{m.n}</span>
            <span className="v09-mlabel">{m.key}</span>
          </button>
        ))}
        <Tile area="proj" tone="lav" title="项目" icon={<FolderKanban size={13} />} onExpand={() => setFocus("projects")}>
          <Projects activeId={projectId} onSwitch={setProjectId} />
        </Tile>
        <Tile area="graph" tone="white" title="研究图谱" icon={<Network size={13} />} onExpand={() => setFocus("graph")}>
          <div className="v09-graphwrap">
            <div className="v09-legend">
              {["待审查", "待验证", "已支持", "已采纳"].map((s) => <span key={s} className="v09-leg"><i style={{ background: STATE[s] }} />{s}</span>)}
            </div>
            <Graph selectedId={selectedId} onSelect={setSelectedId} sciOf={sciOf} onOpen={() => setFocus("graph")} />
          </div>
        </Tile>
        <Tile area="det" tone="white" title={`详情 · ${sel.id}`} icon={<CheckCircle2 size={13} />} onExpand={() => setFocus("detail")}>
          <Detail {...detailProps} />
        </Tile>
        <Tile area="chat" tone="white" title="Orchestrator" icon={<MessageSquare size={13} />} onExpand={() => setFocus("chat")}>
          <Chat {...chatProps} />
        </Tile>
        <Tile area="queue" tone="apricot" title={`执行队列 · ${counts.running + counts.queued}`} icon={<ListOrdered size={13} />} onExpand={() => setFocus("queue")}>
          <Queue onSelect={setSelectedId} selectedId={selectedId} />
        </Tile>
        <Tile area="act" tone="mint" title="活动流" icon={<Activity size={13} />} onExpand={() => setFocus("activity")}>
          <ActivityList onSelect={setSelectedId} />
        </Tile>
      </div>
      {focus && (
        <div className="v09-focus">
          <div className="v09-fhead">
            <b>{FOCUS_TITLE[focus]}</b>
            <span className="v09-dim">已选 <b className="v09-mono">{sel.id}</b> {sel.title} · {counts.running} 运行 / {counts.queued} 排队 / {counts.review} 待审查 · Esc 关闭</span>
            <button className="v09-iconbtn" onClick={() => setFocus(null)} aria-label="关闭"><X size={16} /></button>
          </div>
          <div className="v09-fbody">
            {focus === "graph" && (
              <div className="v09-fsplit">
                <div className="v09-panel v09-fill">
                  <div className="v09-legend">
                    {["待审查", "待验证", "已支持", "已采纳"].map((s) => <span key={s} className="v09-leg"><i style={{ background: STATE[s] }} />{s}</span>)}
                  </div>
                  <Graph full selectedId={selectedId} onSelect={setSelectedId} sciOf={sciOf} />
                </div>
                <div className="v09-fcol">
                  <div className="v09-panel v09-scroll"><Detail {...detailProps} /></div>
                  <div className="v09-panel"><Chat {...chatProps} /></div>
                </div>
              </div>
            )}
            {focus === "detail" && (
              <div className="v09-fsplit">
                <div className="v09-panel v09-scroll v09-fill"><Detail {...detailProps} /></div>
                <div className="v09-panel v09-fside"><Chat {...chatProps} /></div>
              </div>
            )}
            {focus === "chat" && <div className="v09-panel v09-chatcenter"><Chat {...chatProps} /></div>}
            {focus === "queue" && <div className="v09-panel v09-scroll v09-fill"><Queue full onSelect={setSelectedId} selectedId={selectedId} /></div>}
            {focus === "activity" && <div className="v09-panel v09-scroll v09-fill"><ActivityList full onSelect={setSelectedId} /></div>}
            {focus === "projects" && <div className="v09-panel v09-scroll v09-fill"><Projects full activeId={projectId} onSwitch={setProjectId} /></div>}
          </div>
        </div>
      )}
    </section>
  );
}
