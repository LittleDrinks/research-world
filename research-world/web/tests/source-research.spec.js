import { expect, test } from "@playwright/test";
import { agents, bootstrap, mockBase, node, thread, threadDetail } from "./fixtures";


const TOOL_IDS = ["crossref", "openalex", "arxiv", "pubmed", "project_files"];


function sourcePreset(status = "ready") {
  const tools = TOOL_IDS.map((id) => capability(id, status));
  return { id: "source-researcher", name: "文献研究员", description: "检索一手来源、核验全文与书目元数据。",
    spec: { id: "source-researcher", name: "文献研究员", instructions: "Return SourceCandidate only.",
      skills: ["source-research"], tools: [...TOOL_IDS] }, tools,
    skills: [capability("source-research", "ready", "执行证据边界检查")] };
}


function capability(id, status, recommendation = `使用 ${id}`) {
  return { id, status, recommendation,
    ...(status === "ready" ? {} : { reason: "not_installed" }) };
}


function sourceCatalog(status = "ready") {
  const preset = sourcePreset(status);
  return { endpoints: [{ id: "openai-compatible", name: "OpenAI", available: true }],
    models: [{ id: "qwen3.7-flash", endpoint: "openai-compatible" }],
    skills: [{ id: "source-research", name: "Source Research" }],
    tools: status === "ready" ? preset.tools.map((item) => ({ ...item, name: item.id })) : [],
    presets: [preset] };
}


function sourceDraft() {
  const preset = sourcePreset();
  return { preset_id: preset.id, reason: preset.description,
    spec: { ...preset.spec, endpoint: "openai-compatible", model: "qwen3.7-flash",
      options: { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 12, token_budget: 200000 } },
    tools: preset.tools, skills: preset.skills, confirmable: true, issues: [] };
}


function candidate(directionId, title = "Auditable source") {
  return { title, authors: ["Ada Researcher"], year: 2026, venue: "Journal of Evidence",
    doi: "10.1000/evidence", url: "https://example.test/evidence", source_type: "journal_article",
    license: "CC-BY-4.0", access_status: "open", artifact: { id: "artifact:evidence",
      project_file: "sources/evidence.txt", media_type: "text/plain", sha256: "a".repeat(64) },
    relationship: { direction_id: directionId, use: "supports", relevance: "Direct test.",
      claims: ["Supported."], locations: [{ locator: "Results 2", quote: "Measured evidence." }] },
    retrieval: { query: "auditable evidence", database: "Crossref; OpenAlex", verified_at: "2026-08-24T03:00:00Z" },
    unresolved_questions: [] };
}


function sourceNode(id, value, lifeState, rejection = null) {
  return node(id, "source", { parent_id: value.relationship.direction_id, payload: value,
    life_state: lifeState, rejection_reason: rejection });
}


function sourceRun(candidates, sources) {
  return { id: "run:source", project_id: "project:test", node_id: "node:d", lineage_id: "lineage:node:d",
    pipeline_id: "source-research", definition_snapshot: { id: "source-research", name: "文献检索与全文核验", stages: [] },
    stage: "submit", status: "completed", payload: { thread_id: "thread:t1",
      _pipeline: { values: { source_candidates: candidates, sources } } }, auto: 0,
    created_at: "2026-08-24T03:00:00Z", updated_at: "2026-08-24T03:01:00Z", steps: [], events: [] };
}


function inViewport(box, width) {
  return box.x >= 0 && box.x + box.width <= width;
}


test("shows blocked source Preset readiness without clipping the 390px Agent page", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockBase(page);
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: sourceCatalog("unavailable") }));
  await page.goto("/agents/research-assistant");
  const panel = page.getByRole("region", { name: "Profile Presets" });
  await expect(panel).toContainText("文献研究员");
  await expect(panel).toContainText("project_files（unavailable / not_installed）");
  await expect(page.locator(".sidebar")).toBeHidden();
  expect(inViewport(await page.locator(".agent-form-header h1").boundingBox(), 390)).toBe(true);
  expect(inViewport(await panel.getByRole("button", { name: "应用为草稿" }).boundingBox(), 390)).toBe(true);
  await panel.getByRole("button", { name: "应用为草稿" }).click();
  const dialog = page.getByRole("dialog", { name: "应用 Preset：文献研究员" });
  await expect(dialog.getByRole("alert")).toContainText("Tool 不可用：project_files（unavailable / not_installed）");
  await expect(dialog.getByRole("link", { name: "Tool Catalog", exact: true })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "创建 Agent", exact: true })).toBeDisabled();
  expect(inViewport(await dialog.getByRole("alert").boundingBox(), 390)).toBe(true);
});


