// THROWAWAY PROTOTYPE: twelve radically different future-facing UI concepts for Research World.
// Access at /prototype/deep-sea?variant=A .. L. Switch with bottom bar or ← / →.
import { ArrowLeft, ArrowRight, Activity, Atom, Beaker, BookOpen, Bot, Boxes, Braces, Bug,
  CheckCircle2, ChevronRight, Circle, Cpu, Database, FileCode2, FileText, GitBranch, Globe,
  Layers, LineChart, ListTree, Loader2, MessageSquare, Network, Play, Radar, Radio, Rocket,
  Search, Server, Settings2, Sparkles, Terminal, Users, Workflow, X, Zap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import "./deep-sea-design-prototype.css";


const VARIANTS = {
  A: "Abyss Glass",
  B: "ASCII Terminal",
  C: "Mission Control",
  D: "Blueprint",
  E: "Editorial Future",
  F: "Submarine HUD",
  G: "Neural Field",
  H: "Quantum Console",
  I: "Agent Deck",
  J: "Minimal Abyss",
  K: "Orbital Timeline",
  L: "Pixel Lab",
};


const PROJECTS = [
  { id: "q001", title: "素数分布中的特殊规律", question: "素数间隔是否存在可计算、可复现且可被反驳的结构？", nodes: 37, workflows: 12, updated: "2 分钟前", auto: true },
  { id: "q049", title: "行星轨道长期稳定性", question: "多体摄动下轨道要素的长期漂移是否可预测？", nodes: 24, workflows: 8, updated: "18 分钟前", auto: true },
  { id: "q089", title: "能量转换效率极限", question: "材料界面对热-电转换效率的损失机制如何量化？", nodes: 41, workflows: 15, updated: "1 小时前", auto: false },
];

const NODES = [
  { id: "Q-001", kind: "question", title: "素数分布中的特殊规律", status: "已入图", detail: "核心研究问题", parent: null, x: 8, y: 46, tone: "cyan" },
  { id: "D-001", kind: "direction", title: "素数间隔计数", status: "已支持", detail: "基础计数", parent: "Q-001", x: 24, y: 22, tone: "blue" },
  { id: "D-002", kind: "direction", title: "短区间素数密度", status: "运行中", detail: "基础计数", parent: "Q-001", x: 24, y: 46, tone: "blue" },
  { id: "D-003", kind: "direction", title: "相邻间隔相关性", status: "已支持", detail: "基础计数", parent: "Q-001", x: 24, y: 70, tone: "blue" },
  { id: "E-001", kind: "experiment", title: "间隔数据扫描", status: "完成", detail: "实验节点", parent: "D-001", x: 44, y: 12, tone: "green" },
  { id: "E-002", kind: "experiment", title: "密度基线对照", status: "运行中", detail: "实验节点", parent: "D-002", x: 44, y: 42, tone: "green" },
  { id: "R-001", kind: "review", title: "统计显著性审查", status: "排队", detail: "审查节点", parent: "D-003", x: 64, y: 72, tone: "amber" },
  { id: "R-002", kind: "review", title: "跨尺度复现审查", status: "运行中", detail: "审查节点", parent: "D-002", x: 64, y: 40, tone: "amber" },
];

const WORKFLOWS = [
  { id: "W-2041", name: "短区间素数密度 · 规划→执行→审查→反思", node: "D-002", status: "running", progress: 62, agent: "Qwen Researcher", started: "12:04" },
  { id: "W-2042", name: "间隔数据扫描 · 独立复核", node: "E-001", status: "queued", progress: 8, agent: "Claude Code", started: "12:09" },
  { id: "W-2043", name: "跨尺度复现审查 · 证据链检查", node: "R-002", status: "waiting", progress: 35, agent: "Pi", started: "11:58" },
];

const ACTIVITY = [
  { time: "12:11", actor: "orchestrator", text: "D-002 完成第 3 步，生成区间密度对照表", type: "run" },
  { time: "12:09", actor: "reviewer#1", text: "R-001 通过统计显著性阈值检查", type: "approve" },
  { time: "12:06", actor: "reviewer#2", text: "E-001 反例扫描未发现边界异常", type: "approve" },
  { time: "12:02", actor: "human", text: "人工确认 R-002 的跨尺度复现策略", type: "human" },
  { time: "11:58", actor: "orchestrator", text: "D-003 被支持，开始派生 R-001", type: "branch" },
];


function StatusPill({ status, small = false }) {
  const map = { "已入图": "ok", "已支持": "ok", "完成": "ok", "运行中": "run", "排队": "wait", "等待": "wait" };
  const cls = map[status] || "muted";
  return <span className={`ds-pill ds-pill-${cls} ${small ? "small" : ""}`}>{status}</span>;
}


function NodeIcon({ kind, size = 16 }) {
  const map = { question: Atom, direction: GitBranch, experiment: Beaker, review: ShieldCheck, source: BookOpen };
  const Icon = map[kind] || Atom;
  return <Icon size={size} />;
}


function ShieldCheck({ size = 16 }) {
  return <CheckCircle2 size={size} />;
}


function StateSurface({ variant, selected, view }) {
  const state = { variant: VARIANTS[variant], view, selected_node: selected, source: "mock data", persistence: "none" };
  return <details className="ds-state"><summary>Prototype state</summary><pre>{JSON.stringify(state, null, 2)}</pre></details>;
}


function VariantSwitcher({ variant, params, setParams }) {
  const move = (delta) => {
    const keys = Object.keys(VARIANTS);
    const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
    const updated = new URLSearchParams(params);
    updated.set("variant", next);
    setParams(updated, { replace: true });
  };
  return <div className="ds-switcher">
    <button onClick={() => move(-1)} title="上一个变体"><ArrowLeft size={16} /></button>
    <b>{variant} — {VARIANTS[variant]}</b>
    <button onClick={() => move(1)} title="下一个变体"><ArrowRight size={16} /></button>
  </div>;
}


function useVariantKeys(variant, params, setParams) {
  useEffect(() => {
    const handler = (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key) || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
      const keys = Object.keys(VARIANTS);
      const delta = event.key === "ArrowLeft" ? -1 : 1;
      const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
      const updated = new URLSearchParams(params);
      updated.set("variant", next);
      setParams(updated, { replace: true });
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [variant, params, setParams]);
}


export function DeepSeaDesignPrototype() {
  const [params, setParams] = useSearchParams();
  const variant = VARIANTS[params.get("variant")] ? params.get("variant") : "A";
  const [selected, setSelected] = useState("D-002");
  const [view, setView] = useState("map");
  useVariantKeys(variant, params, setParams);
  const props = { selected, setSelected, view, setView };
  return <section className={`deepsea-prototype variant-${variant.toLowerCase()}`}>
    {variant === "A" && <VariantA {...props} />}
    {variant === "B" && <VariantB {...props} />}
    {variant === "C" && <VariantC {...props} />}
    {variant === "D" && <VariantD {...props} />}
    {variant === "E" && <VariantE {...props} />}
    {variant === "F" && <VariantF {...props} />}
    {variant === "G" && <VariantG {...props} />}
    {variant === "H" && <VariantH {...props} />}
    {variant === "I" && <VariantI {...props} />}
    {variant === "J" && <VariantJ {...props} />}
    {variant === "K" && <VariantK {...props} />}
    {variant === "L" && <VariantL {...props} />}
    <StateSurface variant={variant} selected={selected} view={view} />
    <VariantSwitcher variant={variant} params={params} setParams={setParams} />
  </section>;
}


/* A — Abyss Glass: floating glass panels over a deep-sea gradient */
function VariantA({ selected, setSelected }) {
  const node = NODES.find((item) => item.id === selected) || NODES[0];
  return <div className="ds-a">
    <aside className="ds-a-side"><div className="ds-a-brand"><span className="ds-a-mark">研</span><div><b>RESEARCH WORLD</b><small>深海研究站</small></div></div>
      <nav>{["研究地图", "节点对话", "活动", "项目"].map((item, index) => <a className={index === 0 ? "active" : ""} key={item} href="#prototype">{index === 0 ? <Network size={16} /> : index === 1 ? <MessageSquare size={16} /> : index === 2 ? <Activity size={16} /> : <Boxes size={16} />}<span>{item}</span></a>)}</nav>
      <div className="ds-a-foot"><span className="live-dot" /> LIVE · 自动推进开启</div></aside>
    <div className="ds-a-main">
      <header className="ds-a-top"><div><b>素数分布中的特殊规律</b><span>Q-001 · 37 节点 · 12 工作流</span></div>
        <div className="ds-a-actions"><span className="ds-a-search"><Search size={14} />搜索图谱</span><button className="ds-a-btn"><Play size={14} />运行</button></div></header>
      <div className="ds-a-body">
        <div className="ds-a-canvas"><div className="ds-a-waves" /><div className="ds-a-grid" />
          {NODES.map((item) => <button key={item.id} className={`ds-a-node ${item.id === selected ? "selected" : ""}`} style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => setSelected(item.id)}>
            <span className={`ds-a-node-icon tone-${item.tone}`}><NodeIcon kind={item.kind} size={14} /></span><span><b>{item.title}</b><small>{item.id} · {item.detail}</small></span><StatusPill status={item.status} small /></button>)}
          <div className="ds-a-canvas-label"><span>DEEP SEA RESEARCH GRAPH</span><small>节点即证据，边即审查</small></div>
        </div>
        <aside className="ds-a-inspector"><div className="ds-a-inspector-head"><span>{node.kind}</span><b>{node.id}</b></div>
          <h2>{node.title}</h2><p>{node.detail} · {node.status}</p>
          <div className="ds-a-metrics"><div><b>2</b><span>依赖</span></div><div><b>3</b><span>证据</span></div><div><b>1</b><span>审查</span></div></div>
          <section><h3>审查意见</h3><div className="ds-a-review"><b>Reviewer #1</b><p>统计阈值通过，建议补充跨尺度复核。</p></div><div className="ds-a-review"><b>Reviewer #2</b><p>代码与随机种子完整，可复现。</p></div></section>
          <button className="ds-a-btn primary"><Zap size={15} />从此节点派生</button></aside>
      </div>
    </div>
  </div>;
}


/* B — ASCII Terminal: everything is text, pipes, and scanlines */
function VariantB({ selected, setSelected }) {
  const tree = `Q-001 素数分布
├─ D-001 素数间隔计数
│  ├─ E-001 间隔数据扫描 [完成]
│  └─ E-002 密度基线对照 [运行]
├─ D-002 短区间素数密度
│  └─ R-002 跨尺度复现审查 [运行]
└─ D-003 相邻间隔相关性
   └─ R-001 统计显著性审查 [排队]`;
  return <div className="ds-b">
    <header className="ds-b-top"><span className="ds-b-logo">RESEARCH://WORLD</span><span className="ds-b-path">/q001/prime-distribution</span><span className="ds-b-status">● LIVE</span></header>
    <div className="ds-b-body">
      <aside className="ds-b-side"><b>FILES</b><pre>{tree}</pre><div className="ds-b-meta">PROJECT: q001<br />NODES: 37<br />WORKFLOWS: 12<br />AUTO: ON</div></aside>
      <main className="ds-b-main"><div className="ds-b-banner">
<pre>{`
  ██████╗ ███████╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
  ██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
  ██████╔╝█████╗  ███████╗███████╗███████║██████╔╝██║     ███████║
  ██╔══██╗██╔══╝  ╚════██║╚════██║██╔══██║██╔══██╗██║     ██╔══██║
  ██║  ██║███████╗███████║███████║██║  ██║██║  ██║╚██████╗██║  ██║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
`}</pre></div>
        <div className="ds-b-split">
          <section className="ds-b-panel"><header>ACTIVE WORKFLOWS</header>{WORKFLOWS.map((item) => <button key={item.id} className={item.node === selected ? "active" : ""} onClick={() => setSelected(item.node)}><span className={`ds-b-status-dot ${item.status}`} />{item.name}<small>{item.agent} · {item.progress}%</small></button>)}</section>
          <section className="ds-b-panel"><header>LIVE TRACE</header><div className="ds-b-log">{ACTIVITY.map((item) => <p key={item.time}><i>[{item.time}]</i> <b>{item.actor}</b> {item.text}</p>)}</div></section>
        </div>
        <footer className="ds-b-command"><span>❯</span><input defaultValue="graph query --node D-002 --depth 2" aria-label="命令输入" /></footer>
      </main>
    </div>
    <div className="ds-b-scan" />
  </div>;
}


/* C — Mission Control: dense operations dashboard */
function VariantC({ selected, setSelected }) {
  return <div className="ds-c">
    <header className="ds-c-top"><div className="ds-c-logo"><Rocket size={18} /><b>RESEARCH MISSION CONTROL</b></div><div className="ds-c-clock">UTC+8 · 12:14:22</div><div className="ds-c-avatar">R</div></header>
    <div className="ds-c-metrics">
      <div><span>活跃节点</span><b>37</b><small>+3 本周</small></div>
      <div><span>进行中工作流</span><b>6</b><small>2 个等待人工</small></div>
      <div><span>自动推进</span><b>ON</b><small>预算 42%</small></div>
      <div><span>审查积压</span><b>4</b><small>最长等待 18m</small></div>
    </div>
    <div className="ds-c-body">
      <section className="ds-c-left"><header><h2>研究扇区</h2><span>按证据密度排序</span></header>
        <div className="ds-c-cards">{NODES.filter((item) => item.kind !== "question").map((item) => <button key={item.id} className={item.id === selected ? "active" : ""} onClick={() => setSelected(item.id)}><span className={`ds-c-orb tone-${item.tone}`} /><div><b>{item.title}</b><small>{item.id} · {item.status}</small></div><em>{item.parent}</em></button>)}</div>
        <div className="ds-c-queue"><header>工作流队列</header>{WORKFLOWS.map((item) => <div key={item.id}><span className={`ds-c-queue-dot ${item.status}`} /><div><b>{item.name}</b><small>{item.agent}</small></div><progress value={item.progress} max="100" /></div>)}</div>
      </section>
      <section className="ds-c-right"><header><h2>实时遥测</h2><span><Radio size={13} /> LIVE</span></header>
        <div className="ds-c-telemetry"><div className="ds-c-radar"><div className="ds-c-radar-sweep" /><i /><i /><i /><i /><b>D-002</b></div><div className="ds-c-chart"><div className="ds-c-bars">{Array.from({ length: 16 }, (_, i) => <i key={i} style={{ height: `${20 + ((i * 37) % 70)}%` }} />)}</div></div></div>
        <div className="ds-c-feed">{ACTIVITY.slice(0, 4).map((item) => <div key={item.time}><time>{item.time}</time><b>{item.actor}</b><span>{item.text}</span></div>)}</div>
      </section>
    </div>
  </div>;
}


/* D — Blueprint: schematic drawing of the research graph */
function VariantD({ selected, setSelected }) {
  return <div className="ds-d">
    <header className="ds-d-header"><div className="ds-d-title"><FileText size={18} /><b>RESEARCH BLUEPRINT</b><span>Q-001 · 素数分布</span></div><div className="ds-d-scale">SCALE 1:1 · GRID 24px</div></header>
    <div className="ds-d-body">
      <aside className="ds-d-legend"><h3>图例</h3><div><span className="ds-d-line lineage" />谱系</div><div><span className="ds-d-line supports" />支持</div><div><span className="ds-d-line refutes" />反驳</div><div><span className="ds-d-box pending" />待审</div><div><span className="ds-d-box ghost" />幽灵</div></aside>
      <main className="ds-d-sheet">
        {NODES.map((item) => <button key={item.id} className={`ds-d-node ${item.id === selected ? "selected" : ""}`} style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => setSelected(item.id)}>
          <span className="ds-d-id">{item.id}</span><b>{item.title}</b><small>{item.detail}</small><span className="ds-d-dim">{item.x * 8}.0 × {item.y * 8}.0</span></button>)}
        <div className="ds-d-connector c1" /><div className="ds-d-connector c2" /><div className="ds-d-connector c3" /><div className="ds-d-note">NOTE: 所有节点必须携带可复现执行凭据</div>
      </main>
      <aside className="ds-d-spec"><h3>节点规格</h3><dl><dt>ID</dt><dd>D-002</dd><dt>KIND</dt><dd>DIRECTION</dd><dt>STATUS</dt><dd>RUNNING</dd><dt>REVIEW</dt><dd>2/2</dd><dt>TRACE</dt><dd>14 STEPS</dd><dt>ARTIFACTS</dt><dd>6 FILES</dd></dl><div className="ds-d-stamp">APPROVED<br />FOR RESEARCH</div></aside>
    </div>
  </div>;
}


