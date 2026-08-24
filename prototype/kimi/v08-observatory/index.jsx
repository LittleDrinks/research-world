// THROWAWAY PROTOTYPE variant v08-observatory — 星图缩放导航。
import { useEffect, useMemo, useRef, useState } from "react";
import { Telescope, ScrollText, Crosshair, Lock, Check, X, Send, ZoomIn, ZoomOut } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, kimiMetrics, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const QID = "Q-001";
const CX = 600;
const CY = 410;
const STAR_R = { question: 11, direction: 5, experiment: 4, review: 4 };
const MAG = { question: "-1.46", direction: "+2.10", experiment: "+3.60", review: "+3.90" };
const CONS = [
  { group: "基础计数", cx: 880, cy: 205, rot: 12 },
  { group: "解析与估计", cx: 905, cy: 605, rot: 168 },
  { group: "计算实验", cx: 300, cy: 610, rot: 196 },
  { group: "结构规律", cx: 290, cy: 205, rot: -28 },
];
const SHAPE = [[-95, -25], [-45, 15], [5, -30], [55, 0], [100, -50]];

function rot2([x, y], deg) {
  const a = (deg * Math.PI) / 180;
  return [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];
}

function buildLayout() {
  const pos = { [QID]: [CX, CY] };
  for (const c of CONS) {
    const members = kimiTasks.filter((t) => t.group === c.group && t.type === "direction");
    members.forEach((m, i) => {
      const [dx, dy] = rot2(SHAPE[i], c.rot);
      pos[m.id] = [c.cx + dx, c.cy + dy];
    });
  }
  for (const t of kimiTasks) {
    if (t.type !== "experiment" && t.type !== "review") continue;
    const [px, py] = pos[t.parent];
    const ang = Math.atan2(py - CY, px - CX);
    const sibs = kimiTasks.filter((s) => s.parent === t.parent && s.type !== "direction" && s.type !== "question");
    const idx = sibs.findIndex((s) => s.id === t.id);
    const dist = t.type === "experiment" ? 58 : 88;
    const off = (idx - (sibs.length - 1) / 2) * 0.55;
    pos[t.id] = [px + Math.cos(ang + off) * dist, py + Math.sin(ang + off) * dist];
  }
  return pos;
}

const LAYOUT = buildLayout();

const TICKS = Array.from({ length: 60 }, (_, i) => {
  const a = (i * 6 * Math.PI) / 180;
  const big = i % 5 === 0;
  const r2 = big ? 336 : 346;
  return {
    x1: CX + Math.cos(a) * 356, y1: CY + Math.sin(a) * 356,
    x2: CX + Math.cos(a) * r2, y2: CY + Math.sin(a) * r2,
    big, label: big ? `${(i / 5) * 2}h` : null,
    lx: CX + Math.cos(a) * 322, ly: CY + Math.sin(a) * 322 + 3,
  };
});

const raOf = ([x]) => ((x / 1200) * 24).toFixed(2);
const decOf = ([, y]) => (((CY - y) / CY) * 90).toFixed(1);

