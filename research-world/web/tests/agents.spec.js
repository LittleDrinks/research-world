import { expect, test } from "@playwright/test";
import { agents, catalog, mockBase } from "./fixtures";


async function mockConnectorRegistry(page, registered) {
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => {
    const value = catalog();
    value.connectors.push(...registered.map(publicConnector));
    return route.fulfill({ json: value });
  });
  await page.route(/\/api\/v1\/runtime\/connectors$/, (route) => {
    const value = route.request().postDataJSON();
    registered.push(value);
    return route.fulfill({ status: 201, json: publicConnector(value) });
  });
}


function publicConnector(value) {
  return { id: value.id, name: value.name, description: "", transport: value.transport,
    source: "runtime", available: true };
}


async function beginConnector(page, id, name, transport) {
  await page.getByRole("button", { name: "添加" }).click();
  const form = page.locator(".connector-form");
  await form.getByLabel("ID").fill(id);
  await form.getByLabel("名称").fill(name);
  await form.getByLabel("Transport").selectOption(transport);
  return form;
}


test("offers recognizable endpoint, model and effort choices from the catalog", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("Endpoint")).toHaveValue("openai-compatible");
  await expect(page.getByLabel("Endpoint").locator("option")).toHaveCount(2);
  await expect(page.getByLabel("模型")).toHaveValue("qwen3.7-flash");
  await expect(page.getByLabel("推理强度")).toHaveValue("high");
  await expect(page.getByLabel("推理强度").locator("option")).toHaveCount(4);
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


test("uses canonical Runtime option defaults when AgentSpec omits options", async ({ page }) => {
  const minimal = { ...agents()[0] };
  delete minimal.options;
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [minimal] }));
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    saved = route.request().postDataJSON();
    return route.fulfill({ json: saved });
  });
  await page.goto("/agents/research-assistant");
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved).toBeTruthy();
  expect(saved.options.max_rounds).toBe(12);
  expect(saved.options.token_budget).toBe(200000);
});


test("requires non-blank name and instructions before saving", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await page.getByLabel("名称").fill("   ");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("名称不能为空");
  await page.getByLabel("名称").fill("研究助手");
  await page.getByLabel("指令").fill("\n\t");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("指令不能为空");
});


test("enforces the AgentSpec numeric option ranges", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await page.locator(".agent-advanced summary").click();
  await expect(page.getByLabel("最大轮次")).toHaveAttribute("max", "64");
  await page.getByLabel("最大轮次").fill("65");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("最大轮次必须是 1 到 64 的整数");
  await page.getByLabel("最大轮次").fill("64");
  await page.getByLabel("Token 预算").fill("0");
  await expect(page.locator(".agent-form-footer")).toContainText("Token 预算必须是正整数");
});


test("rebuilds the saved AgentSpec without legacy or unknown fields", async ({ page }) => {
  const current = agents()[0];
  const loaded = { ...current, runtime: "legacy", mcp_servers: ["legacy-mcp"], unknown: true,
    options: { ...current.options, legacy_option: "drop-me" } };
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [loaded] }));
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    saved = route.request().postDataJSON();
    return route.fulfill({ json: saved });
  });
  await page.goto("/agents/research-assistant");
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved).toBeTruthy();
  expect(saved).toEqual(current);
});


test("syncs the model to the chosen endpoint and keeps the pair saveable", async ({ page }) => {
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    if (route.request().method() === "PUT") { saved = route.request().postDataJSON(); return route.fulfill({ json: saved }); }
    return route.fulfill({ json: agents()[0] });
  });
  await page.goto("/agents/research-assistant");
  await page.getByLabel("Endpoint").selectOption("codex");
  await expect(page.getByLabel("模型")).toHaveValue("gpt-5.2");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved).toBeTruthy();
  expect(saved.endpoint).toBe("codex");
  expect(saved.model).toBe("gpt-5.2");
});


test("blocks saving when the model is not in the catalog", async ({ page }) => {
  const invalid = { ...agents()[0], model: "ghost-model" };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [invalid] }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("模型")).toHaveValue("ghost-model");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("模型与 Endpoint 不匹配");
});


test("blocks an unavailable endpoint even when its model is recognized", async ({ page }) => {
  const unavailable = catalog();
  unavailable.endpoints[0].available = false;
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: unavailable }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.locator(".agent-form-footer")).toContainText("Endpoint 当前不可用");
});


