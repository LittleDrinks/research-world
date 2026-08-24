// THROWAWAY PROTOTYPE — V01 深海玻璃 Deep-Sea Glass
import { useState } from "react";
import { Compass, FolderOpen, Activity, X, Send, Check, Lock, RotateCcw } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const GROUP_BOX = {
  "研究问题": { cx: 925, cy: 125, depth: "0m · 海面" },
  "基础计数": { cx: 250, cy: 520, depth: "−380m" },
  "解析与估计": { cx: 690, cy: 520, depth: "−420m" },
  "计算实验": { cx: 1130, cy: 520, depth: "−460m" },
  "结构规律": { cx: 1570, cy: 520, depth: "−500m" },
  "实验节点": { cx: 520, cy: 985, depth: "−1050m" },
  "审查节点": { cx: 1330, cy: 985, depth: "−1200m" },
};
const OFFSETS = {
  1: [[0, 0]],
  4: [[0, -100], [-92, 6], [92, 6], [0, 106]],
  5: [[0, -108], [-92, -20], [92, -20], [-58, 86], [58, 86]],
};
const POS = {};
for (const g of PROTOTYPE_GROUPS) {
  const members = kimiTasks.filter((t) => t.group === g);
  const offs = OFFSETS[members.length];
  members.forEach((t, i) => { POS[t.id] = { x: GROUP_BOX[g].cx + offs[i][0], y: GROUP_BOX[g].cy + offs[i][1] }; });
}
const NODE_R = { question: 16, direction: 9, experiment: 7, review: 7 };
const EXEC_CLASS = { 运行: "run", 排队: "queue", 完成: "done", 失败: "fail", 空闲: "idle" };
const CHIP = {
  待审查: "amber", 待验证: "blue", 已支持: "green", 已入图: "cyan", 已采纳: "teal",
  草稿: "dim", 已配置: "blue", 已锁定: "violet",
  运行: "cyan", 排队: "amber", 完成: "green", 失败: "red", 空闲: "dim",
};
const BUBBLES = [
  { left: "6%", width: 14, height: 14, animationDuration: "26s", animationDelay: "-4s" },
  { left: "14%", width: 7, height: 7, animationDuration: "19s", animationDelay: "-12s" },
  { left: "27%", width: 10, height: 10, animationDuration: "31s", animationDelay: "-20s" },
  { left: "46%", width: 6, height: 6, animationDuration: "17s", animationDelay: "-7s" },
  { left: "63%", width: 12, height: 12, animationDuration: "28s", animationDelay: "-15s" },
  { left: "78%", width: 8, height: 8, animationDuration: "22s", animationDelay: "-2s" },
  { left: "90%", width: 15, height: 15, animationDuration: "34s", animationDelay: "-25s" },
  { left: "97%", width: 6, height: 6, animationDuration: "18s", animationDelay: "-10s" },
];
const edgePath = (a, b) => `M ${a.x} ${a.y} C ${a.x} ${(a.y + b.y) / 2} ${b.x} ${(a.y + b.y) / 2} ${b.x} ${b.y}`;

function regionBounds(g) {
  const pts = kimiTasks.filter((t) => t.group === g).map((t) => POS[t.id]);
  const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
  const x = Math.min(...xs) - 126, y = Math.max(10, Math.min(...ys) - 132);
  return { x, y, w: Math.max(...xs) - Math.min(...xs) + 252, h: Math.max(...ys) + 126 - y };
}

