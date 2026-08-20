// 前端全流程 QA：经真实 UI 创建项目、发起 brainstorm；Auto 下引擎自动为已入图方向派生研究工作流，
// 脚本只经 UI 处理人工门（双审分歧批准 / 执行确认），轮询终态并产出截图与报告。
// 用法：node scripts/qa-full-flow.mjs            新建项目跑全流程
//       QA_TITLE="标题" node scripts/...         续跑已有项目（等待在途工作流收尾）
import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";

const BASE = "http://127.0.0.1:8095";
const OUT = new URL("../qa-results/", import.meta.url).pathname;
const QUESTION = "素数在整数中的分布存在哪些可计算的特殊规律？";
const RESUME_TITLE = process.env.QA_TITLE;
const TITLE = RESUME_TITLE || `QA 素数分布全流程 ${new Date().toISOString().slice(11, 19)}`;
const ACTIVE = ["queued", "running", "waiting_human"];
const TERMINAL = ["completed", "paused", "failed"];
const shots = [];
const log = (msg) => console.log(`[${new Date().toISOString().slice(11, 19)}] ${msg}`);

async function shot(page, name) {
  await page.screenshot({ path: `${OUT}${name}.png`, fullPage: false });
  shots.push(`${name}.png`);
  log(`截图 ${name}.png`);
}

async function bootstrap(projectId) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  const response = await fetch(`${BASE}/api/v1/bootstrap${query}`);
  if (!response.ok) throw new Error(`bootstrap ${response.status}`);
  return response.json();
}

// 等待项目内全部工作流进入终态；出现 waiting_human 时经真实 UI 按钮放行。
async function drainWorkflows(page, projectId, { timeoutMs = 45 * 60_000 } = {}) {
  const start = Date.now();
  for (;;) {
    const data = await bootstrap(projectId);
    const waiting = data.workflows.filter((item) => item.status === "waiting_human");
    if (waiting.length) {
      for (const workflow of waiting) {
        const conflict = Boolean(workflow.payload?.conflict_node);
        log(`等待人工：${workflow.kind} ${workflow.id.slice(10, 18)}（${conflict ? "双审分歧" : "执行确认"}，stage=${workflow.stage}）`);
        const index = data.workflows.findIndex((item) => item.id === workflow.id);
        await page.locator(".workflow-list button").nth(index).click({ timeout: 10_000 });
        await page.waitForTimeout(600);
        if (conflict) await page.locator('button[title="批准"]').first().click({ timeout: 10_000 });
        else await page.getByRole("button", { name: "继续执行", exact: true }).first().click({ timeout: 10_000 });
        await page.waitForTimeout(4000);
      }
      continue;
    }
    const active = data.workflows.filter((item) => ACTIVE.includes(item.status));
    if (!active.length) return data;
    log(`在途 ${active.length} 个：${active.map((item) => `${item.kind === "brainstorm" ? "构思" : "研究"}@${item.stage}`).join("、")}`);
    if (Date.now() - start > timeoutMs) throw new Error("超时：工作流未全部到达终态");
    await page.waitForTimeout(8000);
  }
}

