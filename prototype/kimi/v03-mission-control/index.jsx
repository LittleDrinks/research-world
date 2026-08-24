// THROWAWAY PROTOTYPE
import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Clock3, Crosshair, ListOrdered, MessageSquare, Radio, Satellite, X } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, kimiMetrics, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const EXEC_COLOR = { 运行: "#35d0ff", 排队: "#ffb000", 失败: "#ff5252", 完成: "#57d98a", 空闲: "#5f6b7d" };
const pad = (n) => String(n).padStart(2, "0");
const fmtMET = (ms) => { const s = Math.floor(ms / 1000); return `T+${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`; };
const COL_X = { question: 46, direction: 330, experiment: 610, review: 800 };
const COL_LABEL = { question: "研究问题", direction: "方向 ×20", experiment: "实验 ×5", review: "审查 ×4" };

function useClock() {
  const [now, setNow] = useState(Date.now);
  const [t0] = useState(Date.now);
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t); }, []);
  return { now, met: fmtMET(now - t0) };
}

function PanelHead({ icon: Icon, title, right }) {
  return <div className="v03-ph"><Icon size={12} /><span>{title}</span><span className="v03-ph-r">{right}</span></div>;
}

function Boards({ counts }) {
  const boards = [
    ["节点总数", counts.total, "cyan"], ["运行", counts.running, "cyan"], ["排队", counts.queued, "amber"],
    ["失败", counts.failed, counts.failed > 0 ? "red alert" : "red"], ["待审查", counts.pending, "amber"],
    ["待验证", counts.verified, "cyan"], ["已支持", counts.supported, "green"], ["已锁定", counts.locked, "dim"],
  ];
  return (
    <div className="v03-boards">
      {boards.map(([label, value, tone]) => (
        <div key={label} className={`v03-board ${tone}`}>
          <div className="v03-board-num">{pad(value)}</div>
          <div className="v03-board-label">{label}</div>
        </div>
      ))}
    </div>
  );
}

