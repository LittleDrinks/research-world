import assert from "node:assert/strict";
import { chromium } from "playwright";
import { truncateUtf8 } from "../src/prototype/agent-runtime/trace-content.js";

const base = process.env.TRACE_PROTOTYPE_BASE_URL || "http://127.0.0.1:8195";
const trace = "/prototype/agent-runtime?view=trace&project_id=project%3Aq49&thread_id=thread%3Aorbital&run_id=fixture%3Arun-running&from=%2Fchat%2Fthread%3Aorbital";
const shots = "../../docs/adr/assets/0029-trace-ui/prototype";

async function geometry(page, width) {
  const result = await page.evaluate(() => {
    const overflow = [document.body, document.documentElement].some((node) => node.scrollWidth > innerWidth);
    const rows = [...document.querySelectorAll(".tp-row")].filter((node) => node.getBoundingClientRect().height);
    const overlaps = rows.flatMap((row) => {
      const rects = [...row.children]
        .map((node) => node.getBoundingClientRect())
        .filter((rect) => rect.width && rect.height)
        .sort((a, b) => a.x - b.x);
      return rects.slice(1).flatMap((rect, index) => (
        rects[index].right > rect.left + .5 ? [[rects[index].right, rect.left]] : []
      ));
    });
    return { overflow, overlaps };
  });
  assert.equal(result.overflow, false, `${width}px page overflow`);
  assert.deepEqual(result.overlaps, [], `${width}px row overlap`);
}

async function stateMatrix(page, width) {
  const expected = { running: "运行中", completed: "已完成", failed: "graph_query 失败", cancelled: "Turn 2 已取消" };
  for (const entry of Object.entries(expected)) await visibleScene(page, width, entry);
  for (const state of ["empty", "loading"]) await isolatedScene(page, width, state);
  await page.locator(".tp-scene select").selectOption("running");
  await selectionCleared(page);
}

async function visibleScene(page, width, [state, text]) {
  await page.locator(".tp-scene select").selectOption(state);
  await assertText(page, text);
  await selectionCleared(page);
  await geometry(page, width);
  await page.locator("#tool-long-json").click();
}

async function isolatedScene(page, width, state) {
  await page.locator(".tp-scene select").selectOption(state);
  assert.equal(await page.locator(".tp-inspector,.tp-tree").count(), 0);
  await geometry(page, width);
  await page.getByRole("button", { name: "查看 running fixture" }).click();
  await selectionCleared(page);
  await page.locator("#tool-long-json").click();
}

async function selectionCleared(page) {
  assert.equal(await page.locator('.tp-row[aria-selected="true"]').count(), 0);
  assert.ok((await page.locator(".tp-inspector-empty").innerText()).includes("未选择任何 row"));
}

async function assertText(page, text) {
  await page.locator(".tp-shell").waitFor();
  const matches = await page.getByText(text, { exact: false }).all();
  const visibility = await Promise.all(matches.map((match) => match.isVisible()));
  assert.ok(visibility.some(Boolean), `missing visible text: ${text}`);
}

async function interactions(page) {
  await page.locator(".tp-scene select").selectOption("failed");
  await page.locator(".tp-search input").fill("no-match");
  await page.getByRole("button", { name: /graph_query 失败/ }).click();
  assert.equal(await page.locator(".tp-search input").inputValue(), "");
  assert.equal(await page.locator("#tool-search").getAttribute("aria-selected"), "true");
  await assertText(page, "tool · failed · fixture");
  await page.getByRole("button", { name: "概览" }).click();
  await failedInspector(page);
  await filterInteractions(page);
}

async function filterInteractions(page) {
  await page.locator(".tp-search input").fill("graph_query");
  assert.equal(await page.locator(".tp-row").count(), 5);
  await page.locator(".tp-search input").fill("");
  await page.getByRole("button", { name: "折叠" }).click();
  assert.equal(await page.locator(".tp-row").count(), 3);
  await page.getByRole("button", { name: "展开" }).click();
  assert.equal(await page.locator(".tp-row").count(), 15);
  await page.locator(".tp-select select").selectOption("tool");
  assert.equal(await page.locator("#tool-long-json,#tool-large-output,#tool-search").count(), 3);
  await page.locator(".tp-select select").selectOption("all");
  await page.locator(".tp-errors input").check();
  assert.equal(await page.locator("#tool-search").count(), 1);
  await page.locator(".tp-errors input").uncheck();
}

