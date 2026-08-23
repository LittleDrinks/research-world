import { expect, test } from "@playwright/test";
import { bootstrap, mockBase, node, run, sse, thread, threadDetail } from "./fixtures";


async function mockChat(page, detail = threadDetail()) {
  await mockBase(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: detail }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/threads/, (route) => route.fulfill({ json: [thread()] }));
}


test("renders project thread messages and sends via the prompts stream", async ({ page }) => {
  let request;
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) => {
    request = route.request().postDataJSON();
    return route.fulfill(sse([["delta", { text: "先生成并筛选" }], ["delta", { text: "多个研究方向。" }], ["done", { stop_reason: "end_turn" }]]));
  });
  await page.goto("/chat/thread%3At1");
  await expect(page.getByText("已带入问题上下文")).toBeVisible();
  await expect(page.locator(".pin-strip")).toHaveCount(0);
  const composer = await page.locator(".composer-wrap").boundingBox();
  expect(composer.y + composer.height).toBe(await page.evaluate(() => innerHeight));
  await page.screenshot({ path: "test-results/chat-desktop.png" });
  await page.getByLabel("消息").fill("下一步做什么？");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("先生成并筛选多个研究方向。")).toBeVisible();
  expect(request).toEqual({ message: "下一步做什么？" });
});


test("keeps the composer IME-safe", async ({ page }) => {
  let sends = 0;
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) => { sends += 1; return route.fulfill(sse([["done", { stop_reason: "end_turn" }]])); });
  await page.goto("/chat/thread%3At1");
  const input = page.getByLabel("消息");
  await input.fill("分析当前节点");
  await input.dispatchEvent("keydown", { key: "Enter", isComposing: true });
  await page.waitForTimeout(150);
  expect(sends).toBe(0);
  await input.dispatchEvent("keydown", { key: "Enter", shiftKey: true });
  expect(sends).toBe(0);
  await input.press("Enter");
  await expect.poll(() => sends).toBe(1);
});


test("searches real nodes on @ and pins the selected node", async ({ page }) => {
  let pinned;
  await mockChat(page);
  await page.route(/\/api\/v1\/tools\/graph-query/, (route) =>
    route.fulfill({ json: [{ id: "node:d", kind: "direction", life_state: "admitted", summary: "direction 节点 node:d" }] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1\/nodes$/, (route) => {
    pinned = route.request().postDataJSON();
    return route.fulfill({ json: { ...thread(), nodes: [node("node:q", "question"), node("node:d", "direction")] } });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("参考 @d");
  await page.locator(".mention-menu button").first().click();
  await expect(page.getByLabel("消息")).toHaveValue("参考 @node:d ");
  await expect(page.locator(".thread-header")).toContainText("2 个引用节点");
  expect(pinned).toEqual({ node_id: "node:d" });
});


test("uses one chat scroll container and keeps the composer reachable", async ({ page }) => {
  const messages = Array.from({ length: 30 }, (_, index) => ({ role: "assistant", content: `回复 ${index}` }));
  await mockChat(page, threadDetail({ runtime: { ...threadDetail().runtime, messages } }));
  await page.goto("/chat/thread%3At1");
  await expect(page.locator(".chat-page")).toBeVisible();
  await expect(page.locator(".chat-runs")).toHaveCount(0);
  const overflow = await page.evaluate(() => Object.fromEntries([".chat-page", ".chat-scroll"]
    .map((selector) => [selector, getComputedStyle(document.querySelector(selector)).overflowY])));
  expect(overflow).toEqual({ ".chat-page": "hidden", ".chat-scroll": "auto" });
  await expect.poll(() => page.locator(".chat-scroll").evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true);
  const scrollHeight = await page.locator(".chat-scroll").evaluate((element) => element.scrollHeight);
  await page.getByRole("button", { name: "研究运行" }).click();
  await expect(page.getByRole("dialog", { name: "研究运行与流程" })).toBeVisible();
  expect(await page.locator(".chat-scroll").evaluate((element) => element.scrollHeight)).toBe(scrollHeight);
  const composer = await page.locator(".composer-wrap").boundingBox();
  expect(Math.abs(composer.y + composer.height - await page.evaluate(() => innerHeight))).toBeLessThanOrEqual(1);
});


test("renders run cards linked by thread_id and navigates to the trace", async ({ page }) => {
  await mockChat(page);
  await page.goto("/chat/thread%3At1");
  const section = page.getByRole("button", { name: /研究运行/ });
  await expect(section).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".run-card")).toHaveCount(0);
  await section.click();
  const card = page.locator(".run-card");
  await expect(card).toHaveCount(1);
  await expect(card).toContainText("生成研究方向");
  await card.locator(".run-card-head").click();
  await page.locator(".session-row").click();
  await expect(page).toHaveURL(/\/traces\/run%3Ar1\?session=s-abc&from=thread%3At1/);
  await expect(page.getByRole("button", { name: "返回对话" })).toBeVisible();
  await page.getByRole("button", { name: "返回对话" }).click();
  await expect(page).toHaveURL(/\/chat\/thread%3At1$/);
});


test("locally hides terminal runs without removing trace access", async ({ page }) => {
  const terminal = [run({ status: "completed" }), run({ id: "run:r2", status: "failed" })];
  await mockBase(page, bootstrap({ runs: [...terminal, run({ id: "run:r3" })] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: /研究运行/ }).click();
  await expect(page.locator(".run-card")).toHaveCount(3);
  await expect(page.getByRole("button", { name: /从当前列表移除运行/ })).toHaveCount(2);
  await page.getByRole("button", { name: /从当前列表移除运行/ }).first().click();
  await expect(page.locator(".run-card")).toHaveCount(2);
  await expect(page.getByRole("button", { name: "查看轨迹" })).toHaveCount(2);
  await page.getByRole("button", { name: "恢复已移出的 1 项" }).click();
  await expect(page.locator(".run-card")).toHaveCount(3);
  await expect(page.getByRole("button", { name: "查看轨迹" })).toHaveCount(3);
  await page.getByRole("button", { name: /从当前列表移除运行/ }).first().click();
  await page.reload();
  await page.getByRole("button", { name: /研究运行/ }).click();
  await expect(page.locator(".run-card")).toHaveCount(3);
});


test("launches a pipeline explicitly with the thread id in the payload", async ({ page }) => {
  let request;
  await mockChat(page);
  await page.route(/\/api\/v1\/projects\/project%3Atest\/runs/, (route) => {
    request = route.request().postDataJSON();
    return route.fulfill({ status: 201, json: run() });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "研究运行" }).click();
  await page.getByLabel("选择流程").selectOption("research");
  await page.getByRole("button", { name: "启动流程" }).click();
  await expect.poll(() => request).toBeTruthy();
  expect(request.pipeline_id).toBe("research");
  expect(request.node_id).toBe("node:q");
  expect(request.payload.thread_id).toBe("thread:t1");
});


test("dismisses the research popover and restores trigger focus", async ({ page }) => {
  await mockChat(page);
  await page.goto("/chat/thread%3At1");
  const trigger = page.getByRole("button", { name: "研究运行" });
  await trigger.click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "研究运行与流程" })).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.locator(".thread-header h1").click();
  await expect(page.getByRole("dialog", { name: "研究运行与流程" })).toHaveCount(0);
  await expect(trigger).toBeFocused();
});


