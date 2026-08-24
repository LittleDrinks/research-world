from pathlib import Path
import shutil

ROOT = Path(__file__).parent
CSS = (ROOT / "react/deep-sea-design-prototype.css").read_text()


def page(title, body):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="deepsea-prototype">
{body}
</div>
</body>
</html>
"""


variants = {}

variants["01-abyss-glass"] = page(
    "01 · Abyss Glass — Research World 视觉原型",
    """
<div class="ds-a">
  <aside class="ds-a-side">
    <div class="ds-a-brand"><span class="ds-a-mark">研</span><div><b>RESEARCH WORLD</b><small>深海研究站</small></div></div>
    <nav>
      <a class="active" href="#"><span class="ds-a-nav-icon">◈</span><span>研究地图</span></a>
      <a href="#"><span class="ds-a-nav-icon">✉</span><span>节点对话</span></a>
      <a href="#"><span class="ds-a-nav-icon">≋</span><span>活动</span></a>
      <a href="#"><span class="ds-a-nav-icon">▣</span><span>项目</span></a>
    </nav>
    <div class="ds-a-foot"><span class="live-dot"></span> LIVE · 自动推进开启</div>
  </aside>
  <div class="ds-a-main">
    <header class="ds-a-top">
      <div><b>素数分布中的特殊规律</b><span>Q-001 · 37 节点 · 12 工作流</span></div>
      <div class="ds-a-actions"><span class="ds-a-search">⌕ 搜索图谱</span><button class="ds-a-btn">▶ 运行</button></div>
    </header>
    <div class="ds-a-body">
      <div class="ds-a-canvas">
        <div class="ds-a-waves"></div><div class="ds-a-grid"></div>
        <button class="ds-a-node selected" style="left:8%;top:46%"><span class="ds-a-node-icon tone-cyan">◈</span><span><b>素数分布中的特殊规律</b><small>Q-001 · 核心研究问题</small></span><span class="ds-pill ds-pill-ok small">已入图</span></button>
        <button class="ds-a-node" style="left:24%;top:22%"><span class="ds-a-node-icon tone-blue">⌥</span><span><b>素数间隔计数</b><small>D-001 · 基础计数</small></span><span class="ds-pill ds-pill-ok small">已支持</span></button>
        <button class="ds-a-node" style="left:24%;top:46%"><span class="ds-a-node-icon tone-blue">⌥</span><span><b>短区间素数密度</b><small>D-002 · 基础计数</small></span><span class="ds-pill ds-pill-run small">运行中</span></button>
        <button class="ds-a-node" style="left:24%;top:70%"><span class="ds-a-node-icon tone-blue">⌥</span><span><b>相邻间隔相关性</b><small>D-003 · 基础计数</small></span><span class="ds-pill ds-pill-ok small">已支持</span></button>
        <button class="ds-a-node" style="left:44%;top:12%"><span class="ds-a-node-icon tone-green">⚗</span><span><b>间隔数据扫描</b><small>E-001 · 实验节点</small></span><span class="ds-pill ds-pill-ok small">完成</span></button>
        <button class="ds-a-node" style="left:44%;top:42%"><span class="ds-a-node-icon tone-green">⚗</span><span><b>密度基线对照</b><small>E-002 · 实验节点</small></span><span class="ds-pill ds-pill-run small">运行中</span></button>
        <button class="ds-a-node" style="left:64%;top:72%"><span class="ds-a-node-icon tone-amber">✓</span><span><b>统计显著性审查</b><small>R-001 · 审查节点</small></span><span class="ds-pill ds-pill-wait small">排队</span></button>
        <button class="ds-a-node" style="left:64%;top:40%"><span class="ds-a-node-icon tone-amber">✓</span><span><b>跨尺度复现审查</b><small>R-002 · 审查节点</small></span><span class="ds-pill ds-pill-run small">运行中</span></button>
        <div class="ds-a-canvas-label"><span>DEEP SEA RESEARCH GRAPH</span><small>节点即证据，边即审查</small></div>
      </div>
      <aside class="ds-a-inspector">
        <div class="ds-a-inspector-head"><span>direction</span><b>D-002</b></div>
        <h2>短区间素数密度</h2><p>基础计数 · 运行中</p>
        <div class="ds-a-metrics"><div><b>2</b><span>依赖</span></div><div><b>3</b><span>证据</span></div><div><b>1</b><span>审查</span></div></div>
        <section><h3>审查意见</h3>
          <div class="ds-a-review"><b>Reviewer #1</b><p>统计阈值通过，建议补充跨尺度复核。</p></div>
          <div class="ds-a-review"><b>Reviewer #2</b><p>代码与随机种子完整，可复现。</p></div>
        </section>
        <button class="ds-a-btn primary">⚡ 从此节点派生</button>
      </aside>
    </div>
  </div>
