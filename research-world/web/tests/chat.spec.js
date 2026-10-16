import { expect, test } from "@playwright/test";
import { agentDraft, agents, bootstrap, catalog, mockBase, node, run, sse, thread, threadDetail } from "./fixtures";


async function mockChat(page, detail = threadDetail(), onThread) {
  await mockBase(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => { onThread?.(); return route.fulfill({ json: detail }); });
  await page.route(/\/api\/v1\/projects\/project%3Atest\/threads/, (route) => route.fulfill({ json: [thread()] }));
}


function reportStages() {
  return ["projection", "citation_validation", "rendering", "output_validation", "persistence"].map((name) => ({ name, status: "completed" }));
}


function reportResult(publication) {
  return { status: "published", title: "测试项目", publication, stages: reportStages(), assessment: { delivery_level: 4, minimum_source_level: "published", gaps: [] } };
}


function failedCitationReport() {
  return { status: "failed", stages: [{ name: "projection", status: "completed" }, { name: "citation_validation", status: "failed" }], assessment: { gaps: [{ code: "source_missing", path: "facts[0]", value: "node:s" }] } };
}


function failedRenderingReport() {
  return { status: "failed", stages: [{ name: "projection", status: "completed" }, { name: "citation_validation", status: "completed" }, { name: "rendering", status: "failed" }], assessment: { gaps: [{ code: "rendering_invalid", path: "html", value: null }] } };
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
  await page.getByLabel("消息").fill("下一步做什么？");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("先生成并筛选多个研究方向。")).toBeVisible();
  expect(request).toEqual({ message: "下一步做什么？" });
});


test("publishes a validated report card, previews, downloads and saves a version", async ({ page }) => {
  await mockChat(page);
  const publication = { id: "publication:p1", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  const content = "<!doctype html><html><body>Immutable report content</body></html>";
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => route.fulfill({ status: 201, json: reportResult(publication) }));
  await page.route(/\/threads\/thread%3At1\/report\/save$/, (route) => route.fulfill({ status: 201, json: { id: "report:v1" } }));
  await page.context().route(/\/api\/v1\/threads\/.*\/report\/.*\/content(?:\?.*)?$/, (route) => route.fulfill(route.request().url().includes("download=true")
    ? { body: content, headers: { "content-type": "text/html", "content-disposition": "attachment; filename=report.html" } }
    : { contentType: "text/html", body: content }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "生成报告" }).click();
  await expect(page.getByText("已校验")).toBeVisible();
  await expect(page.getByTitle("报告预览")).toHaveAttribute("sandbox", "");
  const downloadLink = page.getByRole("link", { name: /下载 HTML/ });
  await expect(downloadLink).toHaveAttribute("download", "");
  await expect(downloadLink).toHaveAttribute("href", "/api/v1/threads/thread%3At1/report/publication%3Ap1/content?download=true");
  await expect(page.frameLocator('iframe[title="报告预览"]').getByText("Immutable report content")).toBeVisible();
  expect(await page.evaluate(async (href) => (await fetch(href)).text(), await downloadLink.getAttribute("href"))).toBe(content);
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("link", { name: /下载 HTML/ }).click();
  expect((await downloadEvent).url()).toContain("/report/publication%3Ap1/content?download=true");
  await page.getByLabel("报告名称").fill("V1");
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page.getByText("已保存版本 report:v1")).toBeVisible();
});


