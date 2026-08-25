import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests",
  use: { baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:18136", browserName: "chromium" },
});