</div>
""",
)

variants["02-ascii-terminal"] = page(
    "02 · ASCII Terminal — Research World 视觉原型",
    """
<div class="ds-b">
  <header class="ds-b-top"><span class="ds-b-logo">RESEARCH://WORLD</span><span class="ds-b-path">/q001/prime-distribution</span><span class="ds-b-status">● LIVE</span></header>
  <div class="ds-b-body">
    <aside class="ds-b-side"><b>FILES</b><pre>Q-001 素数分布
├─ D-001 素数间隔计数
│  ├─ E-001 间隔数据扫描 [完成]
│  └─ E-002 密度基线对照 [运行]
├─ D-002 短区间素数密度
│  └─ R-002 跨尺度复现审查 [运行]
└─ D-003 相邻间隔相关性
   └─ R-001 统计显著性审查 [排队]</pre><div class="ds-b-meta">PROJECT: q001<br />NODES: 37<br />WORKFLOWS: 12<br />AUTO: ON</div></aside>
    <main class="ds-b-main">
      <div class="ds-b-banner"><pre>
  ██████╗ ███████╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
  ██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
  ██████╔╝█████╗  ███████╗███████╗███████║██████╔╝██║     ███████║
  ██╔══██╗██╔══╝  ╚════██║╚════██║██╔══██║██╔══██╗██║     ██╔══██║
  ██║  ██║███████╗███████║███████║██║  ██║██║  ██║╚██████╗██║  ██║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
      </pre></div>
      <div class="ds-b-split">
        <section class="ds-b-panel"><header>ACTIVE WORKFLOWS</header>
          <button class="active"><span class="ds-b-status-dot running"></span>短区间素数密度 · 规划→执行→审查→反思<small>Qwen Researcher · 62%</small></button>
          <button><span class="ds-b-status-dot queued"></span>间隔数据扫描 · 独立复核<small>Claude Code · 8%</small></button>
          <button><span class="ds-b-status-dot waiting"></span>跨尺度复现审查 · 证据链检查<small>Pi · 35%</small></button>
        </section>
        <section class="ds-b-panel"><header>LIVE TRACE</header><div class="ds-b-log">
          <p><i>[12:11]</i> <b>orchestrator</b> D-002 完成第 3 步，生成区间密度对照表</p>
          <p><i>[12:09]</i> <b>reviewer#1</b> R-001 通过统计显著性阈值检查</p>
          <p><i>[12:06]</i> <b>reviewer#2</b> E-001 反例扫描未发现边界异常</p>
          <p><i>[12:02]</i> <b>human</b> 人工确认 R-002 的跨尺度复现策略</p>
        </div></section>
      </div>
      <footer class="ds-b-command"><span>❯</span><input value="graph query --node D-002 --depth 2" aria-label="命令输入" /></footer>
    </main>
  </div>
  <div class="ds-b-scan"></div>
</div>
""",
)

variants["03-mission-control"] = page(
    "03 · Mission Control — Research World 视觉原型",
    """
