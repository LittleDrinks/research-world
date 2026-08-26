import { expect, test } from "@playwright/test";
import { mockBase } from "./fixtures";


async function openSettings(page, width = 1280) {
  await page.setViewportSize({ width, height: 844 });
  await mockBase(page);
  await page.route(/\/api\/v1\/projects\/project%3Atest\/export$/, (route) => route.fulfill({
    body: "project export", headers: { "content-disposition": "attachment; filename=project-export.zip" },
  }));
  await page.goto("/settings");
}


async function expectDownload(page) {
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "下载研究包" }).click();
  expect((await download).suggestedFilename()).toBe("project-export.zip");
}


test("downloads the current project export from settings", async ({ page }) => {
  await openSettings(page);
  const link = page.getByRole("link", { name: "下载研究包" });
  await expect(link).toHaveAttribute("href", "/api/v1/projects/project%3Atest/export");
  await expect(link).toHaveAttribute("download", "");
  await expectDownload(page);
});


test("keeps the export download reachable at 390 pixels", async ({ page }) => {
  await openSettings(page, 390);
  await expect(page.getByRole("link", { name: "下载研究包" })).toBeVisible();
  await expectDownload(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
