// 验收2：刷新后同一问与同一答仍在。
import { expect, test } from "./fixtures.js";
import { openNewThread, sendMessage, settledAnswers, snapshot, waitForReply } from "./helpers/chat.js";

const PROMPT = "1+1 等于几？请用一句话回答。";

test("验收2：刷新后同一问与同一答仍在", async ({ page }, testInfo) => {
  const threadId = await openNewThread(page);
  await sendMessage(page, PROMPT);
  const answer = await waitForReply(page, 0);
  await snapshot(page, testInfo, "02-before-reload");
  await page.reload({ waitUntil: "networkidle" });
  expect(page.url()).toContain(encodeURIComponent(threadId));
  const userTexts = (await page.locator("article.message.user p").allInnerTexts()).join("\n");
  expect(userTexts, "刷新后用户提问丢失").toContain(PROMPT);
  const answers = (await settledAnswers(page).allInnerTexts()).map((text) => text.trim());
  expect(answers, "刷新后回答与刷新前不一致").toContain(answer);
  await snapshot(page, testInfo, "02-after-reload");
});