<div class="ds-c">
  <header class="ds-c-top"><div class="ds-c-logo">🚀 RESEARCH MISSION CONTROL</div><div class="ds-c-clock">UTC+8 · 12:14:22</div><div class="ds-c-avatar">R</div></header>
  <div class="ds-c-metrics">
    <div><span>活跃节点</span><b>37</b><small>+3 本周</small></div>
    <div><span>进行中工作流</span><b>6</b><small>2 个等待人工</small></div>
    <div><span>自动推进</span><b>ON</b><small>预算 42%</small></div>
    <div><span>审查积压</span><b>4</b><small>最长等待 18m</small></div>
  </div>
  <div class="ds-c-body">
    <section class="ds-c-left">
      <header><h2>研究扇区</h2><span>按证据密度排序</span></header>
      <div class="ds-c-cards">
        <button class="active"><span class="ds-c-orb tone-cyan"></span><div><b>短区间素数密度</b><small>D-002 · 运行中</small></div><em>Q-001</em></button>
        <button><span class="ds-c-orb tone-blue"></span><div><b>素数间隔计数</b><small>D-001 · 已支持</small></div><em>Q-001</em></button>
        <button><span class="ds-c-orb tone-green"></span><div><b>间隔数据扫描</b><small>E-001 · 完成</small></div><em>D-001</em></button>
        <button><span class="ds-c-orb tone-amber"></span><div><b>跨尺度复现审查</b><small>R-002 · 运行中</small></div><em>D-002</em></button>
      </div>
      <div class="ds-c-queue"><header>工作流队列</header>
        <div><span class="ds-c-queue-dot running"></span><div><b>短区间素数密度 · 规划→执行→审查→反思</b><small>Qwen Researcher</small></div><progress value="62" max="100"></progress></div>
        <div><span class="ds-c-queue-dot queued"></span><div><b>间隔数据扫描 · 独立复核</b><small>Claude Code</small></div><progress value="8" max="100"></progress></div>
        <div><span class="ds-c-queue-dot waiting"></span><div><b>跨尺度复现审查 · 证据链检查</b><small>Pi</small></div><progress value="35" max="100"></progress></div>
      </div>
    </section>
    <section class="ds-c-right">
      <header><h2>实时遥测</h2><span>📡 LIVE</span></header>
      <div class="ds-c-telemetry">
        <div class="ds-c-radar"><div class="ds-c-radar-sweep"></div><i></i><i></i><i></i><i></i><b>D-002</b></div>
        <div class="ds-c-chart"><div class="ds-c-bars"><i style="height:22%"></i><i style="height:45%"></i><i style="height:38%"></i><i style="height:62%"></i><i style="height:55%"></i><i style="height:80%"></i><i style="height:70%"></i><i style="height:92%"></i><i style="height:58%"></i><i style="height:66%"></i><i style="height:74%"></i><i style="height:88%"></i><i style="height:50%"></i><i style="height:63%"></i><i style="height:42%"></i><i style="height:35%"></i></div></div>
      </div>
      <div class="ds-c-feed">
        <div><time>12:11</time><b>orchestrator</b><span>D-002 完成第 3 步，生成区间密度对照表</span></div>
        <div><time>12:09</time><b>reviewer#1</b><span>R-001 通过统计显著性阈值检查</span></div>
        <div><time>12:06</time><b>reviewer#2</b><span>E-001 反例扫描未发现边界异常</span></div>
        <div><time>12:02</time><b>human</b><span>人工确认 R-002 的跨尺度复现策略</span></div>
      </div>
    </section>
  </div>
</div>
""",
)

variants["04-blueprint"] = page(
    "04 · Blueprint — Research World 视觉原型",
    """
