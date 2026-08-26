import assert from "node:assert/strict";
import test from "node:test";
import * as reportState from "../src/components/chat/reportState.js";


const { createReportRequests, replaceTrace, replacementsForThread } = reportState;


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


test("keeps a save current across publication activity", () => {
  const requests = createReportRequests();
  const card = "report-card:thread:a";
  const save = requests.next(reportState.reportOperationScope(card, "save"));
  const publish = requests.next(reportState.reportOperationScope(card, "publish"));
  const retry = requests.next(reportState.reportOperationScope(card, "retry"));
  assert.equal(requests.latest(save), true);
  assert.equal(requests.latest(publish), true);
  assert.equal(requests.latest(retry), true);
  const newerSave = requests.next(reportState.reportOperationScope(card, "save"));
  assert.equal(requests.latest(save), false);
  assert.equal(requests.latest(newerSave), true);
});


test("ignores an older response from the same operation", () => {
  const requests = createReportRequests();
  const scope = reportState.reportOperationScope("report-card:thread:a", "retry");
  const older = requests.next(scope);
  const newer = requests.next(scope);
  assert.equal(requests.latest(older), false);
  assert.equal(requests.latest(newer), true);
});