/* E — Editorial Future: magazine-like landing for a research world */
function VariantE({ selected, setSelected }) {
  return <div className="ds-e">
    <header className="ds-e-nav"><div className="ds-e-brand"><Sparkles size={16} /> RESEARCH/WORLD</div><nav><a href="#prototype">图谱</a><a href="#prototype">对话</a><a href="#prototype">活动</a><a href="#prototype">项目</a></nav><button className="ds-e-cta">进入研究站</button></header>
    <main className="ds-e-main">
      <section className="ds-e-hero"><span className="ds-e-kicker">A FUTURE FOR SCIENTIFIC AGENTS</span><h1>在深海般的图谱中，<br />让每一个判断都可被反驳。</h1><p>Research World 把多智能体的规划、实验、审查与反思沉淀为一张可追溯的研究图谱。</p><div className="ds-e-hero-actions"><button className="ds-e-primary">打开研究地图</button><button className="ds-e-ghost">观看 90 秒演示</button></div></section>
      <section className="ds-e-projects"><header><h2>研究项目</h2><span>125 个科学问题正在生长</span></header>{PROJECTS.map((project) => <button key={project.id} className={project.id === "q001" ? "featured" : ""} onClick={() => setSelected("Q-001")}><span className="ds-e-index">0{PROJECTS.indexOf(project) + 1}</span><div><b>{project.title}</b><small>{project.question}</small></div><div className="ds-e-meta"><span>{project.nodes} 节点</span><span>{project.workflows} 工作流</span><span>{project.updated}</span></div><ChevronRight size={18} /></button>)}</section>
      <section className="ds-e-quote"><blockquote>“好的科研界面不是让人读完所有记录，而是让人在 30 秒内知道该质疑什么。”</blockquote><cite>— 设计原则</cite></section>
    </main>
  </div>;
}