<div class="ds-d">
  <header class="ds-d-header"><div class="ds-d-title">📐 RESEARCH BLUEPRINT <span>Q-001 · 素数分布</span></div><div class="ds-d-scale">SCALE 1:1 · GRID 24px</div></header>
  <div class="ds-d-body">
    <aside class="ds-d-legend"><h3>图例</h3>
      <div><span class="ds-d-line lineage"></span>谱系</div>
      <div><span class="ds-d-line supports"></span>支持</div>
      <div><span class="ds-d-line refutes"></span>反驳</div>
      <div><span class="ds-d-box pending"></span>待审</div>
      <div><span class="ds-d-box ghost"></span>幽灵</div>
    </aside>
    <main class="ds-d-sheet">
      <button class="ds-d-node selected" style="left:8%;top:46%"><span class="ds-d-id">Q-001</span><b>素数分布中的特殊规律</b><small>核心研究问题</small><span class="ds-d-dim">64.0 × 368.0</span></button>
      <button class="ds-d-node" style="left:24%;top:22%"><span class="ds-d-id">D-001</span><b>素数间隔计数</b><small>基础计数</small><span class="ds-d-dim">192.0 × 176.0</span></button>
      <button class="ds-d-node" style="left:24%;top:46%"><span class="ds-d-id">D-002</span><b>短区间素数密度</b><small>基础计数</small><span class="ds-d-dim">192.0 × 368.0</span></button>
      <button class="ds-d-node" style="left:24%;top:70%"><span class="ds-d-id">D-003</span><b>相邻间隔相关性</b><small>基础计数</small><span class="ds-d-dim">192.0 × 560.0</span></button>
      <button class="ds-d-node" style="left:44%;top:12%"><span class="ds-d-id">E-001</span><b>间隔数据扫描</b><small>实验节点</small><span class="ds-d-dim">352.0 × 96.0</span></button>
      <button class="ds-d-node" style="left:44%;top:42%"><span class="ds-d-id">E-002</span><b>密度基线对照</b><small>实验节点</small><span class="ds-d-dim">352.0 × 336.0</span></button>
      <button class="ds-d-node" style="left:64%;top:72%"><span class="ds-d-id">R-001</span><b>统计显著性审查</b><small>审查节点</small><span class="ds-d-dim">512.0 × 576.0</span></button>
      <button class="ds-d-node" style="left:64%;top:40%"><span class="ds-d-id">R-002</span><b>跨尺度复现审查</b><small>审查节点</small><span class="ds-d-dim">512.0 × 320.0</span></button>
      <div class="ds-d-connector c1"></div><div class="ds-d-connector c2"></div><div class="ds-d-connector c3"></div>
      <div class="ds-d-note">NOTE: 所有节点必须携带可复现执行凭据</div>
    </main>
    <aside class="ds-d-spec"><h3>节点规格</h3><dl>
      <dt>ID</dt><dd>D-002</dd><dt>KIND</dt><dd>DIRECTION</dd><dt>STATUS</dt><dd>RUNNING</dd><dt>REVIEW</dt><dd>2/2</dd><dt>TRACE</dt><dd>14 STEPS</dd><dt>ARTIFACTS</dt><dd>6 FILES</dd>
    </dl><div class="ds-d-stamp">APPROVED<br />FOR RESEARCH</div></aside>
  </div>
</div>
""",
)

variants["05-editorial-future"] = page(
    "05 · Editorial Future — Research World 视觉原型",
    """
<div class="ds-e">
  <header class="ds-e-nav"><div class="ds-e-brand">✦ RESEARCH/WORLD</div><nav><a href="#">图谱</a><a href="#">对话</a><a href="#">活动</a><a href="#">项目</a></nav><button class="ds-e-cta">进入研究站</button></header>
  <main class="ds-e-main">
    <section class="ds-e-hero"><span class="ds-e-kicker">A FUTURE FOR SCIENTIFIC AGENTS</span>
      <h1>在深海般的图谱中，<br />让每一个判断都可被反驳。</h1>
      <p>Research World 把多智能体的规划、实验、审查与反思沉淀为一张可追溯的研究图谱。</p>
      <div class="ds-e-hero-actions"><button class="ds-e-primary">打开研究地图</button><button class="ds-e-ghost">观看 90 秒演示</button></div>
    </section>
    <section class="ds-e-projects"><header><h2>研究项目</h2><span>125 个科学问题正在生长</span></header>
      <button class="featured"><span class="ds-e-index">01</span><div><b>素数分布中的特殊规律</b><small>素数间隔是否存在可计算、可复现且可被反驳的结构？</small></div><div class="ds-e-meta"><span>37 节点</span><span>12 工作流</span><span>2 分钟前</span></div><span>›</span></button>
      <button><span class="ds-e-index">02</span><div><b>行星轨道长期稳定性</b><small>多体摄动下轨道要素的长期漂移是否可预测？</small></div><div class="ds-e-meta"><span>24 节点</span><span>8 工作流</span><span>18 分钟前</span></div><span>›</span></button>
      <button><span class="ds-e-index">03</span><div><b>能量转换效率极限</b><small>材料界面对热-电转换效率的损失机制如何量化？</small></div><div class="ds-e-meta"><span>41 节点</span><span>15 工作流</span><span>1 小时前</span></div><span>›</span></button>
    </section>
    <section class="ds-e-quote"><blockquote>“好的科研界面不是让人读完所有记录，而是让人在 30 秒内知道该质疑什么。”</blockquote><cite>— 设计原则</cite></section>
  </main>