async function failedInspector(page) {
  assert.deepEqual(await inspectorField(page, "Status"), { value: "failed", source: "existing" });
  assert.deepEqual(await inspectorField(page, "Duration"), { value: "2m 11s", source: "derived" });
  assert.deepEqual(await inspectorField(page, "Session"), { value: "session-b", source: "derived" });
  assert.deepEqual(await inspectorField(page, "Parent"), { value: "turn-execute", source: "existing" });
  assert.deepEqual(await inspectorField(page, "Event type"), { value: "tool", source: "existing" });
  assert.deepEqual(await inspectorField(page, "Event id"), { value: "tool-search", source: "existing" });
}

async function inspectorField(page, label) {
  return page.locator(".tp-inspector-grid div").filter({ has: page.locator("dt", { hasText: label }) }).evaluate((node) => ({
    value: node.querySelector("dd").textContent,
    source: node.querySelector(".tp-source").dataset.source,
  }));
}

async function cancelledHierarchy(page) {
  await page.locator(".tp-scene select").selectOption("cancelled");
  const rows = await page.locator(".tp-row").evaluateAll((nodes) => nodes.map((node) => ({
    id: node.id,
    depth: node.style.getPropertyValue("--depth"),
    cancelled: node.textContent.includes("Turn 已取消"),
  })));
  assertCancelledRows(rows);
  await page.locator("#turn-execute").click();
  await page.getByRole("button", { name: "概览" }).click();
  assert.deepEqual(await inspectorField(page, "Status"), { value: "cancelled", source: "existing" });
  assert.deepEqual(await inspectorField(page, "Session"), { value: "session-b", source: "derived" });
  assert.deepEqual(await inspectorField(page, "Event type"), { value: "turn", source: "existing" });
  await page.locator(".tp-scene select").selectOption("running");
  await selectionCleared(page);
}

function assertCancelledRows(rows) {
  const ids = rows.map((row) => row.id);
  assert.ok(ids.indexOf("session-b") < ids.indexOf("turn-execute"));
  assert.ok(ids.indexOf("turn-execute") < ids.indexOf("tool-search"));
  assert.deepEqual(rows.filter((row) => row.cancelled), [{ id: "turn-execute", depth: "3", cancelled: true }]);
  assert.equal(rows.find((row) => row.id === "session-b").depth, "2");
  assert.equal(rows.find((row) => row.id === "tool-search").depth, "4");
}

async function longContent(page) {
  await page.locator("#tool-long-json").click();
  await page.getByRole("button", { name: "输入" }).click();
  await assertText(page, "1102 行");
  assert.equal(await lineCount(page), 200);
  await page.getByRole("button", { name: "展开全部 1102 行" }).click();
  assert.equal(await lineCount(page), 1102);
  assert.equal(await locallyScrollable(page, ".tp-code"), true);
  await page.locator(".tp-bounded .tp-icon-button").click();
  assert.ok((await page.evaluate(() => navigator.clipboard.readText())).includes("event_220"));
}

async function lineCount(page) {
  return page.locator(".tp-code code").evaluate((node) => node.textContent.split("\n").length);
}

async function locallyScrollable(page, selector) {
  return page.locator(selector).evaluate((node) => node.scrollHeight > node.clientHeight || node.scrollWidth > node.clientWidth);
}

async function largeContent(page) {
  await page.locator("#tool-large-output").click();
  await page.getByRole("button", { name: "输出" }).click();
  await assertText(page, "282805 bytes");
  const visible = await page.locator(".tp-terminal pre").innerText();
  assert.equal(new TextEncoder().encode(visible).length, 262143);
  assert.equal(visible.includes("�"), false);
  await assertText(page, "已显示 262143 bytes（上限 256 KiB）");
  await assertText(page, "其余 20662 bytes 已截断");
  assert.equal(await locallyScrollable(page, ".tp-terminal"), true);
  await page.locator(".tp-bounded .tp-icon-button").click();
  assert.equal(new TextEncoder().encode(await page.evaluate(() => navigator.clipboard.readText())).length, 262143);
  await page.screenshot({ path: `${shots}/trace-long-output-playwright.png`, fullPage: false });
  await page.locator(".tp-inspector>nav button").nth(3).click();
  await assertText(page, "normalized diff");
  await page.locator(".tp-inspector>nav button").nth(4).click();
  assert.equal(await page.getByRole("button", { name: "打开 Artifact" }).isDisabled(), true);
}

