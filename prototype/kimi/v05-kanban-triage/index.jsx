// THROWAWAY PROTOTYPE
import { useEffect, useMemo, useState } from "react";
import { LayoutGrid, List, Network, Inbox, Search, X, ChevronLeft, ChevronRight, ArrowRight, Check, Lock, Folder, Command, CircleDot } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, kimiMetrics, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const COLUMNS = [
  { id: "待审查", color: "#d97706", hint: "新提交,等待分诊" },
  { id: "待验证", color: "#0969da", hint: "已入图,证据不足" },
  { id: "已支持", color: "#1a7f37", hint: "证据链完整" },
  { id: "已锁定", color: "#8250df", hint: "分流终点,冻结" },
];
const TYPE_COLOR = { question: "#1f2328", direction: "#0969da", experiment: "#0e7490", review: "#8250df" };
const EXEC_COLOR = { 运行: "#1a7f37", 排队: "#b45309", 完成: "#6e7781", 失败: "#cf222e", 空闲: "#9fa4a9" };
function initialCol(t) {
  if (t.scienceState === "待审查") return "待审查";
  if (t.scienceState === "待验证") return "待验证";
  if (t.scienceState === "已支持") return "已支持";
  return "已锁定";
}

function Dot({ color, pulse }) {
  return <span className={`v05-dot${pulse ? " v05-dot-pulse" : ""}`} style={{ background: color }} />;
}

function NodeChip({ id, onOpen }) {
  const t = taskById(id);
  if (!t) return <span className="v05-chip">{id}</span>;
  return (
    <button className="v05-chip v05-chip-link" onClick={() => onOpen(id)}>
      <Dot color={TYPE_COLOR[t.type]} /> {t.id} {t.title}
    </button>
  );
}

