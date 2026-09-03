// T1 五步验证驱动：真实 Chromium，无任何请求拦截。
// 产物写入 research-world/.scratch/t1-five-step/
import { chromium } from "playwright";
import fs from "node:fs";

const BASE = process.env.T1_BASE || "http://127.0.0.1:8095";
const OUT = new URL("../../.scratch/t1-five-step/", import.meta.url).pathname;
fs.mkdirSync(OUT, { recursive: true });

const MESSAGE = "请用一句话回答：1+1 等于几？";
const log = [];
const note = (line) => {
  const stamp = new Date().toISOString();
  log.push(`${stamp} ${line}`);
  console.log(`${stamp} ${line}`);
};

const netFailures = [];
const consoleErrors = [];

const browser = await chromium.launch();
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
page.on("requestfailed", (r) => netFailures.push(`${r.method()} ${r.url()} :: ${r.failure()?.errorText}`));
page.on("response", (r) => { if (r.status() >= 400) netFailures.push(`${r.request().method()} ${r.url()} :: ${r.status()}`); });
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });

// 步骤 2：浏览器进入 Chat
await page.goto(`${BASE}/chat`, { waitUntil: "networkidle" });
note(`进入 ${BASE}/chat，URL=${page.url()}`);

const createButton = page.getByRole("button", { name: "新建对话" });
if (await createButton.count()) {
  await createButton.first().click();
  await page.waitForURL(/\/chat\/.+/, { timeout: 30000 });
  note(`已新建对话，URL=${page.url()}`);
}
await page.waitForSelector("textarea[aria-label=\"消息\"]", { timeout: 30000 });

// 步骤 3：发消息并观察流式
await page.fill("textarea[aria-label=\"消息\"]", MESSAGE);
await page.click("button[aria-label=\"发送\"]");
note(`已发送消息：「${MESSAGE}」`);

const samples = [];
const deadline = Date.now() + 180000;
let answered = false;
while (Date.now() < deadline) {
  const streaming = await page.locator(".markdown.streaming").count()
    ? await page.locator(".markdown.streaming").innerText().catch(() => "")
    : "";
  const settled = await page.locator("article.message.assistant .markdown").count();
  samples.push({ t: Date.now(), streamingLen: streaming.length, settledAssistant: settled });
  if (!streaming && settled > 0 && samples.length > 2) { answered = true; break; }
  await page.waitForTimeout(150);
}
const growth = samples.filter((s, i) => i === 0 || s.streamingLen !== samples[i - 1].streamingLen);
note(`流式采样：${samples.length} 帧，其中 ${growth.length} 次文本长度变化（流式证据）`);
if (growth.length) note(`流式长度轨迹：${growth.map((s) => s.streamingLen).join(" → ")}`);

const assistantText = (await page.locator("article.message.assistant .markdown").last().innerText().catch(() => "")) || "";
note(`回答收尾：${answered ? "正常收尾" : "超时未收尾"}，回答长度=${assistantText.length}`);
note(`回答内容：「${assistantText.slice(0, 300)}」`);
await page.screenshot({ path: `${OUT}01-answer.png`, fullPage: true });

// 步骤 4：刷新恢复同一对话
await page.reload({ waitUntil: "networkidle" });
await page.waitForSelector("article.message", { timeout: 30000 });
const userAfter = (await page.locator("article.message.user p").allInnerTexts()).join("\n");
const assistantAfter = (await page.locator("article.message.assistant .markdown").last().innerText().catch(() => "")) || "";
await page.screenshot({ path: `${OUT}02-after-reload.png`, fullPage: true });
note(`刷新后 URL=${page.url()}`);
note(`刷新后用户消息在列：${userAfter.includes(MESSAGE)}`);
note(`刷新后回答一致：${assistantAfter === assistantText}（长度 ${assistantAfter.length}）`);
note(`刷新后回答内容：「${assistantAfter.slice(0, 300)}」`);

fs.writeFileSync(`${OUT}run.log`, log.join("\n"));
fs.writeFileSync(`${OUT}stream-samples.json`, JSON.stringify(samples, null, 2));
fs.writeFileSync(`${OUT}network-failures.json`, JSON.stringify(netFailures, null, 2));
fs.writeFileSync(`${OUT}console-errors.json`, JSON.stringify(consoleErrors, null, 2));
fs.writeFileSync(`${OUT}summary.json`, JSON.stringify({
  url: page.url(), message: MESSAGE, answered, assistantText, userAfterIncludesMessage: userAfter.includes(MESSAGE),
  assistantSameAfterReload: assistantAfter === assistantText, netFailures, consoleErrors,
}, null, 2));

await browser.close();