test("interleaves a report event at its trace turn and sequence", async ({ page }) => {
  const publication = { id: "publication:p4", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  const turns = [{ id: "t1", input: [{ type: "text", text: "先发布" }], output: "报告之后", events: [] }, { id: "t2", input: [{ type: "text", text: "后续问题" }], output: "后续答复", events: [] }];
  const runtime = { ...threadDetail().runtime, turns, reports: [{ ...reportResult(publication), turn_id: "t1", seq: 2 }] };
  await mockChat(page, threadDetail({ runtime, report_publications: [{ ...publication, title: "测试项目" }] }));
  await page.goto("/chat/thread%3At1");
  const text = await page.locator(".message-list").innerText();
  expect(text.indexOf("报告已发布")).toBeGreaterThan(text.indexOf("先发布"));
  expect(text.indexOf("报告已发布")).toBeLessThan(text.indexOf("报告之后"));
  await expect(page.locator(".report-message")).toHaveCount(1);
});


test("renders a failed traced report without a publication key", async ({ page }) => {
  const runtime = { ...threadDetail().runtime, reports: [{ ...failedCitationReport(), turn_id: "t1", seq: 2 }], turns: [{ id: "t1", input: [], output: "失败后继续", events: [] }] };
  await mockChat(page, threadDetail({ runtime }));
  await page.goto("/chat/thread%3At1");
  await expect(page.locator(".report-message")).toHaveCount(1);
  await expect(page.getByRole("alert")).toContainText("source_missing");
});


test("keeps failed publication stages and gaps without refreshing", async ({ page }) => {
  await mockChat(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const failed = failedCitationReport();
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => route.fulfill({ status: 422, json: failed }));
  await page.goto("/chat/thread%3At1");
  const refresh = page.waitForRequest(/\/api\/v1\/threads\/thread%3At1$/, { timeout: 200 }).then(() => true).catch(() => false);
  await page.getByRole("button", { name: "生成报告" }).click();
  await expect(page.getByRole("alert")).toContainText("source_missing: facts[0] = null");
  await expect(page.getByRole("link", { name: /下载 HTML/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "重试" })).toBeVisible();
  await expect(page.locator(".report-stages .completed")).toHaveCount(1);
  await expect(page.locator(".report-stages .failed")).toHaveCount(1);
  await expect(page.locator(".report-stages")).not.toContainText("生成");
  expect(await refresh).toBe(false);
});


test("restores named thread report cards after reload", async ({ page }) => {
  const reports = [{ id: "report:v1", title: "V1", publication_id: "publication:p1" }];
  await mockChat(page, threadDetail({ reports }));
  await page.context().route(/\/report\/publication%3Ap1\/content/, (route) => route.fulfill({ contentType: "text/html", body: "<!doctype html><html><body>Immutable saved version</body></html>" }));
  await page.goto("/chat/thread%3At1");
  await expect(page.getByText("V1")).toBeVisible();
  await page.reload();
  await expect(page.getByText("V1")).toBeVisible();
  await expect(page.getByRole("link", { name: "下载" })).toHaveAttribute("download", "");
  const opened = page.waitForEvent("popup");
  await page.getByRole("link", { name: "预览" }).click();
  await expect((await opened).locator("body")).toHaveText("Immutable saved version");
});


test("restores a Runtime-published report as a complete chat message", async ({ page }) => {
  const publication = { id: "publication:p1", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  const detail = threadDetail({ runtime: { ...threadDetail().runtime, reports: [reportResult(publication)] }, report_publications: [{ ...publication, title: "测试项目" }] });
  await mockChat(page, detail);
  await page.goto("/chat/thread%3At1");
  await expect(page.getByText("报告已发布")).toBeVisible();
  await expect(page.getByTitle("报告预览")).toHaveAttribute("sandbox", "");
  await expect(page.getByRole("link", { name: /下载 HTML/ })).toHaveAttribute("download", "");
  await expect(page.locator(".report-message")).toHaveCount(1);
  await page.reload();
  await expect(page.getByText("报告已发布")).toBeVisible();
  await expect(page.locator(".report-message")).toHaveCount(1);
});


test("restores a retry publication from the Thread record without duplicating Trace cards", async ({ page }) => {
  const failed = failedCitationReport();
  const publication = { id: "publication:p2", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  await mockRetryPublication(page, failed, publication);
  await page.goto("/chat/thread%3At1");
  const message = page.locator(".report-message");
  await assertFailedReport(message);
  await message.getByRole("button", { name: "重试" }).click();
  await expect(page.locator(".report-message")).toHaveCount(1);
  await expect(page.getByTitle("报告预览")).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.reload();
  await expect(page.locator(".report-message")).toHaveCount(1);
  await expect(page.getByTitle("报告预览")).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
});


async function mockRetryPublication(page, failed, publication) {
  let detail = threadDetail({ runtime: { ...threadDetail().runtime, reports: [failed] }, report_publications: [] });
  await mockChat(page, detail);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: detail }));
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => {
    detail = threadDetail({ runtime: { ...threadDetail().runtime, reports: [failed] }, report_publications: [{ ...publication, title: "测试项目" }] });
    return route.fulfill({ status: 201, json: reportResult(publication) });
  });
}


