// THROWAWAY PROTOTYPE: v06 chat orchestrator
import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, Check, ChevronDown, ChevronRight, FolderKanban, ListTree, Pin, Send, X } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, childrenOf, taskById, PROTOTYPE_GROUPS } from "../seed";
import "./style.css";

const STATE_DOT = { 运行: "run", 排队: "queue", 完成: "done", 失败: "fail", 空闲: "idle" };

function buildInitial() {
  const msgs = [];
  kimiChat.forEach((m, i) => {
    msgs.push({ id: `c-${i}`, role: m.role, text: m.text, nodes: m.nodes || [] });
    kimiActivity.slice(i * 3, i * 3 + 3).forEach((a, j) => msgs.push({ id: `a-${i}-${j}`, role: "system", activity: a }));
  });
  return msgs;
}

function Dot({ state }) {
  return <span className={`v06-dot v06-dot-${STATE_DOT[state] || "idle"}`} />;
}

function NodeCard({ id, pinned, expanded, effective, onToggle, onPin, onSpawn, onApprove }) {
  const t = taskById(id);
  if (!t) return null;
  const kids = childrenOf(id);
  const science = effective[id] || t.scienceState;
  return (
    <div className={`v06-card ${expanded ? "open" : ""}`}>
      <div className="v06-card-head" onClick={onToggle}>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="v06-id">{t.id}</span>
        <span className="v06-card-title">{t.title}</span>
        <span className="v06-kind">{t.kind}</span>
        <span className="v06-chip"><Dot state={t.executionState} />{t.executionState}</span>
      </div>
      {expanded && (
        <div className="v06-card-body">
          <p className="v06-prompt">{t.prompt}</p>
          <div className="v06-kv"><span>科学状态</span><b>{science}</b><span>编撰状态</span><b>{t.authoringState}</b></div>
          <div className="v06-kv"><span>Agent</span><b>{t.agent}</b><span>通道</span><b>{t.channel}</b></div>
          <div className="v06-kv"><span>模型</span><b>{t.model}</b><span>Provider</span><b>{t.provider}</b></div>
          <div className="v06-kv"><span>工作区</span><b className="v06-mono">{t.workspace}</b><span>权限</span><b>{t.permission}</b></div>
          <div className="v06-kv"><span>派生</span><b>{kids.length} 个子节点{kids.length > 0 ? `（${kids.map((k) => k.id).join("、")}）` : ""}</b></div>
          <div className="v06-tags">{t.tools.map((tool) => <span key={tool} className="v06-tag">{tool}</span>)}</div>
          <ul className="v06-acc">{t.acceptance.map((a) => <li key={a}>{a}</li>)}</ul>
          <div className="v06-card-actions">
            <button className="v06-btn" onClick={onPin}>{pinned ? "取消钉入" : "钉入上下文"}</button>
            {kids.length > 0 && <button className="v06-btn" onClick={onSpawn}>展开{t.id} 的子节点</button>}
            {science === "待审查" && <button className="v06-btn v06-btn-primary" onClick={onApprove}><Check size={12} />批准入图</button>}
          </div>
        </div>
      )}
    </div>
  );
}

