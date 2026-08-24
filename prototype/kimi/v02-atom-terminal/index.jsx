// THROWAWAY PROTOTYPE: V02 ASCII 原子终端 —— 键盘优先 CLI-in-GUI，log 主流 + ASCII 字符图谱。
import { useEffect, useMemo, useRef, useState } from "react";
import { Keyboard, Activity, Layers, CircleDot } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const CHAT_TIME = ["09:05", "09:06", "11:20", "11:21", "12:50"];

const ATOM = `  ·   ·
· ( o ) ·
  ·   ·`;

const BANNER = `      ·       ·
   ·     ___     ·
  ·     ( o )     ·     A T O M   T E R M I N A L  v2.0
   ·     ~~~     ·      research-world // 磷光内核上线
      ·       ·
────────────────────────────────────────────────────────────
:help 命令表 · :map 图谱 · :open D-001 节点详情 · 裸文本 = 与 Orchestrator 对话`;

const HELP = [
  ":map               渲染 ASCII 研究图谱（33 节点全量，点击编号下钻）",
  ":log               返回日志流（对话与系统事件同流）",
  ":open <ID>         打开节点详情舱，如 :open D-001",
  ":act               活动流舱        :ls      项目目录舱",
  ":use <项目id>      切换项目        :approve 批准选中的待审节点",
  ":close / Esc       关闭侧舱        ↑ / ↓    命令历史        :clear 清屏",
];

const now = () => new Date().toTimeString().slice(0, 5);

const wide = (c) => /[\u1100-\u115F\u2E80-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60]/.test(c) ? 2 : 1;

const stc = (s) => ({
  待审查: "v02-warn", 待验证: "v02-info", 已支持: "v02-ok", 已采纳: "v02-ok", 已入图: "v02-info",
  已锁定: "v02-lock", 草稿: "v02-dim", 已配置: "v02-info",
  运行: "v02-hot", 排队: "v02-pend", 完成: "v02-ok", 失败: "v02-err", 空闲: "v02-dim",
}[s] || "");

function seedLog() {
  const chat = kimiChat.map((m, i) => ({ id: `c${i}`, time: CHAT_TIME[i], kind: m.role === "user" ? "user" : "orch", text: m.text, nodes: m.nodes }));
  const sys = kimiActivity.map((a) => ({ id: a.id, time: a.time, kind: "sys", actor: a.actor, action: a.action, target: a.target, state: a.state, text: a.detail }));
  return [{ id: "banner", time: "08:30", kind: "banner" }, ...[...chat, ...sys].sort((a, b) => a.time.localeCompare(b.time))];
}

