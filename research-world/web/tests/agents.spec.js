import { expect, test } from "@playwright/test";
import { agents, catalog, mockBase } from "./fixtures";


test("offers recognizable runtime, model and effort choices from the catalog", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("Runtime")).toHaveValue("openai-compatible");
  await expect(page.getByLabel("Runtime").locator("option")).toHaveCount(2);
  await expect(page.getByLabel("模型")).toHaveValue("qwen3.7-flash");
  await expect(page.getByLabel("推理强度")).toHaveValue("high");
  await expect(page.locator(".capability-picker", { hasText: "工具" }).locator(".capability-chip")).not.toContainText("未识别");
  await page.screenshot({ path: "test-results/agents-desktop.png", fullPage: true });
});


test("adds and removes skills via searchable catalog entries", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  const picker = page.locator(".capability-picker", { hasText: "Skills" });
  await picker.getByLabel("搜索Skills").fill("综述");
  await picker.locator(".capability-options button").first().click();
  await expect(picker.locator(".capability-chip")).toHaveCount(1);
  await expect(picker.locator(".capability-chip")).toContainText("文献综述");
  await picker.getByRole("button", { name: "移除 文献综述" }).click();
  await expect(picker.locator(".capability-chip")).toHaveCount(0);
});


test("saves the agent through the real API with advanced settings", async ({ page }) => {
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    if (route.request().method() === "PUT") { saved = route.request().postDataJSON(); return route.fulfill({ json: saved }); }
    return route.fulfill({ json: agents()[0] });
  });
  await page.goto("/agents/research-assistant");
  await page.locator(".agent-advanced summary").click();
  const sandbox = page.getByLabel("Sandbox");
  await expect(sandbox.locator("option")).toHaveCount(2);
  await expect(sandbox.locator("option").nth(0)).toHaveAttribute("value", "read-only");
  await expect(sandbox.locator("option").nth(1)).toHaveAttribute("value", "workspace-write");
  await sandbox.selectOption("workspace-write");
  await page.getByLabel("最大轮次").fill("20");
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved).toBeTruthy();
  expect(saved.id).toBe("research-assistant");
  expect(saved.options.max_rounds).toBe(20);
  expect(saved.options.reasoning_effort).toBe("high");
  expect(saved.options.sandbox).toBe("workspace-write");
  await expect(page.locator(".agent-form-footer")).toContainText("已保存");
});


test("syncs the model to the chosen runtime and keeps the pair saveable", async ({ page }) => {
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    if (route.request().method() === "PUT") { saved = route.request().postDataJSON(); return route.fulfill({ json: saved }); }
    return route.fulfill({ json: agents()[0] });
  });
  await page.goto("/agents/research-assistant");
  await page.getByLabel("Runtime").selectOption("codex");
  await expect(page.getByLabel("模型")).toHaveValue("gpt-5.2");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved).toBeTruthy();
  expect(saved.runtime).toBe("codex");
  expect(saved.model).toBe("gpt-5.2");
});


test("blocks saving when the model is not in the catalog", async ({ page }) => {
  const legacy = { ...agents()[0], model: "ghost-model" };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [legacy] }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("模型")).toHaveValue("ghost-model");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("模型与 Runtime 不匹配");
});


test("blocks an unavailable runtime even when its model is recognized", async ({ page }) => {
  const unavailable = catalog();
  unavailable.runtimes[0].available = false;
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: unavailable }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("Runtime 当前不可用");
});


test("marks capabilities missing from the runtime catalog", async ({ page }) => {
  const legacy = { ...agents()[0], skills: ["ghost-skill"], tools: ["ghost-tool"], mcp_servers: ["ghost-mcp"] };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [legacy] }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip.missing")).toHaveCount(3);
  await expect(page.locator(".agent-form-footer")).toContainText("ghost-skill、ghost-tool、ghost-mcp");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
});


test("retries runtime catalog recognition after a transient failure", async ({ page }) => {
  let attempts = 0;
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => {
    attempts += 1;
    return attempts === 1 ? route.fulfill({ status: 503, json: { detail: "Runtime 暂不可用" } })
      : route.fulfill({ json: catalog() });
  });
  await page.goto("/agents/research-assistant");
  await expect(page.getByText("Runtime 目录载入失败")).toBeVisible();
  await page.getByRole("button", { name: "重试识别" }).click();
  await expect(page.getByLabel("Runtime")).toHaveValue("openai-compatible");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
});


test("keeps the long agent form scrollable", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 500 });
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  const overflow = await page.locator(".agent-form").evaluate((element) => getComputedStyle(element).overflowY);
  expect(overflow).toBe("auto");
  await expect(page.getByRole("button", { name: "保存" })).toBeVisible();
});
