import { expect, test } from "@playwright/test";
import { mockBase } from "./fixtures";


async function openSettings(page, width = 1280) {
  await page.setViewportSize({ width, height: 844 });
  await mockBase(page);
  await page.goto("/settings");
}
test("downloads the current project export from settings", async ({ page }) => {
  await openSettings(page);
  const link = page.getByRole("link", { name: "下载研究包" });
  await expect(link).toHaveAttribute("href", "/api/v1/projects/project%3Atest/export");
  await expect(link).toHaveAttribute("download", "");
});


test("keeps the export download reachable at 390 pixels", async ({ page }) => {
  await openSettings(page, 390);
  const link = page.getByRole("link", { name: "下载研究包" });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "/api/v1/projects/project%3Atest/export");
  await expect(link).toHaveAttribute("download", "");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