function buildMap(tasks, selectedId) {
  const W = 118, H = 20, TC = 15, DC = 17, EC = 58, RC = 90;
  const ch = Array.from({ length: H }, () => Array(W).fill(" "));
  const meta = Array.from({ length: H }, () => Array(W).fill(null));
  const putc = (r, c, chr, m = null) => { if (r >= 0 && r < H && c >= 0 && c < W) { ch[r][c] = chr; meta[r][c] = m; } };
  const put = (r, c, text, m = null) => { let x = c; for (const chr of text) { const w = wide(chr); putc(r, x, chr, m); if (w === 2) putc(r, x + 1, "", m); x += w; } return x; };
  const hline = (r, c1, c2) => { for (let c = c1; c <= c2; c++) if (ch[r][c] === " ") putc(r, c, "─", { cls: "v02-edge" }); };
  const dirs = tasks.filter((t) => t.type === "direction");
  const rowOf = (id) => dirs.findIndex((d) => d.id === id);
  const clsOf = (t) => [t.id === selectedId && "v02-sel", t.scienceState === "待审查" && "v02-warn", t.executionState === "失败" && "v02-err", t.executionState === "运行" && "v02-hot"].filter(Boolean).join(" ");
  for (let r = 0; r < H; r++) putc(r, TC, "│", { cls: "v02-edge" });
  const q = tasks.find((t) => t.type === "question");
  const qr = 9;
  hline(qr, 14, TC - 1);
  dirs.forEach((d, r) => { putc(r, TC, "├", { cls: "v02-edge" }); hline(r, TC + 1, DC - 1); });
  tasks.filter((t) => t.type === "experiment").forEach((e) => hline(rowOf(e.parent), 44, EC - 1));
  tasks.filter((t) => t.type === "review").forEach((v) => {
    const hasE = tasks.some((e) => e.type === "experiment" && e.parent === v.parent);
    hline(rowOf(v.parent), hasE ? 82 : 44, RC - 1);
  });
  if (q) put(qr, 2, `( o ) ${q.id}`, { node: q.id, cls: clsOf(q) });
  dirs.forEach((d, r) => put(r, DC, `( o ) ${d.id} ${d.title}`, { node: d.id, cls: clsOf(d) }));
  tasks.filter((t) => t.type === "experiment").forEach((e) => put(rowOf(e.parent), EC, `( o ) ${e.id} ${e.title}`, { node: e.id, cls: clsOf(e) }));
  tasks.filter((t) => t.type === "review").forEach((v) => put(rowOf(v.parent), RC, `( o ) ${v.id} ${v.title}`, { node: v.id, cls: clsOf(v) }));
  return ch.map((_, r) => {
    const segs = [];
    let cur = null;
    for (let c = 0; c < W; c++) {
      const chr = ch[r][c];
      if (chr === "") continue;
      const m = meta[r][c];
      const key = m ? `${m.node || ""}:${m.cls || ""}` : "";
      if (cur && cur.key === key) cur.text += chr;
      else { cur = { key, text: chr, node: m?.node || null, cls: m?.cls || "" }; segs.push(cur); }
    }
    return segs;
  });
}

function Ref({ id, open }) {
  return <button className="v02-ref" title={taskById(id)?.title || id} onClick={() => open(id)}>{id}</button>;
}

function Target({ t, open }) {
  const [head, ...rest] = String(t).split(" ");
  if (!/^[QDER]-\d{3}$/.test(head)) return <>{t}</>;
  return <><Ref id={head} open={open} />{" "}{rest.join(" ")}</>;
}

function LineBody({ e, open }) {
  if (e.kind === "echo") return <span className="v02-echo">$ {e.text}</span>;
  if (e.kind === "user") return <span className="v02-user">❯ {e.text}</span>;
  if (e.kind === "orch") return <span className="v02-orch">◈ {e.text} {e.nodes?.map((n) => <Ref key={n} id={n} open={open} />)}</span>;
  if (e.kind === "sys") return <span>◆ {e.actor} · {e.action} → <Target t={e.target} open={open} /> <b className={stc(e.state)}>【{e.state}】</b>{e.text ? <span className="v02-dim"> — {e.text}</span> : null}</span>;
  if (e.kind === "err") return <span className="v02-err">✗ {e.text}</span>;
  return <span className="v02-note">← {e.text}</span>;
}

