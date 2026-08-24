import assert from "node:assert/strict";
import { chromium } from "playwright";

const base = process.env.TRACE_PROTOTYPE_BASE_URL || "http://127.0.0.1:8195";
const trace = "/prototype/agent-runtime?view=trace&project_id=project%3Aq49&thread_id=thread%3Aorbital&from=%2Fchat%2Fthread%3Aorbital";
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
  const expected = { running: "运行中", completed: "已完成", failed: "graph_query 失败", cancelled: "Turn 已取消" };
  for (const [state, text] of Object.entries(expected)) {
    await page.locator(".tp-scene select").selectOption(state);
    await assertText(page, text);
    await geometry(page, width);
  }
  for (const state of ["empty", "loading"]) {
    await page.locator(".tp-scene select").selectOption(state);
    assert.equal(await page.locator(".tp-inspector,.tp-tree").count(), 0);
    await geometry(page, width);
    await page.getByRole("button", { name: "查看 running fixture" }).click();
  }
}

async function assertText(page, text) {
  const matches = await page.getByText(text, { exact: false }).all();
  const visibility = await Promise.all(matches.map((match) => match.isVisible()));
  assert.ok(visibility.some(Boolean), `missing visible text: ${text}`);
}

async function interactions(page) {
  await page.locator(".tp-scene select").selectOption("failed");
  await page.getByRole("button", { name: /graph_query 失败/ }).click();
  assert.ok(await page.locator("#tool-search").isVisible());
  await page.locator(".tp-search input").fill("graph_query");
  assert.equal(await page.locator(".tp-row").count(), 4);
  await page.locator(".tp-search input").fill("");
  await page.getByRole("button", { name: "折叠" }).click();
  assert.equal(await page.locator(".tp-row").count(), 3);
  await page.getByRole("button", { name: "展开" }).click();
  assert.equal(await page.locator(".tp-row").count(), 14);
  await page.locator(".tp-select select").selectOption("tool");
  assert.equal(await page.locator("#tool-long-json,#tool-large-output,#tool-search").count(), 3);
  await page.locator(".tp-select select").selectOption("all");
  await page.locator(".tp-errors input").check();
  assert.equal(await page.locator("#tool-search").count(), 1);
  await page.locator(".tp-errors input").uncheck();
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
  await assertText(page, "282799 bytes");
  assert.equal(await page.locator(".tp-terminal pre").evaluate((node) => node.textContent.length), 262144);
  await assertText(page, "其余 20655 bytes 已截断");
  assert.equal(await locallyScrollable(page, ".tp-terminal"), true);
  await page.locator(".tp-bounded .tp-icon-button").click();
  assert.equal((await page.evaluate(() => navigator.clipboard.readText())).length, 262144);
  await page.screenshot({ path: `${shots}/trace-long-output-playwright.png`, fullPage: false });
  await page.locator(".tp-inspector>nav button").nth(3).click();
  await assertText(page, "normalized diff");
  await page.locator(".tp-inspector>nav button").nth(4).click();
  assert.equal(await page.getByRole("button", { name: "打开 Artifact" }).isDisabled(), true);
}

async function navigation(page) {
  const cases = [
    ["project%3Aq49", "", "%2Fprojects", "/projects", "返回 Project"],
    ["project%3Aq49", "", "%2Fmap%3Fnode%3Dnode%253Afixture-running", "/map?node=node%3Afixture-running", "返回 Graph"],
    ["project%3Aq49", "thread%3Aorbital", "%2Fchat%2Fthread%3Aorbital", "/chat/thread%3Aorbital", "返回 Chat"],
    ["project%3Aq49", "thread%3Aorbital", "https%3A%2F%2Fevil.example%2Fx", "/chat/thread%3Aorbital", "返回 Chat"],
    ["project%3Aq49", "thread%3Aorbital", "%2Fchat%2F%25E0%25A4%25A", "/chat/thread%3Aorbital", "返回 Chat"],
    ["bad", "thread%3Aorbital", "%2Fmap", "/projects", "返回 Project"],
  ];
  for (const item of cases) await navigationCase(page, item);
}

async function navigationCase(page, [project, thread, from, href, label]) {
  const threadQuery = thread ? `&thread_id=${thread}` : "";
  await page.goto(`${base}/prototype/agent-runtime?view=trace&project_id=${project}${threadQuery}&from=${from}`);
  assert.equal(await page.locator(".tp-back-chat").getAttribute("href"), href);
  assert.equal((await page.locator(".tp-back-chat").innerText()).trim(), label);
}

async function desktop(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, permissions: ["clipboard-read", "clipboard-write"] });
  const page = await context.newPage();
  await page.goto(`${base}${trace}`);
  await stateMatrix(page, 1440);
  await interactions(page);
  await longContent(page);
  await largeContent(page);
  assert.equal(await page.locator(".tp-relations a").count(), 1);
  assert.equal(await page.locator(".tp-relations a").getAttribute("href"), "/map?node=node%3Afixture-running");
  assert.equal(await page.locator(".tp-relations button:disabled").count(), 6);
  await geometry(page, 1440);
  await page.goto(`${base}${trace}`);
  await page.locator(".tp-overview").waitFor();
  await page.screenshot({ path: `${shots}/trace-desktop-playwright.png`, fullPage: false });
  await navigation(page);
  await context.close();
}

async function mobile(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto(`${base}${trace}`);
  await stateMatrix(page, 390);
  await geometry(page, 390);
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
  await desktop(browser);
  await mobile(browser);
  console.log("issue64 prototype QA passed");
} finally {
  await browser.close();
}
