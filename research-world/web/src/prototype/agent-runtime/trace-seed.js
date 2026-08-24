export const TRACE_RUNS = [
  { id: "6c9d9d0", name: "规划与验证", node: "6038aad", status: "completed", time: "08/23 07:24", error: "" },
  { id: "91bf2a8", name: "轨道敏感性复算", node: "821cf39", status: "running", time: "08/24 14:08", error: "" },
  { id: "0443196", name: "规划与验证", node: "6038aad", status: "failed", time: "08/23 07:13", error: "Connection closed" },
  { id: "42f4e5d", name: "参数边界复核", node: "f71a03b", status: "paused", time: "08/22 21:40", error: "" },
];

export const TRACE_ROWS = [
  { id: "stage-plan", depth: 0, type: "stage", label: "plan", meta: "research-assistant", status: "completed", start: 0, width: 18, duration: "1m 12s", tokens: "12.4k" },
  { id: "session-plan", parent: "stage-plan", depth: 1, type: "session", label: "planner", meta: "gpt-5.6-sol", status: "completed", start: 1, width: 16, duration: "1m 08s", tokens: "12.4k" },
  { id: "turn-plan", parent: "session-plan", depth: 2, type: "turn", label: "Turn 1", meta: "1 model response", status: "completed", start: 2, width: 14, duration: "1m 03s", tokens: "12.4k" },
  { id: "response-plan", parent: "turn-plan", depth: 3, type: "response", label: "模型响应", meta: "研究方案与执行约束", status: "completed", start: 8, width: 8, duration: "36s", tokens: "4.1k" },
  { id: "stage-execute", depth: 0, type: "stage", label: "execute", meta: "execute-experiment", status: "running", start: 20, width: 62, duration: "进行中", tokens: "18.7k" },
  { id: "step-1", parent: "stage-execute", depth: 1, type: "step", label: "执行 #1", meta: "建立基线积分", status: "completed", start: 21, width: 21, duration: "1m 31s", tokens: "6.2k" },
  { id: "session-a", parent: "step-1", depth: 2, type: "session", label: "experiment-a", meta: "gpt-5.6-sol", status: "completed", start: 22, width: 19, duration: "1m 22s", tokens: "6.2k" },
  { id: "tool-shell", parent: "session-a", depth: 3, type: "tool", label: "execute_experiment", meta: "python3 scripts/integrate.py", status: "completed", start: 27, width: 12, duration: "48s", tokens: "--" },
  { id: "step-2", parent: "stage-execute", depth: 1, type: "step", label: "执行 #2", meta: "扰动扫描", status: "running", start: 34, width: 42, duration: "进行中", tokens: "8.9k" },
  { id: "session-b", parent: "step-2", depth: 2, type: "session", label: "experiment-b", meta: "gpt-5.6-sol", status: "running", start: 35, width: 40, duration: "进行中", tokens: "8.9k" },
  { id: "tool-write", parent: "session-b", depth: 3, type: "tool", label: "write_file", meta: "results/stability-summary.md", status: "completed", start: 43, width: 14, duration: "52s", tokens: "--" },
  { id: "tool-search", parent: "session-b", depth: 3, type: "tool", label: "graph_query", meta: "检索 admitted source", status: "running", start: 60, width: 14, duration: "进行中", tokens: "--" },
  { id: "step-3", parent: "stage-execute", depth: 1, type: "step", label: "执行 #3", meta: "边界复算", status: "queued", start: 80, width: 8, duration: "--", tokens: "--" },
  { id: "stage-review", depth: 0, type: "stage", label: "review", meta: "independent-reviewer", status: "queued", start: 90, width: 8, duration: "--", tokens: "--" },
];

export const TRACE_SUMMARY = [
  { label: "耗时", value: "6m 42s", note: "时间戳派生" },
  { label: "进度", value: "2 / 5", note: "当前 execute" },
  { label: "Session / Tool", value: "3 / 3", note: "1 正在运行" },
  { label: "Token", value: "31.1k", note: "prompt 24.8k · output 6.3k" },
  { label: "Model", value: "gpt-5.6-sol", note: "1 model" },
  { label: "Cost", value: "未记录", note: "待 API" },
];

export const TRACE_RELATIONS = [
  { label: "Node", value: "6038aad", tone: "node" },
  { label: "Lineage", value: "lineage:8f3d", tone: "lineage" },
  { label: "Direction", value: "supported", tone: "success" },
  { label: "Source", value: "3", tone: "source" },
  { label: "Admission", value: "admitted", tone: "success" },
  { label: "Review", value: "待执行", tone: "pending" },
  { label: "Artifact", value: "1", tone: "artifact" },
];

export const TRACE_CONTENT = {
  "tool-write": {
    title: "write_file",
    subtitle: "Tool call · completed · 52s",
    input: { path: "results/stability-summary.md", content_length: 4286, overwrite: false },
    output: "Wrote 4,286 bytes to results/stability-summary.md\nCaptured immutable Artifact reference.",
    markdown: "## 稳定性结论\n\n在基线参数附近，偏心率扰动保持有界；接近共振边界时最大 Lyapunov 指数显著上升。\n\n- 基线窗口：`0.02 <= e <= 0.08`\n- 待 Review：共振带采样密度\n- Admission：`admitted` source 已关联",
    diff: [
      "@@ -0,0 +1,7 @@",
      "+## 稳定性结论",
      "+",
      "+在基线参数附近，偏心率扰动保持有界。",
      "+接近共振边界时最大 Lyapunov 指数显著上升。",
      "+",
      "+Artifact: artifact:9fe2c7e4...8bd1",
    ],
    artifact: { id: "artifact:9fe2c7e4c61a7a5d3f70b1f771d0bdc9b784aa07915d02b5b96cc25e73b18bd1", media_type: "未记录", size: "未记录", admission: "admitted" },
  },
};

export const FALLBACK_CONTENT = {
  title: "模型响应",
  subtitle: "Trace event",
  input: { source: "当前选择", loaded: true },
  output: "当前事件的结构化输出在检查器中显示；未知内容类型回退为纯文本。",
  markdown: "### 当前选择\n\n沿因果树选择 Tool call、模型响应或 Turn 查看对应内容。",
  diff: ["无 normalized diff content block", "待 API"],
  artifact: { id: "未关联", media_type: "--", size: "--", admission: "--" },
};

export const STATUS_LABEL = {
  completed: "已完成", running: "运行中", failed: "失败", paused: "已暂停", queued: "排队中", cancelled: "Turn 已取消",
};
