import { defineConfig } from "@playwright/test";

// T2 验收套件：真实 Compose 产品（生产同一路由 8095），零请求拦截、零模型 mock。
export default defineConfig({
  testDir: "tests/t2",
  timeout: 240000,
  expect: { timeout: 30000 },
  workers: 1,
  retries: 0,
  outputDir: "test-results/t2/artifacts",
  reporter: [
    ["list"],
    ["json", { outputFile: "test-results/t2/report.json" }],
    ["html", { outputFolder: "test-results/t2/html", open: "never" }],
  ],
  use: {
    baseURL: process.env.T2_BASE_URL || "http://127.0.0.1:8095",
    browserName: "chromium",
    viewport: { width: 1440, height: 900 },
    screenshot: "on",
    trace: "on",
  },
});
