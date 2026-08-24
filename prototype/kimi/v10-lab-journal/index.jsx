// THROWAWAY PROTOTYPE
import { useState } from "react";
import { BookOpen, CalendarDays, Map as MapIcon, PenLine, Stamp } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, kimiMetrics, taskById } from "../seed";
import "./style.css";

const WEEK = [15, 16, 17, 18, 19, 20, 21];
const WDAY = { 15: "周六", 16: "周日", 17: "周一", 18: "周二", 19: "周三", 20: "周四", 21: "周五" };
const SCI = { 待审查: "sci-rev", 待验证: "sci-ver", 已支持: "sci-sup", 已采纳: "sci-acc" };
const EXE = { 运行: "exe-run", 排队: "exe-que", 完成: "exe-done", 失败: "exe-fail", 空闲: "exe-idle" };
const AUTH = { 草稿: "auth-draft", 已配置: "auth-conf", 已锁定: "auth-lock" };
const DIRECTIONS = kimiTasks.filter((t) => t.type === "direction");

function actionOf(t) {
  if (t.type === "question") return "立项，研究问题入图";
  if (t.executionState === "失败") return "执行失败，保留完整 trace";
  if (t.scienceState === "待审查") return "提交审查，等待双审";
  if (t.scienceState === "已支持") return "证据链闭合，标记已支持";
  if (t.authoringState === "已锁定") return "复核通过，配置锁定";
  if (t.executionState === "完成") return "运行完成，产出归档";
  if (t.executionState === "排队") return "排入执行队列";
  if (t.executionState === "运行") return "启动运行";
  return "起草草稿";
}

const ENTRIES = [
  ...kimiTasks.map((t, i) => ({
    id: `J-${t.id}`,
    day: 15 + (i % 6),
    time: `${String(9 + ((i * 7) % 9)).padStart(2, "0")}:${String((i * 13) % 60).padStart(2, "0")}`,
    actor: t.agent,
    action: actionOf(t),
    note: t.prompt,
    node: t,
  })),
  ...kimiActivity.map((a) => ({
    id: `T-${a.id}`,
    day: 21,
    time: a.time,
    actor: a.actor,
    action: a.action,
    state: a.state,
    note: a.detail,
    node: taskById(a.target.split(" ")[0]),
  })),
].sort((a, b) => a.day - b.day || a.time.localeCompare(b.time));

const DAY_COUNT = ENTRIES.reduce((m, e) => { m[e.day] = (m[e.day] || 0) + 1; return m; }, {});

const CAL_CELLS = (() => {
  const cells = [];
  for (let i = 0; i < 5; i += 1) cells.push(null);
  for (let d = 1; d <= 31; d += 1) cells.push(d);
  return cells;
})();

function seedNotes() {
  const notes = {};
  kimiChat.forEach((m, i) => {
    const who = m.role === "user" ? "我" : "Orchestrator";
    const time = `08:${String(36 + i * 7).padStart(2, "0")}`;
    (m.nodes || ["Q-001"]).forEach((id) => {
      (notes[id] = notes[id] || []).push({ who, text: m.text, time });
    });
  });
  return notes;
}

const NODE_W = { question: 150, direction: 190, experiment: 170, review: 160 };
const NODE_H = 40;
const MAP_W = 980;
const MAP_H = 1150;

function mapPos(t) {
  if (t.type === "question") return { x: 30, y: 40 + 9.5 * 54 };
  if (t.type === "direction") return { x: 250, y: 40 + DIRECTIONS.findIndex((d) => d.id === t.id) * 54 };
  const pi = DIRECTIONS.findIndex((d) => d.id === t.parent);
  return { x: t.type === "experiment" ? 520 : 780, y: 40 + pi * 54 };
}

