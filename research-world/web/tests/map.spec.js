import { expect, test } from "@playwright/test";


test.describe.configure({ mode: "serial" });


function uniqueToken() {
  return `local-map-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}


async function projectId(page) {
  const health = await page.request.get("/api/v1/health");
  expect(health.status()).toBe(200);
  expect(await health.json()).toEqual({ ok: true });
  const response = await page.request.get("/api/v1/bootstrap");
  return (await response.json()).active_project_id;
}


async function createRecord(page, project, type, token) {
  const response = await page.request.post(`/api/v1/projects/${project}/records`, {
    data: { type, content: { title: `${type} ${token}`, text: token } },
  });
  expect(response.status()).toBe(201);
  return response.json();
}


async function connect(page, project, source, target, type = "supports") {
  const response = await page.request.post(`/api/v1/projects/${project}/relations`, {
    data: { source_id: source, target_id: target, type },
  });
  expect(response.status()).toBe(201);
  return response.json();
}


async function seedGraph(page) {
  const project = await projectId(page);
  const token = uniqueToken();
  const source = await createRecord(page, project, "source", token);
  const direction = await createRecord(page, project, "direction", token);
  const experiment = await createRecord(page, project, "experiment", token);
  const relations = [
    await connect(page, project, source.id, direction.id),
    await connect(page, project, experiment.id, direction.id, "refutes"),
  ];
  return { project, token, records: [source, direction, experiment], relations };
}


async function removeRelation(page, project, relation) {
  expect((await page.request.delete(`/api/v1/projects/${project}/relations/${relation.id}`)).status()).toBe(204);
}


async function removeRecord(page, project, record) {
  expect((await page.request.delete(`/api/v1/projects/${project}/records/${record.id}`)).status()).toBe(204);
}


async function removeGraph(page, graph) {
  for (const relation of graph.relations) {
    await page.request.delete(`/api/v1/projects/${graph.project}/relations/${relation.id}`);
  }
  for (const record of graph.records) await page.request.delete(`/api/v1/projects/${graph.project}/records/${record.id}`);
}


test("renders and refreshes the local graph through Kernel HTTP", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.goto(`/map?text=${encodeURIComponent(graph.token)}`);
    await expect(page.locator(".research-node")).toHaveCount(3);
    await expect(page.locator(".react-flow__edge")).toHaveCount(2);
    await removeRelation(page, graph.project, graph.relations[0]);
    await expect.poll(() => page.locator(".react-flow__edge").count()).toBe(1);
    await removeRecord(page, graph.project, graph.records[1]);
    await expect.poll(() => page.locator(".research-node").count()).toBe(2);
  } finally {
    await removeGraph(page, graph);
  }
});


test("node references expose adjacent direct relations", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.goto(`/map?node=${encodeURIComponent(graph.records[1].id)}`);
    await expect(page.locator(".research-node")).toHaveCount(1);
    await expect(page.locator(".relation-list button")).toHaveCount(2);
    await expect(page.locator(".relation-list")).toContainText(graph.records[0].id);
    await expect(page.locator(".relation-list")).toContainText(graph.records[2].id);
  } finally {
    await removeGraph(page, graph);
  }
});


test("search input changes the LocalMap request", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.goto("/map");
    await expect(page.locator(".research-node")).toHaveCount(0);
    await page.getByLabel("检索局部地图").fill(graph.token);
    await page.getByRole("button", { name: "检索" }).click();
    await expect(page).toHaveURL(new RegExp(`text=${encodeURIComponent(graph.token)}`));
    await expect(page.locator(".research-node")).toHaveCount(3);
  } finally {
    await removeGraph(page, graph);
  }
});


test("keeps the map and inspector usable without mobile page overflow", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/map?text=${encodeURIComponent(graph.token)}`);
    await expect(page.locator(".research-node")).toHaveCount(3);
    await expect(page.locator(".graph-canvas")).toBeVisible();
    const workspace = page.locator(".map-workspace");
    await expect(workspace).toBeVisible();
    expect(await workspace.evaluate((element) => getComputedStyle(element).overflowY)).toBe("auto");
    await workspace.evaluate((element) => { element.scrollTop = element.scrollHeight; });
    await expect(page.locator(".inspector-section", { hasText: "节点 ID" })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  } finally {
    await removeGraph(page, graph);
  }
});


test("shows record titles and direct relation labels from LocalMap", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.goto(`/map?text=${encodeURIComponent(graph.token)}`);
    await expect(page.locator(".research-node")).toHaveCount(3);
    for (const record of graph.records) {
      await expect(page.locator(".research-node", { hasText: record.content.title })).toBeVisible();
    }
    const relations = page.locator(".relation-list");
    await expect(relations).toContainText("支持");
    await expect(relations).toContainText(graph.records[1].content.title);
  } finally {
    await removeGraph(page, graph);
  }
});


test("copies the exact node ID from the LocalMap inspector", async ({ page, context }) => {
  const graph = await seedGraph(page);
  try {
    await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: "http://127.0.0.1:18136" });
    await page.goto(`/map?node=${encodeURIComponent(graph.records[1].id)}`);
    const inspector = page.locator(".inspector");
    const section = inspector.locator(".inspector-section", { hasText: "节点 ID" });
    await expect(section.locator("code")).toHaveText(graph.records[1].id);
    await section.getByRole("button", { name: "复制节点 ID" }).click();
    await expect(section.getByRole("button", { name: "已复制节点 ID" })).toBeVisible();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(graph.records[1].id);
  } finally {
    await removeGraph(page, graph);
  }
});
