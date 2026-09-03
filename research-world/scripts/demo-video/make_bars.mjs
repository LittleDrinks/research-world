// 生成录屏字幕条：1920×160 透明 PNG，叠在录屏底部。
// 用法：node scripts/demo-video/make_bars.mjs → <repo>/.scratch/video/bars/*.png
import { mkdirSync } from "node:fs";
import path from "node:path";
import { pw, REPO } from "./record_lib.mjs";

const OUT = path.join(REPO, ".scratch/video/bars");
mkdirSync(OUT, { recursive: true });

const BARS = {
  "bar-site": "125 结果站点（本地构建）：看板滚动 → 领域筛选 → 终态筛选 → q049 详情",
  "bar-prodA": "Compose 实栈 · 新建项目 → /chat 发问 → 流式回答（真实模型，无 mock）",
  "bar-prodB": "刷新页面：同一问与同一答仍在",
  "bar-prodC": "/map 研究地图：问题节点、关系与节点详情",
};

const html = (text) => `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin:0; padding:0; } body { width:1920px; height:160px; background:transparent;
  display:flex; align-items:center; justify-content:center;
  font-family:"Noto Sans SC",sans-serif; }
  .bar { background:rgba(5,8,14,0.82); border-radius:14px; padding:20px 54px;
  font-size:44px; color:#f2f4f8; font-weight:600; letter-spacing:1px; }
</style></head><body><div class="bar">${text}</div></body></html>`;

const { chromium } = pw();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 160 } });
for (const [name, text] of Object.entries(BARS)) {
  await page.setContent(html(text));
  await page.screenshot({ path: path.join(OUT, `${name}.png`), omitBackground: true });
  console.log("bar:", name);
}
await browser.close();
