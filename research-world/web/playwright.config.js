import { defineConfig } from "@playwright/test";

const baseURL = "http://127.0.0.1:18136";
const apiURL = "http://127.0.0.1:8095";

export default defineConfig({
  testDir: "tests",
  use: { baseURL, browserName: "chromium" },
  webServer: [
    { command: "PYTHONPATH=.. uv run --project .. python tests/localmap_backend.py --port 8095", url: `${apiURL}/api/v1/health`, reuseExistingServer: false },
    { command: "npm run dev -- --port 18136 --strictPort", url: baseURL, reuseExistingServer: false },
  ],
});