/* F — Submarine HUD: periscope-style operational console */
function VariantF({ selected, setSelected }) {
  const node = NODES.find((item) => item.id === selected) || NODES[1];
  return <div className="ds-f">
    <header className="ds-f-top"><div className="ds-f-brand"><Radar size={18} /><b>SUB-RESEARCH // HUD</b></div><div><span className="ds-f-depth">DEPTH -420m</span><span className="ds-f-pressure">2.4 ATM</span></div></header>
    <div className="ds-f-body">
      <section className="ds-f-radar-panel"><div className="ds-f-radar"><div className="ds-f-ring r1" /><div className="ds-f-ring r2" /><div className="ds-f-ring r3" /><div className="ds-f-cross" /><div className="ds-f-blip b1" /><div className="ds-f-blip b2" /><div className="ds-f-blip b3" /><b>Q-001</b></div><div className="ds-f-readout"><span>SONAR: 8 CONTACTS</span><span>BEARING 042°</span><span>RANGE 3.2km</span></div></section>
      <section className="ds-f-console"><header><h2>{node.id} · {node.title}</h2><StatusPill status={node.status} /></header>
        <div className="ds-f-gauges"><div><span>信任度</span><b>82%</b><i style={{ width: "82%" }} /></div><div><span>可复现</span><b>94%</b><i style={{ width: "94%" }} /></div><div><span>审查冲突</span><b>1</b><i style={{ width: "12%" }} /></div></div>
        <div className="ds-f-log">{ACTIVITY.map((item) => <p key={item.time}><i>{item.time}</i><b>{item.actor}</b>{item.text}</p>)}</div>
        <div className="ds-f-controls"><button className="ds-f-btn primary"><Play size={14} />发射工作流</button><button className="ds-f-btn"><Settings2 size={14} />调整装配</button><button className="ds-f-btn"><Bug size={14} />人工裁决</button></div>
      </section>
      <aside className="ds-f-side"><div className="ds-f-compass"><N /><E /><S /><W /><div /></div><div className="ds-f-sonar-list">{NODES.slice(1, 6).map((item) => <button key={item.id} className={item.id === selected ? "active" : ""} onClick={() => setSelected(item.id)}><i className={`tone-${item.tone}`} />{item.id}<span>{item.status}</span></button>)}</div></aside>
    </div>
  </div>;
}