</div>
""",
)

variants["06-submarine-hud"] = page(
    "06 · Submarine HUD — Research World 视觉原型",
    """
<div class="ds-f">
  <header class="ds-f-top"><div class="ds-f-brand">📡 SUB-RESEARCH // HUD</div><div><span class="ds-f-depth">DEPTH -420m</span><span class="ds-f-pressure">2.4 ATM</span></div></header>
  <div class="ds-f-body">
    <section class="ds-f-radar-panel">
      <div class="ds-f-radar"><div class="ds-f-ring r1"></div><div class="ds-f-ring r2"></div><div class="ds-f-ring r3"></div><div class="ds-f-cross"></div><div class="ds-f-blip b1"></div><div class="ds-f-blip b2"></div><div class="ds-f-blip b3"></div><b>Q-001</b></div>
      <div class="ds-f-readout"><span>SONAR: 8 CONTACTS</span><span>BEARING 042°</span><span>RANGE 3.2km</span></div>
    </section>
    <section class="ds-f-console">
      <header><h2>D-002 · 短区间素数密度</h2><span class="ds-pill ds-pill-run">运行中</span></header>
      <div class="ds-f-gauges">
        <div><span>信任度</span><b>82%</b><i></i></div>
        <div><span>可复现</span><b>94%</b><i></i></div>
        <div><span>审查冲突</span><b>1</b><i></i></div>
      </div>
      <div class="ds-f-log">
        <p><i>12:11</i><b>orchestrator</b>D-002 完成第 3 步，生成区间密度对照表</p>
        <p><i>12:09</i><b>reviewer#1</b>R-001 通过统计显著性阈值检查</p>
        <p><i>12:06</i><b>reviewer#2</b>E-001 反例扫描未发现边界异常</p>
        <p><i>12:02</i><b>human</b>人工确认 R-002 的跨尺度复现策略</p>
      </div>
      <div class="ds-f-controls"><button class="ds-f-btn primary">▶ 发射工作流</button><button class="ds-f-btn">⚙ 调整装配</button><button class="ds-f-btn">🐞 人工裁决</button></div>
    </section>
    <aside class="ds-f-side">
      <div class="ds-f-compass"><span>N</span><span>E</span><span>S</span><span>W</span><div></div></div>
      <div class="ds-f-sonar-list">
        <button class="active"><i class="tone-cyan"></i>D-002<span>运行中</span></button>
        <button><i class="tone-blue"></i>D-001<span>已支持</span></button>
        <button><i class="tone-green"></i>E-001<span>完成</span></button>
        <button><i class="tone-amber"></i>R-002<span>运行中</span></button>
      </div>
    </aside>
  </div>
</div>
""",
)

variants["07-neural-field"] = page(
    "07 · Neural Field — Research World 视觉原型",
    """
