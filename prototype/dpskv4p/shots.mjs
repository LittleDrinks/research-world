// THROWAWAY PROTOTYPE screenshots: node shots.mjs (from prototype/dpskv4p). Uses the repo's existing Playwright install.
import pw from "../../research-world/web/node_modules/@playwright/test/index.js";
const { chromium } = pw;
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const out = join(root, "shots");
mkdirSync(out, { recursive: true });
const pages = [["index", "index.html"], ...Array.from({ length: 24 }, (_, i) => {
  const n = `v${String(i + 1).padStart(2, "0")}`;
  const slug = ["fleet","cartography","ledger","docket","lineage-rail","assembly","wet-lab","orbit","matrix","budget","inbox","dissector","ghost-archive","impact","time-window","palette","repro-card","density","alarm","citation","scifact","matbench","sleep","selection"][i];
  return [n, `${n}-${slug}/index.html`];
})];
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
let failed = 0;
for (const [name, rel] of pages) {
  const errors = [];
  const handler = (e) => errors.push(String(e));
  page.on("pageerror", handler);
  await page.goto(pathToFileURL(join(root, rel)).href, { waitUntil: "load", timeout: 20000 });
  await page.waitForTimeout(900);
  await page.screenshot({ path: join(out, `${name}.png`) });
  if (errors.length) failed++;
  console.log(name, errors.length ? `PAGEERROR ${errors.join(" | ").slice(0, 300)}` : "ok");
  page.off("pageerror", handler);
}
await browser.close();
process.exit(failed ? 1 : 0);