export default function V06ChatOrchestrator() {
  const [messages, setMessages] = useState(buildInitial);
  const [input, setInput] = useState("");
  const [pinned, setPinned] = useState(["D-003", "D-014"]);
  const [selected, setSelected] = useState("D-003");
  const [expanded, setExpanded] = useState({ "D-014": true });
  const [effective, setEffective] = useState({});
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [projOpen, setProjOpen] = useState(false);
  const [activeProj, setActiveProj] = useState("prime-distribution");
  const scrollRef = useRef(null);
  const seq = useRef(0);

  const metrics = useMemo(() => {
    const sci = (t) => effective[t.id] || t.scienceState;
    return {
      total: kimiTasks.length,
      running: kimiTasks.filter((t) => t.executionState === "运行").length,
      failed: kimiTasks.filter((t) => t.executionState === "失败").length,
      pending: kimiTasks.filter((t) => sci(t) === "待审查").length,
      verified: kimiTasks.filter((t) => sci(t) === "待验证").length,
      supported: kimiTasks.filter((t) => sci(t) === "已支持").length,
    };
  }, [effective]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const push = (msg) => setMessages((ms) => [...ms, { id: `m-${seq.current++}`, ...msg }]);

  const spawnChildren = (id) => {
    const t = taskById(id);
    const kids = childrenOf(id);
    setSelected(id);
    push({ role: "user", text: `展开 ${id} 的子节点`, nodes: [] });
    push({ role: "orchestrator", text: `${id} ${t.title} 共派生 ${kids.length} 个子节点：`, nodes: kids.map((k) => k.id) });
  };

  const send = (raw) => {
    const text = (raw ?? input).trim();
    if (!text) return;
    setInput("");
    push({ role: "user", text, nodes: [] });
    const refs = [...text.matchAll(/@([QDER]-\d{3})/g)].map((m) => m[1]).filter((id) => taskById(id));
    if (refs.length === 0) {
      push({ role: "orchestrator", text: "收到。用 @节点编号（如 @D-001）引用图谱节点，我会把它物化成卡片并列出派生子节点。", nodes: [] });
      return;
    }
    refs.forEach((id) => {
      const t = taskById(id);
      const kids = childrenOf(id);
      setSelected(id);
      setExpanded((e) => ({ ...e, [id]: true }));
      push({ role: "orchestrator", text: `已调出 ${id} ${t.title}（${t.kind} · ${t.executionState}），派生 ${kids.length} 个子节点。`, nodes: [id, ...kids.map((k) => k.id)] });
    });
  };

  const locate = (id) => {
    const t = taskById(id);
    if (!t) return;
    setSelected(id);
    setDrawerOpen(false);
    setExpanded((e) => ({ ...e, [id]: true }));
    push({ role: "orchestrator", text: `按编号索引到 ${id} ${t.title}：`, nodes: [id] });
  };

  const switchProject = (p) => {
    setActiveProj(p.id);
    setProjOpen(false);
    push({ role: "system", activity: { time: "现在", actor: "Orchestrator", action: "切换项目", target: p.name, state: "—", detail: `问题：${p.question} · ${p.nodes} 节点` } });
  };

  const approve = (id) => {
    setEffective((e) => ({ ...e, [id]: "待验证" }));
    push({ role: "system", activity: { time: "现在", actor: "你", action: "批准", target: `${id} ${taskById(id).title}`, state: "待验证", detail: "本地通过审查，进入待验证" } });
  };

  const proj = kimiProjects.find((p) => p.id === activeProj);
  const sel = taskById(selected);
  const groups = PROTOTYPE_GROUPS;

  return (
    <section className="v06-root">
      <header className="v06-top">
        <button className={`v06-iconbtn ${drawerOpen ? "on" : ""}`} onClick={() => setDrawerOpen((v) => !v)} title="按编号索引"><ListTree size={16} /></button>
        <div className="v06-projwrap">
          <button className="v06-projbtn" onClick={() => setProjOpen((v) => !v)}>
            <FolderKanban size={14} /><b>{proj.name}</b><span>{proj.nodes} 节点 · 运行 {proj.running} · 待审 {proj.pending}</span><ChevronDown size={13} />
          </button>
          {projOpen && (
            <div className="v06-projmenu">
              {kimiProjects.map((p) => (
                <button key={p.id} className={`v06-projitem ${p.id === activeProj ? "on" : ""}`} onClick={() => switchProject(p)}>
                  <b>{p.name}</b><span>{p.question}</span>
                  <em>{p.nodes} 节点 · 运行 {p.running} · 待审 {p.pending} · {p.updated}</em>
                  {p.id === activeProj && <Check size={14} />}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="v06-topstats">
          <span>总 {metrics.total}</span><span>运行 {metrics.running}</span><span>失败 {metrics.failed}</span>
          <span>待审查 {metrics.pending}</span><span>待验证 {metrics.verified}</span><span>已支持 {metrics.supported}</span>
        </div>
      </header>

      <div className="v06-body">
        <aside className={`v06-drawer ${drawerOpen ? "open" : ""}`}>
          <div className="v06-drawer-head">按编号索引<em>{kimiTasks.length} 节点</em></div>
          <div className="v06-drawer-scroll">
            {groups.map((g) => (
              <div key={g} className="v06-g">
                <div className="v06-g-name">{g}</div>
                {kimiTasks.filter((t) => t.group === g).map((t) => (
                  <button key={t.id} className={`v06-g-row ${t.id === selected ? "on" : ""}`} onClick={() => locate(t.id)}>
                    <Dot state={t.executionState} />
                    <span className="v06-id">{t.id}</span>
                    <span className="v06-g-title">{t.title}</span>
                    <em>{t.scienceState}</em>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </aside>

        <main className="v06-main">
          <div className="v06-scroll" ref={scrollRef}>
            <div className="v06-col">
              {messages.map((m) => {
                if (m.role === "system") {
                  const a = m.activity;
                  return (
                    <div key={m.id} className="v06-sys">
                      <span className="v06-sys-time">{a.time}</span>
                      <b>{a.actor}</b><span>{a.action}</span>
                      <button className="v06-sys-target" onClick={() => locate(a.target.split(" ")[0])}>{a.target}</button>
                      <span className="v06-sys-detail">{a.detail}</span>
                    </div>
                  );
                }
                if (m.role === "user") return <div key={m.id} className="v06-msg-user">{m.text}</div>;
                return (
                  <div key={m.id} className="v06-msg-orch">
                    <div className="v06-avatar"><Bot size={16} /></div>
                    <div className="v06-orch-body">
                      <div className="v06-bubble">{m.text}</div>
                      {(m.nodes || []).map((id) => (
                        <NodeCard key={id} id={id}
                          pinned={pinned.includes(id)} expanded={!!expanded[id]} effective={effective}
                          onToggle={() => { setExpanded((e) => ({ ...e, [id]: !e[id] })); setSelected(id); }}
                          onPin={() => setPinned((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))}
                          onSpawn={() => spawnChildren(id)}
                          onApprove={() => approve(id)} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="v06-inputwrap">
            <div className="v06-inputcol">
              <div className="v06-sugg">
                {["展开 D-001 的子节点", "@D-014 为什么失败", "@R-001 审查进度", "@D-010"].map((s) => (
                  <button key={s} className="v06-suggchip" onClick={() => (s.startsWith("@") ? send(s) : spawnChildren("D-001"))}>{s}</button>
                ))}
              </div>
              <div className="v06-inputbox">
                <input value={input} placeholder="回复 Orchestrator，用 @编号 引用节点…"
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()} />
                <button className="v06-send" onClick={() => send()}><Send size={15} /></button>
              </div>
            </div>
          </div>
        </main>

        <aside className="v06-rail">
          <div className="v06-rail-sec">
            <h3>当前选中</h3>
            {sel && (
              <div className="v06-sel">
                <div className="v06-sel-top"><span className="v06-id">{sel.id}</span><Dot state={sel.executionState} /><em>{sel.executionState}</em></div>
                <b>{sel.title}</b>
                <span className="v06-sel-meta">{sel.kind} · {sel.agent} · {effective[sel.id] || sel.scienceState}</span>
                <span className="v06-sel-meta">派生 {childrenOf(sel.id).length} 个子节点</span>
              </div>
            )}
          </div>
          <div className="v06-rail-sec v06-rail-grow">
            <h3><Pin size={12} />已钉入上下文<em>{pinned.length}</em></h3>
            {pinned.length === 0 && <p className="v06-empty">在卡片上点“钉入上下文”。</p>}
            {pinned.map((id) => {
              const t = taskById(id);
              return t ? (
                <button key={id} className={`v06-pin ${id === selected ? "on" : ""}`} onClick={() => locate(id)}>
                  <Dot state={t.executionState} />
                  <span className="v06-id">{t.id}</span>
                  <span className="v06-pin-title">{t.title}</span>
                  <em>派生 {childrenOf(id).length}</em>
                  <X size={12} className="v06-pin-x" onClick={(e) => { e.stopPropagation(); setPinned((p) => p.filter((x) => x !== id)); }} />
                </button>
              ) : null;
            })}
          </div>
          <div className="v06-rail-sec">
            <h3>队列速览</h3>
            {kimiTasks.filter((t) => t.executionState === "运行" || t.executionState === "失败").map((t) => (
              <button key={t.id} className="v06-q-row" onClick={() => locate(t.id)}>
                <Dot state={t.executionState} /><span className="v06-id">{t.id}</span>
                <span className="v06-q-title">{t.title}</span><em>{t.agent}</em>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
