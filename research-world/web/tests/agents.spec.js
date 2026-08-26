import { expect, test } from "@playwright/test";
import { agents, catalog, mockBase, preset } from "./fixtures";


test("offers recognizable endpoint, model and effort choices from the catalog", async ({ page }) => {
  await mockBase(page);
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("Endpoint")).toHaveValue("openai-compatible");
  await expect(page.getByLabel("Endpoint").locator("option")).toHaveCount(2);
  await expect(page.getByLabel("模型")).toHaveValue("qwen3.7-flash");
  await expect(page.getByLabel("推理强度")).toHaveValue("high");
  await expect(page.getByLabel("推理强度").locator("option")).toHaveCount(4);
  await expect(page.locator(".capability-picker", { hasText: "工具" }).locator(".capability-chip")).toHaveCount(0);
  await page.screenshot({ path: "test-results/agents-desktop.png", fullPage: true });
});


test("creates a new Agent from the sidebar and opens its editor", async ({ page }) => {
  const values = agents();
  let created;
  let createUrl;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => {
    if (route.request().method() === "GET") return route.fulfill({ json: values });
    created = route.request().postDataJSON(); values.push(created); createUrl = route.request().url();
    return route.fulfill({ status: 201, json: created });
  });
  await page.goto("/agents/research-assistant");
  await page.getByRole("button", { name: "新建 Agent" }).click();
  const dialog = page.getByRole("dialog", { name: "新建 Agent" });
  await dialog.getByLabel("ID").fill("proof-reviewer");
  await dialog.getByLabel("名称").fill("形式化复核");
  await dialog.getByLabel("指令").fill("检查证明并报告反例。");
  const idField = await dialog.getByLabel("ID").locator("..").boundingBox();
  const nameField = await dialog.getByLabel("名称").locator("..").boundingBox();
  const hint = await dialog.getByText("小写字母、数字、连字符，创建后不可改").boundingBox();
  expect(idField.x + idField.width).toBeLessThanOrEqual(nameField.x);
  expect(hint.x).toBeGreaterThanOrEqual(idField.x);
  expect(hint.x + hint.width).toBeLessThanOrEqual(idField.x + idField.width);
  await page.screenshot({ path: "test-results/new-agent-dialog.png", fullPage: true });
  await dialog.getByRole("button", { name: "创建 Agent" }).click();
  await expect.poll(() => created).toBeTruthy();
  expect(createUrl).toContain("project_id=project%3Atest");
  expect(created).toEqual({ id: "proof-reviewer", name: "形式化复核", instructions: "检查证明并报告反例。",
    runtime: { id: "codex", realm: "container:runtime" },
    endpoint: "openai-compatible", model: "qwen3.7-flash", skills: [], tools: [],
    options: { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 12, token_budget: 200000 } });
  await expect(page).toHaveURL(/\/agents\/proof-reviewer$/);
  await expect(page.getByRole("heading", { name: "形式化复核" })).toBeVisible();
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
  await page.route(/\/api\/v1\/agents\/research-assistant\?/, (route) => {
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
  await page.route(/\/api\/v1\/agents\/research-assistant\?/, (route) => {
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


test("keeps an unknown Runtime reference visible and blocks saving", async ({ page }) => {
  const current = agents()[0];
  const loaded = { ...current, runtime: { id: "codex", realm: "legacy:runtime" }, mcp_servers: ["legacy-mcp"], unknown: true,
    options: { ...current.options, legacy_option: "drop-me" } };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [loaded] }));
  await page.setViewportSize({ width: 390, height: 700 });
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("Runtime")).toHaveValue(JSON.stringify(["codex", "legacy:runtime"]));
  await expect(page.getByLabel("Runtime").locator("option:checked")).toContainText("不在 catalog");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.getByRole("alert")).toContainText("Runtime 不在 catalog");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});


test("blocks saving when the Runtime is unavailable", async ({ page }) => {
  const value = catalog();
  value.runtimes[0] = { ...value.runtimes[0], status: "unavailable", reason: { code: "not_installed" } };
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByLabel("Runtime").locator("option:checked")).toContainText("not_installed");
  await expect(page.getByLabel("Runtime").locator("option:checked")).toHaveAttribute("disabled", "");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.getByRole("alert")).toContainText("Runtime 当前不可用");
});


test("syncs the model to the chosen endpoint and keeps the pair saveable", async ({ page }) => {
  let saved;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents\/research-assistant\?/, (route) => {
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


test("blocks saving when the Endpoint is incompatible with the Runtime", async ({ page }) => {
  const value = catalog();
  value.endpoints[0] = { ...value.endpoints[0], runtime_refs: [] };
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.getByRole("alert")).toContainText("Endpoint 与 Runtime 不兼容");
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
  const invalid = { ...agents()[0], skills: ["ghost-skill"], tools: ["ghost-tool"] };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [invalid] }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip.missing")).toHaveCount(2);
  await expect(page.locator(".agent-form-footer")).toContainText("ghost-skill、ghost-tool");
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
});


test("retries runtime catalog recognition after a transient failure", async ({ page }) => {
  let attempts = 0;
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => {
    attempts += 1;
    return attempts < 3 ? route.fulfill({ status: 503, json: { detail: "Runtime 暂不可用" } })
      : route.fulfill({ json: catalog() });
  });
  await page.goto("/agents/research-assistant");
  await expect(page.getByText("Runtime 目录载入失败")).toBeVisible();
  await page.getByRole("button", { name: "重试识别" }).click();
  await expect(page.getByLabel("Endpoint")).toHaveValue("openai-compatible");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
});