test("keeps long research runs inside the composer popover on mobile", async ({ page }) => {
  const runs = Array.from({ length: 12 }, (_, index) => run({ id: `run:r${index}` }));
  await page.setViewportSize({ width: 390, height: 844 });
  await mockBase(page, bootstrap({ runs }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "研究运行" }).click();
  await expect.poll(() => page.locator(".research-popover-runs").evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole("button", { name: "发送" })).toBeVisible();
  await page.screenshot({ path: "test-results/research-popover-mobile.png" });
});


test("shows an empty state with a create action when no thread exists", async ({ page }) => {
  await mockBase(page, bootstrap({ threads: [], runs: [] }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/threads/, (route) =>
    route.request().method() === "POST" ? route.fulfill({ status: 201, json: threadDetail() }) : route.fulfill({ json: [] }));
  await page.goto("/chat");
  await expect(page.getByText("项目还没有对话")).toBeVisible();
  await page.locator(".empty-state").getByRole("button", { name: "新建对话" }).click();
  await expect(page).toHaveURL(/\/chat\/thread%3At1/);
});


test("restores the draft on stream error and stays readable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) =>
    route.fulfill(sse([["delta", { text: "部分" }], ["error", { detail: "模型超时" }]])));
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("分析一下");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByRole("alert")).toContainText("模型超时");
  await expect(page.getByLabel("消息")).toHaveValue("分析一下");
  await page.screenshot({ path: "test-results/chat-mobile.png", fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const toast = await page.getByRole("alert").boundingBox();
  const mobileBar = await page.locator(".mobile-bar").boundingBox();
  const composer = await page.locator(".composer-wrap").boundingBox();
  expect(toast.y + toast.height).toBeLessThanOrEqual(mobileBar.y);
  expect(mobileBar.y + mobileBar.height).toBeLessThanOrEqual(composer.y);
  expect(toast.y + toast.height).toBeLessThanOrEqual(composer.y);
});