function deferred() {
  let resolve;
  return { wait: new Promise((value) => { resolve = value; }), release: () => resolve() };
}


async function blockThreadRefresh(page) {
  const gate = deferred();
  let block = false;
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => block ? gate.wait.then(() => route.fulfill({ json: threadDetail() })) : route.fulfill({ json: threadDetail() }));
  return { block: () => { block = true; }, release: gate.release };
}


async function mockReportProgressPrompt(page, onStart) {
  const start = { sessionUpdate: "tool_call", title: "发布科研报告", kind: "other", status: "in_progress" };
  const updates = [["tool", { update: start }], ["tool", { update: { sessionUpdate: "tool_call_update", status: "completed" } }], ["done", { stop_reason: "end_turn" }]];
  await page.route(/\/threads\/thread%3At1\/prompts/, (route) => { onStart(); return route.fulfill(sse(updates)); });
}


async function mockOverlappingRetry(page, failed, publication) {
  const first = deferred();
  let requests = 0;
  let detail = threadDetail({ runtime: { ...threadDetail().runtime, reports: [failed] }, report_publications: [] });
  await mockChat(page, detail);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: detail }));
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, async (route) => {
    requests += 1;
    if (requests === 1) { await first.wait; return route.fulfill({ status: 422, json: failedRenderingReport() }); }
    detail = threadDetail({ runtime: { ...threadDetail().runtime, reports: [failed] }, report_publications: [{ ...publication, title: "测试项目" }] });
    return route.fulfill({ status: 201, json: reportResult(publication) });
  });
  return first;
}


async function mockOutOfOrderPublicationRefresh(page, older, newer) {
  const stale = deferred();
  const entered = deferred();
  const details = [threadDetail({ report_publications: [older] }), threadDetail({ report_publications: [newer] })];
  let detail = threadDetail();
  let refreshes = 0;
  let publishes = 0;
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, async (route) => {
    refreshes += 1;
    if (refreshes < 3) return route.fulfill({ json: detail });
    if (refreshes !== 3) return route.fulfill({ json: detail });
    entered.release(); await stale.wait;
    return route.fulfill({ json: details[0] });
  });
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => {
    detail = details[publishes];
    return route.fulfill({ status: 201, json: reportResult([older, newer][publishes++]) });
  });
  return { entered, release: stale.release };
}


async function assertFailedReport(message) {
  await expect(message.getByRole("alert")).toContainText("source_missing");
  await expect(message.locator(".report-stages .completed")).toHaveCount(1);
  await expect(message.locator(".report-stages .failed")).toHaveCount(1);
  await expect(message.getByRole("link", { name: /下载 HTML/ })).toHaveCount(0);
}


test("keeps retry failure stages and gaps without refreshing", async ({ page }) => {
  const first = failedCitationReport();
  const runtime = { ...threadDetail().runtime, reports: [{ ...first, turn_id: "t1", seq: 2 }] };
  await mockChat(page, threadDetail({ runtime }));
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => route.fulfill({ status: 422, json: failedRenderingReport() }));
  await page.goto("/chat/thread%3At1");
  const refresh = page.waitForRequest(/\/api\/v1\/threads\/thread%3At1$/, { timeout: 200 }).then(() => true).catch(() => false);
  await page.locator(".report-message").getByRole("button", { name: "重试" }).click();
  await expect(page.getByRole("alert")).toContainText("rendering_invalid");
  await expect(page.locator(".report-stages .completed")).toHaveCount(2);
  await expect(page.locator(".report-stages .failed")).toHaveCount(1);
  expect(await refresh).toBe(false);
});


test("keeps a published preview and saved version when refresh fails", async ({ page }) => {
  const publication = { id: "publication:p3", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  let refreshFails = false;
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill(refreshFails ? { status: 500, json: { detail: "reload failed" } } : { json: threadDetail() }));
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => { refreshFails = true; return route.fulfill({ status: 201, json: reportResult(publication) }); });
  await page.route(/\/threads\/thread%3At1\/report\/save$/, (route) => route.fulfill({ status: 201, json: { id: "report:v2" } }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "生成报告" }).click();
  await expect(page.getByTitle("报告预览")).toBeVisible();
  await expect(page.getByRole("status")).toContainText("报告已发布，刷新失败。");
  await page.getByLabel("报告名称").fill("V2");
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page.getByText("已保存版本 report:v2")).toBeVisible();
  await expect(page.getByTitle("报告预览")).toHaveCount(1);
});


