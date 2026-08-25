import { expect, test } from "@playwright/test";
import { agentDraft, agents, bootstrap, catalog, mockBase, node, run, sse, thread, threadDetail } from "./fixtures";


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
  await expect(page.getByRole("link", { name: "研究运行 1" })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const composer = await page.locator(".composer-wrap").boundingBox();
  expect(Math.abs(composer.y + composer.height - await page.evaluate(() => innerHeight))).toBeLessThanOrEqual(1);
});


test("renders a compact context link without an inline run list", async ({ page }) => {
  await mockChat(page);
  await page.goto("/chat/thread%3At1");
  const section = page.getByRole("link", { name: "研究运行 1" });
  await expect(section).toHaveAttribute("href", /\/traces\?project_id=project%3Atest&thread_id=thread%3At1&from=%2Fchat%2Fthread%253At1/);
  await expect(page.locator(".run-card")).toHaveCount(0);
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


test("counts only current project and thread runs without changing mobile composer size", async ({ page }) => {
  const foreignThread = run({ id: "run:r2", payload: { thread_id: "thread:other" } });
  const foreignProject = run({ id: "run:r3", project_id: "project:other" });
  await page.setViewportSize({ width: 390, height: 844 });
  await mockBase(page, bootstrap({ runs: [run(), foreignThread, foreignProject] }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  const link = page.getByRole("link", { name: "研究运行 1" });
  await expect(link).toBeVisible();
  await expect(page.locator(".run-card, .research-popover")).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const composer = await page.locator(".composer-wrap").boundingBox();
  expect(composer.y + composer.height).toBe(await page.evaluate(() => innerHeight));
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


test("drafts an Agent profile from a Preset and confirms creation", async ({ page }) => {
  const values = agents();
  const editableCatalog = catalog();
  editableCatalog.models.push({ id: "gpt-5.3", endpoint: "codex" });
  let created;
  await mockChat(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: editableCatalog }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/agent-drafts/, (route) =>
    route.fulfill({ status: 201, json: agentDraft() }));
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => {
    if (route.request().method() === "GET") return route.fulfill({ json: values });
    created = route.request().postDataJSON(); values.push(created);
    return route.fulfill({ status: 201, json: created });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /数学证明/ }).click();
  const card = page.getByRole("region", { name: "Agent 草稿" });
  await expect(card).toContainText("形式化证明 Agent");
  await expect(card.getByLabel("ID")).toHaveValue("math-proof");
  await expect(card.getByLabel("Endpoint")).toHaveValue("openai-compatible");
  await page.screenshot({ path: "test-results/profile-draft-desktop.png", fullPage: true });
  await card.getByLabel("Endpoint").selectOption("codex");
  await card.getByLabel("模型").selectOption("gpt-5.3");
  await card.getByLabel("指令").fill("逐项检查并形式化证明。");
  await card.getByLabel("推理强度").selectOption("high");
  await card.getByText("权限与限制").click();
  await card.getByLabel("Sandbox").selectOption("workspace-write");
  await card.getByLabel("最大轮次").fill("20");
  await card.getByLabel("Token 预算").fill("300000");
  const skills = card.locator(".capability-picker", { hasText: "Skills" });
  await skills.getByLabel("搜索Skills").fill("文献综述");
  await skills.locator(".capability-options button").click();
  const tools = card.locator(".capability-picker", { hasText: "工具" });
  await tools.getByRole("button", { name: "移除 Lean4" }).click();
  await tools.getByLabel("搜索工具").fill("图谱");
  await tools.locator(".capability-options button").click();
  await page.setViewportSize({ width: 390, height: 844 });
  const mask = page.locator(".sidebar-mask");
  if (await mask.count()) await mask.click({ force: true });
  await expect.poll(async () => {
    const box = await page.locator(".sidebar").boundingBox();
    return box ? box.x + box.width : 0;
  }).toBeLessThanOrEqual(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: "test-results/profile-draft-mobile.png", fullPage: true });
  await card.getByLabel("名称").fill("证明助手");
  await card.getByRole("button", { name: "确认创建" }).click();
  await expect.poll(() => created).toBeTruthy();
  expect(created.name).toBe("证明助手");
  expect(created.endpoint).toBe("codex");
  expect(created.model).toBe("gpt-5.3");
  expect(created.instructions).toBe("逐项检查并形式化证明。");
  expect(created.tools).toEqual(["graph_query"]);
  expect(created.skills).toEqual(["skill-review"]);
  expect(created.options).toEqual({ reasoning_effort: "high", sandbox: "workspace-write", max_rounds: 20, token_budget: 300000 });
  await page.getByRole("link", { name: "打开 Agent 设置" }).click();
  await expect(page).toHaveURL(/\/agents\/math-proof$/);
});


test("dismisses the Agent Preset menu and restores trigger focus", async ({ page }) => {
  await mockChat(page);
  await page.goto("/chat/thread%3At1");
  const trigger = page.getByRole("button", { name: "起草 Agent" });
  await trigger.click();
  await expect(page.getByRole("menu")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("menu")).toHaveCount(0);
  await expect(trigger).toBeFocused();
});


test("keeps the Profile draft local and discards it on cancel", async ({ page }) => {
  let creates = 0;
  await mockChat(page);
  await page.route(/\/api\/v1\/projects\/project%3Atest\/agent-drafts/, (route) =>
    route.fulfill({ status: 201, json: agentDraft() }));
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => {
    if (route.request().method() === "POST") creates += 1;
    return route.fulfill({ json: agents() });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /数学证明/ }).click();
  const card = page.getByRole("region", { name: "Agent 草稿" });
  await expect(card).toBeVisible();
  await card.getByLabel("名称").fill("不会保存");
  await card.getByRole("button", { name: "取消" }).click();
  await expect(card).toHaveCount(0);
  expect(creates).toBe(0);
});


test("blocks confirmation while a Preset Tool is unavailable and shows id and status", async ({ page }) => {
  const draft = agentDraft({ tools: [{ id: "lean4", status: "unavailable", reason: "not_installed" }], confirmable: false,
    issues: ["tool unavailable: lean4 (unavailable / not_installed)"] });
  await mockChat(page);
  await page.route(/\/api\/v1\/projects\/project%3Atest\/agent-drafts/, (route) =>
    route.fulfill({ status: 201, json: draft }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => {
    const value = catalog();
    value.tools = value.tools.filter((tool) => tool.id !== "lean4");
    return route.fulfill({ json: value });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /数学证明/ }).click();
  const card = page.getByRole("region", { name: "Agent 草稿" });
  await expect(card.getByRole("alert")).toContainText("Tool 不可用：lean4（unavailable / not_installed）");
  const submit = card.getByRole("button", { name: "确认创建", exact: true });
  await expect(submit).toHaveText("确认创建");
  await expect(submit).toBeDisabled();
  await card.getByRole("button", { name: "移除 lean4" }).click();
  await expect(submit).toBeEnabled();
});


test("shows server-side create errors inside the draft card", async ({ page }) => {
  await mockChat(page);
  await page.route(/\/api\/v1\/projects\/project%3Atest\/agent-drafts/, (route) =>
    route.fulfill({ status: 201, json: agentDraft() }));
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => route.request().method() === "POST"
    ? route.fulfill({ status: 400, json: { detail: "tool unavailable: lean4 (missing)" } })
    : route.fulfill({ json: agents() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /数学证明/ }).click();
  const card = page.getByRole("region", { name: "Agent 草稿" });
  await card.getByRole("button", { name: "确认创建" }).click();
  await expect(card.getByRole("alert")).toContainText("tool unavailable: lean4 (missing)");
  await expect(page).toHaveURL(/\/chat\/thread%3At1$/);
});
