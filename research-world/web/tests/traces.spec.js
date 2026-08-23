import { expect, test } from "@playwright/test";
import { bootstrap, mockBase, run } from "./fixtures";


test("renders the run -> stage -> session -> turn -> tool tree", async ({ page }) => {
  await mockBase(page);
  await page.goto("/traces/run%3Ar1");
  await expect(page.locator(".tree-row", { hasText: "RUN" })).toBeVisible();
  await expect(page.locator(".tree-row", { hasText: "STAGE" })).toBeVisible();
  await expect(page.locator(".tree-row", { hasText: "SESSION" })).toBeVisible();
  await page.locator(".tree-row", { hasText: "SESSION" }).click();
  await expect(page.locator(".tree-row", { hasText: "TURN 1" })).toBeVisible();
  const tool = page.locator(".tree-leaf.tool");
  await expect(tool).toContainText("graph_query");
  await expect(tool.locator("pre")).toHaveCount(1);
  await expect(tool.locator("pre")).not.toBeVisible();
  await tool.locator("summary").click();
  await expect(tool.locator("pre")).toBeVisible();
  await expect(tool.locator("pre")).toContainText("arguments");
  await page.screenshot({ path: "test-results/traces-desktop.png" });
});


test("marks sessions unavailable instead of fabricating them", async ({ page }) => {
  const legacy = run();
  delete legacy.events[0].payload.stage_id;
  await mockBase(page, bootstrap({ runs: [legacy] }));
  await page.route(/\/api\/v1\/runtime\/sessions\/[^/]+$/, (route) => route.fulfill({ status: 404, json: { detail: "not found" } }));
  await page.goto("/traces/run%3Ar1");
  await expect(page.locator(".tree-row", { hasText: "未分组会话" })).toBeVisible();
  await expect(page.locator(".tree-row", { hasText: "SESSION" })).toContainText("会话不可用");
});


test("shows the durable failure reason in the run header", async ({ page }) => {
  const failed = run({ status: "failed", stage: "failed", payload: { error: "runtime response must be a JSON object" } });
  await mockBase(page, bootstrap({ runs: [failed] }));
  await page.goto("/traces/run%3Ar1");
  await expect(page.locator(".run-header .trace-error")).toHaveText("runtime response must be a JSON object");
});


test("confirms a waiting run through the real API", async ({ page }) => {
  let confirmed = false;
  let rejected;
  await mockBase(page, bootstrap({ runs: [run({ status: "waiting_human" })] }));
  await page.route(/\/api\/v1\/runs\/run%3Ar1\/confirm/, (route) => { confirmed = true; return route.fulfill({ status: 202, json: run() }); });
  await page.route(/\/api\/v1\/runs\/run%3Ar1\/resolve/, (route) => {
    rejected = route.request().postDataJSON(); return route.fulfill({ status: 202, json: run() });
  });
  await page.goto("/traces/run%3Ar1");
  await expect(page.getByRole("button", { name: "批准" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "驳回", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "驳回计划" })).toBeVisible();
  await page.getByRole("button", { name: "驳回计划" }).click();
  await expect.poll(() => rejected).toEqual({ decision: "reject", reason: "人工驳回实验计划" });
  await page.reload();
  await page.getByRole("button", { name: "确认继续" }).click();
  await expect.poll(() => confirmed).toBe(true);
  await expect(page.getByRole("button", { name: "确认继续" })).toBeDisabled();
});


test("resolves a conflict gate with approve or reject only", async ({ page }) => {
  let decision;
  const conflicted = run({ status: "waiting_human", payload: { thread_id: "thread:t1", conflict_node: "node:x" } });
  await mockBase(page, bootstrap({ runs: [conflicted] }));
  await page.route(/\/api\/v1\/runs\/run%3Ar1\/resolve/, (route) => {
    decision = route.request().postDataJSON();
    return route.fulfill({ status: 202, json: run() });
  });
  await page.goto("/traces/run%3Ar1");
  await expect(page.getByRole("button", { name: "确认继续" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "驳回" })).toBeVisible();
  await page.getByRole("button", { name: "批准" }).click();
  await expect.poll(() => decision).toEqual({ decision: "approve", reason: "人工批准" });
  await expect(page.getByRole("button", { name: "批准" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "驳回" })).toBeDisabled();
});


test("unlocks the next manual gate in the same stage", async ({ page }) => {
  let confirms = 0;
  let current = run({ status: "waiting_human", updated_at: "2026-08-16T01:00:00Z" });
  await mockBase(page, bootstrap({ runs: [current] }));
  await page.route(/\/api\/v1\/bootstrap/, (route) => route.fulfill({ json: bootstrap({ runs: [current] }) }));
  await page.route(/\/api\/v1\/runs\/run%3Ar1\/confirm/, (route) => {
    confirms += 1;
    current = run({ status: confirms === 1 ? "waiting_human" : "completed",
      updated_at: `2026-08-16T0${confirms + 1}:00:00Z` });
    return route.fulfill({ status: 202, json: current });
  });
  await page.goto("/traces/run%3Ar1");
  await page.getByRole("button", { name: "确认继续" }).click();
  await expect(page.getByRole("button", { name: "确认继续" })).toBeEnabled();
  await page.getByRole("button", { name: "确认继续" }).click();
  await expect.poll(() => confirms).toBe(2);
});


test("shows an empty state when the project has no runs", async ({ page }) => {
  await mockBase(page, bootstrap({ runs: [] }));
  await page.goto("/traces");
  await expect(page.getByText("暂无运行")).toBeVisible();
});
