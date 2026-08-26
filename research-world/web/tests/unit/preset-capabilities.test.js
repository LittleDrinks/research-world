import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";


const root = fileURLToPath(new URL("../..", import.meta.url));


test("PresetCapabilities renders purpose, status and reason", async (context) => {
  const vite = await createServer({ root, server: { middlewareMode: true }, appType: "custom" });
  context.after(() => vite.close());
  const { PresetCapabilities } = await vite.ssrLoadModule(
    "/src/components/agents/PresetCapabilities.jsx"
  );
  const preset = { tools: [{ id: "project_files", status: "setup_required",
    reason: "not_configured", recommendation: "保存完整正文" }], skills: [] };

  const html = renderToStaticMarkup(React.createElement(PresetCapabilities, { preset }));

  assert.match(html, /project_files/);
  assert.match(html, /保存完整正文/);
  assert.match(html, /（setup_required \/ not_configured）/);
});
