import assert from "node:assert/strict";
import { treeKeyAction, truncateUtf8, writeClipboard } from "../src/prototype/agent-runtime/trace-content.js";

function utf8Cases() {
  assert.deepEqual(truncateUtf8("中文", 4), { visible: "中", visibleBytes: 3, totalBytes: 6, remainingBytes: 3 });
  assert.deepEqual(truncateUtf8("A😀B", 4), { visible: "A", visibleBytes: 1, totalBytes: 6, remainingBytes: 5 });
  assert.deepEqual(truncateUtf8("你😀好", 7), { visible: "你😀", visibleBytes: 7, totalBytes: 10, remainingBytes: 3 });
}

async function clipboardCases() {
  assert.equal(await writeClipboard(undefined, "id"), "unavailable");
  assert.equal(await writeClipboard({}, "id"), "unavailable");
  assert.equal(await writeClipboard({ writeText() { throw new Error("blocked"); } }, "id"), "failed");
  assert.equal(await writeClipboard({ writeText() { return Promise.reject(new Error("denied")); } }, "id"), "failed");
  assert.equal(await writeClipboard({ writeText() { return Promise.resolve(); } }, "id"), "success");
}

function treeCases() {
  assert.deepEqual(treeKeyAction("ArrowRight", { expandable: true, open: false }), { type: "expand" });
  assert.deepEqual(treeKeyAction("ArrowRight", { expandable: true, open: true, firstChild: "child" }), { type: "focus", id: "child" });
  assert.deepEqual(treeKeyAction("ArrowLeft", { expandable: true, open: true }), { type: "collapse" });
  assert.deepEqual(treeKeyAction("ArrowLeft", { expandable: true, open: false, parent: "parent" }), { type: "focus", id: "parent" });
  assert.equal(treeKeyAction("ArrowRight", { expandable: false, parent: "parent" }), null);
}

utf8Cases();
await clipboardCases();
treeCases();
console.log("issue64 prototype unit tests passed");
