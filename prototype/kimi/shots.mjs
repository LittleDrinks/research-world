// THROWAWAY PROTOTYPE: screenshot all 10 variants. Run: cd research-world/web && node ../../prototype/kimi/shots.mjs
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const out = join(dirname(fileURLToPath(import.meta.url)), "shots");
mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
for (let v = 1; v <= 10; v++) {
  const id = String(v).padStart(2, "0");
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(`http://localhost:5173/prototype/kimi?v=${id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1400);
  await page.screenshot({ path: join(out, `v${id}.png`) });
  console.log(`v${id}`, errors.length ? `PAGEERROR: ${errors[0]}` : "ok");
}
await browser.close();