test("offers inline restart when the session spec is outdated", async ({ page }) => {
  let restarted = false;
  const sent = [];
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) => {
    sent.push(route.request().postDataJSON());
    return restarted
      ? route.fulfill(sse([["delta", { text: "重启后的答复" }], ["done", { stop_reason: "end_turn" }]]))
      : route.fulfill(sse([["error", { detail: "此对话的 Agent 配置已变更，需要重启会话", code: "session_spec_invalid" }]]));
  });
  await page.route(/\/api\/v1\/threads\/thread%3At1\/restart/, (route) => {
    restarted = true;
    return route.fulfill({ json: threadDetail({ session_id: "s-new" }) });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("继续讨论");
  await page.getByRole("button", { name: "发送" }).click();
  const notice = page.locator(".spec-notice");
  await expect(notice).toContainText("此对话的 Agent 配置已变更，需要重启会话");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByLabel("消息")).toHaveValue("继续讨论");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await notice.getByRole("button", { name: "重启会话" }).click();
  await expect(notice).toHaveCount(0);
  await expect(page.getByLabel("消息")).toHaveValue("继续讨论");
  await page.getByRole("button", { name: "发送" }).click();
  await expect.poll(() => sent.length).toBe(2);
  expect(sent[1]).toEqual({ message: "继续讨论" });
});


test("only lists runs bound to the thread id", async ({ page }) => {
  const foreign = run({ id: "run:r2", node_id: "node:q", payload: {} });
  await mockBase(page, bootstrap({ runs: [run(), foreign] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: /研究运行/ }).click();
  await expect(page.locator(".run-card")).toHaveCount(1);
  await expect(page.locator(".run-card")).not.toContainText("run:r2");
});


test("always offers a trace link on run cards, even without sessions", async ({ page }) => {
  const quiet = run({ id: "run:r9", events: [], steps: [], payload: { thread_id: "thread:t1" } });
  await mockBase(page, bootstrap({ runs: [quiet] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: /研究运行/ }).click();
  const card = page.locator(".run-card");
  await expect(card).toHaveCount(1);
  await expect(card.locator(".run-card-head")).toHaveAttribute("aria-expanded", "false");
  await card.getByRole("button", { name: "查看轨迹" }).click();
  await expect(page).toHaveURL(/\/traces\/run%3Ar9\?from=thread%3At1/);
  await expect(page.getByRole("button", { name: "返回对话" })).toBeVisible();
});


test("waits for the pin to persist before allowing send", async ({ page }) => {
  let releasePin;
  const gate = new Promise((resolve) => { releasePin = resolve; });
  let message;
  await mockChat(page);
  await page.route(/\/api\/v1\/tools\/graph-query/, (route) =>
    route.fulfill({ json: [{ id: "node:d", kind: "direction", life_state: "admitted", summary: "direction 节点 node:d" }] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1\/nodes$/, async (route) => {
    await gate;
    return route.fulfill({ json: { ...thread(), nodes: [node("node:q", "question"), node("node:d", "direction")] } });
  });
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) => {
    message = route.request().postDataJSON();
    return route.fulfill(sse([["done", { stop_reason: "end_turn" }]]));
  });
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("参考 @d");
  await page.locator(".mention-menu button").first().click();
  await expect(page.getByRole("button", { name: "发送" })).toBeDisabled();
  await page.getByLabel("消息").press("Enter");
  await page.waitForTimeout(150);
  expect(message).toBeUndefined();
  releasePin();
  await expect(page.getByLabel("消息")).toHaveValue("参考 @node:d ");
  await expect(page.getByRole("button", { name: "发送" })).toBeEnabled();
  await page.getByRole("button", { name: "发送" }).click();
  await expect.poll(() => message).toEqual({ message: "参考 @node:d" });
});


test("shows an error state with retry when the thread fails to load", async ({ page }) => {
  let fail = true;
  await mockBase(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) =>
    fail ? route.fulfill({ status: 404, json: { detail: "not found" } }) : route.fulfill({ json: threadDetail() }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/threads/, (route) => route.fulfill({ json: [thread()] }));
  await page.goto("/chat/thread%3At1");
  await expect(page.getByText("Thread 载入失败")).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "重试" }).click();
  await expect(page.getByText("已带入问题上下文")).toBeVisible();
});


test("does not insert the mention when the pin fails", async ({ page }) => {
  let message;
  await mockChat(page);
  await page.route(/\/api\/v1\/tools\/graph-query/, (route) =>
    route.fulfill({ json: [{ id: "node:d", kind: "direction", life_state: "admitted", summary: "direction 节点 node:d" }] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1\/nodes$/, (route) => route.fulfill({ status: 409, json: { detail: "节点已锁定" } }));
  await page.route(/\/api\/v1\/threads\/thread%3At1\/prompts/, (route) => {
    message = route.request().postDataJSON();
    return route.fulfill(sse([["done", { stop_reason: "end_turn" }]]));
  });
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("参考 @d");
  await page.locator(".mention-menu button").first().click();
  await expect(page.getByRole("alert")).toContainText("节点已锁定");
  await expect(page.getByLabel("消息")).toHaveValue("参考 @d");
  await expect(page.locator(".pin-strip")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "发送" })).toBeEnabled();
  await page.getByLabel("消息").press("Enter");
  await expect.poll(() => message).toEqual({ message: "参考 @d" });
});
