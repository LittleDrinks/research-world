import { expect, test } from "@playwright/test";
import { bootstrap, mockBase, node, run, thread, threadDetail } from "./fixtures";


function mapFixture() {
  const nodes = [node("node:q", "question"), node("node:s", "source"),
    node("node:d", "direction", { parent_id: "node:q" }), node("node:e", "experiment", { parent_id: "node:d" })];
  return bootstrap({ nodes,
    edges: [{ source: "node:s", target: "node:d", polarity: "supports" }, { source: "node:e", target: "node:d", polarity: "refutes" }],
    pipelines: [{ id: "custom-cycle", name: "自定义流程", stages: [] }, { id: "research", name: "规划与验证", stages: [] }] });
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


test("lays out the four fixed node kinds as graph lanes", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.goto("/map");
  await expect(page.locator(".research-node")).toHaveCount(4);
  expect(await nodeX(page, "node:s")).toBeGreaterThan(await nodeX(page, "node:q"));
  expect(await nodeX(page, "node:d")).toBeGreaterThan(await nodeX(page, "node:s"));
  expect(await nodeX(page, "node:e")).toBeGreaterThan(await nodeX(page, "node:d"));
  await expect(page.locator(".react-flow__edge")).toHaveCount(3);
  await page.screenshot({ path: "test-results/map-desktop.png" });
});


test("keeps admitted and ghost experiments from overlapping in one lane", async ({ page }) => {
  const nodes = [node("node:q", "question"), node("node:d", "direction", { parent_id: "node:q" }),
    node("node:a1", "experiment", { parent_id: "node:d" }), node("node:a2", "experiment", { parent_id: "node:d" }),
    node("node:g1", "experiment", { parent_id: "node:d", life_state: "ghost" }),
    node("node:g2", "experiment", { parent_id: "node:d", life_state: "ghost" })];
  const edges = [{ source: "node:a1", target: "node:d", polarity: "supports" },
    { source: "node:a2", target: "node:d", polarity: "supports" }];
  await mockBase(page, bootstrap({ nodes, edges }));
  await page.goto("/map");
  const experiments = ".react-flow__node:has(.kind-experiment)";
  await expect(page.locator(experiments)).toHaveCount(4);
  expect(await overlappingPairs(page, experiments)).toEqual([]);
});


test("shows the research journal as a fact timeline", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.goto("/map");
  await page.getByRole("button", { name: "科研日志" }).click();
  await expect(page.locator(".journal li").first()).toBeVisible();
  await expect(page.locator(".journal")).toContainText("启动运行：生成研究方向");
  await expect(page.locator(".journal")).toContainText("创建问题");
  await expect(page.locator(".graph-canvas")).toHaveCount(0);
  await page.getByRole("button", { name: "地图", exact: true }).click();
  await expect(page.locator(".research-node").first()).toBeVisible();
});


test("starts a run for the selected node from the inspector", async ({ page }) => {
  let request;
  await mockBase(page, mapFixture());
  await page.route(/\/api\/v1\/projects\/project%3Atest\/runs/, (route) => {
    request = route.request().postDataJSON();
    return route.fulfill({ status: 201, json: run({ id: "run:new" }) });
  });
  await page.goto("/map?node=node%3Ad");
  await expect(page.getByLabel("选择流程")).toHaveValue("custom-cycle");
  await page.getByLabel("选择流程").selectOption("research");
  await page.getByLabel("选择流程").selectOption("custom-cycle");
  await page.getByRole("button", { name: "发起运行" }).click();
  await expect.poll(() => request).toBeTruthy();
  expect(request).toEqual({ node_id: "node:d", pipeline_id: "custom-cycle" });
  await expect(page).toHaveURL(/\/traces\/run%3Anew/);
});


test("keeps evidence edge direction from the backend", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.goto("/map");
  const refutes = page.locator(".signal-edge.polarity-refutes");
  await expect(refutes).toHaveCount(1);
  await expect(refutes).toHaveAttribute("data-source", "node:e");
  await expect(refutes).toHaveAttribute("data-target", "node:d");
  const supports = page.locator(".signal-edge.polarity-supports");
  await expect(supports).toHaveAttribute("data-source", "node:s");
  await expect(supports).toHaveAttribute("data-target", "node:d");
});


test("selects a node from the sidebar record list", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.goto("/map");
  await page.locator(".record-list .record-item", { hasText: "direction 节点 node:d" }).click();
  await expect(page).toHaveURL(/\/map\?node=node%3Ad/);
  await expect(page.locator(".inspector h1")).toHaveText("direction 节点 node:d");
});