<div class="ds-g">
  <div class="ds-g-stars"></div>
  <header class="ds-g-top"><div class="ds-g-brand">⚛ NEURAL FIELD</div><div class="ds-g-coord">X 0.42 · Y 0.78 · Z 12</div><button class="ds-g-btn">聚焦 D-002</button></header>
  <main class="ds-g-main">
    <button class="ds-g-node selected" style="left:8%;top:46%"><span class="ds-g-core tone-cyan"></span><b>Q-001</b><small>素数分布中的特殊规律</small></button>
    <button class="ds-g-node" style="left:24%;top:22%"><span class="ds-g-core tone-blue"></span><b>D-001</b><small>素数间隔计数</small></button>
    <button class="ds-g-node" style="left:24%;top:46%"><span class="ds-g-core tone-blue"></span><b>D-002</b><small>短区间素数密度</small></button>
    <button class="ds-g-node" style="left:24%;top:70%"><span class="ds-g-core tone-blue"></span><b>D-003</b><small>相邻间隔相关性</small></button>
    <button class="ds-g-node" style="left:44%;top:12%"><span class="ds-g-core tone-green"></span><b>E-001</b><small>间隔数据扫描</small></button>
    <button class="ds-g-node" style="left:44%;top:42%"><span class="ds-g-core tone-green"></span><b>E-002</b><small>密度基线对照</small></button>
    <button class="ds-g-node" style="left:64%;top:72%"><span class="ds-g-core tone-amber"></span><b>R-001</b><small>统计显著性审查</small></button>
    <button class="ds-g-node" style="left:64%;top:40%"><span class="ds-g-core tone-amber"></span><b>R-002</b><small>跨尺度复现审查</small></button>
    <div class="ds-g-connector g1"></div><div class="ds-g-connector g2"></div><div class="ds-g-connector g3"></div>
    <div class="ds-g-focus">D-002 · 短区间素数密度<br /><small>正在运行 · 3 条证据 · 2 个审查</small></div>
  </main>
  <footer class="ds-g-foot"><span>拖拽探索</span><span>滚轮缩放</span><span>点击节点查看证据</span></footer>
</div>
""",
)

variants["08-quantum-console"] = page(
    "08 · Quantum Console — Research World 视觉原型",
    """
<div class="ds-h">
  <header class="ds-h-titlebar"><span class="ds-h-dot red"></span><span class="ds-h-dot yellow"></span><span class="ds-h-dot green"></span><b>research-world — q001</b><span class="ds-h-right">▣ Console</span></header>
  <div class="ds-h-body">
    <aside class="ds-h-side"><header>EXPLORER</header><div class="ds-h-tree">
      <details open><summary>Q-001</summary><button>D-001 素数间隔计数</button><button class="active">D-002 短区间素数密度</button><button>D-003 相邻间隔相关性</button></details>
      <details><summary>experiments</summary><button>E-001 数据扫描</button><button>E-002 基线对照</button></details>
    </div></aside>
    <main class="ds-h-editor">
      <div class="ds-h-tabs"><span class="active">📄 direction.md</span><span>⌗ workflow.json</span><span>▣ trace.log</span></div>
      <div class="ds-h-code"><pre># 短区间素数密度
> 基础计数

## 目标
形成可引用、可复现、可反驳的局部判断。

## 状态
- life_state: 运行中
- direction: proposed
- reviewers: 2/2
- artifacts: sha256:9f2c…e1

## 下一步
- [x] 数值扫描
- [x] 独立复核
- [ ] 人工确认跨尺度策略</pre></div>
      <div class="ds-h-terminal"><span>❯</span><input value="research run --node D-002 --plan" aria-label="命令" /></div>
    </main>
    <aside class="ds-h-inspector"><header>INSPECTOR</header>
      <div class="ds-h-meta"><span>ID</span><b>D-002</b><span>KIND</span><b>direction</b><span>PARENT</span><b>Q-001</b><span>STATUS</span><b>运行中</b></div>
      <section><h3>执行凭据</h3><pre>image: qwen-research:latest
seed: 20260821
cpus: 4
memory: 8Gi
pids: 256</pre></section>
      <button class="ds-h-run">▶ Run Workflow</button>
    </aside>
  </div>
  <footer class="ds-h-status"><span>⎇ refactor/acp-runtime</span><span>0 errors · 0 warnings</span><span>Qwen Researcher</span><span>UTF-8 · LF</span></footer>
</div>
""",
)

variants["09-agent-deck"] = page(
    "09 · Agent Deck — Research World 视觉原型",
    """
