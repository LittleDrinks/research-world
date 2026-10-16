// 产品实栈录屏：新建项目 → /chat 发问流式回答 → 刷新恢复 → /map 图谱一眼。
// 前置：docker compose -p rw297 up --build -d（四容器 healthy），真实模型凭证经 .env 注入。
// 用法：node scripts/demo-video/record_product.mjs
import { pw, record } from "./record_lib.mjs";

const BASE = "http://localhost:8095";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

await record("product", { width: 1920, height: 1080 }, async (page) => {
  // 1) 项目列表 → 新建项目
  await page.goto(`${BASE}/projects`, { waitUntil: "networkidle" });
  await sleep(1200);
  await page.getByRole("button", { name: "新建项目" }).first().click();
  await page.getByLabel("项目名称").fill("行星轨道稳定性（q049）");
  await page.getByLabel("研究问题").fill(
    "Why don't the orbits of planets decay and cause them to crash into each other?",
  );
  await sleep(600);
  await page.getByRole("button", { name: "创建项目" }).click();
  await page.waitForURL(/\/map/, { timeout: 30000 });
  await sleep(3200);

  // 2) /chat 发问 → 流式回答
  await page.goto(`${BASE}/chat`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "新建对话" }).first().click();
  await page.getByLabel("消息").waitFor({ state: "visible", timeout: 30000 });
  await sleep(800);
  await page.getByLabel("消息").fill(
    "请用150字左右的连续段落回答：为什么行星轨道不会衰减并导致行星坠入太阳？不要分点。",
  );
  await page.getByRole("button", { name: "发送" }).click();
  await page.locator(".markdown.streaming").waitFor({ state: "visible", timeout: 60000 });
  await sleep(3000); // 拍到流式过程
  // 等收尾：流式区消失且助手回答非空（同 T2 判据）
  for (;;) {
    const err = await page.locator(".error-toast").count();
    if (err) throw new Error("回答失败：出现错误提示");
    const settled = page.locator("article.message.assistant .markdown:not(.streaming)");
    if (!(await page.locator(".markdown.streaming").count()) && (await settled.count())) {
      if ((await settled.last().innerText()).trim()) break;
    }
    await sleep(400);
  }
  await sleep(6000);

  // 3) 刷新恢复：同一问与同一答仍在
  await page.reload({ waitUntil: "networkidle" });
  await page.locator("article.message.assistant .markdown").first().waitFor({ timeout: 30000 });
  await sleep(6000);

  // 4) 图谱页一眼
  await page.goto(`${BASE}/map`, { waitUntil: "networkidle" });
  await sleep(8000);
});