test("does not offer a Thread entry for a ghost node", async ({ page }) => {
  const ghost = node("node:g", "direction", { life_state: "ghost", rejection_reason: "证据不足" });
  await mockBase(page, bootstrap({ nodes: [node("node:q", "question"), ghost] }));
  await page.goto("/map?node=node%3Ag");
  const inspector = page.locator(".inspector");
  await expect(inspector).toContainText("已驳回");
  await expect(inspector.locator(".inspector-section", { hasText: "讨论" })).toHaveCount(0);
  await expect(inspector.getByRole("button", { name: "新建对话并钉入该节点" })).toHaveCount(0);
  await expect(inspector.getByRole("button", { name: "发起运行" })).toHaveCount(0);
  await expect(inspector.getByLabel("选择流程")).toHaveCount(0);
});


test("shows claim evidence and support challenge arguments without scores", async ({ page }) => {
  const reviewed = node("node:d", "direction", {
    payload: { text: "可验证方向", claims: [{ id: "claim:1", text: "效应高于基线", verdict: "supported", evidence: ["node:s"] }] },
    rebuttal: {
      reviewer_a: { stance: "support", decision: "approve", argument: "来源支持该机制", evidence: ["claim:1", "node:s"] },
      reviewer_b: { stance: "challenge", decision: "reject", argument: "仍需补实验", evidence: ["artifact:abc"] },
    },
  });
  await mockBase(page, bootstrap({ nodes: [node("node:q", "question"), reviewed] }));
  await page.goto("/map?node=node%3Ad");
  const inspector = page.locator(".inspector");
  const claim = inspector.locator(".claim-list > li");
  await expect(claim).toContainText("效应高于基线");
  await expect(claim).toContainText("已支持");
  await expect(claim).toContainText("node:s");
  const reviews = inspector.locator(".review-grid article");
  await expect(reviews.nth(0)).toContainText("支持方");
  await expect(reviews.nth(0)).toContainText("通过");
  await expect(reviews.nth(0)).toContainText("claim:1");
  await expect(reviews.nth(0)).toContainText("node:s");
  await expect(reviews.nth(1)).toContainText("质疑方");
  await expect(reviews.nth(1)).toContainText("驳回");
  await expect(reviews.nth(1)).toContainText("仍需补实验");
  await expect(reviews.nth(1)).toContainText("artifact:abc");
  await expect(inspector).not.toContainText("quality");
  await expect(inspector).not.toContainText("diversity");
});


test("keeps graph and inspector side by side on a desktop grid", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.goto("/map");
  expect(await page.locator(".map-workspace").evaluate((element) => getComputedStyle(element).display)).toBe("grid");
  const graph = await page.locator(".graph-canvas").boundingBox();
  const inspector = await page.locator(".inspector").boundingBox();
  expect(graph.width).toBeGreaterThan(0);
  expect(inspector.x).toBeGreaterThanOrEqual(graph.x + graph.width - 1);
  expect(inspector.x + inspector.width).toBeLessThanOrEqual(page.viewportSize().width);
  expect(inspector.y + inspector.height).toBe(await page.evaluate(() => innerHeight));
  expect(await page.locator(".map-toolbar").evaluate((element) => getComputedStyle(element).display)).toBe("flex");
  const title = await page.locator(".map-toolbar > div").first().boundingBox();
  const tools = await page.locator(".map-tools").boundingBox();
  expect(title.x + title.width).toBeLessThanOrEqual(tools.x);
});


test("scrolls the map workspace down to the inspector on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockBase(page, mapFixture());
  await page.goto("/map");
  const workspace = page.locator(".map-workspace");
  expect(await workspace.evaluate((element) => getComputedStyle(element).overflowY)).toBe("auto");
  await workspace.evaluate((element) => { element.scrollTop = element.scrollHeight; });
  await expect(page.locator(".inspector-section", { hasText: "讨论" })).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});


test("enters the thread that already pinned the node", async ({ page }) => {
  await mockBase(page, mapFixture());
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/map?node=node%3Aq");
  await page.getByRole("button", { name: /继续对话/ }).click();
  await expect(page).toHaveURL(/\/chat\/thread%3At1$/);
});


test("creates a thread pinned to the node from the inspector", async ({ page }) => {
  let body;
  await mockBase(page, mapFixture());
  await page.route(/\/api\/v1\/projects\/project%3Atest\/threads/, (route) => {
    if (route.request().method() !== "POST") return route.fulfill({ json: [thread()] });
    body = route.request().postDataJSON();
    return route.fulfill({ status: 201, json: thread({ id: "thread:t2", title: "新对话", nodes: [] }) });
  });
  await page.route(/\/api\/v1\/threads\/thread%3At2$/, (route) => route.fulfill({ json: threadDetail({ id: "thread:t2", title: "新对话" }) }));
  await page.goto("/map?node=node%3Ad");
  await page.getByRole("button", { name: "新建对话并钉入该节点" }).click();
  await expect.poll(() => body).toEqual({ node_ids: ["node:d"] });
  await expect(page).toHaveURL(/\/chat\/thread%3At2/);
});
