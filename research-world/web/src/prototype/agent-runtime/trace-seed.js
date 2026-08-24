const longJson = Object.fromEntries(Array.from({ length: 220 }, (_, index) => [
  `event_${String(index + 1).padStart(3, "0")}`,
  { sequence: index + 1, status: "recorded", source: "existing API fixture" },
]));

const largeOutput = Array.from({ length: 280 }, (_, index) =>
  `line ${String(index + 1).padStart(3, "0")} ${"x".repeat(1000)}`).join("\n");

export const SOURCE_LABEL = {
  existing: "existing API · fixture",
  derived: "derived",
  missing: "missing",
};

export const TRACE_RUNS = [
  { id: "fixture:run-completed", name: "规划与验证", node: "node:fixture-completed", status: "completed", time: "08/23 07:24", source: "existing" },
  { id: "fixture:run-running", name: "轨道敏感性复算", node: "node:fixture-running", status: "running", time: "08/24 14:08", source: "existing" },
  { id: "fixture:run-failed", name: "规划与验证", node: "node:fixture-failed", status: "failed", time: "08/23 07:13", source: "existing" },
];

export const TRACE_ROWS = [
  { id: "stage-plan", depth: 0, type: "stage", label: "plan", meta: "research-assistant", status: "completed", start: 0, width: 18, duration: "1m 12s", tokens: "12.4k", source: "existing" },
  { id: "session-plan", parent: "stage-plan", depth: 1, type: "session", label: "planner", meta: "gpt-5.6-sol", status: "completed", start: 1, width: 16, duration: "1m 08s", tokens: "12.4k", source: "existing" },
  { id: "turn-plan", parent: "session-plan", depth: 2, type: "turn", label: "Turn 1", meta: "1 model response", status: "completed", start: 2, width: 14, duration: "1m 03s", tokens: "12.4k", source: "existing" },
  { id: "response-plan", parent: "turn-plan", depth: 3, type: "response", label: "模型响应", meta: "研究方案与执行约束", status: "completed", start: 8, width: 8, duration: "36s", tokens: "4.1k", source: "existing" },
  { id: "stage-execute", depth: 0, type: "stage", label: "execute", meta: "execute-experiment", status: "running", start: 20, width: 62, duration: "进行中", tokens: "18.7k", source: "existing" },
  { id: "step-1", parent: "stage-execute", depth: 1, type: "step", label: "执行 #1", meta: "建立基线积分", status: "completed", start: 21, width: 21, duration: "1m 31s", tokens: "6.2k", source: "existing" },
  { id: "session-a", parent: "step-1", depth: 2, type: "session", label: "experiment-a", meta: "gpt-5.6-sol", status: "completed", start: 22, width: 19, duration: "1m 22s", tokens: "6.2k", source: "existing" },
  { id: "tool-long-json", parent: "session-a", depth: 3, type: "tool", label: "read_trace_fixture", meta: ">200 JSON lines", status: "completed", start: 27, width: 12, duration: "48s", tokens: "--", source: "existing" },
  { id: "step-2", parent: "stage-execute", depth: 1, type: "step", label: "执行 #2", meta: "扰动扫描", status: "running", start: 34, width: 42, duration: "进行中", tokens: "8.9k", source: "existing" },
  { id: "session-b", parent: "step-2", depth: 2, type: "session", label: "experiment-b", meta: "gpt-5.6-sol", status: "running", start: 35, width: 40, duration: "进行中", tokens: "8.9k", source: "existing" },
  { id: "tool-large-output", parent: "session-b", depth: 3, type: "tool", label: "stream_output", meta: ">256 KiB output", status: "completed", start: 43, width: 14, duration: "52s", tokens: "--", source: "existing" },
  { id: "tool-search", parent: "session-b", depth: 3, type: "tool", label: "graph_query", meta: "检索 admitted source", status: "running", start: 60, width: 14, duration: "进行中", tokens: "--", source: "existing" },
  { id: "step-3", parent: "stage-execute", depth: 1, type: "step", label: "执行 #3", meta: "边界复算", status: "queued", start: 80, width: 8, duration: "--", tokens: "--", source: "existing" },
  { id: "stage-review", depth: 0, type: "stage", label: "review", meta: "independent-reviewer", status: "queued", start: 90, width: 8, duration: "--", tokens: "--", source: "existing" },
];

export const TRACE_SUMMARY = [
  { label: "耗时", value: "6m 42s", note: "时间戳计算", source: "derived" },
  { label: "进度", value: "2 / 5", note: "Stage 状态计算", source: "derived" },
  { label: "Session / Tool", value: "3 / 3", note: "事件聚合", source: "derived" },
  { label: "Token", value: "31.1k", note: "usage 去重聚合", source: "derived" },
  { label: "Model", value: "gpt-5.6-sol", note: "Session spec", source: "existing" },
  { label: "Cost", value: "待 API/不可用", note: "pricing revision 缺失", source: "missing" },
];

export const TRACE_RELATIONS = [
  { label: "Node", value: "node:fixture-running", source: "existing", action: "node" },
  { label: "Lineage", value: "lineage:fixture", source: "existing" },
  { label: "Direction", value: "待 API/不可用", source: "missing" },
  { label: "Source", value: "待 API/不可用", source: "missing" },
  { label: "Admission", value: "待 API/不可用", source: "missing" },
  { label: "Review", value: "待 API/不可用", source: "missing" },
  { label: "Artifact", value: "待 API/不可用", source: "missing" },
];

const unavailable = { source: "missing", value: "待 API/不可用" };

export const TRACE_CONTENT = {
  "tool-long-json": {
    title: "read_trace_fixture", subtitle: "Tool call · completed · fixture", source: "existing",
    input: { source: "existing", value: longJson },
    output: { source: "existing", value: "读取 220 条 fixture event。" },
    diff: unavailable, artifact: unavailable,
  },
  "tool-large-output": {
    title: "stream_output", subtitle: "Tool result · completed · fixture", source: "existing",
    input: { source: "existing", value: { fixture: ">256 KiB ASCII output" } },
    output: { source: "existing", value: largeOutput },
    diff: unavailable, artifact: unavailable,
  },
};

export const FALLBACK_CONTENT = {
  title: "Trace event", subtitle: "选择的 existing API fixture", source: "existing",
  input: { source: "existing", value: { event: "当前选择" } },
  output: { source: "existing", value: "当前事件没有额外 fixture 内容。" },
  diff: unavailable, artifact: unavailable,
};

export const STATUS_LABEL = {
  completed: "已完成", running: "运行中", failed: "失败", queued: "排队中", cancelled: "Turn 已取消", paused: "已暂停",
};
