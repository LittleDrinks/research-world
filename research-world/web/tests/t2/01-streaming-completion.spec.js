// 验收1：回答以流式到达且正常收尾，终态非空。
import { expect, test } from "./fixtures.js";
import { openNewThread, sendMessage, settledAnswers, snapshot, toastText, waitForReply } from "./helpers/chat.js";

const PROMPT = "请用120字左右的连续段落介绍：什么是过拟合？不要分点，不要标题。";

test("验收1：回答流式到达并正常收尾，终态非空", async ({ page }, testInfo) => {
  await openNewThread(page);
  await sendMessage(page, PROMPT);
  const samples = [];
  let firstStreamed = "";
  const deadline = Date.now() + 180000;
  while (Date.now() < deadline) {
    const streaming = page.locator(".markdown.streaming");
    const text = (await streaming.count()) ? (await streaming.innerText({ timeout: 500 }).catch(() => "")).trim() : "";
    samples.push(text.length);
    if (text && !firstStreamed) firstStreamed = text;
    if (!text && (await settledAnswers(page).count())) break;
    if (await toastText(page)) break;
    await page.waitForTimeout(200);
  }
  await testInfo.attach("stream-samples.json", { body: JSON.stringify(samples), contentType: "application/json" });
  const lengths = [...new Set(samples)];
  expect(lengths.length, `流式证据不足：文本长度序列 ${lengths.join(" → ")}`).toBeGreaterThanOrEqual(3);
  const answer = await waitForReply(page, 0);
  expect(answer.length, "终态回答为空").toBeGreaterThan(0);
  const proof = firstStreamed.slice(0, 20);
  expect(answer).toContain(proof);
  await snapshot(page, testInfo, "01-final-answer");
});
