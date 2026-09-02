// 验收5：回答是模型文本轮，无工具调用伪装成回答或内部工具载荷直出。
import { expect, test } from "./fixtures.js";
import { openNewThread, sendMessage, snapshot, waitForReply } from "./helpers/chat.js";

const PROMPT = "用一句话解释：什么是假设检验？";

test("验收5：无工具纯文本轮", async ({ page }, testInfo) => {
  const threadId = await openNewThread(page);
  await sendMessage(page, PROMPT);
  const answer = await waitForReply(page, 0);
  expect(await page.locator("article.message.report-message").count(), "出现工具/报告载荷卡片").toBe(0);
  for (const marker of ['"type": "function"', "tool_call", "sessionUpdate"]) {
    expect(answer.includes(marker), `回答含工具载荷标记 "${marker}"`).toBe(false);
  }
  const response = await page.request.get(`/api/v1/threads/${encodeURIComponent(threadId)}`);
  expect(response.status()).toBe(200);
  const turns = (await response.json())?.runtime?.turns || [];
  const turn = turns.at(-1);
  expect(turn?.status, "末轮未正常完成").toBe("completed");
  expect(turn?.output?.trim(), "持久化轮输出与页面回答不一致").toBe(answer);
  expect(turn?.provider_items, "文本轮携带 provider 工具项").toEqual([]);
  const toolEvents = (turn?.events || []).filter((event) => event.type.startsWith("tool_"));
  expect(toolEvents, "文本轮出现工具事件").toHaveLength(0);
  await snapshot(page, testInfo, "04-text-round");
});