<div class="ds-i">
  <header class="ds-i-top"><div class="ds-i-brand">🤖 AGENT DECK</div><div class="ds-i-live">📡 3 agents online</div></header>
  <div class="ds-i-body">
    <aside class="ds-i-agents">
      <button><span class="ds-i-avatar">O</span><div><b>Orchestrator</b><small>idle</small></div><i></i></button>
      <button class="active"><span class="ds-i-avatar">Q</span><div><b>Qwen Researcher</b><small>running</small></div><i class="run"></i></button>
      <button><span class="ds-i-avatar">C</span><div><b>Claude Code</b><small>idle</small></div><i></i></button>
      <button><span class="ds-i-avatar">P</span><div><b>Pi Reviewer</b><small>reviewing</small></div><i class="wait"></i></button>
    </aside>
    <main class="ds-i-stream">
      <header><h2>事件流</h2><span>append-only · 可审计</span></header>
      <article class="type-run"><time>12:11</time><b>orchestrator</b><p>D-002 完成第 3 步，生成区间密度对照表</p><span class="ds-i-hash">#1211f3a</span></article>
      <article class="type-approve"><time>12:09</time><b>reviewer#1</b><p>R-001 通过统计显著性阈值检查</p><span class="ds-i-hash">#1209ab2</span></article>
      <article class="type-approve"><time>12:06</time><b>reviewer#2</b><p>E-001 反例扫描未发现边界异常</p><span class="ds-i-hash">#1206c01</span></article>
      <article class="type-human"><time>12:02</time><b>human</b><p>人工确认 R-002 的跨尺度复现策略</p><span class="ds-i-hash">#1202447</span></article>
      <article class="type-branch"><time>11:58</time><b>orchestrator</b><p>D-003 被支持，开始派生 R-001</p><span class="ds-i-hash">#1158e88</span></article>
    </main>
    <section class="ds-i-graph">
      <header>◈ 实时图谱</header>
      <div class="ds-i-mini">
        <button class="active" style="left:8%;top:46%"><i class="tone-cyan"></i>Q-001</button>
        <button style="left:24%;top:22%"><i class="tone-blue"></i>D-001</button>
        <button style="left:24%;top:46%"><i class="tone-blue"></i>D-002</button>
        <button style="left:44%;top:42%"><i class="tone-green"></i>E-002</button>
        <button style="left:64%;top:40%"><i class="tone-amber"></i>R-002</button>
        <div class="ds-i-link l1"></div><div class="ds-i-link l2"></div>
      </div>
      <div class="ds-i-decide"><b>待人工裁决</b><p>R-002 跨尺度复现策略：两个审查员分歧</p><div><button>支持</button><button>驳回</button></div></div>
    </section>
  </div>
</div>
""",
)

variants["10-minimal-abyss"] = page(
    "10 · Minimal Abyss — Research World 视觉原型",
    """
<div class="ds-j">
  <header class="ds-j-top"><span>RESEARCH WORLD</span><span>Q-001</span><span class="ds-j-live">LIVE</span></header>
  <main class="ds-j-main">
    <div class="ds-j-orb"></div>
    <div class="ds-j-title"><h1>短区间素数密度</h1><p>基础计数 · 运行中 · 2 个审查进行中</p></div>
    <div class="ds-j-list">
      <button><span>Q-001</span><b>素数分布</b><em>已入图</em></button>
      <button class="active"><span>D-002</span><b>短区间素数密度</b><em>运行中</em></button>
      <button><span>E-002</span><b>密度基线对照</b><em>完成</em></button>
      <button><span>R-002</span><b>跨尺度复现审查</b><em>等待</em></button>
    </div>
    <footer class="ds-j-foot"><span>37 nodes</span><span>12 workflows</span><span>4 reviews</span></footer>
  </main>
</div>
""",
)

variants["11-orbital-timeline"] = page(
    "11 · Orbital Timeline — Research World 视觉原型",
    """
