// THROWAWAY PROTOTYPE
import { useRef, useState } from "react";
import { Crosshair, FileText, Layers, Maximize, Send, Stamp, Table, ZoomIn, ZoomOut } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const W = 240, H = 56, CW = 1520, CH = 1980;
const COL = { question: 70, direction: 440, experiment: 830, review: 1210 };
const KIND = { question: "研究问题", direction: "方向", experiment: "实验", review: "审查" };
const DIRS = kimiTasks.filter((t) => t.type === "direction");
const STRATA = ["任务书", "验收标准", "工具", "环境"];

function posOf(t) {
  if (t.type === "question") return { x: COL.question, y: 920 };
  const row = t.type === "direction" ? DIRS.findIndex((d) => d.id === t.id) : DIRS.findIndex((d) => d.id === t.parent);
  return { x: COL[t.type], y: 60 + row * 92 };
}

export default function V07BlueprintCad() {
  const [tasks, setTasks] = useState(kimiTasks);
  const [sel, setSel] = useState("Q-001");
  const [view, setView] = useState("sheet");
  const [project, setProject] = useState("prime-distribution");
  const [layers, setLayers] = useState({ question: true, direction: true, experiment: true, review: true });
  const [group, setGroup] = useState("全部");
  const [cam, setCam] = useState({ x: 24, y: 0, k: 0.52 });
  const [chat, setChat] = useState(kimiChat);
  const [draft, setDraft] = useState("");
  const [openStrata, setOpenStrata] = useState(["任务书"]);
  const dragRef = useRef(null);
  const movedRef = useRef(false);

  const task = (id) => tasks.find((t) => t.id === id);
  const selTask = task(sel);
  const kids = childrenOf(sel);
  const visible = tasks.filter((t) => layers[t.type] && (group === "全部" || t.group === group));
  const visibleIds = new Set(visible.map((t) => t.id));
  const edges = tasks.filter((t) => t.parent && visibleIds.has(t.id) && visibleIds.has(t.parent));
  const selChat = chat.filter((m) => m.nodes && m.nodes.includes(sel));
  const pendCount = tasks.filter((t) => t.scienceState === "待审查").length;
  const projectName = kimiProjects.find((p) => p.id === project)?.name;

  const zoom = (f) => setCam((c) => ({ ...c, k: Math.min(1.8, Math.max(0.3, c.k * f)) }));
  const onDown = (e) => {
    if (e.target.closest(".v07-node")) return;
    dragRef.current = { sx: e.clientX, sy: e.clientY, ox: cam.x, oy: cam.y };
    movedRef.current = false;
  };
  const onMove = (e) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.sx, dy = e.clientY - dragRef.current.sy;
    if (Math.abs(dx) + Math.abs(dy) > 4) movedRef.current = true;
    setCam((c) => ({ ...c, x: dragRef.current.ox + dx, y: dragRef.current.oy + dy }));
  };
  const onUp = () => { dragRef.current = null; };
  const pick = (id) => { if (!movedRef.current) setSel(id); movedRef.current = false; };
  const approve = () => setTasks((ts) => ts.map((t) => (t.id === sel ? { ...t, scienceState: "已入图" } : t)));
  const send = () => {
    if (!draft.trim()) return;
    setChat((c) => [...c, { role: "user", text: draft.trim(), nodes: [sel] }]);
    setDraft("");
  };
  const toggleStrata = (s) => setOpenStrata((o) => (o.includes(s) ? o.filter((x) => x !== s) : [...o, s]));

  const edgePath = (t) => {
    const p = posOf(task(t.parent)), c = posOf(t);
    const sx = p.x + W, sy = p.y + H / 2, ex = c.x, ey = c.y + H / 2;
    const mx = Math.round((sx + ex) / 2);
    return `M ${sx} ${sy} H ${mx} V ${ey} H ${ex}`;
  };

  const renderNode = (t) => {
    const p = posOf(t);
    const seq = kimiTasks.findIndex((x) => x.id === t.id) + 1;
    const cls = ["v07-node", sel === t.id ? "is-sel" : "", t.executionState === "失败" ? "is-fail" : "", t.executionState === "运行" ? "is-run" : ""].join(" ");
    return (
      <g key={t.id} className={cls} onClick={() => pick(t.id)}>
        {t.scienceState === "待审查" && <rect x={p.x + 2} y={p.y + 2} width={W - 4} height={H - 4} fill="url(#v07hatch)" />}
        <rect className="v07-frame" x={p.x} y={p.y} width={W} height={H} />
        <rect className="v07-inner" x={p.x + 5} y={p.y + 5} width={W - 10} height={H - 10} />
        <line className="v07-tick" x1={p.x - 10} y1={p.y + H / 2} x2={p.x} y2={p.y + H / 2} />
        <text className="v07-nid" x={p.x + 12} y={p.y + 21}>{t.id} · {t.kind}</text>
        <text className="v07-ntitle" x={p.x + 12} y={p.y + 42}>{t.title}</text>
        <text className="v07-nstate" x={p.x + W - 12} y={p.y + 21} textAnchor="end">{t.executionState}</text>
        <text className="v07-nstate" x={p.x + W - 12} y={p.y + 42} textAnchor="end">{t.scienceState}</text>
        <line className="v07-leader" x1={p.x + W} y1={p.y} x2={p.x + W + 22} y2={p.y - 18} />
        <circle className="v07-balloon" cx={p.x + W + 33} cy={p.y - 26} r={11} />
        <text className="v07-bnum" x={p.x + W + 33} y={p.y - 22} textAnchor="middle">{seq}</text>
      </g>
    );
  };

  const strataBody = (s) => {
    if (s === "任务书") return (<><p className="v07-prompt">{selTask.prompt}</p><p className="v07-goal">目标 — {selTask.goal}</p></>);
    if (s === "验收标准") return (<ol className="v07-acc">{selTask.acceptance.map((a) => <li key={a}>{a}</li>)}</ol>);
    if (s === "工具") return (<div className="v07-chips">{selTask.tools.map((t) => <span key={t} className="v07-chip">{t}</span>)}</div>);
    return (
      <dl className="v07-env">
        <div><dt>代理</dt><dd>{selTask.agent}</dd></div>
        <div><dt>通道</dt><dd>{selTask.channel}</dd></div>
        <div><dt>模型</dt><dd>{selTask.model}</dd></div>
        <div><dt>提供方</dt><dd>{selTask.provider}</dd></div>
        <div><dt>工作区</dt><dd>{selTask.workspace}</dd></div>
        <div><dt>权限</dt><dd>{selTask.permission}</dd></div>
      </dl>
    );
  };

  return (
    <section className="v07-root">
      <header className="v07-top">
        <div className="v07-brand"><Stamp size={15} /><span>RW 蓝图所</span><em>{projectName} · 总装图 SHEET-01</em></div>
        <nav className="v07-tabs">
          {[["sheet", Layers, "总图"], ["index", FileText, "图纸目录"], ["rev", Table, "修订表"]].map(([v, Icon, label]) => (
            <button key={v} className={view === v ? "on" : ""} onClick={() => setView(v)}><Icon size={13} />{label}</button>
          ))}
        </nav>
        <div className="v07-layers">
          <span>图层</span>
          {Object.keys(KIND).map((k) => (
            <label key={k} className={layers[k] ? "on" : ""}>
              <input type="checkbox" checked={layers[k]} onChange={() => setLayers((l) => ({ ...l, [k]: !l[k] }))} />{KIND[k]}
            </label>
          ))}
          <select value={group} onChange={(e) => setGroup(e.target.value)}>
            {["全部", ...PROTOTYPE_GROUPS].map((g) => <option key={g} value={g}>{g === "全部" ? "全部专业" : g}</option>)}
          </select>
        </div>
        <div className="v07-zoom">
          <button onClick={() => zoom(1 / 1.25)}><ZoomOut size={14} /></button>
          <b>{Math.round(cam.k * 100)}%</b>
          <button onClick={() => zoom(1.25)}><ZoomIn size={14} /></button>
          <button onClick={() => setCam({ x: 24, y: 0, k: 0.52 })}><Maximize size={14} /></button>
        </div>
      </header>

      {view === "sheet" && (
        <div className="v07-sheet">
          <div className="v07-canvas" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={onUp}>
            <svg width={CW} height={CH} style={{ transform: `translate(${cam.x}px, ${cam.y}px) scale(${cam.k})`, transformOrigin: "0 0" }}>
              <defs>
                <pattern id="v07hatch" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
                  <line x1="0" y1="0" x2="0" y2="7" stroke="rgba(214,236,255,.28)" strokeWidth="1" />
                </pattern>
                <marker id="v07arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                  <path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="rgba(214,236,255,.9)" strokeWidth="1.4" />
                </marker>
              </defs>
              <g className="v07-dim">
                <line x1="70" y1="30" x2="1450" y2="30" />
                <line x1="70" y1="22" x2="70" y2="38" /><line x1="1450" y1="22" x2="1450" y2="38" />
                <text x="760" y="20" textAnchor="middle">|←———————— 总装跨度 1380 ————————→|</text>
                <line x1="34" y1="60" x2="34" y2="1808" />
                <line x1="26" y1="60" x2="42" y2="60" /><line x1="26" y1="1808" x2="42" y2="1808" />
                <text x="20" y="934" textAnchor="middle" transform="rotate(-90 20 934)">|←—— 方向列 20 × 92 ——→|</text>
              </g>
              {edges.map((t) => (
                <path key={t.id} className={"v07-edge" + (t.executionState === "运行" ? " is-run" : "") + (t.id === sel || t.parent === sel ? " is-hot" : "")} d={edgePath(t)} markerEnd="url(#v07arrow)" />
              ))}
              {visible.map(renderNode)}
            </svg>
            <div className="v07-status">
              <Crosshair size={12} /> SEL {sel} · 派生 {kids.length} · 图元 {visible.length}/33 · ZOOM {Math.round(cam.k * 100)}%
            </div>
            <div className="v07-titleblock">
              <div className="v07-tb-row"><span>图号</span><b>RW-2026-Q001</b><span>版次</span><b>C</b></div>
              <div className="v07-tb-row"><span>图名</span><b>{projectName} · 研究总装图</b></div>
              <div className="v07-tb-row"><span>比例</span><b>1:1</b><span>日期</span><b>2026-08-21</b></div>
              <div className="v07-tb-row"><span>审批</span><b>待审查 {pendCount}</b><span>选中</span><b>{sel}</b></div>
            </div>
          </div>

          <aside className="v07-inspector">
            <header className="v07-insp-head">
              <svg viewBox="0 0 34 20" className="v07-sec-sym">
                <circle cx="8" cy="10" r="6" fill="none" stroke="currentColor" strokeWidth="1.4" />
                <text x="8" y="13.5" textAnchor="middle" fontSize="8" fill="currentColor">A</text>
                <line x1="14" y1="10" x2="32" y2="10" stroke="currentColor" strokeWidth="1.4" />
                <path d="M26 5 L33 10 L26 15" fill="none" stroke="currentColor" strokeWidth="1.4" />
              </svg>
              <span>A-A 剖面详图</span><b>{selTask.id} · {selTask.kind}</b>
            </header>
            <h3 className="v07-insp-title">{selTask.title}</h3>
            <div className="v07-states">
              <span className="v07-chip">{selTask.scienceState}</span>
              <span className="v07-chip">{selTask.authoringState}</span>
              <span className="v07-chip">{selTask.executionState}</span>
              {selTask.scienceState === "待审查" && <button className="v07-approve" onClick={approve}>批准入图</button>}
            </div>
            <div className="v07-strata">
              {STRATA.map((s, i) => (
                <div key={s} className={"v07-stratum" + (openStrata.includes(s) ? " open" : "")}>
                  <button onClick={() => toggleStrata(s)}>
                    <span>剖面 {String(i + 1).padStart(2, "0")} — {s}</span><em>{openStrata.includes(s) ? "−" : "+"}</em>
                  </button>
                  {openStrata.includes(s) && <div className="v07-stratum-body">{strataBody(s)}</div>}
                </div>
              ))}
            </div>
            <div className="v07-kids">
              <span>派生图元 × {kids.length}</span>
              <div>{kids.length === 0 && <em>无下游件</em>}{kids.map((k) => <button key={k.id} onClick={() => setSel(k.id)}>{k.id} {k.title}</button>)}</div>
            </div>
            <div className="v07-chat">
              <div className="v07-chat-head">现场批注 · {sel}</div>
              <div className="v07-chat-log">
                {selChat.length === 0 && <div className="v07-chat-empty">该节点暂无批注记录</div>}
                {selChat.map((m, i) => (
                  <div key={i} className={"v07-msg " + m.role}>
                    <div className="v07-msg-role">{m.role === "user" ? "现场" : "Orchestrator"}</div>
                    <p>{m.text}</p>
                    {m.nodes && <div className="v07-msg-nodes">{m.nodes.map((n) => <button key={n} onClick={() => taskById(n) && setSel(n)}>@{n}</button>)}</div>}
                  </div>
                ))}
              </div>
              <div className="v07-composer">
                <input value={draft} placeholder={`批注 @${sel} …`} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
                <button onClick={send}><Send size={13} /></button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {view === "index" && (
        <main className="v07-tableview">
          <h2>图纸目录 <em>DRAWING INDEX</em></h2>
          <table>
            <thead><tr><th>图号</th><th>图纸名称</th><th>研究问题</th><th>图元</th><th>运行</th><th>待审</th><th>更新</th><th>版次状态</th></tr></thead>
            <tbody>
              {kimiProjects.map((p, i) => (
                <tr key={p.id} className={project === p.id ? "on" : ""} onClick={() => { setProject(p.id); setView("sheet"); }}>
                  <td className="v07-mono">RW-2026-{String(i + 1).padStart(2, "0")}</td>
                  <td>{p.name}</td><td>{p.question}</td>
                  <td className="v07-mono">{p.nodes}</td><td className="v07-mono">{p.running}</td><td className="v07-mono">{p.pending}</td>
                  <td>{p.updated}</td><td>{p.lead ? "现行" : "归档"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="v07-hint">点击行 = 调取该图纸进入总图视图</p>
        </main>
      )}

      {view === "rev" && (
        <main className="v07-tableview">
          <h2>修订表 <em>REVISION TABLE</em></h2>
          <table>
            <thead><tr><th>REV</th><th>时间</th><th>制图</th><th>修订</th><th>对象</th><th>状态</th><th>说明</th></tr></thead>
            <tbody>
              {kimiActivity.map((a) => (
                <tr key={a.id}>
                  <td className="v07-mono">{a.id}</td><td className="v07-mono">{a.time}</td><td>{a.actor}</td><td>{a.action}</td>
                  <td><button className="v07-link" onClick={() => { const id = a.target.split(" ")[0]; if (taskById(id)) { setSel(id); setView("sheet"); } }}>{a.target}</button></td>
                  <td><span className="v07-chip">{a.state}</span></td><td>{a.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="v07-hint">点击对象 = 在总图中定位该图元</p>
        </main>
      )}
    </section>
  );
}