/* G — Neural Field: immersive glowing graph */
function VariantG({ selected, setSelected }) {
  return <div className="ds-g">
    <div className="ds-g-stars" />
    <header className="ds-g-top"><div className="ds-g-brand"><Atom size={17} /> NEURAL FIELD</div><div className="ds-g-coord">X 0.42 · Y 0.78 · Z 12</div><button className="ds-g-btn">聚焦 D-002</button></div>
    <main className="ds-g-main">
      {NODES.map((item) => <button key={item.id} className={`ds-g-node ${item.id === selected ? "selected" : ""}`} style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => setSelected(item.id)}><span className={`ds-g-core tone-${item.tone}`} /><b>{item.id}</b><small>{item.title}</small></button>)}
      <div className="ds-g-connector g1" /><div className="ds-g-connector g2" /><div className="ds-g-connector g3" />
      <div className="ds-g-focus">D-002 · 短区间素数密度<br /><small>正在运行 · 3 条证据 · 2 个审查</small></div>
    </main>
    <footer className="ds-g-foot"><span>拖拽探索</span><span>滚轮缩放</span><span>点击节点查看证据</span></footer>
  </div>;
}


/* H — Quantum Console: developer IDE for research authoring */
function VariantH({ selected, setSelected }) {
  const node = NODES.find((item) => item.id === selected) || NODES[1];
  return <div className="ds-h">
    <header className="ds-h-titlebar"><span className="ds-h-dot red" /><span className="ds-h-dot yellow" /><span className="ds-h-dot green" /><b>research-world — q001</b><span className="ds-h-right"><Terminal size={14} /> Console</span></header>
    <div className="ds-h-body">
      <aside className="ds-h-side"><header>EXPLORER</header><div className="ds-h-tree"><details open><summary>Q-001</summary><button className={node.id === "D-001" ? "active" : ""} onClick={() => setSelected("D-001")}>D-001 素数间隔计数</button><button className={node.id === "D-002" ? "active" : ""} onClick={() => setSelected("D-002")}>D-002 短区间素数密度</button><button className={node.id === "D-003" ? "active" : ""} onClick={() => setSelected("D-003")}>D-003 相邻间隔相关性</button></details><details><summary>experiments</summary><button className={node.id === "E-001" ? "active" : ""} onClick={() => setSelected("E-001")}>E-001 数据扫描</button><button className={node.id === "E-002" ? "active" : ""} onClick={() => setSelected("E-002")}>E-002 基线对照</button></details></div></aside>
      <main className="ds-h-editor"><div className="ds-h-tabs"><span className="active"><FileCode2 size={13} /> direction.md</span><span><Braces size={13} /> workflow.json</span><span><Terminal size={13} /> trace.log</span></div>
        <div className="ds-h-code"><pre>{`# ${node.title}
> ${node.detail}

## 目标
形成可引用、可复现、可反驳的局部判断。

## 状态
- life_state: ${node.status}
- direction: proposed
- reviewers: 2/2
- artifacts: sha256:9f2c…e1

## 下一步
- [x] 数值扫描
- [x] 独立复核
- [ ] 人工确认跨尺度策略
`}</pre></div>
        <div className="ds-h-terminal"><span>❯</span><input defaultValue={`research run --node ${node.id} --plan`} aria-label="命令" /></div>
      </main>
      <aside className="ds-h-inspector"><header>INSPECTOR</header><div className="ds-h-meta"><span>ID</span><b>{node.id}</b><span>KIND</span><b>{node.kind}</b><span>PARENT</span><b>{node.parent || "—"}</b><span>STATUS</span><b>{node.status}</b></div><section><h3>执行凭据</h3><pre>{`image: qwen-research:latest
seed: 20260821
cpus: 4
memory: 8Gi
pids: 256`}</pre></section><button className="ds-h-run"><Play size={13} /> Run Workflow</button></aside>
    </div>
    <footer className="ds-h-status"><span>⎇ refactor/acp-runtime</span><span>0 errors · 0 warnings</span><span>Qwen Researcher</span><span>UTF-8 · LF</span></footer>
  </div>;
}


