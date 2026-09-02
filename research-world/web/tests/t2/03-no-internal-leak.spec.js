// 验收4：页面/响应不泄露 Run、Turn、Trace 等内部标识之外的内部状态，不泄露凭证。
// 凭证值泄露由 fixtures 的自动守卫断言（值已脱敏）；本用例另断言内部凭证字段与页面内部标记。
import { expect, test } from "./fixtures.js";
import { openNewThread, sendMessage, snapshot, waitForReply } from "./helpers/chat.js";
import { findInternalKeyLeak } from "./helpers/wire.js";

const PROMPT = "请只回答两个字：你好";

test("验收4：无内部标识泄露", async ({ page, wire }, testInfo) => {
  await openNewThread(page);
  await sendMessage(page, PROMPT);
  await waitForReply(page, 0);
  await wire.settle();
  for (const entry of wire.entries) {
    const field = findInternalKeyLeak(entry.body);
    expect(field, `响应 ${entry.url} 携带内部凭证字段 "${field}"`).toBeNull();
  }
  const pageText = await page.innerText("body");
  const markers = ["RUNTIME_API_KEY", "RUNTIME_API_BASE", '"type": "function"', "sessionUpdate", "tool_call_id"];
  for (const marker of markers) {
    expect(pageText.includes(marker), `页面渲染了内部标记 "${marker}"`).toBe(false);
  }
  await snapshot(page, testInfo, "03-no-leak");
});