test("creates a source Profile snapshot in Chat and starts the Admission pipeline", async ({ page }) => {
  const direction = node("node:d", "direction", { parent_id: "node:q" });
  const value = candidate(direction.id);
  const pending = sourceNode("node:s", value, "pending");
  const run = sourceRun([value], [pending]);
  const state = bootstrap({ nodes: [node("node:q", "question"), direction], edges: [], runs: [],
    pipelines: [{ id: "source-research", name: "文献检索与全文核验", stages: [] }],
    threads: [thread({ nodes: [direction] })] });
  let created;
  let launched;
  await mockBase(page, state);
  await page.route(/\/api\/v1\/bootstrap/, (route) => route.fulfill({ json: state }));
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) =>
    route.fulfill({ json: threadDetail({ nodes: [direction] }) }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: sourceCatalog() }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/agent-drafts/, (route) => route.fulfill({ status: 201, json: sourceDraft() }));
  await page.route(/\/api\/v1\/agents(\?|$)/, (route) => agentRoute(route, (value) => { created = value; }));
  await page.route(/\/api\/v1\/projects\/project%3Atest\/runs/, (route) => {
    launched = route.request().postDataJSON(); state.runs = [run]; state.nodes = [...state.nodes, pending];
    return route.fulfill({ status: 201, json: run });
  });
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "起草 Agent" }).click();
  await page.getByRole("menuitem", { name: /文献研究员/ }).click();
  const draft = page.getByRole("region", { name: "Agent 草稿" });
  await expect(draft).toContainText("project_files（ready）");
  await draft.getByLabel("名称").fill("文献核验员");
  await draft.getByRole("button", { name: "确认创建" }).click();
  await expect.poll(() => created).toBeTruthy();
  expect(created.tools).toEqual(TOOL_IDS);
  expect(created.name).toBe("文献核验员");
  await page.getByRole("button", { name: "研究运行" }).click();
  await page.getByRole("button", { name: "启动流程" }).click();
  await expect.poll(() => launched).toBeTruthy();
  expect(launched).toEqual({ node_id: direction.id, pipeline_id: "source-research", payload: { thread_id: "thread:t1" } });
  await page.locator(".run-card-head").click();
  const card = page.locator(".source-projection");
  await expect(card).toContainText("Auditable source");
  await expect(card).toContainText("待 Admission");
  await expect(card).toContainText("artifact:evidence");
  await card.getByRole("button", { name: "Auditable source" }).click();
  await expect(page).toHaveURL(/\/map\?node=node%3As/);
  await expect(page.locator(".inspector")).toContainText("待审查");
  await expect(page.locator(".inspector")).toContainText("sources/evidence.txt");
});


test("keeps admitted and rejected Source details distinct", async ({ page }) => {
  const direction = node("node:d", "direction", { parent_id: "node:q" });
  const admittedValue = candidate(direction.id, "Admitted source");
  const ghostValue = candidate(direction.id, "Rejected source");
  const admitted = sourceNode("node:admitted", admittedValue, "admitted");
  const ghost = sourceNode("node:ghost", ghostValue, "ghost", "Metadata does not match the primary record");
  const run = sourceRun([admittedValue, ghostValue], [admitted, ghost]);
  const body = bootstrap({ nodes: [node("node:q", "question"), direction, admitted, ghost],
    edges: [{ source: admitted.id, target: direction.id, polarity: "supports" }], runs: [run] });
  await mockBase(page, body);
  await page.route(/\/api\/v1\/threads\/thread%3At1$/, (route) => route.fulfill({ json: threadDetail() }));
  await page.goto("/chat/thread%3At1");
  await page.getByRole("button", { name: "研究运行" }).click();
  await page.locator(".run-card-head").click();
  const admittedRow = page.locator(".source-projection li", { hasText: "Admitted source" });
  const ghostRow = page.locator(".source-projection li", { hasText: "Rejected source" });
  await expect(admittedRow).toContainText("已准入");
  await expect(admittedRow).not.toContainText("Metadata does not match");
  await expect(ghostRow).toContainText("已驳回");
  await expect(ghostRow).toContainText("Metadata does not match the primary record");
  await ghostRow.getByRole("button", { name: "Rejected source" }).click();
  await expect(page.locator(".inspector-header")).toContainText("已驳回");
  await expect(page.locator(".inspector-header")).toContainText("Metadata does not match the primary record");
  await page.locator(".inspector").getByRole("button", { name: direction.id }).click();
  await expect(page).toHaveURL(/node=node%3Ad/);
});


function agentRoute(route, onCreate) {
  if (route.request().method() === "GET") return route.fulfill({ json: agents() });
  const value = route.request().postDataJSON();
  onCreate(value);
  return route.fulfill({ status: 201, json: value });
}