test("marks capabilities missing from the runtime catalog", async ({ page }) => {
  const invalid = { ...agents()[0], skills: ["ghost-skill"], tools: ["ghost-tool"], connectors: ["ghost-connector"] };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [invalid] }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip.missing")).toHaveCount(3);
  await expect(page.locator(".agent-form-footer")).toContainText("ghost-skill、ghost-tool、ghost-connector");
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
  await expect(page.getByLabel("Endpoint")).toHaveValue("openai-compatible");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
});


test("registers a remote Lean4 Connector and saves its selection", async ({ page }) => {
  const registered = [];
  let saved;
  await mockBase(page);
  await mockConnectorRegistry(page, registered);
  await page.route(/\/api\/v1\/agents\/research-assistant$/, (route) => {
    saved = route.request().postDataJSON();
    return route.fulfill({ json: saved });
  });
  await page.goto("/agents/research-assistant");
  const form = await beginConnector(page, "lean4", "Lean4 prover", "http");
  await form.getByLabel("URL").fill("https://lean.example/mcp");
  await page.getByRole("button", { name: "注册 Connector" }).click();
  await expect.poll(() => registered.length).toBe(1);
  expect(registered[0]).toEqual({ id: "lean4", name: "Lean4 prover", transport: "http",
    url: "https://lean.example/mcp" });
  await expect(page.locator(".capability-chip", { hasText: "Lean4 prover" })).toBeVisible();
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
  await page.getByRole("button", { name: "保存" }).click();
  await expect.poll(() => saved?.connectors).toEqual(["lean4"]);
});


test("maps one SSE header to a runtime environment reference", async ({ page }) => {
  const registered = [];
  await mockBase(page);
  await mockConnectorRegistry(page, registered);
  await page.goto("/agents/research-assistant");
  const form = await beginConnector(page, "private-db", "Private database", "sse");
  await form.getByLabel("URL").fill("https://lab.example/sse");
  await form.getByLabel("Header 名").fill("X-Lab-Api-Key");
  await form.getByLabel("来源环境变量").fill("lab_api_token");
  await form.getByRole("button", { name: "注册 Connector" }).click();
  await expect.poll(() => registered.length).toBe(1);
  expect(registered[0].headers).toEqual({ "X-Lab-Api-Key": "${lab_api_token}" });
});


test("maps one installed stdio Connector env key to a runtime environment reference", async ({ page }) => {
  const registered = [];
  await mockBase(page);
  await mockConnectorRegistry(page, registered);
  await page.goto("/agents/research-assistant");
  const form = await beginConnector(page, "lab-tools", "Lab tools", "stdio");
  await form.getByLabel("命令").fill("/opt/connectors/lab-mcp");
  await form.getByLabel("参数").fill("--profile\nproduction");
  await form.getByLabel("进程 Env key").fill("DATABASE_URL");
  await form.getByLabel("来源环境变量").fill("lab_database_url");
  await form.getByRole("button", { name: "注册 Connector" }).click();
  await expect.poll(() => registered.length).toBe(1);
  expect(registered[0].env).toEqual({ DATABASE_URL: "${lab_database_url}" });
});


test("keeps the expanded Connector form inside a narrow agent page", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 700 });
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await page.getByRole("button", { name: "添加" }).click();
  const overflow = await page.locator(".agent-form").evaluate((element) => getComputedStyle(element).overflowY);
  expect(overflow).toBe("auto");
  const widths = await page.locator(".agent-form").evaluate((element) => [element.scrollWidth, element.clientWidth]);
  expect(widths[0]).toBeLessThanOrEqual(widths[1]);
  const columns = await page.locator(".agent-grid, .connector-credential").evaluateAll((elements) =>
    elements.map((element) => getComputedStyle(element).gridTemplateColumns));
  expect(columns.every((value) => !value.includes(" "))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await expect(page.getByRole("button", { name: "保存" })).toBeVisible();
});


test("wraps long Connector catalog values at 390px without exposing its location", async ({ page }) => {
  const longId = `connector-${"i".repeat(96)}`;
  const longName = `Connector${"N".repeat(120)}`;
  const longSource = `runtime-${"s".repeat(100)}`;
  const value = { id: longId, name: longName, description: "D".repeat(160), transport: "http",
    source: longSource, available: true, url: "https://private.example/mcp" };
  const customCatalog = { ...catalog(), connectors: [value] };
  const configured = { ...agents()[0], connectors: [longId] };
  await page.setViewportSize({ width: 390, height: 700 });
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [configured] }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: customCatalog }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip", { hasText: longName })).toBeVisible();
  await expect(page.getByText("https://private.example/mcp")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const widths = await page.locator(".capability-picker").evaluate((element) => [element.scrollWidth, element.clientWidth]);
  expect(widths[0]).toBeLessThanOrEqual(widths[1]);
});
