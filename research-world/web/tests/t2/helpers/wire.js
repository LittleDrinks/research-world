// 线缆采集：记录同源 /api 响应（含 SSE 完成后的完整 body），供泄露断言与归档。
import { findLeak, leakContext } from "./env.js";

export function attachWireCollector(page) {
  const entries = [];
  const pending = [];
  page.on("response", (response) => {
    let pathname = "";
    try { pathname = new URL(response.url()).pathname; } catch { return; }
    if (!pathname.startsWith("/api/")) return;
    const entry = { url: response.url(), status: response.status(), body: "" };
    entries.push(entry);
    pending.push(response.text().then((text) => { entry.body = text; }).catch(() => {}));
  });
  return {
    entries,
    async settle(timeoutMs = 8000) {
      await Promise.race([Promise.allSettled(pending), new Promise((done) => setTimeout(done, timeoutMs))]);
    },
  };
}

async function pageText(page) {
  return page.innerText("body").catch(() => "");
}

// 验收4 守卫：凭证值（.env 与注入的测试凭证）不得出现在页面或任何 /api 响应中。
export async function assertNoCredentialLeak(wire, page) {
  await wire.settle();
  const surfaces = [["页面文本", await pageText(page)], ...wire.entries.map((entry) => [`响应 ${entry.url}`, entry.body])];
  for (const [where, text] of surfaces) {
    const secret = findLeak(text ?? "");
    if (secret) throw new Error(`凭证值泄露到${where}（值已脱敏，长度 ${secret.length}）：…${leakContext(text, secret)}…`);
  }
}

// 响应 body 中出现非空凭证型 JSON 字段即视为内部字段泄露。
export function findInternalKeyLeak(body) {
  const match = /"(api_?key|base_?url|authorization|secret_?key|access_?token)"\s*:\s*"[^"]+/i.exec(body ?? "");
  return match ? match[1] : null;
}
