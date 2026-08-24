import { chromium } from "@playwright/test";
import fs from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const URL = pathToFileURL(join(here, "../../prototype/ascii-glass-light/index.html")).href;
const OUT = fs.mkdtempSync(join(tmpdir(), "ascii-glass-shots-"));

const errors = [];
const browser = await chromium.launch();

for (const [name, vp] of [["desktop", { width: 1440, height: 900 }], ["mobile", { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport: vp });
  page.on("pageerror", e => errors.push(`[${name}] ${e.message}`));
  await page.goto(URL, { waitUntil: "load" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${OUT}/${name}-full.png`, fullPage: true });
  const sections = await page.$$("section");
  for (let i = 0; i < sections.length; i++) {
    await sections[i].scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await sections[i].screenshot({ path: `${OUT}/${name}-v${String(i + 1).padStart(2, "0")}.png` });
  }
  const hScroll = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  console.log(`${name}: horizontal-scroll=${hScroll}`);
  await page.close();
}

await browser.close();
console.log(`pageerrors: ${errors.length}`);
errors.forEach(e => console.log("  " + e));
console.log(`shots in ${OUT}`);
