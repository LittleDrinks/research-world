// Chat 页生产路由步骤：新建对话、发送、等回答、等错误提示、截图归档。
import { redact } from "./env.js";

export async function openNewThread(page) {
  await page.goto("/chat", { waitUntil: "networkidle" });
  if (!/\/chat\/.+/.test(new URL(page.url()).pathname))
    await page.waitForURL((url) => /\/chat\/.+/.test(url.pathname), { timeout: 30000 }).catch(() => {});
  const before = page.url();
  await page.getByRole("button", { name: "新建对话" }).first().click();
  await page.waitForURL((url) => url.toString() !== before && /\/chat\/.+/.test(url.pathname), { timeout: 30000 });
  await page.getByLabel("消息").waitFor({ state: "visible", timeout: 30000 });
  return decodeURIComponent(page.url().split("/chat/")[1]);
}

export async function sendMessage(page, text) {
  await page.getByLabel("消息").fill(text);
  await page.getByRole("button", { name: "发送" }).click();
}

export function settledAnswers(page) {
  return page.locator("article.message.assistant .markdown:not(.streaming)");
}

export function hasErrorToast(page) {
  return page.locator(".error-toast").count();
}

export async function toastText(page) {
  const toast = page.locator(".error-toast");
  if (!(await toast.count())) return "";
  return (await toast.innerText({ timeout: 500 }).catch(() => "")).trim();
}

// 等待发送收尾：流式区消失、新增助手回答非空（发送键不作为信号：发送成功后草稿清空，按钮仍 disabled）。
export async function waitForReply(page, baselineCount, deadlineMs = 180000) {
  const deadline = Date.now() + deadlineMs;
  for (;;) {
    if (await toastText(page)) throw new Error(`回答未到达，Chat 出现错误提示：「${redact(await toastText(page))}」`);
    if (!(await page.locator(".markdown.streaming").count())) {
      const texts = (await settledAnswers(page).allInnerTexts()).map((text) => text.trim());
      if (texts.length > baselineCount && texts.at(-1)) return texts.at(-1);
    }
    if (Date.now() > deadline) throw new Error(`回答 ${deadlineMs}ms 内未收尾（助手消息数 ${await settledAnswers(page).count()}）`);
    await page.waitForTimeout(300);
  }
}

// 等待错误提示出现（凭证失败用例）：返回提示文本。
export async function waitForErrorToast(page, deadlineMs = 90000) {
  const deadline = Date.now() + deadlineMs;
  for (;;) {
    const text = await toastText(page);
    if (text) return text;
    if (Date.now() > deadline) throw new Error(`${deadlineMs}ms 内 Chat 未出现错误提示（.error-toast）`);
    await page.waitForTimeout(300);
  }
}

export async function closeToast(page) {
  const close = page.locator(".error-toast button[title=\"关闭提示\"]");
  if (await close.count()) await close.click();
}

export async function snapshot(page, testInfo, name) {
  const file = testInfo.outputPath(`${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  await testInfo.attach(`${name}.png`, { path: file });
}