const EDGES = kimiTasks.filter((t) => t.parent).map((t) => {
  const p = taskById(t.parent);
  const a = mapPos(p);
  const b = mapPos(t);
  const x1 = a.x + NODE_W[p.type];
  const y1 = a.y + NODE_H / 2;
  const y2 = b.y + NODE_H / 2;
  const mx = (x1 + b.x) / 2;
  return { id: `${p.id}-${t.id}`, d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${b.x} ${y2}` };
});

export default function V10LabJournal() {
  const [view, setView] = useState("journal");
  const [day, setDay] = useState(null);
  const [sel, setSel] = useState("D-014");
  const [open, setOpen] = useState(null);
  const [stamps, setStamps] = useState(() => new Set(["D-008"]));
  const [notes, setNotes] = useState(seedNotes);
  const [draft, setDraft] = useState("");
  const [project, setProject] = useState("prime-distribution");

  const selNode = taskById(sel);
  const activeProject = kimiProjects.find((p) => p.id === project) || kimiProjects[0];
  const pending = kimiTasks.filter((t) => t.scienceState === "待审查");
  const queue = kimiTasks.filter((t) => t.executionState === "运行" || t.executionState === "排队");
  const failed = kimiTasks.filter((t) => t.executionState === "失败");

  function focusNode(id) {
    setSel(id);
    const entry = ENTRIES.find((e) => e.node && e.node.id === id);
    if (entry) {
      setView("journal");
      setDay(entry.day);
      setOpen(entry.id);
    }
  }

  function toggleStamp(id) {
    setStamps((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function addNote(id) {
    const text = draft.trim();
    if (!text) return;
    setNotes((n) => ({ ...n, [id]: [...(n[id] || []), { who: "我", text, time: "刚刚" }] }));
    setDraft("");
  }

  const renderNodeCard = (node) => (
    <div className="v10-node">
      <span className="v10-nid">{node.id}</span>
      <span className="v10-ntitle">{node.title}</span>
      <span className="v10-nkind">{node.kind}</span>
      <span className={`v10-chip ${SCI[node.scienceState] || ""}`}>{node.scienceState}</span>
      <span className={`v10-chip ${EXE[node.executionState] || ""}`}>{node.executionState}</span>
      <span className="v10-chip">{node.authoringState}</span>
      {stamps.has(node.id) && <span className="v10-stamp">APPROVED<i>08 · 21</i></span>}
    </div>
  );

  const renderDetail = (node) => (
    <div className="v10-detail" onClick={(e) => e.stopPropagation()}>
      <p className="v10-prompt">{node.prompt}</p>
      <div className="v10-meta">
        <span>负责 {node.agent}</span>
        <span>通道 {node.channel}</span>
        <span>模型 {node.model}</span>
        <span>{node.provider}</span>
        <span>工作区 {node.workspace}</span>
        <span>权限 {node.permission}</span>
      </div>
      <div className="v10-accept">
        {node.acceptance.map((a) => <span key={a}>☐ {a}</span>)}
      </div>
      <div className="v10-tools">
        {node.tools.map((t) => <code key={t}>{t}</code>)}
      </div>
      <p className="v10-goal">目标：{node.goal}</p>
      <div className="v10-thread">
        <h4><PenLine size={13} /> 批注 {(notes[node.id] || []).length}</h4>
        {(notes[node.id] || []).map((n, i) => (
          <div key={i} className={`v10-note-line ${n.who === "我" ? "mine" : ""}`}>
            <b>{n.who}</b><span className="v10-note-time">{n.time}</span>
            <p>{n.text}</p>
          </div>
        ))}
        <div className="v10-note-form">
          <input
            value={draft}
            placeholder="写一条批注…"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") addNote(node.id); }}
          />
          <button onClick={() => addNote(node.id)}>记下</button>
        </div>
      </div>
      <div className="v10-detail-actions">
        <button className={`v10-approve ${stamps.has(node.id) ? "on" : ""}`} onClick={() => toggleStamp(node.id)}>
          <Stamp size={13} /> {stamps.has(node.id) ? "撤销批准" : "批准"}
        </button>
        <button onClick={() => focusNode(node.id)}>在日志中打开</button>
      </div>
    </div>
  );

  const stickItem = (t) => (
    <li key={t.id}>
      <button className="v10-stick-item" onClick={() => focusNode(t.id)}>
        <i className={`v10-dot ${EXE[t.executionState] || ""}`} />
        <b>{t.id}</b>
        <span>{t.title}</span>
      </button>
    </li>
  );

  return (
    <section className="v10-root">
      <aside className="v10-side">
        <div className="v10-brand">
          <h1 className="v10-hand">实验日志</h1>
          <p>LAB JOURNAL · VOL.07 · 2026.08.15—08.21</p>
        </div>
        <nav className="v10-nav">
          <button className={view === "cover" ? "on" : ""} onClick={() => setView("cover")}><BookOpen size={14} /> 封面 · 项目</button>
          <button className={view === "journal" ? "on" : ""} onClick={() => setView("journal")}><PenLine size={14} /> 日志 · 本周</button>
          <button className={view === "map" ? "on" : ""} onClick={() => setView("map")}><MapIcon size={14} /> 卷首总图</button>
        </nav>
        <div className="v10-cal">
          <h4><CalendarDays size={13} /> 2026 年 8 月</h4>
          <div className="v10-cal-grid">
            {["一", "二", "三", "四", "五", "六", "日"].map((w) => <span key={w} className="v10-cal-w">{w}</span>)}
            {CAL_CELLS.map((d, i) => (d === null ? <span key={`b${i}`} /> : (
              <button
                key={d}
                className={`v10-cal-d ${WEEK.includes(d) ? "has" : ""} ${d === 21 ? "today" : ""} ${day === d ? "on" : ""}`}
                onClick={() => { if (WEEK.includes(d)) { setDay(day === d ? null : d); setView("journal"); } }}
              >
                {d}{DAY_COUNT[d] ? <i /> : null}
              </button>
            )))}
          </div>
          {day !== null && <button className="v10-alldays" onClick={() => setDay(null)}>← 显示整周</button>}
        </div>
        <div className="v10-overview">
          <h4>本周概览</h4>
          <div className="v10-ogrid">
            <span>节点<b>{kimiMetrics.total}</b></span>
            <span>运行<b>{kimiMetrics.running}</b></span>
            <span>排队<b>{kimiMetrics.queued}</b></span>
            <span>失败<b>{kimiMetrics.failed}</b></span>
            <span>待审<b>{kimiMetrics.pending}</b></span>
            <span>锁定<b>{kimiMetrics.locked}</b></span>
          </div>
        </div>
        <div className="v10-selected">
          <span>当前选中</span>
          <b>{selNode ? `${selNode.id} · ${selNode.title}` : "—"}</b>
          <small>{selNode ? `${selNode.kind} / ${selNode.scienceState} / ${selNode.executionState}` : ""}</small>
          <small>本周记录 {ENTRIES.length} 条 · 已盖章 {stamps.size}</small>
        </div>
      </aside>
      <main className="v10-main">
        {view === "journal" && (
          <div className="v10-stream">
            <header className="v10-jhead">
              <h1 className="v10-hand">实验日志</h1>
              <div className="v10-jmeta">
                <span>《{activeProject.name}》 · {activeProject.question}</span>
                <span>{day ? `8月${day}日` : "8月15日 — 8月21日"} · {ENTRIES.length} 条记录</span>
              </div>
            </header>
            {(day ? [day] : WEEK).map((d) => (
              <section className="v10-day" key={d}>
                <header className="v10-date">
                  <span className="v10-date-big v10-hand">8月{d}日</span>
                  <span className="v10-date-sub">{WDAY[d]}{d === 21 ? " · 今天 · 活动流" : ""} · {DAY_COUNT[d] || 0} 条</span>
                </header>
                <div className="v10-timeline">
                  {ENTRIES.filter((e) => e.day === d).map((e) => (
                    <article key={e.id} className={`v10-entry ${open === e.id ? "open" : ""} ${e.node && sel === e.node.id ? "sel" : ""}`}>
                      <div className="v10-time">{e.time}</div>
                      <div className="v10-ebody" onClick={() => { setOpen(open === e.id ? null : e.id); if (e.node) setSel(e.node.id); }}>
                        <header className="v10-ehead">
                          <b>{e.actor}</b>
                          <span>{e.action}</span>
                          {e.state && <i className={`v10-tag ${EXE[e.state] || SCI[e.state] || ""}`}>{e.state}</i>}
                          <span className="v10-expand">{open === e.id ? "收起 ↑" : "展开 ↓"}</span>
                        </header>
                        {e.node && renderNodeCard(e.node)}
                        <p className="v10-enote">{e.note}</p>
                        {open === e.id && e.node && renderDetail(e.node)}
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
        {view === "cover" && (
          <div className="v10-coverpage">
            <p className="v10-cover-kicker">RESEARCH WORLD · 工作台藏书</p>
            <h1 className="v10-hand v10-cover-title">实验日志</h1>
            <p className="v10-cover-sub">每一卷对应一个在研项目。翻开一卷，进入它按天书写的日志。</p>
            <div className="v10-shelf">
              {kimiProjects.map((p) => (
                <button
                  key={p.id}
                  className={`v10-book ${p.lead ? "lead" : ""} ${project === p.id ? "current" : ""}`}
                  onClick={() => { setProject(p.id); setView("journal"); setDay(null); }}
                >
                  <span className="v10-book-band" />
                  <h2 className="v10-hand">{p.name}</h2>
                  <p>{p.question}</p>
                  <div className="v10-book-meta">
                    <span>{p.nodes} 节点</span>
                    <span>{p.running} 运行</span>
                    <span>{p.pending} 待办</span>
                  </div>
                  <span className="v10-book-upd">更新 {p.updated}</span>
                  <span className="v10-book-open">{project === p.id ? "当前卷 · 翻开 →" : "翻开 →"}</span>
                </button>
              ))}
            </div>
            <p className="v10-cover-foot">当前卷：《{activeProject.name}》 · 日志跨度 8 月 15 — 21 日</p>
          </div>
        )}
        {view === "map" && (
          <div className="v10-mappage">
            <header className="v10-maphead">
              <h1 className="v10-hand">卷首总图</h1>
              <span>研究问题 → 方向 → 实验 / 审查 · 33 节点全幅 · 点选节点贴出详签</span>
            </header>
            <div className="v10-mapwrap">
              <svg className="v10-map" viewBox={`0 0 ${MAP_W} ${MAP_H}`}>
                {EDGES.map((e) => <path key={e.id} className="v10-edge" d={e.d} />)}
                {kimiTasks.map((t) => {
                  const p = mapPos(t);
                  const w = NODE_W[t.type];
                  return (
                    <g
                      key={t.id}
                      transform={`translate(${p.x},${p.y})`}
                      className={`v10-mnode ${sel === t.id ? "sel" : ""}`}
                      onClick={() => setSel(t.id)}
                    >
                      <rect className={`v10-mbox ${AUTH[t.authoringState] || ""}`} width={w} height={NODE_H} rx="9" />
                      <circle className={`v10-mdot ${EXE[t.executionState] || ""}`} cx="13" cy={NODE_H / 2} r="4" />
                      <text className="v10-mid" x="24" y="16">{t.id}</text>
                      <text className="v10-mtitle" x="24" y="31">{t.title.slice(0, 10)}</text>
                      {sel === t.id && <ellipse className="v10-mcircle" cx={w / 2} cy={NODE_H / 2} rx={w / 2 + 7} ry={NODE_H / 2 + 6} />}
                    </g>
                  );
                })}
              </svg>
            </div>
            {selNode && (
              <aside className="v10-tipon">
                <h3 className="v10-hand">详签 · {selNode.id}</h3>
                {renderNodeCard(selNode)}
                {renderDetail(selNode)}
              </aside>
            )}
          </div>
        )}
      </main>
      <aside className="v10-notes">
        <div className="v10-sticky y">
          <h3>待审查 <span>{pending.length}</span></h3>
          <ul>{pending.map(stickItem)}</ul>
        </div>
        <div className="v10-sticky b">
          <h3>运行 / 排队 <span>{queue.length}</span></h3>
          <ul>{queue.map(stickItem)}</ul>
        </div>
        <div className="v10-sticky p">
          <h3>失败与滞留 <span>{failed.length + 1}</span></h3>
          <ul>{failed.map(stickItem)}</ul>
          <button className="v10-stick-item v10-stick-memo" onClick={() => focusNode("D-018")}>
            <b>D-018</b>
            <span>待审超 24h，建议分流</span>
          </button>
        </div>
        <p className="v10-notes-foot">便签可点：直接跳到对应日志条目。</p>
      </aside>
    </section>
  );
}
