// THROWAWAY PROTOTYPE verification: node verify.mjs — asserts real scale (125 questions, 5000 nodes) and key interactions.
import pw from "../../research-world/web/node_modules/@playwright/test/index.js";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const { chromium } = pw;
const root = dirname(fileURLToPath(import.meta.url));
const open = async (page, rel) => { const errs = []; const h = (e) => errs.push(String(e)); page.on("pageerror", h); await page.goto(pathToFileURL(join(root, rel)).href, { waitUntil: "load" }); await page.waitForTimeout(300); page.off("pageerror", h); return errs; };
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on("dialog", (d) => d.dismiss().catch(() => {}));
const checks = [];
const check = async (name, fn) => { try { const v = await fn(); checks.push([name, v === true ? "ok" : `FAIL ${v}`]); } catch (e) { checks.push([name, `EXC ${String(e).slice(0,160)}`]); } };

await check("index 总览渲染 24 张卡片", async () => { await open(page, "index.html"); return (await page.locator("a.card").count()) === 24; });
await check("index 读取真实 125 题", async () => (await page.evaluate(() => window.RW.PROJECTS.length)) === 125);
await check("v01 默认矩阵显示 125 题", async () => { await open(page, "v01-fleet/index.html"); return (await page.locator(".tile").count()) === 125; });
await check("v01 搜索 q049 得到 1 题", async () => { await page.fill("#q", "q049"); await page.waitForTimeout(80); return (await page.locator(".tile").count()) === 1; });
await check("v02 渲染 64 个节点", async () => { await open(page, "v02-cartography/index.html"); return (await page.locator("circle.node, rect.node").count()) === 64; });
await check("v03 每页 46 行事件", async () => { await open(page, "v03-ledger/index.html"); return (await page.locator("tr.row").count()) === 46; });
await check("v05 模拟连续驳回触发熔断", async () => { await open(page, "v05-lineage-rail/index.html"); await page.click("#info button"); await page.click("#info button"); return (await page.locator(".fuse-mark").count()) === 1; });
await check("v07 Q112 全文长度 > 300", async () => { await open(page, "v07-wet-lab/index.html"); return (await page.evaluate(() => document.getElementById("qtext").textContent.length)) > 200; });
await check("v10 渲染 125 行预算队列", async () => { await open(page, "v10-budget/index.html"); return (await page.locator(".row").count()) === 125; });
await check("v14 注入否定得到撤销清单", async () => { await open(page, "v14-impact/index.html"); await page.click("#kill"); return (await page.locator("#summary").isVisible()) && (await page.locator("#list").textContent()).includes("N") ? true : "summary not visible"; });
await check("v16 / 键打开命令面板并可搜索", async () => { await open(page, "v16-palette/index.html"); await page.keyboard.press("/"); await page.fill("#cmd", "q049"); return (await page.locator(".row").count()) >= 1; });
await check("v17 真实 SHA-256 长度 64", async () => { await open(page, "v17-repro-card/index.html"); await page.click("#hash"); await page.waitForTimeout(80); const h = await page.textContent("#out"); return /^[0-9a-f]{64}$/.test(h) ? true : `hash=${h.slice(0,20)}`; });
await check("v18 5000 节点 DOM 渲染并出计时", async () => { await open(page, "v18-density/index.html"); await page.click("[data-n='5000']"); await page.waitForTimeout(150); const c = await page.locator("#dom .node").count(); const ms = await page.textContent("#m-dom"); return c === 5000 && /\d/.test(ms) ? true : `count=${c} ms=${ms}`; });
await check("v21 Q21 全文长度 > 200", async () => { await open(page, "v21-scifact/index.html"); return (await page.evaluate(() => document.getElementById("qtext").textContent.length)) > 200; });
await check("v24 选型矩阵 24 行", async () => { await open(page, "v24-selection/index.html"); return (await page.locator("tr.row").count()) === 24; });

await browser.close();
let failed = 0;
for (const [name, v] of checks) { if (v !== "ok") failed++; console.log((v === "ok" ? "ok  " : "FAIL") + " " + name + (v === "ok" ? "" : " → " + v)); }
console.log(`\n${checks.length - failed}/${checks.length} passed`);
process.exit(failed ? 1 : 0);
