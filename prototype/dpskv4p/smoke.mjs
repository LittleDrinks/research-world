// THROWAWAY PROTOTYPE smoke: node smoke.mjs — opens every page, clicks buttons, types in inputs, watches for page errors.
import pw from "../../research-world/web/node_modules/@playwright/test/index.js";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const { chromium } = pw;
const root = dirname(fileURLToPath(import.meta.url));
const slugs = ["fleet","cartography","ledger","docket","lineage-rail","assembly","wet-lab","orbit","matrix","budget","inbox","dissector","ghost-archive","impact","time-window","palette","repro-card","density","alarm","citation","scifact","matbench","sleep","selection"];
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on("dialog", (d) => d.dismiss().catch(() => {}));
let failed = 0;
for (const slug of slugs) {
  const errors = [];
  const onErr = (e) => errors.push(String(e));
  page.on("pageerror", onErr);
  await page.goto(pathToFileURL(join(root, `v${String(slugs.indexOf(slug) + 1).padStart(2, "0")}-${slug}/index.html`)).href, { waitUntil: "load" });
  await page.waitForTimeout(250);
  const buttons = page.locator("button:not(.dpsk-bar button)");
  const n = Math.min(await buttons.count(), 6);
  for (let i = 0; i < n; i++) {
    try { await buttons.nth(i).click({ timeout: 500 }); await page.waitForTimeout(60); } catch {}
  }
  const inputs = page.locator("input[type=text], input:not([type]), textarea");
  if (await inputs.count()) { try { await inputs.first().fill("test"); } catch {} }
  await page.keyboard.press("Escape");
  await page.waitForTimeout(120);
  const scroll = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth, body: document.body.innerText.length }));
  const status = errors.length ? "ERROR " + errors.join(" | ").slice(0, 220) : `ok body=${scroll.body} overflow=${scroll.sw > scroll.iw ? scroll.sw - scroll.iw : 0}px`;
  if (errors.length) failed++;
  console.log(slug.padEnd(16), status);
  page.off("pageerror", onErr);
}
await browser.close();
process.exit(failed ? 1 : 0);