<div class="ds-k">
  <header class="ds-k-top"><div class="ds-k-brand">🌐 ORBITAL RESEARCH</div><div class="ds-k-mode"><span>谱系视图</span><span class="active">轨道视图</span><span>时间视图</span></div></header>
  <div class="ds-k-body">
    <div class="ds-k-orbit">
      <div class="ds-k-ring r1"></div><div class="ds-k-ring r2"></div><div class="ds-k-ring r3"></div>
      <button class="ds-k-core">⚛<b>Q-001</b></button>
      <button class="ds-k-satellite active" style="--angle:0deg;--delay:0s"><span>D-001</span><b>素数间隔计数</b></button>
      <button class="ds-k-satellite" style="--angle:52deg;--delay:.4s"><span>D-002</span><b>短区间素数密度</b></button>
      <button class="ds-k-satellite" style="--angle:104deg;--delay:.8s"><span>D-003</span><b>相邻间隔相关性</b></button>
      <button class="ds-k-satellite" style="--angle:156deg;--delay:1.2s"><span>E-001</span><b>间隔数据扫描</b></button>
      <button class="ds-k-satellite" style="--angle:208deg;--delay:1.6s"><span>E-002</span><b>密度基线对照</b></button>
      <button class="ds-k-satellite" style="--angle:260deg;--delay:2s"><span>R-002</span><b>跨尺度复现审查</b></button>
    </div>
    <aside class="ds-k-timeline"><header>时间轴</header>
      <div><time>12:11</time><p>D-002 完成第 3 步，生成区间密度对照表</p><span>orchestrator</span></div>
      <div><time>12:09</time><p>R-001 通过统计显著性阈值检查</p><span>reviewer#1</span></div>
      <div><time>12:06</time><p>E-001 反例扫描未发现边界异常</p><span>reviewer#2</span></div>
      <div><time>12:02</time><p>人工确认 R-002 的跨尺度复现策略</p><span>human</span></div>
    </aside>
  </div>
  <footer class="ds-k-foot"><span>当前轨道周期 42m</span><span>下一事件 12:18</span><span>人工介入 1</span></footer>
</div>
""",
)

variants["12-pixel-lab"] = page(
    "12 · Pixel Lab — Research World 视觉原型",
    """
<div class="ds-l">
  <header class="ds-l-top"><span class="ds-l-pixel-logo">R/W</span><b>PIXEL RESEARCH LAB</b><span class="ds-l-score">SCORE 12,480</span></header>
  <div class="ds-l-body">
    <aside class="ds-l-side"><button class="active">MAP</button><button>CHAT</button><button>LAB</button><button>LOG</button></aside>
    <main class="ds-l-main">
      <div class="ds-l-hud"><span>HP ▮▮▮▮▮▮▮▮</span><span>ENERGY ▮▮▮▮▮▮▮▯</span><span>REVIEW ▮▮▮▮▯▯▯▯</span></div>
      <div class="ds-l-grid">
        <button class="ds-l-node active"><span class="ds-l-sprite tone-cyan">◈</span><b>短区间素数密度</b><small>D-002</small></button>
        <button class="ds-l-node"><span class="ds-l-sprite tone-blue">⌥</span><b>素数间隔计数</b><small>D-001</small></button>
        <button class="ds-l-node"><span class="ds-l-sprite tone-green">⚗</span><b>间隔数据扫描</b><small>E-001</small></button>
        <button class="ds-l-node"><span class="ds-l-sprite tone-amber">✓</span><b>跨尺度复现审查</b><small>R-002</small></button>
      </div>
      <div class="ds-l-actions"><button>▶ RUN</button><button>💾 SAVE</button><button>👥 REVIEW</button></div>
    </main>
    <aside class="ds-l-sidebar"><h3>QUEST LOG</h3>
      <div><i>■</i><span>D-002 完成第 3 步，生成区间密度对照表</span></div>
      <div><i>■</i><span>R-001 通过统计显著性阈值检查</span></div>
      <div><i>■</i><span>E-001 反例扫描未发现边界异常</span></div>
      <div><i>■</i><span>人工确认 R-002 的跨尺度复现策略</span></div>
      <div class="ds-l-boss"><span>BOSS</span><b>R-002</b><progress value="35" max="100"></progress></div>
    </aside>
  </div>
  <footer class="ds-l-foot">INSERT COIN · 2026 RESEARCH WORLD · 1UP</footer>
</div>
""",
)

for folder, html in variants.items():
    path = ROOT / folder / "index.html"
    path.write_text(html, encoding="utf-8")
    print(f"wrote {path}")