export default function V01DeepSea() {
  const [selected, setSelected] = useState(null);
  const [surface, setSurface] = useState("map");
  const [overrides, setOverrides] = useState({});
  const [chatLog, setChatLog] = useState(kimiChat);
  const [draft, setDraft] = useState("");
  const [projectId, setProjectId] = useState("prime-distribution");

  const tasks = kimiTasks.map((t) => ({ ...t, ...(overrides[t.id] || {}) }));
  const sel = selected ? tasks.find((t) => t.id === selected) : null;
  const project = kimiProjects.find((p) => p.id === projectId);
  const related = new Set();
  if (sel) {
    related.add(sel.id);
    if (sel.parent) related.add(sel.parent);
    childrenOf(sel.id).forEach((t) => related.add(t.id));
  }
  const count = (fn) => tasks.filter(fn).length;
  const metrics = {
    total: tasks.length,
    run: count((t) => t.executionState === "运行"),
    queue: count((t) => t.executionState === "排队"),
    fail: count((t) => t.executionState === "失败"),
    review: count((t) => t.scienceState === "待审查"),
    support: count((t) => t.scienceState === "已支持"),
    lock: count((t) => t.authoringState === "已锁定"),
  };

  const patch = (id, p) => setOverrides((o) => ({ ...o, [id]: { ...(o[id] || {}), ...p } }));
  const toggle = (s) => setSurface((cur) => (cur === s ? "map" : s));
  const send = () => {
    const text = draft.trim();
    if (!text) return;
    setChatLog((log) => [...log,
      { role: "user", text },
      { role: "orchestrator", text: `已收到指令，将结合 ${sel.id} 当前状态（${sel.scienceState} / ${sel.executionState}）重新编排。`, nodes: [sel.id] },
    ]);
    setDraft("");
  };
  const chip = (s) => <span className={`v01-chip v01-c-${CHIP[s] || "dim"}`}>{s}</span>;

  return (
    <section className="v01-root">
      <svg className="v01-sea" viewBox="0 0 1850 1240" preserveAspectRatio="xMidYMid meet">
        <rect className="v01-hit" x="0" y="0" width="1850" height="1240" onClick={() => setSelected(null)} />
        {PROTOTYPE_GROUPS.map((g) => {
          const b = regionBounds(g);
          const deep = g === "实验节点" || g === "审查节点";
          return (
            <g key={g}>
              <rect className={`v01-region${deep ? " v01-region-deep" : ""}`} x={b.x} y={b.y} width={b.w} height={b.h} rx="24" />
              <text className="v01-rlabel" x={b.x + 18} y={b.y + 30}>{g} · {kimiTasks.filter((t) => t.group === g).length} 节点</text>
              <text className="v01-rdepth" x={b.x + b.w - 18} y={b.y + 30}>{GROUP_BOX[g].depth}</text>
            </g>
          );
        })}
        {tasks.filter((t) => t.parent).map((t) => (
          <path key={t.id} d={edgePath(POS[t.parent], POS[t.id])}
            className={`v01-edge${related.has(t.id) && related.has(t.parent) ? " v01-edge-hot" : ""}${t.executionState === "运行" ? " v01-edge-run" : ""}`} />
        ))}
        {tasks.map((t) => {
          const p = POS[t.id], r = NODE_R[t.type];
          const cls = ["v01-node", `v01-t-${t.type}`, `v01-x-${EXEC_CLASS[t.executionState]}`, selected === t.id ? "v01-sel" : ""].join(" ");
          return (
            <g key={t.id} className={cls} transform={`translate(${p.x} ${p.y})`} onClick={() => setSelected(t.id)}>
              {t.executionState === "运行" && <circle className="v01-halo" r={r + 8} />}
              {t.type === "question" && <circle className="v01-orbit" r={r + 9} />}
              {selected === t.id && <circle className="v01-selring" r={r + 5} />}
              {t.type === "review"
                ? <rect className="v01-core" x={-r} y={-r} width={r * 2} height={r * 2} transform="rotate(45)" />
                : <circle className="v01-core" r={r} />}
              <text className="v01-nid" y={-(r + 10)}>{t.id}</text>
              <text className="v01-nti" y={r + 22}>{t.title}</text>
            </g>
          );
        })}
      </svg>

      <div className="v01-bubbles">{BUBBLES.map((b, i) => <span key={i} className="v01-bubble" style={b} />)}</div>

      <div className="v01-gauge">
        {[["0m · 海面", 0], ["−400m · 方向层", 36], ["−950m · 实验层", 72], ["−1200m · 深渊", 100]].map(([label, top]) => (
          <div key={label} className="v01-tick" style={{ top: `${top}%` }}><i />{label}</div>
        ))}
      </div>

      <header className="v01-hud v01-glass">
        <div className="v01-hud-k">深海海图 · RESEARCH-WORLD</div>
        <div className="v01-hud-q">{project.name} — {project.question}</div>
        <div className="v01-hud-m">
          <span className="v01-chip v01-c-dim">{metrics.total} 节点</span>
          <span className="v01-chip v01-c-cyan">{metrics.run} 运行</span>
          <span className="v01-chip v01-c-amber">{metrics.queue} 排队</span>
          <span className="v01-chip v01-c-red">{metrics.fail} 失败</span>
          <span className="v01-chip v01-c-amber">{metrics.review} 待审查</span>
          <span className="v01-chip v01-c-green">{metrics.support} 已支持</span>
          <span className="v01-chip v01-c-violet">{metrics.lock} 已锁定</span>
        </div>
      </header>

      {!sel && (
        <div className="v01-legend v01-glass">
          <span><i className="v01-lg v01-lg-q" />问题</span>
          <span><i className="v01-lg v01-lg-d" />方向</span>
          <span><i className="v01-lg v01-lg-e" />实验</span>
          <span><i className="v01-lg v01-lg-r" />审查</span>
          <span><i className="v01-lg v01-lg-run" />运行</span>
          <span><i className="v01-lg v01-lg-fail" />失败</span>
        </div>
      )}

      {surface === "projects" && (
        <aside className="v01-pod v01-projpod v01-glass">
          <header className="v01-pod-h">
            <div><div className="v01-pod-id">PROJECTS</div><h2>项目 · 选择海域</h2></div>
            <button className="v01-x" onClick={() => setSurface("map")}><X size={15} /></button>
          </header>
          <div className="v01-proj-list">
            {kimiProjects.map((p) => (
              <button key={p.id} className={`v01-proj${p.id === projectId ? " v01-proj-on" : ""}`} onClick={() => setProjectId(p.id)}>
                <div className="v01-proj-top">
                  <strong>{p.name}</strong>
                  {p.id === projectId && <span className="v01-chip v01-c-cyan">当前海域</span>}
                  {!p.lead && <span className="v01-chip v01-c-dim">海图未装载</span>}
                </div>
                <div className="v01-proj-q">{p.question}</div>
                <div className="v01-proj-meta">{p.nodes} 节点 · {p.running} 运行 · {p.pending} 待审 · 更新 {p.updated}</div>
              </button>
            ))}
          </div>
        </aside>
      )}

      {surface === "activity" && (
        <aside className="v01-pod v01-actpod v01-glass">
          <header className="v01-pod-h">
            <div><div className="v01-pod-id">TELEMETRY</div><h2>活动流 · 遥测记录</h2></div>
            <button className="v01-x" onClick={() => setSurface("map")}><X size={15} /></button>
          </header>
          <div className="v01-act-list">
            {kimiActivity.map((a) => {
              const id = a.target.split(" ")[0];
              const hit = taskById(id);
              return (
                <div key={a.id} className="v01-act">
                  <div className="v01-act-top">
                    <span className="v01-act-time">{a.time}</span>
                    <span className="v01-act-actor">{a.actor}</span>
                    <span>{a.action}</span>
                    {chip(a.state)}
                  </div>
                  <button className="v01-act-target" onClick={() => hit && setSelected(id)}>{a.target}</button>
                  <div className="v01-act-detail">{a.detail}</div>
                </div>
              );
            })}
          </div>
        </aside>
      )}

      {sel && (
        <aside className="v01-pod v01-detail v01-glass" key={sel.id}>
          <header className="v01-pod-h">
            <div><div className="v01-pod-id">{sel.id} · {sel.kind}</div><h2>{sel.title}</h2></div>
            <button className="v01-x" onClick={() => setSelected(null)}><X size={15} /></button>
          </header>
          <div className="v01-detail-body">
            <p className="v01-prompt">{sel.prompt}</p>
            <div className="v01-chips">{chip(sel.scienceState)}{chip(sel.authoringState)}{chip(sel.executionState)}</div>
            <div className="v01-actions">
              {sel.scienceState === "待审查" && (
                <button className="v01-actbtn" onClick={() => patch(sel.id, { scienceState: "已入图" })}><Check size={13} />批准入图</button>
              )}
              {sel.authoringState !== "已锁定" && (
                <button className="v01-actbtn" onClick={() => patch(sel.id, { authoringState: "已锁定" })}><Lock size={13} />锁定配置</button>
              )}
              {sel.executionState === "失败" && (
                <button className="v01-actbtn" onClick={() => patch(sel.id, { executionState: "排队" })}><RotateCcw size={13} />重新排队</button>
              )}
            </div>
            <dl className="v01-meta">
              {[["执行 Agent", sel.agent], ["通道", sel.channel], ["模型", sel.model], ["Provider", sel.provider], ["工作区", sel.workspace], ["权限", sel.permission]].map(([k, v]) => (
                <div key={k} className="v01-meta-row"><dt>{k}</dt><dd className={k === "工作区" || k === "模型" ? "v01-mono" : ""}>{v}</dd></div>
              ))}
            </dl>
            <div className="v01-goal">目标 · {sel.goal}</div>
            <div className="v01-sec">验收标准</div>
            <ul className="v01-acc">{sel.acceptance.map((a) => <li key={a}>{a}</li>)}</ul>
            <div className="v01-sec">工具</div>
            <div className="v01-tools">{sel.tools.map((t) => <span key={t}>{t}</span>)}</div>
            <div className="v01-sec">谱系</div>
            <div className="v01-line">
              {sel.parent && <button className="v01-ref" onClick={() => setSelected(sel.parent)}>↑ {sel.parent}</button>}
              {tasks.filter((t) => t.parent === sel.id).map((k) => (
                <button key={k.id} className="v01-ref" onClick={() => setSelected(k.id)}>{k.id} {k.title}</button>
              ))}
              {!sel.parent && tasks.every((t) => t.parent !== sel.id) && <span className="v01-dim">无关联节点</span>}
            </div>
          </div>
          <div className="v01-chat">
            <div className="v01-chat-h">ORCHESTRATOR 对话</div>
            <div className="v01-chat-log">
              {chatLog.map((m, i) => (
                <div key={i} className={`v01-msg v01-msg-${m.role}`}>
                  <div className="v01-msg-role">{m.role === "user" ? "我" : "Orchestrator"}</div>
                  <p>{m.text}</p>
                  {m.nodes && (
                    <div className="v01-refs">{m.nodes.map((n) => <button key={n} onClick={() => setSelected(n)}>{n}</button>)}</div>
                  )}
                </div>
              ))}
            </div>
            <div className="v01-chat-in">
              <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder={`就 ${sel.id} 下达指令…`} />
              <button className="v01-actbtn" onClick={send}><Send size={14} /></button>
            </div>
          </div>
        </aside>
      )}

      <nav className="v01-dock v01-glass">
        <button className={`v01-dock-b${surface === "map" ? " v01-on" : ""}`} onClick={() => setSurface("map")}><Compass size={15} />海图</button>
        <button className={`v01-dock-b${surface === "projects" ? " v01-on" : ""}`} onClick={() => toggle("projects")}><FolderOpen size={15} />项目</button>
        <button className={`v01-dock-b${surface === "activity" ? " v01-on" : ""}`} onClick={() => toggle("activity")}><Activity size={15} />活动</button>
        <i className="v01-sep" />
        <span className="v01-dock-sel">{sel ? `◉ ${sel.id} ${sel.title}` : "未选中 · 点击节点下潜"}</span>
        <i className="v01-sep" />
        <span className="v01-dock-m">{metrics.total} 节点 · {metrics.run} 运行 · {metrics.queue} 排队 · {metrics.fail} 失败 · {metrics.review} 待审查</span>
      </nav>
    </section>
  );
}