test("blocks a ready Tool selected for the Codex Runtime", async ({ page }) => {
  const value = catalog();
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));
  await page.goto("/agents/research-assistant");
  const picker = page.locator(".capability-picker", { hasText: "工具" });
  await picker.getByLabel("搜索工具").fill("Lean4");
  await picker.locator(".capability-options button").click();
  await expect(page.locator(".capability-chip", { hasText: "Lean4" })).toBeVisible();
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
  await expect(page.getByRole("alert")).toContainText("Codex Runtime 不支持 Tools");
});


test("blocks saving a Tool that is not ready", async ({ page }) => {
  const value = catalog();
  value.tools.push({ id: "lab-db", name: "实验数据库", status: "setup_required" });
  const configured = { ...agents()[0], tools: ["lab-db"] };
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [configured] }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip.missing", { hasText: "lab-db" })).toBeVisible();
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();
});


test("wraps long Tool catalog values at 390px without exposing its implementation", async ({ page }) => {
  const longId = `tool-${"i".repeat(48)}`;
  const longName = `Tool${"N".repeat(120)}`;
  const longSource = `runtime-${"s".repeat(100)}`;
  const value = { id: longId, name: longName, description: "D".repeat(160), source: longSource, status: "ready" };
  const customCatalog = { ...catalog(), tools: [...catalog().tools, value] };
  const configured = { ...agents()[0], tools: [longId] };
  await page.setViewportSize({ width: 390, height: 700 });
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [configured] }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: customCatalog }));
  await page.goto("/agents/research-assistant");
  await expect(page.locator(".capability-chip", { hasText: longName })).toBeVisible();
  await expect(page.getByText(/stdio|HTTP|SSE|MCP/)).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const picker = page.locator(".capability-picker").filter({ hasText: longName });
  const widths = await picker.evaluate((element) => [element.scrollWidth, element.clientWidth]);
  expect(widths[0]).toBeLessThanOrEqual(widths[1]);
});


test("browses a Profile Preset and applies it as an editable creation draft", async ({ page }) => {
  const values = agents();
  let created;
  await mockBase(page);
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => {
    if (route.request().method() === "GET") return route.fulfill({ json: values });
    created = route.request().postDataJSON(); values.push(created);
    return route.fulfill({ status: 201, json: created });
  });
  await page.goto("/agents/research-assistant");
  const panel = page.getByRole("region", { name: "Profile Presets" });
  await expect(panel).toContainText("数学证明");
  await expect(panel).toContainText("lean4（ready）");
  await panel.getByRole("button", { name: "应用为草稿" }).click();
  const dialog = page.getByRole("dialog", { name: "应用 Preset：数学证明" });
  await expect(dialog).toContainText("形式化证明 Agent");
  await expect(dialog.getByLabel("ID")).toHaveValue("math-proof");
  await expect(dialog.getByLabel("名称")).toHaveValue("数学证明助手");
  await dialog.getByLabel("名称").fill("证明助手 v2");
  await dialog.getByLabel("推理强度").selectOption("high");
  await dialog.getByText("权限与限制").click();
  await dialog.getByLabel("Sandbox").selectOption("workspace-write");
  const skills = dialog.locator(".capability-picker", { hasText: "Skills" });
  await skills.getByLabel("搜索Skills").fill("文献综述");
  await skills.locator(".capability-options button").click();
  await dialog.getByRole("button", { name: "移除 lean4" }).click();
  await dialog.getByRole("button", { name: "创建 Agent" }).click();
  await expect.poll(() => created).toBeTruthy();
  expect(created.id).toBe("math-proof");
  expect(created.name).toBe("证明助手 v2");
  expect(created.tools).toEqual([]);
  expect(created.skills).toEqual(["skill-review"]);
  expect(created.options).toMatchObject({ reasoning_effort: "high", sandbox: "workspace-write" });
  expect(created.endpoint).toBe("openai-compatible");
  expect(created.runtime).toEqual({ id: "codex", realm: "container:runtime" });
  await expect(page).toHaveURL(/\/agents\/math-proof$/);
  await expect(page.getByRole("heading", { name: "证明助手 v2" })).toBeVisible();
});


test("blocks applying a Preset whose Tool is unavailable", async ({ page }) => {
  const value = catalog();
  value.presets = [preset({ tools: [{ id: "lean4", status: "unavailable", reason: "not_installed" }] })];
  value.tools = value.tools.filter((tool) => tool.id !== "lean4");
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));
  await page.goto("/agents/research-assistant");
  await expect(page.getByRole("region", { name: "Profile Presets" }))
    .toContainText("lean4（unavailable / not_installed）");
  await page.getByRole("button", { name: "应用为草稿" }).click();
  const dialog = page.getByRole("dialog", { name: "应用 Preset：数学证明" });
  await expect(dialog.getByRole("alert")).toContainText("lean4（unavailable / not_installed）");
  const submit = dialog.getByRole("button", { name: "创建 Agent", exact: true });
  await expect(submit).toHaveText("创建 Agent");
  await expect(submit).toBeDisabled();
});


test("shows an unavailable Tool reason separately from the disabled save command", async ({ page }) => {
  const value = catalog();
  value.tools = value.tools.filter((tool) => tool.id !== "lean4");
  value.presets = [preset({ tools: [{ id: "lean4", status: "unavailable", reason: "not_installed" }] })];
  await mockBase(page);
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: [{ ...agents()[0], tools: ["lean4"] }] }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: value }));

  await page.goto("/agents/research-assistant");

  await expect(page.getByRole("alert")).toContainText("Tool 不可用：lean4（unavailable / not_installed）");
  const save = page.getByRole("button", { name: "保存", exact: true });
  await expect(save).toHaveText("保存");
  await expect(save).toBeDisabled();
});