function utf8Boundaries() {
  const cases = [
    { value: "中文", limit: 4, visible: "中", visibleBytes: 3, remainingBytes: 3 },
    { value: "A😀B", limit: 4, visible: "A", visibleBytes: 1, remainingBytes: 5 },
    { value: "你😀好", limit: 7, visible: "你😀", visibleBytes: 7, remainingBytes: 3 },
  ];
  for (const item of cases) assert.deepEqual(truncateUtf8(item.value, item.limit), {
    visible: item.visible, visibleBytes: item.visibleBytes,
    totalBytes: new TextEncoder().encode(item.value).length, remainingBytes: item.remainingBytes,
  });
}

async function keyboardTree(page) {
  for (let attempt = 0; attempt < 2; attempt += 1) await keyboardTreeAttempt(page);
}

async function keyboardTreeAttempt(page) {
  await page.goto(`${base}${trace}`);
  const stage = page.locator("#stage-execute");
  await stage.focus();
  assert.equal(await stage.getAttribute("aria-expanded"), "true");
  await page.keyboard.press("ArrowLeft");
  assert.equal(await stage.getAttribute("aria-expanded"), "false");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "step-1");
  await page.keyboard.press("ArrowLeft");
  assert.equal(await page.locator("#step-1").getAttribute("aria-expanded"), "false");
  await page.keyboard.press("ArrowLeft");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "stage-execute");
  assert.equal(await page.locator("#tool-large-output").getAttribute("aria-expanded"), null);
}

