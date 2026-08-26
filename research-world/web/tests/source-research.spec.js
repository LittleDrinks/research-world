import { expect, test } from "@playwright/test";


const ADMITTED = "E2E admitted source";
const REJECTED = "E2E unavailable source";
const REASON = "Complete text is unavailable for claim verification";


test("runs source research and resolves Admission entirely through WebUI", async ({ page }) => {
  test.setTimeout(240_000);
  await createProject(page);
  const threadUrl = await createSourceProfile(page);
  const direction = await createDirection(page);
  await pinDirection(page, threadUrl, direction);
  const card = await startSourceResearch(page);
  await approveSource(page, card);
  await rejectSource(page, threadUrl);
});


async function createProject(page) {
  await page.goto("/projects");
  await page.getByRole("button", { name: "新建项目" }).first().click();
  const dialog = page.getByRole("dialog", { name: "新建研究项目" });
  await dialog.getByLabel("项目名称").fill(`Issue 54 E2E ${Date.now()}`);
  await dialog.getByLabel("研究问题").fill("Can auditable full text support this deterministic direction?");
  await dialog.getByRole("button", { name: "创建项目" }).click();
  await expect(page).toHaveURL(/\/map$/);
}


async function createSourceProfile(page) {
  await page.goto("/chat");
  await page.locator(".empty-state").getByRole("button", { name: "新建对话" }).click();
  await expect(page).toHaveURL(/\/chat\/thread%3A/);
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /文献研究员/ }).click();
  const draft = page.getByRole("region", { name: "Agent 草稿" });
  await expect(draft).toContainText("project_files（ready）");
  await draft.getByRole("button", { name: "确认创建" }).click();
  await expect(draft).toContainText("文献研究员");
  return page.url();
}


async function createDirection(page) {
  await page.goto("/map");
  const inspector = page.locator(".inspector");
  await inspector.getByLabel("选择流程").selectOption("brainstorm");
  await inspector.getByRole("button", { name: "发起运行" }).click();
  await waitForTrace(page, "生成研究方向");
  await page.goto("/map");
  const title = page.locator(".research-node.kind-direction h3").first();
  await expect(title).toBeVisible({ timeout: 30_000 });
  return title.innerText();
}


async function pinDirection(page, threadUrl, direction) {
  await page.goto(threadUrl);
  await page.getByLabel("消息").fill("@");
  await page.locator(".mention-menu button", { hasText: direction }).click();
  await page.getByRole("button", { name: "研究运行" }).click();
  await expect(page.getByLabel("作用节点")).toContainText(direction);
}


async function startSourceResearch(page) {
  await page.getByLabel("选择流程").selectOption("source-research");
  await page.getByRole("button", { name: "启动流程" }).click();
  const card = page.locator(".run-card", { hasText: "文献检索与全文核验" });
  await expect(card).toContainText("已完成", { timeout: 120_000 });
  await card.locator(".run-card-head").click();
  await expect(card).toContainText("待 Admission");
  return card;
}


async function approveSource(page, card) {
  const row = card.locator(".source-projection li", { hasText: ADMITTED });
  await expect(row).toContainText("artifact:");
  await row.getByRole("button", { name: "通过" }).click();
  await expect(row).toContainText("Admission 已通过");
  await expect(row).toContainText("已准入");
  await row.getByRole("button", { name: ADMITTED }).click();
  await assertAdmittedInspector(page);
}


async function assertAdmittedInspector(page) {
  const inspector = page.locator(".inspector");
  await expect(inspector).toContainText("已入图");
  await expect(inspector).toContainText("sources/e2e-full-text.txt");
  await expect(inspector.locator(".relation-list")).toContainText("支持");
  await page.reload();
  await expect(page.locator(".inspector")).toContainText("已入图");
  await expect(page.locator(".relation-list")).toContainText("支持");
}


async function rejectSource(page, threadUrl) {
  const card = await openSourceRun(page, threadUrl);
  await card.getByRole("button", { name: REJECTED }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await fillRejection(page);
  await expect(page.locator(".inspector-header")).toContainText(REASON);
  await page.reload();
  await assertRejectedInspector(page);
}


async function openSourceRun(page, threadUrl) {
  await page.goto(threadUrl);
  await page.getByRole("button", { name: "研究运行" }).click();
  const card = page.locator(".run-card", { hasText: "文献检索与全文核验" });
  await card.locator(".run-card-head").click();
  return card;
}


async function fillRejection(page) {
  const control = page.getByRole("region", { name: "Source Admission" });
  await control.scrollIntoViewIfNeeded();
  expect(inViewport(await control.boundingBox(), 390)).toBe(true);
  await control.getByRole("button", { name: "驳回" }).click();
  await expect(control.getByRole("button", { name: "确认驳回" })).toBeDisabled();
  await control.getByLabel("驳回理由").fill(REASON);
  expect(inViewport(await control.getByLabel("驳回理由").boundingBox(), 390)).toBe(true);
  await control.getByRole("button", { name: "确认驳回" }).click();
  await expect(control).toContainText("Admission 已驳回");
}


async function assertRejectedInspector(page) {
  const inspector = page.locator(".inspector");
  await expect(inspector).toContainText("已驳回");
  await expect(inspector).toContainText(REASON);
  await expect(inspector).toContainText("full_text_unavailable");
  await expect(inspector).toContainText("全文不可得");
  await expect(inspector).toContainText("暂无关系");
}


async function waitForTrace(page, title) {
  await expect(page.locator(".run-title")).toContainText(title);
  await expect(page.locator(".run-header .status-pill")).toHaveText("已完成", { timeout: 120_000 });
}


function inViewport(box, width) {
  return box && box.x >= 0 && box.x + box.width <= width;
}