function NodePanel({ t, log, open, approve, close }) {
  if (!t) return null;
  const kids = childrenOf(t.id);
  const parent = t.parent ? taskById(t.parent) : null;
  const convo = log.filter((e) => (e.kind === "user" || e.kind === "orch") && e.nodes?.includes(t.id));
  const kv = [
    ["类型", `${t.kind} · ${t.group}`],
    ["科学状态", t.scienceState],
    ["撰写状态", t.authoringState],
    ["执行状态", t.executionState],
    ["Agent", `${t.agent} @ ${t.channel}`],
    ["模型", `${t.model} · ${t.provider}`],
    ["权限", t.permission],
    ["工作区", t.workspace],
    ["目标", t.goal],
  ];
  return <div className="v02-panel">
    <div className="v02-phead"><span><CircleDot size={13} /> ( o ) {t.id} · {t.title}</span><button className="v02-x" onClick={close}>[x]</button></div>
    <div className="v02-pbody">
      <p className="v02-pprompt">{t.prompt}</p>
      {kv.map(([k, v]) => <div key={k} className="v02-kv"><span className="v02-dim">{k.padEnd(4, "　")}</span><span className={stc(v)}>{v}</span></div>)}
      <div className="v02-sec">── 验收标准 ──────────────────</div>
      {t.acceptance.map((a) => <div key={a} className="v02-acc">[x] {a}</div>)}
      <div className="v02-sec">── 工具 ──────────────────────</div>
      <div className="v02-tools">{t.tools.map((tool) => <span key={tool} className="v02-tool">{tool}</span>)}</div>
      <div className="v02-sec">── 派生 ({kids.length}) ───────────────</div>
      {parent && <div className="v02-kv"><span className="v02-dim">父　</span><Ref id={parent.id} open={open} /><span className="v02-dim"> {parent.title}</span></div>}
      {kids.length === 0 && <div className="v02-dim">（叶节点，无派生）</div>}
      {kids.map((k) => <button key={k.id} className="v02-kid" onClick={() => open(k.id)}>( o ) {k.id} {k.title} <b className={stc(k.scienceState)}>【{k.scienceState}】</b></button>)}
      <div className="v02-sec">── 对话 ({convo.length}) ───────────────</div>
      {convo.length === 0 && <div className="v02-dim">（暂无关联对话 —— 底部输入含 {t.id} 的文本即可发起）</div>}
      {convo.map((c) => <div key={c.id} className={`v02-cline ${c.kind}`}><span className="v02-time">[{c.time}]</span> {c.kind === "user" ? "❯" : "◈"} {c.text}</div>)}
      {t.scienceState === "待审查" && <button className="v02-approve" onClick={approve}>:approve ── 批准「{t.id}」入图</button>}
    </div>
  </div>;
}

function ActivityPanel({ acts, open, close }) {
  return <div className="v02-panel">
    <div className="v02-phead"><span><Activity size={13} /> ACTIVITY ── 活动流 ({acts.length})</span><button className="v02-x" onClick={close}>[x]</button></div>
    <div className="v02-pbody">
      {acts.map((a) => <div key={a.id} className="v02-act">
        <div><span className="v02-time">[{a.time}]</span> <b>{a.actor}</b> · {a.action} <b className={stc(a.state)}>【{a.state}】</b></div>
        <div className="v02-actt">→ <Target t={a.target} open={open} /></div>
        <div className="v02-dim">{a.detail}</div>
      </div>)}
    </div>
  </div>;
}

function ProjectsPanel({ project, switchTo, close }) {
  return <div className="v02-panel">
    <div className="v02-phead"><span><Layers size={13} /> PROJECTS ── 项目目录</span><button className="v02-x" onClick={close}>[x]</button></div>
    <div className="v02-pbody">
      {kimiProjects.map((p) => <button key={p.id} className={`v02-prj ${p.id === project.id ? "on" : ""}`} onClick={() => switchTo(p.id)}>
        <div className="v02-prjid">{p.id} {p.id === project.id && <span className="v02-hot">◀ 当前接入</span>}</div>
        <div><b>{p.name}</b> ── {p.question}</div>
        <div className="v02-dim">节点 {p.nodes} · 运行 {p.running} · 待办 {p.pending} · 更新 {p.updated}</div>
      </button>)}
      <div className="v02-dim v02-pfoot">:use &lt;id&gt; 切换项目 · 图谱数据为共享内核种子</div>
    </div>
  </div>;
}

