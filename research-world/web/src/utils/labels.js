export const KIND_LABELS = { question: "问题", source: "来源", direction: "方向", experiment: "实验" };
export const LIFE_LABELS = { pending: "待审查", admitted: "已入图", ghost: "已驳回" };
export const DIRECTION_LABELS = { proposed: "待验证", supported: "已支持", refuted: "已反驳" };
export const RUN_STATUS = { queued: "排队中", running: "运行中", waiting_human: "等待人工", completed: "已完成", paused: "已暂停", failed: "失败" };
export const REASONING_EFFORTS = ["low", "medium", "high"];


export function nodeText(node) {
  const values = [node?.payload?.title, node?.payload?.text, node?.payload?.summary];
  return values.find((value) => typeof value === "string" && value.trim()) || "未命名节点";
}


export function shortId(value = "") {
  return value.split(":").at(-1)?.slice(0, 7) || value;
}


export function statusTone(status) {
  return { queued: "queued", running: "running", waiting_human: "blocked", completed: "success", paused: "warning", failed: "failed" }[status] || "queued";
}


export function formatTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date(value));
}


export function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}