export default function V08Observatory() {
  const [level, setLevel] = useState(1);
  const [focusId, setFocusId] = useState("D-001");
  const [selectedId, setSelectedId] = useState(QID);
  const [projectId, setProjectId] = useState("prime-distribution");
  const [logOpen, setLogOpen] = useState(true);
  const [specOpen, setSpecOpen] = useState(false);
  const [overrides, setOverrides] = useState({});
  const [extra, setExtra] = useState([]);
  const [draft, setDraft] = useState("");
  const wheelRef = useRef(0);

  const tasks = useMemo(() => kimiTasks.map((t) => ({ ...t, ...(overrides[t.id] || {}) })), [overrides]);
  const sel = tasks.find((t) => t.id === selectedId) || tasks[0];
  const focusTask = tasks.find((t) => t.id === focusId);
  const kids = childrenOf(selectedId);
  const isLead = projectId === "prime-distribution";
  const proj = kimiProjects.find((p) => p.id === projectId);

  const counts = useMemo(() => ({
    total: tasks.length,
    running: tasks.filter((t) => t.executionState === "运行").length,
    queued: tasks.filter((t) => t.executionState === "排队").length,
    failed: tasks.filter((t) => t.executionState === "失败").length,
    review: tasks.filter((t) => t.scienceState === "待审查").length,
    supported: tasks.filter((t) => t.scienceState === "已支持").length,
    locked: tasks.filter((t) => t.authoringState === "已锁定").length,
  }), [tasks]);

  const camT = (() => {
    if (level === 1) return `translate(${CX - CX * 1.7}px ${CY - CY * 1.7}px) scale(1.7)`;
    if (level === 3) {
      const [fx, fy] = LAYOUT[focusId] || [CX, CY];
      return `translate(${CX - fx * 2.3}px ${CY - fy * 2.3}px) scale(2.3)`;
    }
    return "translate(0px 0px) scale(1)";
  })();

  function drillIn() {
    if (!isLead) return;
    if (level === 1) return setLevel(2);
    if (level === 2) {
      const f = sel.type === "direction" ? sel.id : sel.parent && sel.parent !== QID ? sel.parent : focusId;
      setFocusId(f); setSelectedId(f); setLevel(3);
    }
  }

  function drillUp() {
    if (level === 3) { setLevel(2); setSelectedId(focusId); }
    else if (level === 2) { setLevel(1); setSelectedId(QID); }
  }

  function onStar(t) {
    if (!isLead) return;
    if (t.id === selectedId) {
      if (level === 1 && t.type === "question") return setLevel(2);
      if (level === 2 && t.type === "direction") { setFocusId(t.id); return setLevel(3); }
    }
    setSelectedId(t.id);
    if (level === 3 && t.type === "direction") setFocusId(t.id);
    if (t.type === "experiment" || t.type === "review") setFocusId(t.parent);
  }

  function jump(tid) {
    const t = taskById(tid);
    if (!t) return;
    setSelectedId(tid);
    if (t.type === "experiment" || t.type === "review") { setFocusId(t.parent); setLevel(3); }
    else if (t.type === "direction") { setFocusId(tid); if (level === 1) setLevel(2); }
    else setLevel(1);
  }

  function jumpGroup(g) {
    const t = kimiTasks.find((x) => x.group === g);
    if (t) jump(t.id);
  }

  function cycle(d) {
    const list = level === 3
      ? [focusId, ...childrenOf(focusId).map((c) => c.id)]
      : level === 2
        ? tasks.filter((t) => t.type === "direction").map((t) => t.id)
        : [QID];
    const i = list.indexOf(selectedId);
    setSelectedId(list[(i + d + list.length) % list.length] || list[0]);
  }

  function onWheel(e) {
    const now = Date.now();
    if (now - wheelRef.current < 500) return;
    wheelRef.current = now;
    if (e.deltaY < 0) drillIn(); else drillUp();
  }

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") drillUp();
      if (e.key === "ArrowRight") cycle(1);
      if (e.key === "ArrowLeft") cycle(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const canDrill = isLead && level < 3 && !(level === 2 && sel.type === "question");
  const canApprove = sel.scienceState === "待审查" || sel.scienceState === "待验证";

  function approve() {
    if (canApprove) setOverrides((o) => ({ ...o, [sel.id]: { ...(o[sel.id] || {}), scienceState: "已支持" } }));
  }

  function lock() {
    if (sel.authoringState !== "已锁定") setOverrides((o) => ({ ...o, [sel.id]: { ...(o[sel.id] || {}), authoringState: "已锁定" } }));
  }

  const thread = useMemo(() => [
    ...kimiChat.filter((m) => m.nodes && m.nodes.includes(selectedId)),
    ...extra.filter((m) => m.nodeId === selectedId),
  ], [selectedId, extra]);

  function sendMsg() {
    const text = draft.trim();
    if (!text) return;
    setExtra((x) => [...x,
      { nodeId: selectedId, role: "user", text },
      { nodeId: selectedId, role: "orchestrator", text: `收到。已把「${sel.id} ${sel.title}」列入下一轮编排，证据达标后提交双审。` },
    ]);
    setDraft("");
  }

  const selPos = LAYOUT[sel.id] || [CX, CY];

  return (
    <section className="v08-root">
      <header className="v08-top">
        <div className="v08-brand"><Telescope size={15} /><div>星图天文台<span>OBSERVATORY · PRIME FIELD SURVEY</span></div></div>
        <div className="v08-targets">
          <span>观测目标</span>
          {kimiProjects.map((p) => (
            <button key={p.id} className={p.id === projectId ? "v08-on" : ""} onClick={() => setProjectId(p.id)}>
              {p.name}{p.lead && <i>主</i>}
            </button>
          ))}
        </div>
        <div className="v08-counts">
          <span>星体 <b>{counts.total}</b></span>
          <span>运行 <b>{counts.running}</b></span>
          <span>排队 <b>{counts.queued}</b></span>
          <span className={counts.failed ? "v08-alert" : ""}>失败 <b>{counts.failed}</b></span>
          <span>待审查 <b>{counts.review}</b></span>
          <span>已支持 <b>{counts.supported}</b></span>
          <span>已锁定 <b>{counts.locked}</b></span>
        </div>
        <button className="v08-icon" onClick={() => setLogOpen((v) => !v)} title="观测日志"><ScrollText size={15} /></button>
      </header>

      <div className="v08-bar">
        <span className="v08-bar-label">焦距</span>
        <button className={level === 1 ? "v08-cur" : ""} onClick={() => { setLevel(1); setSelectedId(QID); }}>L1 问题</button>
        <span className="v08-sep">›</span>
        <button className={level === 2 ? "v08-cur" : ""} onClick={() => setLevel(2)}>L2 星座 ×20</button>
        {level === 3 && (<><span className="v08-sep">›</span><span className="v08-cur">L3 星团 {focusId}</span></>)}
        <span className="v08-groups">
          {PROTOTYPE_GROUPS.map((g) => (
            <button key={g} className={sel.group === g ? "v08-on" : ""} onClick={() => jumpGroup(g)}>{g}</button>
          ))}
        </span>
        <span className="v08-hint">滚轮缩放 · 点星选中 · 再点下钻 · Esc 上升 · ←/→ 换星</span>
      </div>

      <div className="v08-sky" onWheel={onWheel}>
        <svg viewBox="0 0 1200 820" preserveAspectRatio="xMidYMid meet">
          <g className="v08-zodiac">
            <circle cx={CX} cy={CY} r={356} className="v08-z-ring" />
            <circle cx={CX} cy={CY} r={300} className="v08-z-ring2" />
            {TICKS.map((tk, i) => (
              <g key={i}>
                <line x1={tk.x1} y1={tk.y1} x2={tk.x2} y2={tk.y2} className={tk.big ? "v08-z-tickbig" : "v08-z-tick"} />
                {tk.label && <text x={tk.lx} y={tk.ly} className="v08-z-label">{tk.label}</text>}
              </g>
            ))}
          </g>
          <g className={`v08-camera v08-l${level}`} style={{ transform: camT }}>
            {tasks.filter((t) => t.parent).map((t) => {
              const [x1, y1] = LAYOUT[t.parent];
              const [x2, y2] = LAYOUT[t.id];
              const branch = t.id === focusId || t.parent === focusId;
              const cls = ["v08-link"];
              if (t.executionState === "运行") cls.push("v08-link-run");
              if (level === 1) cls.push("v08-far");
              if (level === 3 && !branch) cls.push(t.parent === QID ? "v08-mid" : "v08-far");
              return <line key={t.id} x1={x1} y1={y1} x2={x2} y2={y2} className={cls.join(" ")} />;
            })}
            {CONS.map((c) => {
              const pts = tasks.filter((t) => t.group === c.group && t.type === "direction").map((t) => LAYOUT[t.id].join(",")).join(" ");
              const dim = level === 3 && focusTask && focusTask.group !== c.group;
              return <polyline key={c.group} points={pts} className={`v08-consline ${dim ? "v08-far" : ""}`} />;
            })}
            {CONS.map((c) => {
              const ang = Math.atan2(c.cy - CY, c.cx - CX);
              return <text key={c.group} className="v08-consname" x={CX + Math.cos(ang) * 308} y={CY + Math.sin(ang) * 308}>{c.group}</text>;
            })}
            {tasks.map((t) => {
              const [x, y] = LAYOUT[t.id];
              const r = STAR_R[t.type];
              const branch = t.id === focusId || t.parent === focusId || t.id === QID;
              const cls = ["v08-node", `v08-t-${t.type}`];
              if (t.executionState === "运行") cls.push("v08-run");
              if (t.executionState === "失败") cls.push("v08-fail");
              if (t.scienceState === "待审查") cls.push("v08-pending");
              if (t.id === selectedId) cls.push("v08-sel");
              if (level === 1 && t.type !== "question") cls.push("v08-far");
              if (level === 3) cls.push(branch ? "v08-near" : t.type === "direction" ? "v08-mid" : "v08-far");
              return (
                <g key={t.id} className={cls.join(" ")} transform={`translate(${x} ${y})`} onClick={(e) => { e.stopPropagation(); onStar(t); }}>
                  <circle r={r * 3.6} className="v08-halo v08-h3" />
                  <circle r={r * 2.1} className="v08-halo v08-h2" />
                  {t.type === "question" && <path d="M -28 0 H 28 M 0 -28 V 28" className="v08-flare" />}
                  <circle r={r} className="v08-core" />
                  <circle r={r * 0.45} className="v08-nucleus" />
                  {t.authoringState === "已锁定" && <circle r={r + 4.5} className="v08-lockring" />}
                  {t.id === selectedId && (
                    <g className="v08-reticle">
                      <circle r={r + 11} />
                      <path d={`M 0 ${-(r + 16)} V ${-(r + 7)} M 0 ${r + 16} V ${r + 7} M ${-(r + 16)} 0 H ${-(r + 7)} M ${r + 16} 0 H ${r + 7}`} />
                    </g>
                  )}
                  <text className="v08-label" x={r + 6} y={3}>{t.id}</text>
                  {level === 3 && (t.id === focusId || t.parent === focusId) && (
                    <text className="v08-sublabel" x={r + 6} y={15}>{t.title}</text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {!isLead && (
          <div className="v08-off">
            <div className="v08-off-card">
              <span>信号微弱 · SIGNAL WEAK</span>
              <h3>{proj.name}</h3>
              <p>{proj.question}</p>
              <div className="v08-off-stats">星体 {proj.nodes} · 运行 {proj.running} · 待审 {proj.pending} · 更新 {proj.updated}</div>
              <p className="v08-off-note">仅主目标「素数分布研究」已建立完整星图。</p>
              <button className="v08-btn v08-btn-acc" onClick={() => setProjectId("prime-distribution")}>对准主目标</button>
            </div>
          </div>
        )}

        {specOpen && (
          <aside className="v08-spec">
            <header>
              <div><span className="v08-spec-tag">光谱仪 SPECTROGRAPH</span><h3>{sel.id} · {sel.title}</h3></div>
              <button className="v08-icon" onClick={() => setSpecOpen(false)}><X size={14} /></button>
            </header>
            <div className="v08-spec-body">
              <h4>观测摘要</h4><p>{sel.prompt}</p>
              <h4>科学目标</h4><p>{sel.goal}</p>
              <div className="v08-spec-grid">
                <span>科学态</span><b>{sel.scienceState}</b>
                <span>创作态</span><b>{sel.authoringState}</b>
                <span>执行态</span><b>{sel.executionState}</b>
                <span>Agent</span><b>{sel.agent} · {sel.channel}</b>
                <span>模型</span><b>{sel.model} · {sel.provider}</b>
                <span>工作区</span><b>{sel.workspace}</b>
                <span>权限</span><b>{sel.permission}</b>
                <span>父星</span><b>{sel.parent || "—"}</b>
                <span>派生</span><b>{kids.length} 星体{kids.length ? `（${kids.map((k) => k.id).join("、")}）` : ""}</b>
              </div>
              <h4>验收标准</h4>
              <ul>{sel.acceptance.map((a) => <li key={a}>{a}</li>)}</ul>
              <h4>工具</h4>
              <div className="v08-chips">{sel.tools.map((t) => <span key={t}>{t}</span>)}</div>
              <h4>通信记录</h4>
              {thread.length === 0 && <p className="v08-spec-none">暂无以此星体为坐标的通信，可在下方发起。</p>}
              {thread.map((m, i) => (
                <div key={i} className={`v08-msg ${m.role === "user" ? "v08-msg-user" : ""}`}>
                  <span>{m.role === "user" ? "观测员" : "ORCHESTRATOR"}</span>
                  <p>{m.text}</p>
                </div>
              ))}
              <div className="v08-spec-metrics">全场遥测 · 总 {kimiMetrics.total} · 运行 {kimiMetrics.running} · 排队 {kimiMetrics.queued} · 失败 {kimiMetrics.failed} · 待审查 {kimiMetrics.pending} · 待验证 {kimiMetrics.verified} · 已支持 {kimiMetrics.supported} · 已锁定 {kimiMetrics.locked}</div>
            </div>
            <div className="v08-spec-input">
              <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMsg()} placeholder={`以 ${sel.id} 为坐标发送指令…`} />
              <button onClick={sendMsg}><Send size={13} /></button>
            </div>
          </aside>
        )}

        <aside className={`v08-log ${logOpen ? "v08-open" : ""}`}>
          <header><span>观测日志</span><span className="v08-log-n">{kimiActivity.length} 条</span></header>
          <div className="v08-log-list">
            {[...kimiActivity].reverse().map((a) => {
              const tid = a.target.split(" ")[0];
              const known = Boolean(taskById(tid));
              return (
                <button key={a.id} className={`v08-logrow ${tid === selectedId ? "v08-on" : ""}`} onClick={() => known && jump(tid)}>
                  <span className="v08-lr-top"><b>{a.time}</b> {a.actor} · {a.action}</span>
                  <span className="v08-lr-target">{a.target} <i>{a.state}</i></span>
                  <span className="v08-lr-detail">{a.detail}</span>
                </button>
              );
            })}
          </div>
        </aside>
      </div>

      <footer className="v08-eye">
        <div className="v08-eye-col">
          <div className="v08-eye-id"><Crosshair size={12} /> <b>{sel.id}</b> <span>{sel.kind}</span> <em>{sel.title}</em></div>
          <div className="v08-eye-pos">星区 {sel.group} · RA {raOf(selPos)}h · DEC {decOf(selPos)}° · 星等 {MAG[sel.type]}</div>
          <div className="v08-eye-prompt">{sel.prompt}</div>
        </div>
        <div className="v08-eye-col">
          <div className="v08-eye-states">
            <span>科学态 <b>{sel.scienceState}</b></span>
            <span>创作 <b>{sel.authoringState}</b></span>
            <span>执行 <b className={sel.executionState === "运行" ? "v08-hot" : sel.executionState === "失败" ? "v08-bad" : ""}>{sel.executionState}</b></span>
          </div>
          <div className="v08-eye-kids">
            派生 <b>{kids.length}</b> 星体
            {kids.map((k) => <button key={k.id} onClick={() => jump(k.id)}>{k.id}</button>)}
          </div>
          <div className="v08-eye-goal">{sel.goal}</div>
        </div>
        <div className="v08-eye-col v08-eye-env">
          <div>AGENT {sel.agent} · 通道 {sel.channel}</div>
          <div>{sel.model} · {sel.provider}</div>
          <div>{sel.workspace} · 权限 {sel.permission}</div>
        </div>
        <div className="v08-eye-ops">
          <button className="v08-btn" onClick={drillIn} disabled={!canDrill}><ZoomIn size={12} /> 下钻</button>
          <button className="v08-btn" onClick={drillUp} disabled={level === 1}><ZoomOut size={12} /> 上升</button>
          <button className="v08-btn" onClick={approve} disabled={!canApprove}><Check size={12} /> 批准</button>
          <button className="v08-btn" onClick={lock} disabled={sel.authoringState === "已锁定"}><Lock size={12} /> 锁定</button>
          <button className="v08-btn v08-btn-acc" onClick={() => setSpecOpen(true)}>光谱仪</button>
        </div>
      </footer>
    </section>
  );
}