/* I — Agent Deck: multiple agents, live channels, decisions */
function VariantI({ selected, setSelected }) {
  return <div className="ds-i">
    <header className="ds-i-top"><div className="ds-i-brand"><Bot size={18} /><b>AGENT DECK</b></div><div className="ds-i-live"><Radio size={13} /> 3 agents online</div></header>
    <div className="ds-i-body">
      <aside className="ds-i-agents">{["Orchestrator", "Qwen Researcher", "Claude Code", "Pi Reviewer"].map((name, index) => <button key={name} className={index === 1 ? "active" : ""}><span className="ds-i-avatar">{name[0]}</span><div><b>{name}</b><small>{index === 1 ? "running" : index === 3 ? "reviewing" : "idle"}</small></div><i className={index === 1 ? "run" : index === 3 ? "wait" : ""} /></button>)}</aside>
      <main className="ds-i-stream"><header><h2>事件流</h2><span>append-only · 可审计</span></header>{ACTIVITY.map((item) => <article key={item.time} className={`type-${item.type}`}><time>{item.time}</time><b>{item.actor}</b><p>{item.text}</p><span className="ds-i-hash">#{item.time.replace(":", "")}f3a</span></article>)}</main>
      <section className="ds-i-graph"><header><Network size={14} /> 实时图谱</header><div className="ds-i-mini">{NODES.map((item) => <button key={item.id} className={item.id === selected ? "active" : ""} style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => setSelected(item.id)}><i className={`tone-${item.tone}`} />{item.id}</button>)}<div className="ds-i-link l1" /><div className="ds-i-link l2" /></div>
        <div className="ds-i-decide"><b>待人工裁决</b><p>R-002 跨尺度复现策略：两个审查员分歧</p><div><button>支持</button><button>驳回</button></div></div>
      </section>
    </div>
  </div>;
}


/* J — Minimal Abyss: almost nothing, maximum focus */
function VariantJ({ selected, setSelected }) {
  const node = NODES.find((item) => item.id === selected) || NODES[0];
  return <div className="ds-j">
    <header className="ds-j-top"><span>RESEARCH WORLD</span><span>Q-001</span><span className="ds-j-live">LIVE</span></header>
    <main className="ds-j-main">
      <div className="ds-j-orb" />
      <div className="ds-j-title"><h1>{node.title}</h1><p>{node.detail}</p></div>
      <div className="ds-j-list">{NODES.map((item) => <button key={item.id} className={item.id === selected ? "active" : ""} onClick={() => setSelected(item.id)}><span>{item.id}</span><b>{item.title}</b><em>{item.status}</em></button>)}</div>
      <footer className="ds-j-foot"><span>37 nodes</span><span>12 workflows</span><span>4 reviews</span></footer>
    </main>
  </div>;
}


/* K — Orbital Timeline: radial lineage and temporal orbit */
function VariantK({ selected, setSelected }) {
  return <div className="ds-k">
    <header className="ds-k-top"><div className="ds-k-brand"><Globe size={17} /> ORBITAL RESEARCH</div><div className="ds-k-mode"><span>谱系视图</span><span className="active">轨道视图</span><span>时间视图</span></div></header>
    <div className="ds-k-body">
      <div className="ds-k-orbit">
        <div className="ds-k-ring r1" /><div className="ds-k-ring r2" /><div className="ds-k-ring r3" />
        <button className="ds-k-core" onClick={() => setSelected("Q-001")}><Atom size={20} /><b>Q-001</b></button>
        {NODES.slice(1, 7).map((item, index) => <button key={item.id} className={`ds-k-satellite ${item.id === selected ? "active" : ""}`} style={{ "--angle": `${index * 52}deg`, "--delay": `${index * 0.4}s` }} onClick={() => setSelected(item.id)}><span>{item.id}</span><b>{item.title}</b></button>)}
      </div>
      <aside className="ds-k-timeline"><header>时间轴</header>{ACTIVITY.map((item) => <div key={item.time}><time>{item.time}</time><p>{item.text}</p><span>{item.actor}</span></div>)}</aside>
    </div>
    <footer className="ds-k-foot"><span>当前轨道周期 42m</span><span>下一事件 12:18</span><span>人工介入 1</span></footer>
  </div>;
}


/* L — Pixel Lab: retro pixel aesthetics fused with glass depth */
function VariantL({ selected, setSelected }) {
  return <div className="ds-l">
    <header className="ds-l-top"><span className="ds-l-pixel-logo">R/W</span><b>PIXEL RESEARCH LAB</b><span className="ds-l-score">SCORE 12,480</span></header>
    <div className="ds-l-body">
      <aside className="ds-l-side"><button className="active">MAP</button><button>CHAT</button><button>LAB</button><button>LOG</button></aside>
      <main className="ds-l-main">
        <div className="ds-l-hud"><span>HP ▮▮▮▮▮▮▮▮</span><span>ENERGY ▮▮▮▮▮▮▮▯</span><span>REVIEW ▮▮▮▮▯▯▯▯</span></div>
        <div className="ds-l-grid">{NODES.map((item) => <button key={item.id} className={`ds-l-node ${item.id === selected ? "active" : ""}`} onClick={() => setSelected(item.id)}><span className={`ds-l-sprite tone-${item.tone}`}><NodeIcon kind={item.kind} size={14} /></span><b>{item.title}</b><small>{item.id}</small></button>)}</div>
        <div className="ds-l-actions"><button><Play size={13} /> RUN</button><button><Database size={13} /> SAVE</button><button><Users size={13} /> REVIEW</button></div>
      </main>
      <aside className="ds-l-sidebar"><h3>QUEST LOG</h3>{ACTIVITY.slice(0, 4).map((item) => <div key={item.time}><i>■</i><span>{item.text}</span></div>)}<div className="ds-l-boss"><span>BOSS</span><b>R-002</b><progress value="35" max="100" /></div></aside>
    </div>
    <footer className="ds-l-foot">INSERT COIN · 2026 RESEARCH WORLD · 1UP</footer>
  </div>;
}
