// T1 证据补拍：旧 Thread 上发送 → session_spec_invalid 错误可见性 + 刷新后提问丢失。
import { chromium } from "playwright";
import fs from "node:fs";

const BASE = process.env.T1_BASE || "http://127.0.0.1:8095";
const OUT = new URL("../../.scratch/t1-five-step/", import.meta.url).pathname;
fs.mkdirSync(OUT, { recursive: true });
const THREAD = process.env.T1_THREAD || "thread:2fa56c4fa08c00f8ee5b9d4f";
const MESSAGE = "请用一句话回答：1+1 等于几？";
const log = [];
const note = (line) => { const s = new Date().toISOString(); log.push(`${s} ${line}`); console.log(`${s} ${line}`); };

const browser = await chromium.launch();
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
const netFailures = [];
const consoleErrors = [];
page.on("requestfailed", (r) => netFailures.push(`${r.method()} ${r.url()} :: ${r.failure()?.errorText}`));
page.on("response", (r) => { if (r.status() >= 400) netFailures.push(`${r.request().method()} ${r.url()} :: ${r.status()}`); });
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });

await page.goto(`${BASE}/chat/${encodeURIComponent(THREAD)}`, { waitUntil: "networkidle" });
await page.waitForSelector("textarea[aria-label=\"消息\"]", { timeout: 30000 });
await page.fill("textarea[aria-label=\"消息\"]", MESSAGE);
await page.click("button[aria-label=\"发送\"]");
note("已发送消息，等待错误提示或回答…");

const errorToast = page.locator("text=此对话的 Agent 配置已变更").first();
const settled = page.locator("article.message.assistant .markdown").first();
let outcome = "none";
await Promise.race([
  errorToast.waitFor({ state: "visible", timeout: 60000 }).then(() => { outcome = "error-notice"; }),
  settled.waitFor({ timeout: 60000 }).then(() => { outcome = "answered"; }),
]).catch(() => {});
await page.waitForTimeout(1500);
note(`发送结果：${outcome}`);
await page.screenshot({ path: `${OUT}03-send-outcome.png`, fullPage: true });

await page.reload({ waitUntil: "networkidle" });
await page.waitForTimeout(2000);
const userCount = await page.locator("article.message.user").count();
const placeholder = await page.locator("text=暂无消息").count();
note(`刷新后：用户消息条数=${userCount}，空态提示=${placeholder > 0}`);
await page.screenshot({ path: `${OUT}04-after-reload.png`, fullPage: true });

fs.writeFileSync(`${OUT}run-errorpath.log`, log.join("\n"));
fs.writeFileSync(`${OUT}network-failures.json`, JSON.stringify(netFailures, null, 2));
fs.writeFileSync(`${OUT}console-errors.json`, JSON.stringify(consoleErrors, null, 2));
fs.writeFileSync(`${OUT}summary-errorpath.json`, JSON.stringify({ outcome, userCount, placeholder: placeholder > 0, netFailures, consoleErrors }, null, 2));
await browser.close();
