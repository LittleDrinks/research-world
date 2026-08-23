export function nodeTitle(payload) {
  const values = [payload?.title, payload?.text];
  return values.find((value) => typeof value === "string" && value.trim()) || "未命名节点";
}
