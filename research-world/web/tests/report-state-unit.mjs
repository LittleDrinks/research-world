import assert from "node:assert/strict";
import test from "node:test";
import { replaceTrace, replacementsForThread } from "../src/components/chat/reportState.js";


function memoryStorage() {
  const values = new Map();
  return { getItem: (key) => values.get(key) || null, setItem: (key, value) => values.set(key, value) };
}


globalThis.sessionStorage = memoryStorage();


test("keeps trace replacements scoped to their Thread", () => {
  const a = replaceTrace("thread:a", {}, { turn_id: "turn:1", seq: 2 }, "publication:a");
  sessionStorage.setItem("report-replacements:thread:b", JSON.stringify({ "report-turn:1-2": "publication:b" }));
  const visible = replacementsForThread("thread:b", { threadId: "thread:a", replacements: a });
  assert.deepEqual(a, { "report-turn:1-2": "publication:a" });
  assert.deepEqual(visible, { "report-turn:1-2": "publication:b" });
});