test("renders the actual Kernel failed stage sequence", async ({ page }) => {
  const failed = { status: "failed", stages: [{ name: "projection", status: "completed" }, { name: "citation_validation", status: "completed" }, { name: "rendering", status: "failed" }], assessment: { gaps: [{ code: "rendering_invalid", path: "html", value: null }] } };
  await mockChat(page);
  await page.route(/\/threads\/thread%3At1\/report\/publish$/, (route) => route.fulfill({ status: 422, json: failed }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "生成报告" }).click();
  await expect(page.locator(".report-stages .completed")).toHaveCount(2);
  await expect(page.locator(".report-stages .failed")).toHaveCount(1);
  await expect(page.locator(".report-stages")).not.toContainText("最终校验");
});


test("shows the ACP report tool progress until Thread restoration", async ({ page }) => {
  await mockChat(page);
  const refresh = await blockThreadRefresh(page);
  await mockReportProgressPrompt(page, refresh.block);
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("生成报告");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByRole("status")).toContainText("发布科研报告");
  refresh.release();
  await expect(page.getByText("正在生成报告")).toHaveCount(0);
});


test("keeps only the newest retry response after a late callback", async ({ page }) => {
  const failed = failedCitationReport();
  const publication = { id: "publication:p5", thread_id: "thread:t1", created_at: "2026-08-26T00:00:00Z" };
  const first = await mockOverlappingRetry(page, failed, publication);
  await page.goto("/chat/thread%3At1");
  const retry = page.locator(".report-message").getByRole("button", { name: "重试" });
  await retry.click();
  await retry.click();
  await expect(page.locator(".report-message")).toHaveCount(1);
  first.release();
  await expect(page.locator(".report-message")).toHaveCount(1);
  await expect(page.getByTitle("报告预览")).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
});


test("keeps the newest publication when an older detail refresh resolves late", async ({ page }) => {
  const older = { id: "publication:old", thread_id: "thread:t1", title: "旧发布", created_at: "2026-08-26T00:00:00Z" };
  const newer = { id: "publication:new", thread_id: "thread:t1", title: "新发布", created_at: "2026-08-26T00:01:00Z" };
  const refresh = await mockOutOfOrderPublicationRefresh(page, older, newer);
  await page.goto("/chat/thread%3At1");
  const publish = page.getByRole("button", { name: "生成报告" });
  await publish.click();
  await refresh.entered.wait;
  await publish.click();
  await expect(page.locator(".message-list")).toContainText("新发布");
  refresh.release();
  await expect(page.locator(".message-list")).toContainText("新发布");
  await expect(page.locator(".message-list")).not.toContainText("旧发布");
});


test("keeps ACP report progress visible when Thread refresh fails", async ({ page }) => {
  const start = { sessionUpdate: "tool_call", title: "发布科研报告", kind: "other", status: "in_progress" };
  let refreshed = false;
  await mockChat(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill(refreshed ? { status: 500, json: { detail: "reload failed" } } : { json: threadDetail() }));
  await page.route(/\/threads\/thread%3At1\/prompts/, (route) => { refreshed = true; return route.fulfill(sse([["tool", { update: start }], ["done", { stop_reason: "end_turn" }]])); });
  await page.goto("/chat/thread%3At1");
  await page.getByLabel("消息").fill("生成报告");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByRole("status")).toContainText("发布科研报告");
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
  expect(created.tools).toEqual([]);
  expect(created.runtime).toEqual({ id: "codex", realm: "container:runtime" });
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
  await card.getByRole("button", { name: "移除 lean4" }).click();
  await card.getByRole("button", { name: "确认创建" }).click();
  await expect(card.getByRole("alert")).toContainText("tool unavailable: lean4 (missing)");
  await expect(page).toHaveURL(/\/chat\/thread%3At1$/);
});