async function clipboardFailures(browser) {
  for (const [mode, label] of [["missing", "剪贴板不可用"], ["sync", "复制失败"], ["reject", "复制失败"]]) {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${base}${trace}`);
    await stubClipboard(page, mode);
    await page.locator(".tp-header-actions .tp-icon-button").click();
    await page.getByRole("button", { name: label }).waitFor();
    assert.equal((await page.locator(".tp-header-actions").getByRole("status").innerText()).trim(), label);
    await context.close();
  }
}

async function stubClipboard(page, mode) {
  await page.evaluate((kind) => {
    const writeText = () => {
      if (kind === "sync") throw new Error("blocked");
      return Promise.reject(new DOMException("denied", "NotAllowedError"));
    };
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: kind === "missing" ? undefined : { writeText } });
  }, mode);
}

async function navigation(page) {
  const cases = [
    ["project%3Aq49", "", "%2Fprojects", "/projects", "返回 Project"],
    ["project%3Aq49", "", "%2Fmap", "/map", "返回 Graph"],
    ["project%3Aq49", "", "%2Fmap%3Fnode%3Dnode%253Afake", "/map", "返回 Graph"],
    ["project%3Aq49", "thread%3Aorbital", "%2Fchat%2Fthread%3Aorbital", "/chat/thread%3Aorbital", "返回 Chat"],
    ["project%3Aq49", "thread%3Aorbital", "https%3A%2F%2Fevil.example%2Fx", "/chat/thread%3Aorbital", "返回 Chat"],
    ["project%3Aq49", "thread%3Aorbital", "%2Fchat%2F%25E0%25A4%25A", "/chat/thread%3Aorbital", "返回 Chat"],
    ["bad", "thread%3Aorbital", "%2Fmap", "/projects", "返回 Project"],
  ];
  for (const item of cases) await navigationCase(page, item);
  await runIdValidation(page);
}

async function navigationCase(page, [project, thread, from, href, label]) {
  const threadQuery = thread ? `&thread_id=${thread}` : "";
  await page.goto(`${base}/prototype/agent-runtime?view=trace&project_id=${project}${threadQuery}&from=${from}`);
  const back = page.locator(".tp-back-chat,.tp-state-screen a");
  assert.equal(await back.getAttribute("href"), href);
  assert.equal((await back.innerText()).trim(), label);
}

async function runIdValidation(page) {
  await runCase(page, "thread%3Aorbital", "bad", "run_id 非法", "fixture:run-running");
  await runCase(page, "thread%3Aorbital", "fixture%3Arun-unknown", "run_id 不存在", "fixture:run-running");
  await runCase(page, "thread%3Aarchive", "fixture%3Arun-running", "run_id 不属于当前 Project/Thread", "fixture:run-completed");
  await runCase(page, "thread%3Aforeign", "fixture%3Arun-failed", "thread_id 不属于当前 Project", "fixture:run-failed");
  await page.goto(`${base}/prototype/agent-runtime?view=trace&project_id=project%3Aother&run_id=fixture%3Arun-running&from=%2Fmap`);
  await assertText(page, "project_id 无效或不可访问");
  assert.equal(await page.locator(".tp-run-header,.tp-tree").count(), 0);
  assert.equal(await page.getByRole("link", { name: "返回 Project" }).getAttribute("href"), "/projects");
  await page.goto(`${base}${trace.replace("fixture%3Arun-running", "fixture%3Arun-failed")}`);
  assert.equal(await page.locator(".tp-context-banner").count(), 0);
  await assertText(page, "fixture:run-failed");
  assert.equal(await page.locator(".tp-scene select").inputValue(), "failed");
}

async function runCase(page, thread, run, notice, fallback) {
  await page.goto(`${base}/prototype/agent-runtime?view=trace&project_id=project%3Aq49&thread_id=${thread}&run_id=${run}&from=%2Fmap`);
  await assertText(page, notice);
  assert.equal((await page.locator(".tp-heading h1 code").innerText()).trim(), fallback);
}

async function nodeDestination(page) {
  const response = await page.request.get(`${base}/api/v1/projects`);
  assert.deepEqual(await response.json(), []);
  const node = page.locator(".tp-relations button").filter({ hasText: "Node" });
  assert.equal(await node.isDisabled(), true);
  await assertText(page, "当前 Compose 无可达 Node");
  assert.equal(await page.locator('.tp-relations a[href*="node="]').count(), 0);
  assert.equal(await page.locator(".tp-node-disabled").isDisabled(), true);
  assert.equal(await page.locator('.tp-heading a[href*="node="]').count(), 0);
}

async function desktop(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, permissions: ["clipboard-read", "clipboard-write"] });
  const page = await context.newPage();
  await page.goto(`${base}${trace}`);
  await stateMatrix(page, 1440);
  await interactions(page);
  await cancelledHierarchy(page);
  await longContent(page);
  await largeContent(page);
  assert.equal(await page.locator(".tp-relations button:disabled").count(), 7);
  await nodeDestination(page);
  await geometry(page, 1440);
  await page.goto(`${base}${trace}`);
  await page.locator(".tp-overview").waitFor();
  await page.screenshot({ path: `${shots}/trace-desktop-playwright.png`, fullPage: false });
  await navigation(page);
  await context.close();
  await clipboardFailures(browser);
}

async function mobile(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto(`${base}${trace}`);
  await stateMatrix(page, 390);
  await geometry(page, 390);
  await page.locator(".tp-run-header").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${shots}/trace-mobile-390-playwright.png`, fullPage: false });
  await page.locator("#tool-large-output").click();
  const bounds = await page.locator(".tp-inspector.open").boundingBox();
  assert.deepEqual(bounds, { x: 0, y: 53, width: 390, height: 791 });
  await page.screenshot({ path: `${shots}/trace-mobile-inspector-390-playwright.png`, fullPage: false });
  await page.getByRole("button", { name: "关闭检查器" }).click();
  await page.getByRole("button", { name: "打开运行列表" }).click();
  assert.ok(await page.locator(".tp-run-rail").isVisible());
  await geometry(page, 390);
  await context.close();
}

const browser = await chromium.launch({ headless: true });
try {
  utf8Boundaries();
  await desktop(browser);
  const keyboardContext = await browser.newContext();
  await keyboardTree(await keyboardContext.newPage());
  await keyboardContext.close();
  await mobile(browser);
  console.log("issue64 prototype QA passed");
} finally {
  await browser.close();
}
