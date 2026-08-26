import { defineConfig } from "@playwright/test";

const baseURL = "http://127.0.0.1:18136";

export default defineConfig({
  testDir: "tests",
  use: { baseURL, browserName: "chromium" },
  webServer: { command: "npm run dev -- --port 18136 --strictPort", url: baseURL, reuseExistingServer: false },
});
