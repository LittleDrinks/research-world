// 生成演示视频字幕卡/表格卡：HTML → Playwright 截图 → 1920×1080 PNG。
// 用法：cd research-world && node scripts/demo-video/make_cards.mjs
// 输出：<repo>/.scratch/video/cards/*.png；<repo>/.scratch/video/shots/board.png 由 record_site.mjs 生成。
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync, existsSync, readFileSync } from "node:fs";
import { pw } from "./record_lib.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RW = path.resolve(HERE, "../..");
const REPO = path.resolve(RW, "..");
const OUT = path.join(REPO, ".scratch/video/cards");
const SHOTS = path.join(REPO, ".scratch/video/shots");
mkdirSync(OUT, { recursive: true });
const boardUri = existsSync(path.join(SHOTS, "board.png"))
  ? `data:image/png;base64,${readFileSync(path.join(SHOTS, "board.png")).toString("base64")}` : "";

const CSS = `
  * { margin:0; padding:0; box-sizing:border-box; }
  body { width:1920px; height:1080px; background:#0b0e14; color:#f2f4f8;
         font-family:"Noto Sans SC",sans-serif; display:flex; flex-direction:column; overflow:hidden; }
  .frame { flex:1; display:flex; flex-direction:column; padding:72px 110px 56px; }
  .kicker { font-size:30px; letter-spacing:6px; color:#4da3ff; font-weight:700; margin-bottom:26px; }
  h1 { font-size:88px; line-height:1.25; font-weight:800; }
  h2 { font-size:60px; line-height:1.3; font-weight:700; margin-bottom:34px; }
  p, li { font-size:38px; line-height:1.62; color:#c9d2e0; }
  .en { font-family:Georgia,serif; font-style:italic; color:#e8ecf4; }
  ul { list-style:none; } li { margin-bottom:18px; padding-left:34px; position:relative; }
  li::before { content:"·"; position:absolute; left:0; color:#4da3ff; font-weight:900; }
  table { border-collapse:collapse; width:100%; margin-top:8px; }
  th { font-size:30px; color:#4da3ff; text-align:left; padding:14px 22px; border-bottom:2px solid #2a3548; }
  td { font-size:30px; line-height:1.5; padding:16px 22px; border-bottom:1px solid #1c2432; color:#dbe2ee; vertical-align:top; }
  td.num { font-family:ui-monospace,monospace; }
  .good { color:#5ad19b; font-weight:700; } .bad { color:#ff7a7a; font-weight:700; }
  .mono { font-family:ui-monospace,monospace; }
  .foot { padding:0 110px 40px; display:flex; justify-content:space-between;
          font-size:24px; color:#5b667a; }
  .caption { margin-top:auto; font-size:34px; color:#8fa0b8; border-left:6px solid #4da3ff;
             padding:10px 0 10px 28px; margin-top:36px; line-height:1.55; }
  .shot-wrap { border:1px solid #2a3548; border-radius:12px; overflow:hidden; margin-top:6px;
               display:flex; justify-content:center; }
  .shot-wrap img { display:block; width:1700px; height:560px; object-fit:cover; object-position:top; }
  .center { justify-content:center; }
`;

const page = (kicker, body, foot = "Research World · 演示视频（粗剪）· 2026-09") =>
  `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head>
   <body><div class="frame"><div class="kicker">${kicker}</div>${body}</div>
   <div class="foot"><span>${foot}</span><span>issue #297</span></div></body></html>`;

