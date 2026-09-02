// 验收3：模型凭证失败时，用户在 Chat 看到明确失败，不伪装成成功或空回答。
// 手段：以无效 API key 临时重建 runtime 容器，结束后恢复原配置并复验回答可用（同一对话内对照）。
import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import path from "node:path";
import { expect, test } from "./fixtures.js";
import { closeToast, openNewThread, sendMessage, settledAnswers, snapshot, waitForErrorToast, waitForReply } from "./helpers/chat.js";
import { RW_ROOT, redact, registerSecret } from "./helpers/env.js";

const OVERRIDE = path.join(RW_ROOT, "web", "tests", "t2", "credential-override.compose.yaml");
const BASELINE = "1+1 等于几？请用一句话回答。";
const PROMPT = "2+2 等于几？请用一句话回答。";

function compose(args, extraEnv = {}) {
  try {
    return execFileSync("docker", ["compose", ...args], { cwd: RW_ROOT, env: { ...process.env, ...extraEnv }, encoding: "utf8", timeout: 180000, stdio: ["ignore", "pipe", "pipe"] });
  } catch (error) {
    throw new Error(`docker compose ${args.join(" ")} 失败：${redact(String(error.stderr || error.message)).slice(0, 2000)}`);
  }
}

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

async function waitHealthy(request, url, deadlineMs = 120000) {
  const deadline = Date.now() + deadlineMs;
  for (;;) {
    const status = await request.get(url).then((r) => r.status()).catch(() => 0);
    if (status === 200) return;
    if (Date.now() > deadline) throw new Error(`${url} 在 ${deadlineMs}ms 内未恢复 200（最后状态 ${status}）`);
    await sleep(2000);
  }
}

test("验收3：模型凭证失败时 Chat 明确失败可见", async ({ page, request }, testInfo) => {
  test.setTimeout(480000);
  const badKey = `t2-invalid-${randomBytes(12).toString("hex")}`;
  registerSecret(badKey);
  await waitHealthy(request, "/api/v1/health");
  await waitHealthy(request, "http://127.0.0.1:8098/health");
  const threadId = await openNewThread(page);
  await sendMessage(page, BASELINE);
  await waitForReply(page, 0);
  try {
    compose(["-f", "compose.yaml", "-f", OVERRIDE, "up", "-d", "--no-deps", "runtime"], { RW_T2_BAD_API_KEY: badKey });
    await waitHealthy(request, "http://127.0.0.1:8098/health");
    await request.get(`/api/v1/runtime/catalog?project_id=${(await (await request.get("/api/v1/bootstrap")).json()).projects[0].id}`);
    await sendMessage(page, PROMPT);
    const toast = await waitForErrorToast(page, 90000);
    expect(toast.length, "错误提示为空，失败不明确").toBeGreaterThan(0);
    expect(await settledAnswers(page).count(), "失败轮出现了新的助手回答，伪装成成功").toBe(1);
    await snapshot(page, testInfo, "05-credential-failure-visible");
  } finally {
    compose(["-f", "compose.yaml", "up", "-d", "--no-deps", "runtime"]);
    await waitHealthy(request, "http://127.0.0.1:8098/health");
    await waitHealthy(request, "/api/v1/health");
  }
  const evidence = compose(["ps"]);
  await testInfo.attach("compose-ps-after-restore.txt", { body: redact(evidence), contentType: "text/plain" });
  await closeToast(page);
  await sendMessage(page, PROMPT);
  await waitForReply(page, 1);
  await snapshot(page, testInfo, "05-restored-answer");
});
