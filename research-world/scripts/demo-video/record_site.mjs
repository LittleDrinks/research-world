// 125 结果站演示录屏：总看板滚动 → 领域筛选 → 终态筛选 → q049 详情。
// 前置：uv run python scripts/build-results-site.py && python3 -m http.server 8099 -d dist/results-site
// 用法：node scripts/demo-video/record_site.mjs   （另存 shots/board.png 供 03 号卡使用）
import { pw, record, SHOT_DIR } from "./record_lib.mjs";
import path from "node:path";

const BASE = "http://localhost:8099";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function smoothScroll(page, delta, steps = 12) {
  for (let i = 0; i < steps; i++) {
    await page.mouse.wheel(0, delta / steps);
    await sleep(120);
  }
}

await record("site", { width: 1920, height: 1080 }, async (page) => {
  await page.goto(BASE, { waitUntil: "networkidle" });
  await sleep(1800);
  await page.screenshot({ path: path.join(SHOT_DIR, "board.png") });

  await smoothScroll(page, 1500);
  await sleep(1200);
  await smoothScroll(page, -1500);
  await sleep(900);

  // 领域筛选：Astronomy
  await page.selectOption("#f-domain", "Astronomy");
  await sleep(1600);
  await page.selectOption("#f-domain", "");
  await sleep(900);

  // 终态筛选：completed
  await page.selectOption("#f-terminal", "completed");
  await sleep(1600);
  await page.selectOption("#f-terminal", "");
  await sleep(900);

  // 打开 q049 详情
  await page.locator('tr[data-qid="q049"] a').click();
  await page.waitForLoadState("networkidle");
  await sleep(1600);
  await smoothScroll(page, 1100);
  await sleep(1400);
});