const CARDS = {
  "01-title": page("演示视频", `<div class="center" style="flex:1;display:flex;flex-direction:column;justify-content:center">
      <h1>Research World</h1>
      <h1 style="font-size:64px;margin-top:18px">125 个科学问题的 AI 研究工作流</h1>
      <p style="margin-top:46px;font-size:40px">方法链为主 · 旗舰案例 q049 · 125 题全量 · 产品实栈演示</p>
      <p style="margin-top:16px;font-size:30px;color:#5b667a">粗剪 v1 · 无配音 · 全部数字可在仓库 evidence/ 回读</p></div>`),

  "02-oneliner": page("方法总览",
      `<h2>一个问题，一条可审计的流水线</h2>
       <ul>
         <li><b>作者 Session（每题独立）</b>：读 canonical 问题 → 三个可区分 Direction → 横向比较 → 研究计划 → 候选结论</li>
         <li><b>独立评审 Session</b>：固定六维 rubric、12 项检查打分，逐条 finding 可回读</li>
         <li><b>修订留痕</b>：每一版 artifact 与每轮 review、被拒原因全部保留</li>
         <li><b>审计回执</b>：独立 auditor 复核 Session、模型、token、哈希与终态</li>
       </ul>
       <div class="caption">125 题全量轻量运行 ＋ 5 题深查；下面用旗舰案例 q049 走完整条链。</div>`),

  "03-dashboard": page("方法总览",
      `<h2>125 题总看板：全部留下可回读的终态</h2>
       <div class="shot-wrap">${boardUri ? `<img src="${boardUri}">` : ""}</div>
       <div class="caption">125/125 有候选结论：8 completed · 117 partial · 0 failed · 0 waiting_human——partial 表示已有可回读结论但未过轻量门槛，不是未运行。</div>`),

  "04-sec-method": page("第一部分",
      `<div class="center" style="flex:1;display:flex;flex-direction:column;justify-content:center">
       <h1>方法链</h1>
       <p style="margin-top:30px;font-size:44px;color:#4da3ff;font-weight:700">旗舰案例 q049：从问题到 12/12</p></div>`),

  "05-problem": page("方法链 · q049",
      `<h2>问题：行星轨道为什么不衰减坠入太阳？</h2>
       <p class="en" style="font-size:40px;margin-bottom:34px">“Why don't the orbits of planets decay and cause them to crash into each other?”</p>
       <ul>
         <li><b>错误前提</b>：题面假设轨道会衰减、行星终将坠日——先校正前提，再回答</li>
         <li><b>对象与约束</b>：太阳系八大行星；区分保守动力学、微弱耗散、混沌失稳与太阳演化时间边界</li>
         <li><b>来源纪律</b>：优先同行评议或机构一手来源，精确主张必须可回读标识符</li>
         <li><b>执行边界</b>：未执行的模拟与实验一律标 planned，不得写成 executed</li>
       </ul>`),

  "06-v1-directions": page("方法链 · q049 · V1",
      `<h2>V1：三个可区分的机制方向</h2>
       <table>
         <tr><th style="width:90px"></th><th>核心陈述</th><th style="width:640px">V1 处理</th></tr>
         <tr><td class="mono">D1</td><td>N 体混沌可能导致低概率失稳</td>
             <td>降级——概率归因与来源链需修正</td></tr>
         <tr><td class="mono">D2</td><td>潮汐、引力波等微弱耗散长期累积</td>
             <td>不选——功率量级和计划判据错误</td></tr>
         <tr><td class="mono">D3</td><td>太阳演化先于耗散决定内行星命运</td>
             <td>选为主方向——但所引 Rasio 结论被反向转述</td></tr>
       </table>
       <div class="caption">三方向、对照、步骤与停止条件在 V1 已齐备——结构合格不等于科学合格。</div>`),

  "07-v1-score": page("方法链 · q049 · V1",
      `<h2>V1 得分：9/12，五条来源仅 2/5 可用</h2>
       <ul>
         <li>六维 rubric 12 项检查：9 项通过、3 项不通过，判 <span class="mono">revise</span></li>
         <li>典型硬伤：地球—太阳引力波功率写作 <span class="bad mono">~10⁻²⁰ W</span>，
             真实量级 <span class="good mono">~200 W</span>——<b>错约 22 个数量级</b></li>
         <li>判据随之失效：<span class="mono">dE/dt &lt; 10⁻²⁰ W</span> 会把真实的约 200 W 错判成“显著”</li>
       </ul>
       <div class="caption">同一题、同模型（qwen3-max）的直接回答对照只有 4/12 与 6/12，且零显式来源、无 Direction、无计划。</div>`),

  "08-findings": page("方法链 · q049 · 独立评审",
      `<h2>独立评审 review-v1：5 个 finding，全部落到修订</h2>
       <table>
         <tr><th>独立 finding</th><th style="width:560px">修订结果</th></tr>
         <tr><td>Deienno/Nesvorný DOI 属于另一篇论文</td><td>删除错配来源</td></tr>
         <tr><td>Lecar arXiv 号 0111602 错，应为 0111600</td><td>修正标识符并补齐来源记录</td></tr>
         <tr><td>Rasio “Earth may well not survive” 被反向转述</td><td>按原文限定重写</td></tr>
         <tr><td>引力波功率错约 22 个数量级</td><td>改用 Peters 公式＋完整输入＋独立复算</td></tr>
         <tr><td><span class="mono">dE/dt &lt; 10⁻²⁰ W</span> 判据无效</td><td>改为 inspiral 时间与太阳寿命比较</td></tr>
       </table>
       <div class="caption">评审与作者相互独立（不同 Session、不同模型）；发现不可回读即要求修正。</div>`),

  "09-revision": page("方法链 · q049 · 修订链",
      `<h2>V1 → V8：每一轮都留痕</h2>
       <ul>
         <li><span class="mono">v1</span> 9/12 → review-v1 五项 finding → <span class="mono">v2</span> → <span class="mono">v3</span> 首次 12/12</li>
         <li><span class="mono">v4</span> 修正约 1% 水星失稳概率的来源归因（科学主线不变）</li>
         <li><span class="mono">v5–v8</span> 表述投影：把“当前终态”改为“研究结论”、移除自我指涉、紧凑排版</li>
         <li>被拒的 attempt（12 个直答对照）与失败 Session 也全部保留在 <span class="mono">run.md</span></li>
       </ul>
       <div class="caption">最终 <b>v8：12/12、来源 6/6</b>，独立 review-v8 判 <span class="mono">deliverable</span>；receipt-v10 独立复核哈希与账本。</div>`),

  "10-peters": page("方法链 · q049 · 限定计算",
      `<h2>唯一 executed 的科研计算：Peters 公式</h2>
       <ul>
         <li>地球—太阳圆轨道引力波辐射：输入、公式、输出全部留痕</li>
         <li>功率 <span class="good mono">P = 196.291 W</span>（对齐 V1 阶段错 22 个数量级的那个数字）</li>
         <li>时标 <span class="mono">t = 3.374×10³⁰ s ≈ 1.069×10²³ yr</span> —— 远超太阳寿命</li>
         <li>退出码 0，输出 SHA-256 <span class="mono">7a546e…2361</span>；reviewer 独立复算一致</li>
       </ul>
       <div class="caption">结论边界：轨道不会因该机制在相关时标内螺旋坠日；N 体积分、相对论修正、太阳质量损失、潮汐、Monte Carlo 均为 planned。</div>`),

  "11-rubric": page("方法链 · 评分口径",
      `<h2>六维 rubric · 12 项检查</h2>
       <ul style="columns:2;column-gap:80px">
         <li>① 问题理解</li><li>② 文献证据</li><li>③ Direction</li>
         <li>④ 科学推理</li><li>⑤ 研究计划</li><li>⑥ 表达与追溯</li>
       </ul>
       <table style="margin-top:26px">
         <tr><th>q049 分数轨迹</th><th style="width:260px">rubric</th><th style="width:340px">显式来源</th></tr>
         <tr><td>直接回答 attempt 2（实算近似）</td><td class="num bad">4/12</td><td class="num">0 条</td></tr>
         <tr><td>直接回答 attempt 6（长度近似）</td><td class="num bad">6/12</td><td class="num">0 条</td></tr>
         <tr><td>Workflow V1</td><td class="num">9/12</td><td class="num">5 条（2/5 有效）</td></tr>
         <tr><td>Workflow final（V8）</td><td class="num good">12/12</td><td class="num good">6/6</td></tr>
       </table>`),

  "12-cost": page("方法链 · 代价对照",
      `<h2>同条件直答对照：没有免费的 12/12</h2>
       <table>
         <tr><th>指标</th><th>attempt 2 · 实算近似</th><th>attempt 6 · 长度近似</th><th>Workflow V1</th></tr>
         <tr><td>模型</td><td class="mono">qwen3-max</td><td class="mono">qwen3-max</td><td class="mono">qwen3-max</td></tr>
         <tr><td>字符（wc -m）</td><td class="num">2,388</td><td class="num">4,708</td><td class="num">4,970</td></tr>
         <tr><td>调用次数</td><td class="num">21</td><td class="num">27</td><td class="num">25</td></tr>
         <tr><td>非缓存输入 token</td><td class="num">113,326</td><td class="num">1,182,967</td><td class="num">98,844</td></tr>
         <tr><td>rubric</td><td class="num">4/12</td><td class="num">6/12</td><td class="num">9/12</td></tr>
       </table>
       <div class="caption">两个对照各只近似计算量或长度之一；12/12 发生在独立评审、修订与限定计算之后，不能只归因于 Workflow。</div>`),

  "13-deepcases": page("方法链 · 五题深查",
      `<h2>五个深度案例：V1 → final</h2>
       <table>
         <tr><th>案例</th><th>V1</th><th>final</th><th>来源门</th><th>终态</th></tr>
         <tr><td class="mono">q049</td><td class="num">9/12</td><td class="num good">12/12</td><td class="num">6/6</td><td>completed</td></tr>
         <tr><td class="mono">q089</td><td class="num">10/12</td><td class="num good">12/12</td><td class="num">9/9</td><td>completed</td></tr>
         <tr><td class="mono">q021</td><td class="num">10/12</td><td class="num good">12/12</td><td class="num">8/8</td><td>waiting_human</td></tr>
         <tr><td class="mono">q112</td><td class="num">7/12</td><td class="num good">12/12</td><td class="num">9/9</td><td>waiting_human</td></tr>
         <tr><td class="mono">q098</td><td class="num">7/12</td><td class="num good">12/12</td><td class="num">8/8</td><td>waiting_human</td></tr>
       </table>
       <div class="caption">五题合计 3,144 次模型调用；reviewer 的 deliverable 不是免检信号——q112 在 10/12 时仍留有错误方程，继续修订才到 12/12。</div>`),

  "14-sec-site": page("第二部分",
      `<div class="center" style="flex:1;display:flex;flex-direction:column;justify-content:center">
       <h1>125 全量</h1>
       <p style="margin-top:30px;font-size:44px;color:#4da3ff;font-weight:700">结果站点：逐题输出与审计，全部可回读</p></div>`),

  "16-sec-product": page("第三部分",
      `<div class="center" style="flex:1;display:flex;flex-direction:column;justify-content:center">
       <h1>产品演示</h1>
       <p style="margin-top:30px;font-size:44px;color:#4da3ff;font-weight:700">Compose 实栈：发问 → 流式回答 → 刷新恢复 → 图谱</p></div>`),

  "17-compose": page("产品演示 · 起栈",
      `<h2>docker compose up --build -d</h2>
       <ul>
         <li><span class="mono">control :8095</span> —— Web UI 与 API（本次演示入口）</li>
         <li><span class="mono">runtime :8098</span> —— 模型网关（凭证只经 .env 注入，不出现在画面）</li>
         <li><span class="mono">runner-controller</span> / <span class="mono">worker</span> —— 会话编排与执行</li>
         <li>四容器 healthcheck 全部 <span class="good">healthy</span>；启动不自动调用模型</li>
       </ul>
       <div class="caption">以下画面为真实浏览器直连 localhost:8095 的实栈录屏，无 mock、无拦截。</div>`),

  "21-end": page("结尾",
      `<div class="center" style="flex:1;display:flex;flex-direction:column;justify-content:center">
       <h1 style="font-size:72px">可核验入口</h1>
       <ul style="margin-top:44px">
         <li>仓库：<span class="mono">github.com/LittleDrinks/research-world</span></li>
         <li>结果站点：<span class="mono">littledrinks.github.io/research-world</span></li>
         <li>证据：<span class="mono">evidence/contest-2026/</span> —— 125 逐题输出、q049 版本链、审计与运行账本</li>
       </ul>
       <p style="margin-top:44px;font-size:32px;color:#8fa0b8">12/12 是评审结论而非永久事实——分支级独立验收曾推翻过早的 deliverable。</p></div>`),
};

const { chromium } = pw();
const pg0 = await chromium.launch();
const pg = await pg0.newPage({ viewport: { width: 1920, height: 1080 } });
for (const [name, html] of Object.entries(CARDS)) {
  if (name === "03-dashboard" && !existsSync(path.join(SHOTS, "board.png"))) {
    console.log("skip 03 (缺 shots/board.png，先跑 record_site.mjs)");
    continue;
  }
  await pg.setContent(html, { waitUntil: "networkidle" });
  await pg.screenshot({ path: path.join(OUT, `${name}.png`) });
  console.log("card:", name);
}
await pg0.close();