export default function AtomTerminal() {
  const [tasks, setTasks] = useState(kimiTasks);
  const [view, setView] = useState("log");
  const [side, setSide] = useState(null);
  const [selected, setSelected] = useState("Q-001");
  const [project, setProject] = useState(kimiProjects[0]);
  const [log, setLog] = useState(seedLog);
  const [extraAct, setExtraAct] = useState([]);
  const [input, setInput] = useState("");
  const [hist, setHist] = useState([]);
  const [hIdx, setHIdx] = useState(-1);
  const seq = useRef(0);
  const inputRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ block: "end" }); }, [log, view, side]);
  useEffect(() => { inputRef.current?.focus(); }, []);

  const push = (e) => setLog((l) => [...l, { id: `x${++seq.current}`, time: now(), ...e }]);
  const sel = tasks.find((t) => t.id === selected) || null;
  const kids = sel ? childrenOf(sel.id) : [];
  const mRun = tasks.filter((t) => t.executionState === "运行").length;
  const mQue = tasks.filter((t) => t.executionState === "排队").length;
  const mFail = tasks.filter((t) => t.executionState === "失败").length;
  const mRev = tasks.filter((t) => t.scienceState === "待审查").length;
  const map = useMemo(() => buildMap(tasks, selected), [tasks, selected]);

  const openNode = (id) => {
    const t = tasks.find((x) => x.id === id);
    if (!t) { push({ kind: "err", text: `节点不存在：${id} —— :map 查看全图索引` }); return; }
    setSelected(id);
    setSide({ kind: "node", id });
    push({ kind: "note", text: `已打开 ( o ) ${t.id} ${t.title} ── 详情见右侧舱` });
  };

  const approve = () => {
    if (!sel) { push({ kind: "err", text: "未选中节点 —— 先 :open <ID>" }); return; }
    if (sel.scienceState !== "待审查") { push({ kind: "err", text: `${sel.id} 当前「${sel.scienceState}」，仅「待审查」节点可批准` }); return; }
    const next = sel.type === "direction" ? "待验证" : "已采纳";
    setTasks((ts) => ts.map((t) => (t.id === sel.id ? { ...t, scienceState: next } : t)));
    push({ kind: "sys", actor: "你", action: "批准", target: `${sel.id} ${sel.title}`, state: next, text: `:approve 执行 · 待审查 → ${next}` });
    setExtraAct((a) => [{ id: `AX${a.length + 1}`, time: now(), actor: "你", action: "批准", target: `${sel.id} ${sel.title}`, state: next, detail: "命令行 :approve 本地生效" }, ...a]);
  };

  const useProject = (raw) => {
    const p = kimiProjects.find((x) => x.id === raw || x.name === raw);
    if (!p) { push({ kind: "err", text: `项目不存在：${raw || "(空)"} —— :ls 查看目录` }); return; }
    setProject(p);
    setSide({ kind: "projects" });
    push({ kind: "note", text: `已接入项目《${p.name}》── ${p.question}` });
  };

  const chat = (line) => {
    push({ kind: "user", text: line });
    const ids = [...new Set((line.match(/[QDERqder]-\d{3}/gi) || []).map((s) => s.toUpperCase()))].filter((id) => tasks.some((t) => t.id === id));
    if (ids.length) push({ kind: "orch", nodes: ids, text: `已读取 ${ids.join("、")}（${ids.map((id) => tasks.find((t) => t.id === id).scienceState).join("、")}）。:open 下钻详情，:approve 批准待审节点。` });
    else push({ kind: "orch", text: "已记录到研究日志。:map 查看全图，:act 查看动态，:open <ID> 下钻节点。" });
  };

  const run = (line) => {
    push({ kind: "echo", text: line });
    if (!line.startsWith(":")) { chat(line); return; }
    const [cmd, ...args] = line.slice(1).trim().split(/\s+/);
    switch ((cmd || "").toLowerCase()) {
      case "map": setView("map"); push({ kind: "note", text: "ASCII 图谱已渲染：33 节点 · 20 方向 · 5 实验 · 4 审查 ── 点击编号下钻" }); break;
      case "log": setView("log"); break;
      case "open": case "o": args[0] ? openNode(args[0].toUpperCase()) : push({ kind: "err", text: "用法 :open <ID>，如 :open D-001" }); break;
      case "act": case "activity": setSide({ kind: "activity" }); push({ kind: "note", text: "活动流舱已展开" }); break;
      case "ls": case "projects": setSide({ kind: "projects" }); push({ kind: "note", text: "项目目录舱已展开" }); break;
      case "approve": approve(); break;
      case "use": useProject(args.join(" ")); break;
      case "close": setSide(null); break;
      case "clear": setLog(seedLog()); break;
      case "help": case "?": HELP.forEach((h) => push({ kind: "note", text: h })); break;
      default: push({ kind: "err", text: `未知命令 :${cmd} —— :help 查看命令表` });
    }
  };

  const submit = (ev) => {
    ev.preventDefault();
    const line = input.trim();
    if (!line) return;
    setHist((h) => [line, ...h]);
    setHIdx(-1);
    setInput("");
    run(line);
  };

  const onKey = (ev) => {
    if (ev.key === "Escape") setSide(null);
    if (ev.key === "ArrowUp") { ev.preventDefault(); const n = Math.min(hIdx + 1, hist.length - 1); if (hist[n]) { setHIdx(n); setInput(hist[n]); } }
    if (ev.key === "ArrowDown") { ev.preventDefault(); const n = hIdx - 1; setHIdx(n); setInput(n >= 0 ? hist[n] : ""); }
  };

  return <section className="v02-root" onClick={(e) => { if (!e.target.closest("button,input")) inputRef.current?.focus(); }}>
    <div className="v02-scan" /><div className="v02-beam" />
    <header className="v02-top">
      <div className="v02-brand">
        <pre className="v02-atom">{ATOM}</pre>
        <div className="v02-brandtx">
          <b>ATOM TERMINAL <span className="v02-dim">v2.0</span></b>
          <span className="v02-dim">PRJ {project.id} · {project.name} · 更新 {project.updated}</span>
        </div>
      </div>
      <div className="v02-metrics">
        <span>N <b>{tasks.length}</b></span>
        <span className="v02-hot">运行 <b>{mRun}</b></span>
        <span className="v02-pend">排队 <b>{mQue}</b></span>
        <span className="v02-err">失败 <b>{mFail}</b></span>
        <span className="v02-warn">待审 <b>{mRev}</b></span>
        <span className="v02-selchip">SEL {sel ? sel.id : "──"}{sel ? <em> ▸ 派生 {kids.length}</em> : null}</span>
      </div>
      <div className="v02-keys">
        <div className="v02-keysh"><Keyboard size={11} /> KEYS</div>
        <div><b>:map</b> 图谱 <b>:log</b> 日志 <b>:open</b> 详情</div>
        <div><b>:act</b> 活动 <b>:ls</b> 项目 <b>:approve</b> 批准</div>
        <div><b>Esc</b> 关舱 <b>↑↓</b> 历史 <b>文本</b> 对话</div>
      </div>
    </header>
    <div className="v02-main">
      <div className="v02-view">
        {view === "map" ? <div className="v02-map">
          <div className="v02-maptitle">:: RESEARCH GRAPH · {project.question} · {tasks.length} NODES ::</div>
          {map.map((segs, i) => <div key={i} className="v02-mapline">
            {segs.map((s, j) => s.node
              ? <button key={j} className={`v02-mapnode ${s.cls}`} onClick={() => openNode(s.node)}>{s.text}</button>
              : <span key={j} className={s.cls}>{s.text}</span>)}
          </div>)}
          <div className="v02-maptitle v02-dim">图例 ( o )=节点 ─ ├ │=派生线 · 黄=待审查 亮=运行 红=失败 反白=选中</div>
          <div className="v02-maptitle v02-dim">域 {PROTOTYPE_GROUPS.join(" · ")}</div>
        </div> : <div className="v02-log">
          {log.map((e) => e.kind === "banner"
            ? <pre key={e.id} className="v02-banner">{BANNER}</pre>
            : <div key={e.id} className={`v02-line ${e.kind}`}><span className="v02-time">[{e.time}]</span><LineBody e={e} open={openNode} /></div>)}
        </div>}
        <div ref={endRef} />
      </div>
      {side && <aside className="v02-side">
        {side.kind === "node" && <NodePanel t={tasks.find((x) => x.id === side.id)} log={log} open={openNode} approve={approve} close={() => setSide(null)} />}
        {side.kind === "activity" && <ActivityPanel acts={[...extraAct, ...kimiActivity]} open={openNode} close={() => setSide(null)} />}
        {side.kind === "projects" && <ProjectsPanel project={project} switchTo={useProject} close={() => setSide(null)} />}
      </aside>}
    </div>
    <form className="v02-cli" onSubmit={submit}>
      <span className="v02-ps1">research:~$</span>
      <input ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey} placeholder=":help 命令表 · :map 图谱 · 裸文本与 Orchestrator 对话" spellCheck={false} autoComplete="off" autoFocus />
      <span className="v02-cursor">█</span>
    </form>
  </section>;
}
