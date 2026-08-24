import assert from "node:assert/strict";
import test from "node:test";

import { blockedCapabilities, newAgentPayload } from "../../src/utils/agents.js";


const catalog = {
  endpoints: [{ id: "runtime", available: true }],
  models: [{ id: "model", endpoint: "runtime" }],
  skills: [{ id: "source-research" }],
  tools: [{ id: "crossref", status: "ready" },
    { id: "project_files", status: "setup_required", reason: "not_configured" }],
};


test("preset creates an independent editable AgentSpec snapshot", () => {
  const preset = { id: "source-researcher", name: "文献研究员", instructions: "Verify sources." };
  const capabilities = { skills: ["source-research"], tools: ["crossref"] };

  const first = newAgentPayload(preset, catalog, capabilities);
  first.skills.push("edited");
  first.instructions = "Edited";

  assert.deepEqual(capabilities.skills, ["source-research"]);
  assert.equal(preset.instructions, "Verify sources.");
});


test("selected non-ready tools and missing skills block the draft", () => {
  const spec = { tools: ["crossref", "project_files"], skills: ["source-research", "missing"] };
  const blocked = blockedCapabilities(spec, null, catalog);

  assert.deepEqual(blocked.tools.map((item) => item.id), ["project_files"]);
  assert.equal(blocked.tools[0].reason, "not_configured");
  assert.deepEqual(blocked.skills, [{ id: "missing", status: "missing" }]);
});
