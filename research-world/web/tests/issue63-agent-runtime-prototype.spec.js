import { expect, test } from "@playwright/test";

const ROUTE = "/prototype/agent-runtime";
const SHOTS = "screenshots/issue63-prototype";

async function openPrototype(page, width = 1440, height = 900) {
  await page.setViewportSize({ width, height });
  await page.goto(ROUTE);
  await expect(page.getByRole("heading", { name: "Source Researcher" })).toBeVisible();
}

async function expectNoPageOverflow(page) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect.poll(() => page.locator(".arp-shell").evaluate((node) => node.scrollWidth <= node.clientWidth)).toBe(true);
}

async function chooseDraft(page, name) {
  await page.getByRole("button", { name: "新建 Agent" }).click();
  await page.getByRole("button", { name }).click();
  await expect(page.getByRole("heading", { name: "AgentSpec" })).toBeVisible();
}

async function finishOrchestratorDraft(page) {
  await page.getByLabel("Draft Endpoint").selectOption("codex-account");
  await page.getByLabel("Draft Model").fill("gpt-5.6-terra");
  await page.getByLabel("Draft OpenAI Developer Docs").uncheck();
  await expect(page.getByText("AgentSpec 草稿可以保存")).toBeVisible();
}

async function startPrepare(page) {
  const gemini = page.locator(".arp-runtime-row").filter({ hasText: "Gemini CLI" });
  await gemini.getByRole("button", { name: "CLI 准备计划" }).click();
  await expect(page.getByRole("dialog", { name: "CLI 准备计划" })).toBeVisible();
}

async function runPrepare(page, outcome) {
  await page.getByLabel("Prepare 结果").selectOption(outcome);
  await page.getByRole("button", { name: "确认并执行" }).click();
  await expect(page.locator(".arp-prepare-state")).toContainText("running");
  await expect(page.locator(".arp-prepare-state")).toContainText(outcome, { timeout: 2000 });
}

async function expectOverlayInsideViewport(page, selector) {
  const box = await page.locator(selector).boundingBox();
  const viewport = page.viewportSize();
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
}

test("Profile selection and CRUD keep independent snapshots", async ({ page }) => {
  await openPrototype(page);
  await page.getByRole("button", { name: "选择 Proof Reviewer" }).click();
  await expect(page.getByRole("heading", { name: "Proof Reviewer" })).toBeVisible();
  await page.getByRole("button", { name: "复制 Agent" }).click();
  await expect(page.getByRole("heading", { name: "Proof Reviewer Copy" })).toBeVisible();
  await page.getByRole("button", { name: "Profile", exact: true }).click();
  await page.getByLabel("Profile 名称").fill("Proof Reviewer Edited");
  await page.getByRole("button", { name: "保存 Profile" }).click();
  await expect(page.getByText("modified now")).toBeVisible();
  await page.getByRole("button", { name: "删除 Agent" }).click();
  await page.getByRole("button", { name: "确认删除" }).click();
  await expect(page.getByRole("button", { name: "选择 Proof Reviewer Edited" })).toHaveCount(0);
  await page.getByRole("button", { name: "选择 Proof Reviewer" }).click();
  await expect(page.getByRole("heading", { name: "Proof Reviewer" })).toBeVisible();
});

test("all three complete AgentSpec drafts expose readiness", async ({ page }) => {
  await openPrototype(page);
  await chooseDraft(page, "Preset");
  await expect(page.getByLabel("Draft Runtime")).toHaveValue("codex");
  await expect(page.getByText("AgentSpec 草稿可以保存")).toBeVisible();
  await page.getByRole("button", { name: "确认创建 Profile" }).click();
  await expect(page.getByRole("heading", { name: "Source Researcher Copy" })).toBeVisible();
  await chooseDraft(page, "空白");
  await expect(page.getByLabel("Draft Runtime")).toHaveValue("");
  await expect(page.getByLabel("Draft Endpoint")).toHaveValue("");
  await expect(page.getByLabel("Draft Model")).toHaveValue("");
  await expect(page.locator(".arp-draft-capabilities input:checked")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "确认创建 Profile" })).toBeDisabled();
  await page.getByRole("dialog", { name: "新建 Agent 草稿" }).getByRole("button", { name: "关闭" }).click();
  await page.getByRole("button", { name: "新建 Agent" }).click();
  await page.getByRole("button", { name: "描述目标" }).click();
  await page.getByLabel("研究目标").fill("核验官方当前来源");
  await page.getByRole("button", { name: "生成待确认草稿" }).click();
  await expect(page.getByRole("alert")).toContainText("secret_unresolved");
  await expect(page.getByRole("alert")).toContainText("tool_not_ready");
  await finishOrchestratorDraft(page);
  await expect(page.getByRole("button", { name: "确认创建 Profile" })).toBeEnabled();
});

