import { expect, test } from "@playwright/test";
import { bootstrap, mockBase, project, threadDetail } from "./fixtures";


async function mockShell(page) {
  await mockBase(page);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
}


test("keeps project selection outside the application shell", async ({ page }) => {
  await mockShell(page);
  await page.goto("/projects");
  await expect(page.locator(".project-list > button")).toHaveCount(1);
  await expect(page.locator(".sidebar")).toHaveCount(0);
  await page.screenshot({ path: "test-results/projects-desktop.png" });
  await page.locator(".project-list > button").click();
  await expect(page).toHaveURL(/\/map$/);
  await expect(page.locator(".module-nav a")).toHaveCount(5);
  await expect(page.locator(".brand")).toContainText("Research World");
  const dock = page.locator(".project-dock");
  await expect(dock.getByRole("link")).toHaveCount(2);
  await expect(dock).not.toContainText("测试项目");
  await expect(dock).not.toContainText("实时");
  await expect(dock.getByRole("link", { name: "项目设置" })).toHaveAttribute("title", "项目设置");
  await dock.getByRole("link", { name: "切换项目" }).click();
  await expect(page).toHaveURL(/\/projects$/);
});


test("shows only current run activity on project cards", async ({ page }) => {
  const idle = { ...project(), node_count: 13, run_count: 9, active_run_count: 0 };
  const active = { ...project(), id: "project:active", node_count: 7, run_count: 4, active_run_count: 2 };
  await mockBase(page, bootstrap({ projects: [idle, active] }));
  await page.goto("/projects");
  const counts = page.locator(".project-counts");
  await expect(counts.nth(0)).toHaveText("13 节点");
  await expect(counts.nth(1)).toHaveText("7 节点 · 2 运行中");
});


test("shows module record lists in the sidebar", async ({ page }) => {
  await mockShell(page);
  await page.goto("/chat");
  await expect(page).toHaveURL(/\/chat\/thread/);
  await expect(page.locator(".record-list")).toContainText("对话");
  await expect(page.locator(".record-list .record-item")).toHaveCount(1);
  await page.locator(".record-toggle").click();
  await expect(page.locator(".record-list .record-item")).toHaveCount(0);
  await page.locator(".record-toggle").click();
  await expect(page.locator(".record-list .record-item")).toHaveCount(1);
  await page.locator(".module-nav").getByRole("link", { name: "Agent" }).click();
  await expect(page.locator(".record-list")).toContainText("研究助手");
});


test("redirects removed routes to project selection", async ({ page }) => {
  await mockShell(page);
  await page.goto("/activity");
  await expect(page).toHaveURL(/\/projects$/);
});


test("creates a project posting the explicit question title", async ({ page }) => {
  let body;
  await mockShell(page);
  await page.route(/\/api\/v1\/bootstrap/, (route) => {
    const id = new URL(route.request().url()).searchParams.get("project_id");
    const created = { ...bootstrap().projects[0], id: "project:new", name: "新课题", title: "新课题", question: "验证假设 X" };
    return route.fulfill({ json: id === "project:new" ? bootstrap({ active_project_id: "project:new", projects: [created] }) : bootstrap() });
  });
  await page.route(/\/api\/v1\/projects$/, (route) => {
    if (route.request().method() !== "POST") return route.fulfill({ json: [] });
    body = route.request().postDataJSON();
    return route.fulfill({ status: 201, json: { id: "project:new", name: body.name, title: body.title, question: body.question } });
  });
  await page.goto("/projects");
  await page.locator(".projects-bar").getByRole("button", { name: "新建项目" }).click();
  await page.getByLabel("项目名称").fill("新课题");
  await page.getByLabel("研究问题").fill("验证假设 X");
  await page.getByRole("button", { name: "创建项目" }).click();
  await expect.poll(() => body).toEqual({ name: "新课题", title: "新课题", question: "验证假设 X" });
  await expect(page).toHaveURL(/\/map$/);
});


test("stays on project selection when the created project cannot load", async ({ page }) => {
  await mockShell(page);
  await page.route(/\/api\/v1\/bootstrap/, (route) => {
    const id = new URL(route.request().url()).searchParams.get("project_id");
    return id === "project:new" ? route.fulfill({ status: 500, json: { detail: "项目载入失败" } })
      : route.fulfill({ json: bootstrap() });
  });
  await page.route(/\/api\/v1\/projects$/, (route) => route.fulfill({ status: 201,
    json: { id: "project:new", name: "新课题", question: "验证假设 X" } }));
  await page.goto("/projects");
  await page.getByRole("button", { name: "新建项目" }).first().click();
  await page.getByLabel("项目名称").fill("新课题");
  await page.getByLabel("研究问题").fill("验证假设 X");
  await page.getByRole("button", { name: "创建项目" }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("alert")).toContainText("项目载入失败");
  await expect(page.locator(".project-list > button.active")).toHaveCount(1);
});


test("persists the color theme", async ({ page }) => {
  await mockShell(page);
  await page.goto("/projects");
  await page.getByRole("button", { name: "切换深色模式" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});


test("opens the sidebar as an overlay on narrow screens", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockShell(page);
  await page.goto("/map");
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.locator(".module-nav a")).toHaveCount(5);
  await page.locator(".module-nav").getByRole("link", { name: "对话" }).click();
  await expect(page).toHaveURL(/\/chat/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
