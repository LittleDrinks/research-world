import { expect, test } from "@playwright/test";


test.describe.configure({ mode: "serial" });


function uniqueToken() {
  return `local-map-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}


function nodeX(page, id) {
  return page.locator(`.react-flow__node[data-id="${id}"]`).evaluate((element) => new DOMMatrixReadOnly(getComputedStyle(element).transform).m41);
}


function overlappingPairs(page, selector) {
  return page.locator(selector).evaluateAll((elements) => elements.flatMap((left, index) => elements.slice(index + 1).filter((right) => {
    const a = left.getBoundingClientRect();
    const b = right.getBoundingClientRect();
    return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  }).map((right) => [left.dataset.id, right.dataset.id])));
}


function edgeNodeIntersections(page) {
  return page.locator(".signal-edge").evaluateAll((edges) => {
    const nodes = [...document.querySelectorAll(".react-flow__node")];
    return edges.flatMap((edge) => {
      const path = edge.querySelector(".react-flow__edge-path");
      const obstacles = nodes.filter((node) => ![edge.dataset.source, edge.dataset.target].includes(node.dataset.id));
      for (let offset = 0; offset <= path.getTotalLength(); offset += 1) {
        const point = new DOMPoint(path.getPointAtLength(offset).x, path.getPointAtLength(offset).y).matrixTransform(path.getScreenCTM());
        const hit = obstacles.find((node) => { const box = node.getBoundingClientRect(); return point.x > box.left && point.x < box.right && point.y > box.top && point.y < box.bottom; });
        if (hit) return [[edge.dataset.source, edge.dataset.target, hit.dataset.id]];
      }
      return [];
    });
  });
}


function recordContent(title) {
  return { title, text: `Orbit research ${title}` };
}


async function createProject(page) {
  const health = await page.request.get("/api/v1/health");
  expect(health.status()).toBe(200);
  expect(await health.json()).toEqual({ ok: true });
  const token = uniqueToken();
  const response = await page.request.post("/api/v1/projects", {
    data: { name: `Map-${token.slice(-8)}`, question: "Orbit research" },
  });
  expect(response.status()).toBe(201);
  const project = await response.json();
  const bootstrap = await page.request.get(`/api/v1/bootstrap?project_id=${encodeURIComponent(project.id)}`);
  expect(bootstrap.status()).toBe(200);
  expect((await bootstrap.json()).active_project_id).toBe(project.id);
  await page.goto("/projects");
  await page.getByRole("button", { name: new RegExp(project.name) }).click();
  await expect(page).toHaveURL(/\/map$/);
  return { id: project.id, token };
}


async function createProjectInBrowser(page) {
  const token = uniqueToken();
  const name = `Settings-${token.slice(-8)}`;
  await page.goto("/projects");
  await page.locator(".projects-bar").getByRole("button", { name: "新建项目" }).click();
  await page.getByLabel("项目名称").fill(name);
  await page.getByLabel("研究问题").fill("Settings owner question");
  await page.getByRole("button", { name: "创建项目" }).click();
  await expect(page).toHaveURL(/\/map$/);
  const response = await page.request.get("/api/v1/projects");
  return (await response.json()).find((project) => project.name === name);
}


async function createRecord(page, project, type, token) {
  const response = await page.request.post(`/api/v1/projects/${project}/records`, {
    data: { type, content: typeof token === "string" ? { title: `${type} ${token}`, text: token } : token },
  });
  expect(response.status()).toBe(201);
  return response.json();
}


async function seedInspectorGraph(page) {
  const project = await createProject(page);
  const source = await createRecord(page, project.id, "source", {
    title: "Kernel source", text: "Inspector source content", claims: [{ text: "legacy claim" }],
  });
  const direction = await createRecord(page, project.id, "direction", { title: "Kernel direction", text: "Inspector direction content" });
  const relation = await connect(page, project.id, source.id, direction.id);
  return { ...project, source, direction, records: [source, direction], relations: [relation] };
}


async function assertKernelInspector(page, graph) {
  const inspector = page.locator(".inspector");
  await expect(inspector.locator(".node-record")).toContainText(graph.source.content.text);
  await expect(inspector.locator(".inspector-section", { hasText: "直接关系" })).toContainText(graph.direction.id);
  await expect(inspector.getByText("原子主张")).toHaveCount(0);
  await expect(inspector.getByText("审计意见")).toHaveCount(0);
  await expect(inspector.locator(".pipeline-launcher, .workflow-start, .claim-list, .review-grid, .rejection-reason")).toHaveCount(0);
}


async function connect(page, project, source, target, type = "supports") {
  const response = await page.request.post(`/api/v1/projects/${project}/relations`, {
    data: { source_id: source, target_id: target, type },
  });
  expect(response.status()).toBe(201);
  return response.json();
}


async function seedRecords(page, specs, relationSpecs = []) {
  const project = await createProject(page);
  const records = [];
  for (const [type, content] of specs) {
    records.push(await createRecord(page, project.id, type, content));
  }
  const relations = [];
  for (const [source, target, type] of relationSpecs) {
    relations.push(await connect(page, project.id, records[source].id, records[target].id, type));
  }
  return { project: project.id, records, relations };
}


async function seedGraph(page) {
  const token = uniqueToken();
  const graph = await seedRecords(page, [["source", token], ["direction", token], ["experiment", token]], [[0, 1], [2, 1, "refutes"]]);
  return { ...graph, token };
}


async function removeGraph(page, graph) {
  for (const relation of graph.relations) {
    await page.request.delete(`/api/v1/projects/${graph.project}/relations/${relation.id}`);
  }
  for (const record of graph.records) await page.request.delete(`/api/v1/projects/${graph.project}/records/${record.id}`);
}


function trackMapRequests(page) {
  const requests = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (path.endsWith("/local-map") || /\/(records|relations)\//.test(path)) requests.push(`${request.method()} ${path}`);
  });
  return requests;
}


async function confirmDeletion(page, kind, id, requests) {
  const resource = kind === "Record" ? "records" : "relations";
  const encodedId = encodeURIComponent(id);
  const dialog = page.getByRole("dialog", { name: `确认删除 ${kind}` });
  await expect(dialog).toContainText(id);
  const response = page.waitForResponse((value) => value.request().method() === "DELETE" && new URL(value.url()).pathname.endsWith(`/${resource}/${encodedId}`));
  await dialog.getByRole("button", { name: `删除 ${kind}` }).click();
  expect((await response).status()).toBe(204);
  const deletion = requests.findIndex((value) => value.endsWith(`/${resource}/${encodedId}`));
  await expect.poll(() => requests.slice(deletion + 1).some((value) => value.endsWith("/local-map"))).toBe(true);
}


async function confirmFailedDeletion(page, kind, id, status) {
  const resource = kind === "Record" ? "records" : "relations";
  const dialog = page.getByRole("dialog", { name: `确认删除 ${kind}` });
  await expect(dialog).toContainText(id);
  const response = page.waitForResponse((value) => value.request().method() === "DELETE" && new URL(value.url()).pathname.endsWith(`/${resource}/${encodeURIComponent(id)}`));
  await dialog.getByRole("button", { name: `删除 ${kind}` }).click();
  expect((await response).status()).toBe(status);
}


async function deleteRecordFromInspector(page, record, requests) {
  await page.getByRole("button", { name: `删除 Record ${record.id}` }).click({ timeout: 5000 });
  await confirmDeletion(page, "Record", record.id, requests);
  await expect(page).not.toHaveURL(/node=/);
}


async function deleteRelationFromInspector(page, relation, requests) {
  await page.getByRole("button", { name: `删除 Relation ${relation.id}` }).click({ timeout: 5000 });
  await confirmDeletion(page, "Relation", relation.id, requests);
  await expect(page).not.toHaveURL(/node=/);
}


async function createUnselectedProject(page) {
  const token = uniqueToken();
  const response = await page.request.post("/api/v1/projects", { data: { name: `Other-${token.slice(-8)}`, question: "Other question" } });
  expect(response.status()).toBe(201);
  return response.json();
}


async function deleteGraphItems(page, graph, token, requests) {
  await page.goto(`/map?text=${encodeURIComponent(token)}`);
  await expect(page.locator(".research-node")).toHaveCount(3);
  await expect(page.locator(".react-flow__edge")).toHaveCount(3);
  await page.locator(`.react-flow__node[data-id="${graph.records[1].id}"]`).click();
  await deleteRelationFromInspector(page, graph.relations[0], requests);
  await expect(page.locator(".react-flow__edge")).toHaveCount(2);
  await page.goto(`/map?text=${encodeURIComponent(token)}`);
  await page.locator(`.react-flow__node[data-id="${graph.records[1].id}"]`).click();
  await deleteRecordFromInspector(page, graph.records[1], requests);
  await expect.poll(() => page.locator(".research-node").count()).toBe(2);
  await expect(page.locator(".react-flow__edge")).toHaveCount(0);
  await page.reload();
  await expect(page.locator(".research-node")).toHaveCount(2);
}


async function assertStaleDeletionFailure(page, graph) {
  await page.clock.install();
  await page.goto(`/map?text=${encodeURIComponent(graph.token)}`);
  await expect(page.locator(".research-node")).toHaveCount(3);
  await page.locator(`.react-flow__node[data-id="${graph.records[0].id}"]`).click();
  const deletion = page.getByRole("button", { name: `删除 Relation ${graph.relations[0].id}` });
  await expect(deletion).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`node=${encodeURIComponent(graph.records[0].id)}`));
  await expect(page.locator(".research-node")).toHaveCount(1);
  await page.clock.pauseAt(new Date());
  expect((await page.request.delete(`/api/v1/projects/${graph.project}/relations/${graph.relations[0].id}`)).status()).toBe(204);
  await deletion.click();
  await confirmFailedDeletion(page, "Relation", graph.relations[0].id, 404);
  await expect(page.getByRole("alert")).toContainText(graph.relations[0].id);
  await expect(page.getByRole("dialog", { name: "确认删除 Relation" })).toBeVisible();
  await expect(page.locator(".research-node")).toHaveCount(1);
  await expect(deletion).toBeVisible();
}


test("keeps Kernel record kinds in separate graph lanes", async ({ page }) => {
  const graph = await seedRecords(page, [["question", recordContent("Question")], ["source", recordContent("Source")], ["direction", recordContent("Direction")], ["experiment", recordContent("Experiment")]], [[1, 2], [2, 3]]);
  try {
    await page.goto(`/map?text=${encodeURIComponent("Orbit research")}`);
    await expect(page.locator(".research-node")).toHaveCount(4);
    const positions = await Promise.all(graph.records.map((record) => nodeX(page, record.id)));
    expect(positions[1]).toBeGreaterThan(positions[0]);
    expect(positions[2]).toBeGreaterThan(positions[1]);
    expect(positions[3]).toBeGreaterThan(positions[2]);
  } finally {
    await removeGraph(page, graph);
  }
});


test("keeps same-kind Kernel records from overlapping", async ({ page }) => {
  const specs = [["question", recordContent("Question")], ["direction", recordContent("Direction")], ["experiment", recordContent("Experiment 1")], ["experiment", recordContent("Experiment 2")], ["experiment", recordContent("Experiment 3")], ["experiment", recordContent("Experiment 4")]];
  const graph = await seedRecords(page, specs, [[2, 1], [3, 1], [4, 1], [5, 1]]);
  try {
    await page.goto(`/map?text=${encodeURIComponent("Orbit research")}`);
    await expect(page.locator(".research-node.kind-experiment")).toHaveCount(4);
    expect(await overlappingPairs(page, ".research-node.kind-experiment")).toEqual([]);
  } finally {
    await removeGraph(page, graph);
  }
});


test("routes Kernel relations around record nodes", async ({ page }) => {
  const specs = [["question", recordContent("Question")], ["source", recordContent("Source 1")], ["source", recordContent("Source 2")], ["direction", recordContent("Direction")], ["experiment", recordContent("Experiment 1")], ["experiment", recordContent("Experiment 2")]];
  const graph = await seedRecords(page, specs, [[1, 3], [2, 3], [4, 3, "refutes"], [5, 3]]);
  try {
    await page.goto(`/map?text=${encodeURIComponent("Orbit research")}`);
    await expect(page.locator(".signal-edge")).toHaveCount(4);
    expect(await edgeNodeIntersections(page)).toEqual([]);
  } finally {
    await removeGraph(page, graph);
  }
});


test("keeps the real map graph and inspector in a desktop grid", async ({ page }) => {
  const graph = await seedRecords(page, [["question", recordContent("Question")], ["source", recordContent("Source")], ["direction", recordContent("Direction")], ["experiment", recordContent("Experiment")]], [[1, 2], [2, 3]]);
  try {
    await page.goto(`/map?text=${encodeURIComponent("Orbit research")}`);
    const workspace = page.locator(".map-workspace");
    const graphCanvas = page.locator(".graph-canvas");
    const inspector = page.locator(".inspector");
    const workspaceBox = await workspace.boundingBox();
    const graphBox = await graphCanvas.boundingBox();
    const inspectorBox = await inspector.boundingBox();
    expect(await workspace.evaluate((element) => getComputedStyle(element).display)).toBe("grid");
    expect(inspectorBox.x).toBeGreaterThanOrEqual(graphBox.x + graphBox.width - 1);
    expect(inspectorBox.y).toBeGreaterThanOrEqual(workspaceBox.y);
    expect(inspectorBox.y + inspectorBox.height).toBeLessThanOrEqual(workspaceBox.y + workspaceBox.height + 1);
    await expect(page.locator(".map-search")).toBeVisible();
  } finally {
    await removeGraph(page, graph);
  }
});


test("deletes Records and Relations through confirmed Kernel HTTP and refreshes", async ({ page }) => {
  const token = uniqueToken();
  const graph = await seedRecords(page, [["source", token], ["direction", token], ["experiment", token]], [[0, 1], [1, 2, "depends_on"], [2, 1, "refutes"]]);
  const requests = trackMapRequests(page);
  try { await deleteGraphItems(page, graph, token, requests); } finally { await removeGraph(page, graph); }
});


test("keeps deletion scoped to the current Project and rejects unknown targets", async ({ page }) => {
  const graph = await seedGraph(page);
  const other = await createUnselectedProject(page);
  const foreign = await createRecord(page, other.id, "direction", uniqueToken());
  try {
    expect((await page.request.delete(`/api/v1/projects/${graph.project}/records/missing`)).status()).toBe(404);
    expect((await page.request.delete(`/api/v1/projects/${graph.project}/records/${foreign.id}`)).status()).toBe(403);
    await page.goto(`/map?text=${encodeURIComponent(graph.token)}`);
    await expect(page.locator(".research-node")).toHaveCount(3);
    await expect(page.locator(".react-flow__edge")).toHaveCount(2);
  } finally {
    await removeGraph(page, graph);
    await removeGraph(page, { project: other.id, records: [foreign], relations: [] });
  }
});


test("preserves map state and reports a stale deletion failure", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await assertStaleDeletionFailure(page, graph);
  } finally {
    await removeGraph(page, graph);
  }
});


async function assertRelationSelection(page, graph, index) {
  await page.goto(`/map?node=${encodeURIComponent(graph.records[1].id)}`);
  const relations = page.locator(".relation-list .relation-link");
  await expect(relations).toHaveCount(2);
  await relations.nth(index).click();
  await expect(page).toHaveURL(new RegExp(`node=${encodeURIComponent(graph.records[index === 0 ? 0 : 2].id)}`));
}


test("node references expose adjacent direct relations", async ({ page }) => {
  const graph = await seedGraph(page);
  try {
    await page.goto(`/map?node=${encodeURIComponent(graph.records[1].id)}`);
    await expect(page.locator(".research-node")).toHaveCount(1);
    await expect(page.locator(".relation-list")).toContainText(graph.records[0].id);
    await expect(page.locator(".relation-list")).toContainText(graph.records[2].id);
    await assertRelationSelection(page, graph, 0);
    await assertRelationSelection(page, graph, 1);
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
    await expect(page.locator(".node-record")).toContainText(graph.records[0].content.text);
    const relations = page.locator(".relation-list");
    await expect(relations).toContainText("支持");
    await expect(relations).toContainText(graph.records[1].content.title);
    await expect(page.locator(".signal-edge.polarity-refutes")).toHaveAttribute("data-source", graph.records[2].id);
    await expect(page.locator(".signal-edge.polarity-refutes")).toHaveAttribute("data-target", graph.records[1].id);
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
    await expect(inspector.locator(".inspector-section", { hasText: "讨论" })).toHaveCount(0);
    await expect(inspector.getByRole("button", { name: /对话/ })).toHaveCount(0);
  } finally {
    await removeGraph(page, graph);
  }
});


test("renders Kernel project settings without legacy World controls", async ({ page }) => {
  const project = await createProjectInBrowser(page);
  const legacyPatches = [];
  page.on("request", (request) => {
    if (request.method() === "PATCH" && request.url().includes("/api/v1/projects/")) legacyPatches.push(request.url());
  });
  await page.getByRole("link", { name: "项目设置" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  const settings = page.locator(".settings-record");
  await expect(settings.locator("dt")).toHaveText(["名称", "研究问题", "项目 ID", "创建时间"]);
  await expect(settings).toContainText(project.name);
  await expect(settings).toContainText(project.question);
  await expect(settings).toContainText(project.id);
  await expect(settings).not.toContainText("工作区");
  await expect(settings).not.toContainText("规模");
  await expect(settings).not.toContainText("Auto");
  await expect(page.locator("input[type=checkbox]")).toHaveCount(0);
  expect(legacyPatches).toEqual([]);
});


test("renders a pure Kernel LocalMap inspector and selects adjacent records", async ({ page }) => {
  const graph = await seedInspectorGraph(page);
  try {
    await page.goto(`/map?node=${encodeURIComponent(graph.source.id)}`);
    await assertKernelInspector(page, graph);
    await page.locator(".relation-list .relation-link").click();
    await expect(page).toHaveURL(new RegExp(`node=${encodeURIComponent(graph.direction.id)}`));
    await expect(page.locator(".node-record")).toContainText(graph.direction.content.text);
  } finally {
    await removeGraph(page, graph);
  }
});