async function enterProject(page, title) {
  await page.goto(`${BASE}/projects`);
  await page.getByRole("heading", { name: "选择研究项目" }).waitFor();
  const card = page.locator(".project-list > button", { hasText: title }).first();
  await card.waitFor();
  await card.click();
  await page.waitForURL(/\/map/);
  await page.locator(".research-node").first().waitFor();
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.setDefaultTimeout(20_000);

  let projectId;
  if (RESUME_TITLE) {
    await enterProject(page, RESUME_TITLE);
    const listing = await bootstrap();
    projectId = listing.projects.find((item) => item.title === RESUME_TITLE)?.id;
    if (!projectId) throw new Error(`找不到项目：${RESUME_TITLE}`);
    log(`续跑项目 ${projectId}`);
    await page.getByRole("link", { name: "活动" }).click();
    await page.waitForURL(/\/activity/);
    await page.locator(".workflow-list button").first().waitFor();
  } else {
    // 1. 项目页 → 新建项目
    await page.goto(`${BASE}/projects`);
    await page.getByRole("heading", { name: "选择研究项目" }).waitFor();
    await shot(page, "01-projects");
    await page.getByRole("button", { name: "新建项目" }).first().click();
    await page.getByLabel("项目名称").fill(TITLE);
    await page.getByLabel("研究问题").fill(QUESTION);
    await page.getByRole("button", { name: "创建项目" }).click();
    await page.waitForURL(/\/map/);
    await page.locator(".research-node").first().waitFor();
    await shot(page, "02-map-question");
    const created = await bootstrap();
    projectId = created.projects.find((item) => item.title === TITLE)?.id;
    if (!projectId) throw new Error("新建项目未出现在列表");
    log(`项目 ${projectId}`);

    // 2. 打开 Auto（受控勾选框，等 bootstrap 轮询回写后再继续）
    await page.locator(".auto-toggle input").click();
    await page.waitForFunction(() => document.querySelector(".auto-toggle input")?.checked === true, null, { timeout: 20_000 });
    log("Auto 已开启");

    // 3. 从问题节点发起 brainstorm
    await page.locator("article.research-node.kind-question").first().click();
    await page.getByRole("button", { name: "发起工作流", exact: true }).click();
    await page.waitForURL(/\/activity\?workflow=/);
    log(`brainstorm 已发起：${new URL(page.url()).searchParams.get("workflow")}`);
    await shot(page, "03-activity-brainstorm-start");
  }

  // 4. 排空全部工作流（brainstorm + 自动派生的研究工作流），人工门走 UI
  const finalData = await drainWorkflows(page, projectId);
  const brainstorm = finalData.workflows.filter((item) => item.kind === "brainstorm");
  const research = finalData.workflows.filter((item) => item.kind !== "brainstorm");
  log(`终态：brainstorm ${brainstorm.map((item) => item.status).join(",")}；research ${research.map((item) => item.status).join(",")}`);

  // 5. 截图：活动轨迹、终态图谱、对话页（一律经侧栏站内导航，避免整页刷新丢项目上下文）
  await page.getByRole("link", { name: "活动" }).click();
  await page.waitForURL(/\/activity/);
  await page.locator(".workflow-list button").first().waitFor();
  await shot(page, "04-activity-final");
  await page.getByRole("link", { name: "地图" }).click();
  await page.waitForURL(/\/map/);
  await page.waitForTimeout(4000);
  await shot(page, "05-map-final");
  await page.getByRole("link", { name: "对话" }).click();
  await page.waitForURL(/\/chat/);
  await page.locator(".node-rail").waitFor();
  await shot(page, "06-chat");

  await browser.close();

  // 6. 汇总报告
  const nodes = finalData.nodes;
  const experiments = nodes.filter((node) => node.kind === "experiment");
  const report = {
    project: { id: projectId, title: TITLE, question: QUESTION },
    workflows: finalData.workflows.map((item) => ({ id: item.id, kind: item.kind, status: item.status, stage: item.stage, events: (item.events || []).length })),
    nodes: nodes.map((node) => ({ kind: node.kind, life_state: node.life_state, direction_status: node.direction_status, title: (node.payload?.title || node.payload?.text || "").slice(0, 80) })),
    counts: {
      question: nodes.filter((n) => n.kind === "question").length,
      direction: nodes.filter((n) => n.kind === "direction").length,
      direction_admitted: nodes.filter((n) => n.kind === "direction" && n.life_state === "admitted").length,
      direction_supported: nodes.filter((n) => n.kind === "direction" && n.direction_status === "supported").length,
      direction_refuted: nodes.filter((n) => n.kind === "direction" && n.direction_status === "refuted").length,
      experiment: experiments.length,
      experiment_admitted: experiments.filter((n) => n.life_state === "admitted").length,
      edges: finalData.edges.length,
    },
    screenshots: shots,
  };
  writeFileSync(`${OUT}qa-report.json`, JSON.stringify(report, null, 2));
  console.log("\n===== QA 汇总 =====");
  console.log(JSON.stringify({ workflows: report.workflows, counts: report.counts }, null, 2));
  const okResearch = research.some((item) => item.status === "completed");
  const pass = brainstorm.some((item) => item.status === "completed") && okResearch
    && report.counts.direction_admitted >= 1 && experiments.length >= 1;
  console.log(pass ? "PASS：科研全流程走通" : "FAIL：流程未完全走通，检查 qa-report.json");
  process.exit(pass ? 0 : 1);
}

main().catch((error) => { console.error("QA 失败：", error.message); process.exit(1); });