function AgentHealth({ tasks, onSelect }) {
  const agents = [...new Set(tasks.map((t) => t.agent))];
  return (
    <div className="v03-panel v03-agents">
      <PanelHead icon={Radio} title="AGENT / RUNTIME 健康" right={`${agents.length} 单元`} />
      <table>
        <thead><tr><th>单元</th><th>模型</th><th>通道</th><th>节点</th><th>运行</th><th>失败</th><th>状态</th></tr></thead>
        <tbody>
          {agents.map((a) => {
            const mine = tasks.filter((t) => t.agent === a);
            const run = mine.filter((t) => t.executionState === "运行").length;
            const fail = mine.filter((t) => t.executionState === "失败").length;
            const tone = fail > 0 ? "red" : run > 0 ? "cyan" : "dim";
            return (
              <tr key={a} onClick={() => onSelect(mine.find((t) => t.executionState !== "空闲")?.id || mine[0].id)}>
                <td>{a}</td><td className="v03-dim">{mine[0].model}</td>
                <td className="v03-dim">{[...new Set(mine.map((t) => t.channel))].join("/")}</td>
                <td>{mine.length}</td><td className="cyan">{run}</td><td className={fail ? "red" : "v03-dim"}>{fail}</td>
                <td><span className={`v03-lamp ${tone}`} />{fail > 0 ? "ALERT" : run > 0 ? "ACTIVE" : "IDLE"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Queue({ tasks, onSelect }) {
  const rows = tasks.filter((t) => ["失败", "运行", "排队"].includes(t.executionState))
    .sort((a, b) => ({ 失败: 0, 运行: 1, 排队: 2 }[a.executionState] - { 失败: 0, 运行: 1, 排队: 2 }[b.executionState]));
  return (
    <div className="v03-panel v03-queue">
      <PanelHead icon={ListOrdered} title="执行队列" right={`${rows.length} 在控`} />
      <div className="v03-scroll">
        {rows.map((t) => (
          <button key={t.id} className="v03-qrow" onClick={() => onSelect(t.id)}>
            <span className={`v03-lamp ${t.executionState === "失败" ? "red blink" : t.executionState === "运行" ? "cyan" : "amber"}`} />
            <span className="v03-qid">{t.id}</span><span className="v03-qtitle">{t.title}</span>
            <span className="v03-dim">{t.agent}</span>
            <span className="v03-qstate" style={{ color: EXEC_COLOR[t.executionState] }}>{t.executionState}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Graph({ tasks, selectedId, onSelect }) {
  const [grp, setGrp] = useState(null);
  const dirs = tasks.filter((t) => t.type === "direction");
  const yOf = (t) => t.type === "question" ? 300 : 34 + dirs.findIndex((d) => d.id === (t.type === "direction" ? t.id : t.parent)) * 27;
  const edges = tasks.filter((t) => t.parent).map((t) => ({ t, p: taskById(t.parent) }));
  return (
    <div className="v03-panel v03-graph">
      <PanelHead icon={Crosshair} title="研究图谱 · 遥测缩略" right={`${kimiMetrics.total} 节点`} />
      <div className="v03-gchips">
        {PROTOTYPE_GROUPS.map((g) => (
          <button key={g} className={`v03-gchip ${grp === g ? "on" : ""}`} onClick={() => setGrp(grp === g ? null : g)}>{g}</button>
        ))}
      </div>
      <svg viewBox="0 0 960 600" className="v03-svg">
        {Object.entries(COL_X).map(([type, x]) => (
          <text key={type} x={x - 8} y={16} className="v03-col-label">{COL_LABEL[type]}</text>
        ))}
        {edges.map(({ t, p }) => {
          const x1 = COL_X[p.type] + 12, y1 = yOf(p), x2 = COL_X[t.type] - 8, y2 = yOf(t);
          const run = t.executionState === "运行", fail = t.executionState === "失败";
          return <path key={t.id} d={`M ${x1} ${y1} C ${x1 + 90} ${y1}, ${x2 - 90} ${y2}, ${x2} ${y2}`}
            className={`v03-edge ${run ? "run" : ""} ${fail ? "fail" : ""}`} />;
        })}
        {tasks.map((t) => {
          const x = COL_X[t.type], y = yOf(t);
          const dim = grp && t.group !== grp;
          const sel = t.id === selectedId;
          return (
            <g key={t.id} transform={`translate(${x},${y})`} opacity={dim ? 0.18 : 1} onClick={() => onSelect(t.id)} className="v03-node">
              <title>{t.id} {t.title} · {t.scienceState} · {t.executionState}</title>
              {sel && <rect x="-11" y="-11" width="22" height="22" className="v03-node-sel" />}
              <rect x="-6" y="-6" width="12" height="12" fill={EXEC_COLOR[t.executionState]}
                className={t.executionState === "失败" ? "blink" : ""} />
              <text x="12" y="3.5">{t.id}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function ActivityLog({ onSelect }) {
  return (
    <div className="v03-panel v03-log">
      <PanelHead icon={Activity} title="活动流" right={`${kimiActivity.length} 事件`} />
      <div className="v03-scroll">
        {[...kimiActivity].reverse().map((a) => {
          const id = a.target.split(" ")[0];
          const hit = taskById(id);
          return (
            <button key={a.id} className="v03-arow" onClick={() => hit && onSelect(id)}>
              <span className="v03-dim">{a.time}</span>
              <span className="v03-aactor">{a.actor}</span>
              <span className="v03-aaction">{a.action}</span>
              <span className="v03-atarget">{a.target}</span>
              <span className="v03-astate" style={{ color: EXEC_COLOR[a.state] || "#ffb000" }}>{a.state}</span>
              <span className="v03-adetail">{a.detail}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Ticker() {
  const items = [...kimiActivity, ...kimiActivity];
  return (
    <div className="v03-ticker">
      <div className="v03-ticker-track">
        {items.map((a, i) => (
          <span key={i} className="v03-tick">
            <span className="v03-dim">{a.time}</span> <b>{a.actor}</b> {a.action} <span className="cyan">{a.target}</span>
            <em style={{ color: EXEC_COLOR[a.state] || "#ffb000" }}> [{a.state}]</em>
          </span>
        ))}
      </div>
    </div>
  );
}

function Drill({ task, onClose, onJump, onPatch, msgs, onSend }) {
  const [draft, setDraft] = useState("");
  const kids = childrenOf(task.id);
  const parent = task.parent ? taskById(task.parent) : null;
  const fields = [["AGENT", task.agent], ["通道", task.channel], ["分组", task.group], ["模型", task.model],
    ["PROVIDER", task.provider], ["工作区", task.workspace], ["权限", task.permission], ["类型", task.kind]];
  const send = () => { if (!draft.trim()) return; onSend(draft.trim(), task.id); setDraft(""); };
  return (
    <div className="v03-overlay">
      <div className="v03-drill">
        <div className="v03-dhead">
          <span className="v03-dkind">{task.kind}</span>
          <span className="v03-did">{task.id}</span>
          <span className="v03-dtitle">{task.title}</span>
          <span className="v03-chip" style={{ color: EXEC_COLOR[task.executionState] }}>{task.executionState}</span>
          <span className="v03-chip amber">{task.scienceState}</span>
          <span className="v03-chip dim">{task.authoringState}</span>
          {task.scienceState !== "已支持" && task.scienceState !== "已锁定" &&
            <button className="v03-btn" onClick={() => onPatch(task.id, { scienceState: "已支持" })}><CheckCircle2 size={12} /> 批准支持</button>}
          {task.authoringState !== "已锁定" &&
            <button className="v03-btn amber" onClick={() => onPatch(task.id, { authoringState: "已锁定" })}><AlertTriangle size={12} /> 锁定配置</button>}
          <button className="v03-close" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="v03-dbody">
          <div className="v03-dleft v03-scroll">
            <div className="v03-dsec">目标 PROMPT</div>
            <p className="v03-dprompt">{task.prompt}</p>
            <div className="v03-dsec">研究目标</div>
            <p className="v03-dim">{task.goal}</p>
            <div className="v03-dgrid">
              {fields.map(([k, v]) => <div key={k}><div className="v03-dk">{k}</div><div className="v03-dv">{v}</div></div>)}
            </div>
            <div className="v03-dsec">验收标准</div>
            {task.acceptance.map((a) => <div key={a} className="v03-dacc"><CheckCircle2 size={11} /> {a}</div>)}
            <div className="v03-dsec">工具</div>
            <div className="v03-dtools">{task.tools.map((t) => <span key={t} className="v03-chip dim">{t}</span>)}</div>
            <div className="v03-dsec">链路</div>
            <div className="v03-dtools">
              {parent && <button className="v03-chip link" onClick={() => onJump(parent.id)}>↑ {parent.id} {parent.title}</button>}
              {kids.map((k) => <button key={k.id} className="v03-chip link" onClick={() => onJump(k.id)}>↓ {k.id} {k.title}</button>)}
              {!parent && kids.length === 0 && <span className="v03-dim">无关联节点</span>}
            </div>
          </div>
          <div className="v03-dright">
            <div className="v03-dsec"><MessageSquare size={11} /> 编排通讯</div>
            <div className="v03-scroll v03-dmsgs">
              {msgs.map((m, i) => {
                const hit = m.nodes?.includes(task.id);
                return (
                  <div key={i} className={`v03-msg ${m.role} ${hit ? "hit" : ""}`}>
                    <div className="v03-mrole">{m.role === "user" ? "指挥席" : "ORCHESTRATOR"}</div>
                    <div className="v03-mtext">{m.text}</div>
                    {m.nodes && <div className="v03-mnodes">
                      {m.nodes.map((n) => <button key={n} className="v03-chip link" onClick={() => taskById(n) && onJump(n)}>{n}</button>)}
                    </div>}
                  </div>
                );
              })}
            </div>
            <div className="v03-dinput">
              <input value={draft} onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()} placeholder={`就 ${task.id} 下达指令…`} />
              <button className="v03-btn" onClick={send}>发送</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function V03MissionControl() {
  const { now, met } = useClock();
  const [project, setProject] = useState(kimiProjects[0].id);
  const [sel, setSel] = useState(null);
  const [ov, setOv] = useState({});
  const [msgs, setMsgs] = useState(kimiChat);
  const tasks = useMemo(() => kimiTasks.map((t) => (ov[t.id] ? { ...t, ...ov[t.id] } : t)), [ov]);
  const counts = useMemo(() => ({
    total: kimiMetrics.total,
    running: tasks.filter((t) => t.executionState === "运行").length,
    queued: tasks.filter((t) => t.executionState === "排队").length,
    failed: tasks.filter((t) => t.executionState === "失败").length,
    pending: tasks.filter((t) => t.scienceState === "待审查").length,
    verified: tasks.filter((t) => t.scienceState === "待验证").length,
    supported: tasks.filter((t) => t.scienceState === "已支持").length,
    locked: tasks.filter((t) => t.authoringState === "已锁定").length,
  }), [tasks]);
  const selected = sel ? tasks.find((t) => t.id === sel) : null;
  const proj = kimiProjects.find((p) => p.id === project);
  const patch = (id, p) => setOv((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), ...p } }));
  const send = (text, id) => setMsgs((m) => [...m, { role: "user", text, nodes: [id] }]);
  return (
    <section className="v03-root">
      <header className="v03-header">
        <div className="v03-hleft">
          <Satellite size={16} className="cyan" />
          <span className="v03-htitle">MISSION CONTROL</span>
          <div className="v03-tabs">
            {kimiProjects.map((p) => (
              <button key={p.id} className={`v03-tab ${p.id === project ? "on" : ""}`} onClick={() => setProject(p.id)}>
                {p.name}<span className="v03-dim"> {p.running}运/{p.pending}审</span>
              </button>
            ))}
          </div>
        </div>
        <div className="v03-hsel">
          {selected ? <>选中 <b className="amber">{selected.id}</b> {selected.title} · 子节点 {childrenOf(selected.id).length} · {selected.scienceState}</>
            : <>未选中目标 · 点击任意遥测点下钻</>}
        </div>
        <div className="v03-hclock">
          <Clock3 size={13} className="amber" />
          <span className="v03-clock">{new Date(now).toLocaleTimeString("zh-CN", { hour12: false })}</span>
          <span className="v03-met">{met}</span>
        </div>
      </header>
      <Ticker />
      <Boards counts={counts} />
      <main className="v03-grid">
        <AgentHealth tasks={tasks} onSelect={setSel} />
        <Graph tasks={tasks} selectedId={sel} onSelect={setSel} />
        <ActivityLog onSelect={setSel} />
        <Queue tasks={tasks} onSelect={setSel} />
        <div className="v03-panel v03-comms">
          <PanelHead icon={MessageSquare} title="ORCHESTRATOR 通讯" right={`${msgs.length} 条`} />
          <div className="v03-scroll">
            {msgs.slice(-4).map((m, i) => (
              <div key={i} className={`v03-cmsg ${m.role}`}>
                <span className="v03-dim">{m.role === "user" ? "指挥席" : "ORCH"}</span>
                <span>{m.text}</span>
                {m.nodes && <span className="v03-mnodes">{m.nodes.map((n) =>
                  <button key={n} className="v03-chip link" onClick={() => taskById(n) && setSel(n)}>{n}</button>)}</span>}
              </div>
            ))}
          </div>
        </div>
      </main>
      <footer className="v03-footer">
        <span>任务 {proj.name} · {proj.question}</span>
        <span className="v03-dim">更新 {proj.updated}</span>
        <span className={counts.failed > 0 ? "red blink" : "green"}>{counts.failed > 0 ? `⚠ ${counts.failed} 节点失败待处置` : "ALL SYSTEMS NOMINAL"}</span>
      </footer>
      {selected && <Drill task={selected} onClose={() => setSel(null)} onJump={setSel} onPatch={patch} msgs={msgs} onSend={send} />}
    </section>
  );
}