test("readiness blocks unresolved secret and keeps Kimi auth unknown", async ({ page }) => {
  await openPrototype(page);
  await page.getByRole("button", { name: "模型" }).click();
  await page.getByLabel("Endpoint").selectOption("openai-compatible");
  await page.getByLabel("Model").fill("qwen3.7-flash");
  await expect(page.getByRole("button", { name: "保存 Profile" })).toBeDisabled();
  await expect(page.getByText("valid != authenticated")).toBeVisible();
  await page.getByRole("button", { name: "诊断" }).click();
  await expect(page.getByRole("alert")).toContainText("secret_unresolved");
});

test("CLI prepare covers cancel failure retry success and retains logs", async ({ page }) => {
  await openPrototype(page);
  await startPrepare(page);
  await expect(page.locator(".arp-prepare-state")).toContainText("plan");
  await page.getByRole("button", { name: "取消计划" }).click();
  await expect(page.locator(".arp-prepare-state")).toContainText("cancelled");
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.locator(".arp-prepare-state")).toContainText("confirm");
  await runPrepare(page, "failed");
  await page.getByRole("button", { name: "Retry" }).click();
  await runPrepare(page, "succeeded");
  await expect(page.getByLabel("Prepare 日志")).toContainText("cancelled");
  await expect(page.getByLabel("Prepare 日志")).toContainText("failed");
  await expect(page.getByLabel("Prepare 日志")).toContainText("retry");
  await expect(page.getByRole("dialog", { name: "CLI 准备计划" })).not.toContainText("OpenCLI");
});

test("inventory scenarios and desktop geometry handle long values", async ({ page }) => {
  await openPrototype(page);
  await expect(page.locator(".arp-runtime-row")).toHaveCount(6);
  await expect(page.locator(".arp-runtime-list")).not.toContainText("OpenCLI");
  await expect(page.getByText("Pi Coding Agent").locator("..", { hasText: "0.84.2" })).toBeVisible();
  await page.getByRole("button", { name: "Loading" }).click();
  await expect(page.getByLabel("Loading CLI inventory")).toBeVisible();
  await page.getByRole("button", { name: "Empty" }).click();
  await expect(page.getByText("没有 CLI candidates")).toBeVisible();
  await page.getByRole("button", { name: "内容" }).click();
  await page.getByRole("button", { name: "刷新" }).click();
  await expect(page.getByText("正在隔离探测 6 个 candidates")).toBeVisible();
  await expectNoPageOverflow(page);
  await page.getByRole("button", { name: "导出" }).click();
  await expectOverlayInsideViewport(page, ".arp-notice");
  await page.screenshot({ path: `${SHOTS}-desktop.png` });
});

test("390px layout has no page overflow across runtime model and Skills", async ({ page }) => {
  await openPrototype(page, 390, 844);
  const longPath = page.getByText("/opt/research/runtime/bin/lab-agent-with-an-intentionally-long-executable-name");
  await longPath.scrollIntoViewIfNeeded();
  await expect(longPath).toBeVisible();
  await expectNoPageOverflow(page);
  await page.screenshot({ path: `${SHOTS}-mobile-390.png` });
  await page.getByRole("button", { name: "模型" }).click();
  await expectNoPageOverflow(page);
  await page.screenshot({ path: `${SHOTS}-mobile-model-390.png` });
  await page.getByRole("button", { name: "Skills" }).click();
  const longSkill = page.getByText("long-form-validation-and-independent-evidence-review");
  await longSkill.scrollIntoViewIfNeeded();
  await expect(longSkill).toBeVisible();
  await expectNoPageOverflow(page);
  await page.screenshot({ path: `${SHOTS}-mobile-skills-390.png` });
  await page.getByRole("button", { name: "导出" }).click();
  await expectOverlayInsideViewport(page, ".arp-notice");
});