export default function KanbanTriage() {
  const [view, setView] = useState("board");
  const [projectId, setProjectId] = useState("prime-distribution");
  const [selectedId, setSelectedId] = useState(null);
  const [moves, setMoves] = useState({});
  const [dragId, setDragId] = useState(null);
  const [dropCol, setDropCol] = useState(null);
  const [cmdk, setCmdk] = useState(false);
  const [readIds, setReadIds] = useState(() => new Set());
  const [chatExtra, setChatExtra] = useState([]);
  const [draft, setDraft] = useState("");

  const colOf = (t) => moves[t.id] ?? initialCol(t);
  const byCol = useMemo(() => {
    const map = Object.fromEntries(COLUMNS.map((c) => [c.id, []]));
    for (const t of kimiTasks) map[colOf(t)].push(t);
    return map;
  }, [moves]);
  const selected = selectedId ? taskById(selectedId) : null;
  const project = kimiProjects.find((p) => p.id === projectId);
  const unread = kimiActivity.filter((a) => !readIds.has(a.id)).length;

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setCmdk((v) => !v); }
      if (e.key === "Escape") { setCmdk(false); setSelectedId(null); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const openNode = (id) => { setSelectedId(id); setCmdk(false); };
  const moveTo = (id, col) => setMoves((m) => ({ ...m, [id]: col }));
  const sendChat = () => {
    if (!draft.trim()) return;
    setChatExtra((c) => [...c,
      { role: "user", text: draft.trim() },
      { role: "orchestrator", text: `已记录,关联 ${selectedId ?? project.question}。分诊变更会同步到看板。`, nodes: selectedId ? [selectedId] : [] },
    ]);
    setDraft("");
  };

  const TABS = [
    { id: "board", name: "看板", icon: LayoutGrid, badge: kimiMetrics.total },
    { id: "list", name: "列表", icon: List },
    { id: "graph", name: "图谱", icon: Network },
    { id: "inbox", name: "收件箱", icon: Inbox, badge: unread, accent: unread > 0 },
  ];

  return (
    <section className="v05-root">
      <header className="v05-topbar">
        <button className={`v05-project${view === "projects" ? " on" : ""}`} onClick={() => setView("projects")}>
          <Folder size={14} />
          <span className="v05-project-name">{project.name}</span>
          <span className="v05-project-q">{project.question}</span>
        </button>
        <nav className="v05-tabs">
          {TABS.map((t) => (
            <button key={t.id} className={`v05-tab${view === t.id ? " on" : ""}`} onClick={() => setView(t.id)}>
              <t.icon size={13} /> {t.name}
              {t.badge != null && <span className={`v05-badge${t.accent ? " hot" : ""}`}>{t.badge}</span>}
            </button>
          ))}
        </nav>
        <div className="v05-topstats">
          <span><Dot color={EXEC_COLOR.运行} pulse /> 运行 {kimiMetrics.running}</span>
          <span><Dot color={EXEC_COLOR.排队} /> 排队 {kimiMetrics.queued}</span>
          <span><Dot color={EXEC_COLOR.失败} /> 失败 {kimiMetrics.failed}</span>
          {Object.keys(moves).length > 0 && <span className="v05-moved"><ArrowRight size={11} /> 已分流 {Object.keys(moves).length}</span>}
        </div>
        <div className="v05-current">
          {selected ? <><Dot color={TYPE_COLOR[selected.type]} /> 选中 {selected.id} · {colOf(selected)}</> : "未选中节点"}
        </div>
        <button className="v05-cmdk-btn" onClick={() => setCmdk(true)}>
          <Search size={13} /> 搜索或跳转 <kbd><Command size={10} />K</kbd>
        </button>
      </header>

      {view === "board" && (
        <div className="v05-board">
          {COLUMNS.map((col, ci) => (
            <div key={col.id}
              className={`v05-col${dropCol === col.id ? " drop" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDropCol(col.id); }}
              onDragLeave={() => setDropCol((c) => (c === col.id ? null : c))}
              onDrop={(e) => { e.preventDefault(); if (dragId) moveTo(dragId, col.id); setDragId(null); setDropCol(null); }}>
              <div className="v05-colhead">
                <Dot color={col.color} />
                <b>{col.id}</b>
                <span className="v05-count">{byCol[col.id].length}</span>
                <span className="v05-colhint">{col.hint}</span>
              </div>
              <div className="v05-colbody">
                {byCol[col.id].map((t) => (
                  <div key={t.id}
                    className={`v05-card${dragId === t.id ? " dragging" : ""}${selectedId === t.id ? " sel" : ""}`}
                    draggable
                    onDragStart={(e) => { setDragId(t.id); e.dataTransfer.effectAllowed = "move"; }}
                    onDragEnd={() => { setDragId(null); setDropCol(null); }}
                    onClick={() => setSelectedId(t.id)}>
                    <div className="v05-card-top">
                      <span className="v05-id" style={{ color: TYPE_COLOR[t.type] }}><Dot color={TYPE_COLOR[t.type]} />{t.id}</span>
                      <span className="v05-exec"><Dot color={EXEC_COLOR[t.executionState]} pulse={t.executionState === "运行"} />{t.executionState}</span>
                    </div>
                    <div className="v05-card-title">{t.title}</div>
                    <div className="v05-card-meta">
                      <span className="v05-chip">{t.agent}</span>
                      <span className="v05-chip">{t.kind}</span>
                      {t.authoringState === "已锁定" && <span className="v05-chip v05-lock"><Lock size={10} />已锁定</span>}
                      <span className="v05-card-arrows">
                        {ci > 0 && <button title={`移到 ${COLUMNS[ci - 1].id}`} onClick={(e) => { e.stopPropagation(); moveTo(t.id, COLUMNS[ci - 1].id); }}><ChevronLeft size={12} /></button>}
                        {ci < COLUMNS.length - 1 && <button title={`移到 ${COLUMNS[ci + 1].id}`} onClick={(e) => { e.stopPropagation(); moveTo(t.id, COLUMNS[ci + 1].id); }}><ChevronRight size={12} /></button>}
                      </span>
                    </div>
                  </div>
                ))}
                {byCol[col.id].length === 0 && <div className="v05-empty">拖拽卡片到此列</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {view === "list" && (
        <div className="v05-listwrap">
          <table className="v05-list">
            <thead>
              <tr><th>状态</th><th>编号</th><th>类型</th><th>标题</th><th>分组</th><th>Agent</th><th>执行</th><th>撰写</th><th></th></tr>
            </thead>
            <tbody>
              {[...kimiTasks].sort((a, b) => COLUMNS.findIndex((c) => c.id === colOf(a)) - COLUMNS.findIndex((c) => c.id === colOf(b)) || a.id.localeCompare(b.id)).map((t) => {
                const ci = COLUMNS.findIndex((c) => c.id === colOf(t));
                return (
                  <tr key={t.id} className={selectedId === t.id ? "sel" : ""} onClick={() => setSelectedId(t.id)}>
                    <td><Dot color={COLUMNS[ci].color} /> {colOf(t)}</td>
                    <td className="v05-mono" style={{ color: TYPE_COLOR[t.type] }}>{t.id}</td>
                    <td>{t.kind}</td>
                    <td className="v05-ltitle">{t.title}</td>
                    <td>{t.group}</td>
                    <td>{t.agent}</td>
                    <td><Dot color={EXEC_COLOR[t.executionState]} pulse={t.executionState === "运行"} /> {t.executionState}</td>
                    <td>{t.authoringState}</td>
                    <td>{ci < COLUMNS.length - 1 && (
                      <button className="v05-next" onClick={(e) => { e.stopPropagation(); moveTo(t.id, COLUMNS[ci + 1].id); }}>
                        {COLUMNS[ci + 1].id} <ArrowRight size={11} />
                      </button>)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {view === "graph" && <GraphBoard selectedId={selectedId} colOf={colOf} onOpen={openNode} />}
      {view === "inbox" && (
        <div className="v05-inbox">
          <div className="v05-inbox-head">
            <b>活动收件箱</b>
            <span className="v05-count">{unread} 条未读</span>
            <button className="v05-next" onClick={() => setReadIds(new Set(kimiActivity.map((a) => a.id)))}><Check size={11} /> 全部已读</button>
          </div>
          {kimiActivity.map((a) => {
            const nodeId = a.target.split(" ")[0];
            const node = taskById(nodeId);
            const read = readIds.has(a.id);
            return (
              <div key={a.id} className={`v05-msg${read ? " read" : ""}`} onClick={() => { setReadIds((s) => new Set(s).add(a.id)); if (node) openNode(nodeId); }}>
                <span className="v05-unread-dot" />
                <span className="v05-mono v05-time">{a.time}</span>
                <span className="v05-chip">{a.actor}</span>
                <span className="v05-action">{a.action}</span>
                <span className="v05-target">{a.target}</span>
                <span className="v05-chip" style={{ color: EXEC_COLOR[a.state] ?? "#57606a" }}><CircleDot size={10} />{a.state}</span>
                <span className="v05-detail">{a.detail}</span>
              </div>
            );
          })}
        </div>
      )}

      {view === "projects" && (
        <div className="v05-projects">
          <div className="v05-projects-title">项目列表 <span className="v05-count">{kimiProjects.length}</span></div>
          {kimiProjects.map((p) => (
            <button key={p.id} className={`v05-pcard${p.id === projectId ? " on" : ""}`} onClick={() => { setProjectId(p.id); setView("board"); }}>
              <div className="v05-pcard-head">
                <b>{p.name}</b>
                {p.id === projectId && <span className="v05-badge hot">当前项目</span>}
                {p.lead && <span className="v05-badge">LEAD</span>}
              </div>
              <div className="v05-pcard-q">{p.question}</div>
              <div className="v05-pcard-meta">
                <span><Network size={11} /> {p.nodes} 节点</span>
                <span><Dot color={EXEC_COLOR.运行} pulse /> {p.running} 运行</span>
                <span><Dot color={EXEC_COLOR.排队} /> {p.pending} 待办</span>
                <span>更新于 {p.updated}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <aside className="v05-drawer">
          <div className="v05-drawer-head">
            <span className="v05-id" style={{ color: TYPE_COLOR[selected.type] }}><Dot color={TYPE_COLOR[selected.type]} />{selected.id}</span>
            <span className="v05-chip">{selected.kind}</span>
            <span className="v05-chip">{selected.group}</span>
            <button className="v05-close" onClick={() => setSelectedId(null)}><X size={14} /></button>
          </div>
          <div className="v05-drawer-body">
            <h2 className="v05-dtitle">{selected.title}</h2>
            <p className="v05-dprompt">{selected.prompt}</p>
            <div className="v05-triage">
              {COLUMNS.map((c) => (
                <button key={c.id} className={`v05-triage-btn${colOf(selected) === c.id ? " on" : ""}`}
                  style={colOf(selected) === c.id ? { borderColor: c.color, color: c.color } : undefined}
                  onClick={() => moveTo(selected.id, c.id)}>
                  <Dot color={c.color} />{c.id}
                </button>
              ))}
            </div>
            <dl className="v05-fields">
              <div><dt>执行状态</dt><dd><Dot color={EXEC_COLOR[selected.executionState]} pulse={selected.executionState === "运行"} /> {selected.executionState} · {selected.channel}</dd></div>
              <div><dt>撰写状态</dt><dd>{selected.authoringState}</dd></div>
              <div><dt>Agent</dt><dd>{selected.agent}</dd></div>
              <div><dt>模型</dt><dd className="v05-mono">{selected.model} · {selected.provider}</dd></div>
              <div><dt>工作区</dt><dd className="v05-mono">{selected.workspace}</dd></div>
              <div><dt>权限</dt><dd>{selected.permission}</dd></div>
              <div><dt>目标</dt><dd>{selected.goal}</dd></div>
            </dl>
            <div className="v05-sec">验收标准</div>
            <ul className="v05-accept">
              {selected.acceptance.map((a) => <li key={a}><Check size={11} /> {a}</li>)}
            </ul>
            <div className="v05-sec">工具</div>
            <div className="v05-tools">{selected.tools.map((t) => <span key={t} className="v05-chip v05-mono">{t}</span>)}</div>
            <div className="v05-sec">图谱位置</div>
            <div className="v05-rel">
              {selected.parent && <NodeChip id={selected.parent} onOpen={openNode} />}
              {childrenOf(selected.id).map((c) => <NodeChip key={c.id} id={c.id} onOpen={openNode} />)}
              {!selected.parent && childrenOf(selected.id).length === 0 && <span className="v05-detail">无关联节点</span>}
            </div>
            <div className="v05-sec">对话 · Orchestrator</div>
            <div className="v05-chat">
              {[...kimiChat, ...chatExtra].map((m, i) => (
                <div key={i} className={`v05-bubble ${m.role}`}>
                  <span className="v05-bubble-role">{m.role === "user" ? "我" : "Orchestrator"}</span>
                  <p>{m.text}</p>
                  {m.nodes && <div className="v05-bubble-nodes">{m.nodes.map((n) => <NodeChip key={n} id={n} onOpen={openNode} />)}</div>}
                </div>
              ))}
            </div>
          </div>
          <div className="v05-composer">
            <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendChat()} placeholder="回复 Orchestrator…" />
            <button onClick={sendChat}><ArrowRight size={13} /></button>
          </div>
        </aside>
      )}

      {cmdk && <CmdK colOf={colOf} onOpen={openNode} goView={(v) => { setView(v); setCmdk(false); }} close={() => setCmdk(false)} />}
    </section>
  );
}

function CmdK({ colOf, onOpen, goView, close }) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const q = query.trim().toLowerCase();
  const nodeHits = kimiTasks.filter((t) => !q || t.id.toLowerCase().includes(q) || t.title.includes(q) || t.agent.toLowerCase().includes(q) || t.group.includes(q)).slice(0, 7);
  const views = [
    { id: "board", name: "看板" }, { id: "list", name: "列表" }, { id: "graph", name: "图谱" },
    { id: "inbox", name: "收件箱" }, { id: "projects", name: "项目列表" },
  ];
  const items = [
    ...nodeHits.map((t) => ({ key: t.id, run: () => onOpen(t.id), node: t })),
    ...views.map((v) => ({ key: `go-${v.id}`, run: () => goView(v.id), view: v })),
  ];
  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setCursor((c) => Math.min(c + 1, items.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setCursor((c) => Math.max(c - 1, 0)); }
    if (e.key === "Enter" && items[cursor]) items[cursor].run();
    if (e.key === "Escape") close();
  };
  return (
    <div className="v05-cmdk-overlay" onClick={close}>
      <div className="v05-cmdk" onClick={(e) => e.stopPropagation()}>
        <div className="v05-cmdk-input">
          <Search size={14} />
          <input autoFocus value={query} onChange={(e) => { setQuery(e.target.value); setCursor(0); }} onKeyDown={onKey} placeholder="搜索节点、Agent、分组,或跳转视图…" />
          <kbd>ESC</kbd>
        </div>
        <div className="v05-cmdk-list">
          {items.map((it, i) => it.node ? (
            <button key={it.key} className={`v05-cmdk-item${i === cursor ? " on" : ""}`} onMouseEnter={() => setCursor(i)} onClick={it.run}>
              <Dot color={TYPE_COLOR[it.node.type]} />
              <span className="v05-mono">{it.node.id}</span>
              <span className="v05-cmdk-title">{it.node.title}</span>
              <span className="v05-cmdk-hint">{colOf(it.node)} · {it.node.agent}</span>
            </button>
          ) : (
            <button key={it.key} className={`v05-cmdk-item${i === cursor ? " on" : ""}`} onMouseEnter={() => setCursor(i)} onClick={it.run}>
              <ArrowRight size={12} />
              <span className="v05-cmdk-title">跳转到{it.view.name}</span>
              <span className="v05-cmdk-hint">视图</span>
            </button>
          ))}
          {items.length === 0 && <div className="v05-empty">无匹配结果</div>}
        </div>
      </div>
    </div>
  );
}

function GraphBoard({ selectedId, colOf, onOpen }) {
  const dirs = kimiTasks.filter((t) => t.type === "direction")
    .sort((a, b) => PROTOTYPE_GROUPS.indexOf(a.group) - PROTOTYPE_GROUPS.indexOf(b.group) || a.id.localeCompare(b.id));
  const rowH = 58, top = 36, dx = 300, dw = 216, cx = 640, cw = 168, qx = 20, qw = 160;
  const qY = top + (dirs.length * rowH) / 2 - 20;
  const pos = {};
  dirs.forEach((d, i) => {
    pos[d.id] = { x: dx, y: top + i * rowH };
    childrenOf(d.id).forEach((c, ci) => { pos[c.id] = { x: cx + ci * (cw + 12), y: top + i * rowH }; });
  });
  const q = kimiTasks.find((t) => t.type === "question");
  pos[q.id] = { x: qx, y: qY };
  const H = top * 2 + dirs.length * rowH, W = cx + 2 * (cw + 12) + 10;
  const colColor = (id) => COLUMNS.find((c) => c.id === colOf(taskById(id))).color;
  return (
    <div className="v05-graphwrap">
      <svg className="v05-graph" width={W} height={H}>
        {dirs.map((d) => (
          <path key={`q-${d.id}`} d={`M ${qx + qw} ${qY + 20} C ${dx - 90} ${qY + 20}, ${dx - 60} ${pos[d.id].y + 20}, ${dx} ${pos[d.id].y + 20}`}
            fill="none" stroke={d.executionState === "运行" ? "#1a7f37" : "#d0d7de"} strokeWidth={d.executionState === "运行" ? 1.6 : 1} />
        ))}
        {dirs.flatMap((d) => childrenOf(d.id).map((c) => (
          <path key={`${d.id}-${c.id}`} d={`M ${dx + dw} ${pos[d.id].y + 20} L ${pos[c.id].x} ${pos[c.id].y + 20}`}
            fill="none" stroke="#d0d7de" strokeWidth="1" />
        )))}
        {kimiTasks.map((t) => {
          const p = pos[t.id], w = t.type === "question" ? qw : t.type === "direction" ? dw : cw;
          return (
            <g key={t.id} className={`v05-gnode${selectedId === t.id ? " sel" : ""}`} onClick={() => onOpen(t.id)}>
              <rect x={p.x} y={p.y} width={w} height={40} rx={8}
                fill="#fff" stroke={selectedId === t.id ? "#5e6ad2" : colColor(t.id)} strokeWidth={selectedId === t.id ? 2 : 1} />
              <rect x={p.x} y={p.y} width={4} height={40} rx={2} fill={TYPE_COLOR[t.type]} />
              <text x={p.x + 12} y={p.y + 16} className="v05-gid" fill={TYPE_COLOR[t.type]}>{t.id} · {t.kind}</text>
              <text x={p.x + 12} y={p.y + 32} className="v05-gtitle">{t.title.slice(0, t.type === "direction" ? 13 : 9)}{t.title.length > (t.type === "direction" ? 13 : 9) ? "…" : ""}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
