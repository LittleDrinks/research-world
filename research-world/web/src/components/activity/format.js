const ROLE_LABELS = { system: "系统", user: "用户", assistant: "助手", tool: "工具", runtime: "运行时" };

export function roleLabel(role) {
  return ROLE_LABELS[role] || role || "记录";
}

export function fmtTokens(value) {
  const count = Number(value) || 0;
  if (count >= 10000) return `${(count / 10000).toFixed(1)} 万`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
  return String(count);
}

export function fmtMs(ms) {
  if (ms >= 60000) return `${Math.floor(ms / 60000)} 分 ${Math.round((ms % 60000) / 1000)} 秒`;
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)} 秒`;
  return `${Math.round(ms)} 毫秒`;
}

export function fmtDuration(start, end) {
  if (!start) return "-";
  if (!end) return "进行中";
  return fmtMs(Math.max(0, new Date(end) - new Date(start)));
}

export function oneLine(value, max = 200) {
  const line = String(value || "").replace(/\s+/g, " ").trim();
  return line.length > max ? `${line.slice(0, max)}…` : line;
}

export function argSummary(args, max = 100) {
  if (args === null || args === undefined || args === "") return "";
  return oneLine(typeof args === "string" ? args : JSON.stringify(args), max);
}

export function messageText(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return content ? JSON.stringify(content) : "";
  return content.map((part) => part.type === "text" ? part.text : `[${part.type === "image_url" ? "图片" : part.type || "内容"}]`).join("\n");
}
