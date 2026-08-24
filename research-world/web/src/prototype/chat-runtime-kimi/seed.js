// THROWAWAY PROTOTYPE seed: Project > Thread > Message + ResearchRun 引用;Node 只是可钉上下文,不拥有对话。
export const PROJECT = { id: "P-01", name: "素数分布研究" };

export const KIND = { question: "问题", source: "来源", direction: "方向", experiment: "实验" };

export const NODES = [
  { id: "Q-001", kind: "question", title: "短区间素数密度是否服从修正泊松分布", state: "已入图" },
  { id: "S-014", kind: "source", title: "Montgomery–Soundararajan 短区间矩估计", state: "已入图" },
  { id: "D-008", kind: "direction", title: "用 Cramér 模型残差修正短区间计数", state: "已入图" },
  { id: "D-011", kind: "direction", title: "从 Hardy–Littlewood 奇异级数估计方差", state: "待处理" },
  { id: "E-021", kind: "experiment", title: "x ≤ 10⁹ 短区间计数复现实验", state: "已入图" },
];

export const NODE_MAP = Object.fromEntries(NODES.map((node) => [node.id, node]));

const TRACE_MAIN = [
  { time: "14:02:11", actor: "system", text: "挂载 E-021 产物快照 artifacts/e021-counts.parquet" },
  { time: "14:02:14", actor: "assistant", text: "读取计数脚本,确认区间划分参数 h = x^0.525" },
  { time: "14:03:02", actor: "tool", text: "run: python recount.py --limit 1e8 → exit 0,412 行输出" },
  { time: "14:04:37", actor: "tool", text: "run: python recount.py --limit 1e9 → 已运行 92s" },
  { time: "14:05:10", actor: "assistant", text: "初步比对:10⁸ 以下偏差 < 2%,10⁸–10⁹ 方差偏高约 12%" },
];

const TRACE_REVIEW = [
  { time: "14:02:40", actor: "system", text: "独立上下文启动,不读取主执行工作区" },
  { time: "14:03:31", actor: "assistant", text: "核对 p 值口径:双侧检验,与脚本注释一致" },
  { time: "14:04:55", actor: "tool", text: "run: Rscript check_significance.R → exit 0" },
  { time: "14:05:42", actor: "assistant", text: "未发现反例;统计口径与 E-021 脚本一致" },
];

const TRACE_LIT = [
  { time: "11:20:05", actor: "system", text: "检索范围:S-014 及其引用的 3 篇矩估计文献" },
  { time: "11:24:18", actor: "tool", text: "search: singular series short interval variance → 3 篇命中" },
  { time: "11:29:52", actor: "assistant", text: "S-014 的矩估计框架与 D-011 假设兼容;缺 x > 10⁹ 数值证据" },
];

const SESSION_MAIN = {
  runtime: "Codex · ACP", model: "gpt-5.6-codex", started: "14:02:08", workspace: "runs/RR-07/EX-01",
  turns: [
    { id: 1, label: "挂载上下文与复现脚本", steps: [
      { type: "message", actor: "user", time: "14:02:11", text: "读取 @E-021 的脚本与产物,分区重算并与 @D-008 的预测逐项比对。" },
      { type: "message", actor: "assistant", time: "14:02:14", text: "读取计数脚本,确认区间划分参数 h = x^0.525,产物快照锁定为只读。" },
      { type: "tool_call", tool: "fs.mount", time: "14:02:15", input: '{ "artifact": "artifacts/e021-counts.parquet", "mode": "ro" }' },
      { type: "tool_result", tool: "fs.mount", time: "14:02:16", status: "ok", output: "mounted 412MB · schema: x, h, count, ts" },
    ] },
    { id: 2, label: "分区重算", steps: [
      { type: "tool_call", tool: "shell", time: "14:03:02", input: "python recount.py --limit 1e8" },
      { type: "tool_result", tool: "shell", time: "14:03:58", status: "exit 0", output: "412 行输出 · 10⁸ 以下偏差 < 2%" },
      { type: "tool_call", tool: "shell", time: "14:04:37", input: "python recount.py --limit 1e9" },
      { type: "tool_result", tool: "shell", time: "14:06:09", status: "running", output: "已运行 92s · 进度 63%" },
    ] },
    { id: 3, label: "初步比对", steps: [
      { type: "message", actor: "assistant", time: "14:05:10", text: "初步比对:10⁸ 以下偏差 < 2%,10⁸–10⁹ 方差偏高约 12%。等待 10⁹ 全量结果后写回事实。" },
    ] },
  ],
};

const SESSION_REVIEW = {
  runtime: "Claude Code · CLI", model: "claude-sonnet-4.6", started: "14:02:40", workspace: "runs/RR-07/EX-02",
  turns: [
    { id: 1, label: "隔离启动与口径核对", steps: [
      { type: "message", actor: "user", time: "14:02:40", text: "独立检查 @E-021 的显著性口径,不读取主执行的中间结论。" },
      { type: "message", actor: "assistant", time: "14:03:31", text: "核对 p 值口径:双侧检验,与脚本注释一致。" },
      { type: "tool_call", tool: "shell", time: "14:04:55", input: "Rscript check_significance.R" },
      { type: "tool_result", tool: "shell", time: "14:05:36", status: "exit 0", output: "p = 0.031 · 双侧 · n = 412" },
    ] },
    { id: 2, label: "结论", steps: [
      { type: "message", actor: "assistant", time: "14:05:42", text: "未发现反例;统计口径与 E-021 脚本一致。结论已交还 ResearchRun。" },
    ] },
  ],
};

const SESSION_LIT = {
  runtime: "Qwen Researcher · ACP", model: "qwen3-max", started: "11:20:05", workspace: "runs/RR-06/EX-03",
  turns: [
    { id: 1, label: "文献检索与比对", steps: [
      { type: "message", actor: "user", time: "11:20:05", text: "核对 @S-014 能否直接支撑 @D-011,并列出证据缺口。" },
      { type: "tool_call", tool: "arxiv.search", time: "11:24:18", input: '{ "q": "singular series short interval variance", "limit": 3 }' },
      { type: "tool_result", tool: "arxiv.search", time: "11:26:40", status: "ok", output: "3 篇命中 · Montgomery–Soundararajan 2004 在列" },
      { type: "message", actor: "assistant", time: "11:29:52", text: "S-014 的矩估计框架与 D-011 假设兼容;缺 x > 10⁹ 数值证据。" },
    ] },
  ],
};

export const SEED_RUNS = {
  "RR-07": {
    id: "RR-07", intent: "复核 D-008 残差修正的可复现性", status: "运行中", started: "14:02",
    findings: ["10⁸ 以下区间计数与 E-021 脚本一致", "10⁸–10⁹ 区间方差超出 Cramér 预测约 12%"],
    executions: [
      { id: "EX-01", agent: "Codex", channel: "ACP", model: "gpt-5.6-codex", status: "运行中", task: "重跑 E-021 计数脚本并比对", summary: "已挂载产物快照,正在跑 10⁹ 区间…", prompt: "读取 @E-021 的脚本与产物，分区重算并与 @D-008 的预测逐项比对。", skills: ["实验复现", "数据审计"], trace: TRACE_MAIN, session: SESSION_MAIN },
      { id: "EX-02", agent: "Claude Code", channel: "CLI", model: "claude-sonnet-4.6", status: "已完成", task: "独立复核统计口径", summary: "p 值口径与脚本一致,未发现反例。", prompt: "独立检查 @E-021 的显著性口径，不读取主执行的中间结论。", skills: ["统计复核"], trace: TRACE_REVIEW, session: SESSION_REVIEW },
    ],
  },
  "RR-06": {
    id: "RR-06", intent: "评估 D-011 的文献支撑强度", status: "已完成", started: "11:20",
    findings: ["S-014 矩估计框架与 D-011 假设兼容", "缺少 x > 10⁹ 的数值证据"],
    executions: [
      { id: "EX-03", agent: "Qwen Researcher", channel: "ACP", model: "qwen3-max", status: "已完成", task: "检索并比对 3 篇矩估计文献", summary: "S-014 与 D-011 假设兼容。", prompt: "核对 @S-014 能否直接支撑 @D-011，并列出证据缺口。", skills: ["文献检索", "证据审查"], trace: TRACE_LIT, session: SESSION_LIT },
    ],
  },
};

export const SEED_THREADS = [
  { id: "T-01", title: "D-008 残差修正方案", pinned: ["D-008", "E-021"], updated: "14:05", messages: [
    { id: "m1", role: "user", time: "13:58", text: "E-021 的方差偏大,先确认是脚本问题还是模型本身的偏差。" },
    { id: "m2", role: "assistant", time: "14:02", text: "我启动了 RR-07 复核:一个执行重跑计数脚本,另一个独立核对统计口径,两条线互不染上下文。", runs: ["RR-07"] },
    { id: "m3", role: "user", time: "14:04", text: "复核期间先别动 D-008 的状态。" },
    { id: "m4", role: "assistant", time: "14:05", text: "收到。D-008 维持「已入图」,复核结论只作为研究事实写回,由你决定是否改状态。" },
  ] },
  { id: "T-02", title: "Q-001 问题界定", pinned: ["Q-001"], updated: "10:12", messages: [
    { id: "m5", role: "user", time: "10:02", text: "Q-001 的「短区间」要先给出可操作定义,否则后续实验没法对齐。" },
    { id: "m6", role: "assistant", time: "10:12", text: "建议定为 h = x^θ,θ ∈ [0.5, 0.55],与 S-014 的矩估计区间对齐。可先钉住 S-014 再展开。" },
  ] },
  { id: "T-03", title: "S-014 矩估计笔记", pinned: ["S-014"], updated: "11:31", messages: [
    { id: "m7", role: "user", time: "11:18", text: "S-014 能不能直接支撑 D-011?帮我查一下文献口径。" },
    { id: "m8", role: "assistant", time: "11:20", text: "已启动 RR-06 做文献比对,单个执行足够,结论写回科研日志。", runs: ["RR-06"] },
  ] },
];

// 项目级研究活动:只有 Research Kernel 事实,没有 runtime raw trace。
export const ACTIVITY = [
  { id: "a1", time: "14:06", kind: "事实", text: "RR-07 复核确认:E-021 在 10⁸ 以下区间可复现", ref: "RR-07" },
  { id: "a2", time: "14:02", kind: "运行", text: "RR-07 启动:复核 D-008 可复现性(2 个执行)", ref: "RR-07" },
  { id: "a3", time: "13:40", kind: "节点", text: "方向 D-011 由「待处理」进入图谱", ref: "D-011" },
  { id: "a4", time: "11:31", kind: "事实", text: "RR-06 结论:S-014 矩估计与 D-011 假设兼容", ref: "RR-06" },
  { id: "a5", time: "11:20", kind: "运行", text: "RR-06 完成:评估 D-011 文献支撑(1 个执行)", ref: "RR-06" },
  { id: "a6", time: "09:52", kind: "节点", text: "实验 E-021 产物快照 v3 写回节点", ref: "E-021" },
];

export function threadRuns(thread) {
  return [...new Set(thread.messages.flatMap((message) => message.runs || []))];
}

export function findExecution(runs, executionId) {
  for (const run of Object.values(runs)) {
    const execution = run.executions.find((item) => item.id === executionId);
    if (execution) return { run, execution };
  }
  return null;
}

export function makeRun(id, intent) {
  return { id, intent: `核查:${intent.slice(0, 24)}`, status: "运行中", started: "现在",
    findings: ["等待 execution 写回研究事实"],
    executions: [
      { id: `${id}-E1`, agent: "Codex", channel: "ACP", model: "gpt-5.6-codex", status: "运行中", task: "主执行:读取节点上下文并产出证据", summary: "已接收意图,正在准备可复现环境…", prompt: intent, skills: ["实验复现", "证据审查"], trace: [{ time: "现在", actor: "system", text: "runtime 启动,节点上下文快照已隔离" }], session: makeSession(id, "E1", intent, "Codex · ACP", "gpt-5.6-codex") },
      { id: `${id}-E2`, agent: "Pi", channel: "ACP", model: "gpt-5.2", status: "排队中", task: "独立复核:寻找反例与边界条件", summary: "等待主执行产出后启动。", prompt: `独立复核：${intent}`, skills: ["反例搜索"], trace: [{ time: "现在", actor: "system", text: "已入队,与主执行上下文隔离" }], session: makeSession(id, "E2", `独立复核:${intent}`, "Pi · ACP", "gpt-5.2") },
    ] };
}

function makeSession(runId, slot, intent, runtime, model) {
  return { runtime, model, started: "现在", workspace: `runs/${runId}/${runId}-${slot}`,
    turns: [{ id: 1, label: "接收意图", steps: [
      { type: "message", actor: "user", time: "现在", text: intent },
      { type: "message", actor: "assistant", time: "现在", text: "runtime 启动,钉住上下文快照已隔离,正在准备可复现环境。" },
    ] }] };
}

// 事实图谱(仅已验证事实与依赖;失败尝试与 agent 过程不入图)。
export const GRAPH_NODES = [
  { id: "Q-001", kind: "question", life_state: "admitted", parent_id: null, payload: { title: "短区间素数密度是否服从修正泊松分布", 状态: "核心问题", 证据: "2 条" } },
  { id: "S-014", kind: "source", life_state: "admitted", parent_id: "Q-001", payload: { title: "Montgomery–Soundararajan 短区间矩估计", 年份: "2004", 被引: "312" } },
  { id: "D-008", kind: "direction", life_state: "admitted", direction_status: "supported", parent_id: "Q-001", payload: { title: "用 Cramér 模型残差修正短区间计数", 假设: "残差平稳", 支持: "S-014 · E-021" } },
  { id: "D-011", kind: "direction", life_state: "pending", direction_status: "proposed", parent_id: "Q-001", payload: { title: "从 Hardy–Littlewood 奇异级数估计方差", 缺口: "x > 10⁹ 数值证据" } },
  { id: "D-013", kind: "direction", life_state: "ghost", direction_status: "refuted", parent_id: "Q-001", payload: { title: "直接套用高斯截断近似", 驳回理由: "与 S-014 三阶矩矛盾" } },
  { id: "E-021", kind: "experiment", life_state: "admitted", parent_id: "D-008", payload: { title: "x ≤ 10⁹ 短区间计数复现实验", 产物: "e021-counts.parquet", 快照: "v3" } },
  { id: "E-022", kind: "experiment", life_state: "pending", parent_id: "D-011", payload: { title: "奇异级数数值积分验证", 状态: "待启动" } },
];

export const GRAPH_EDGES = [
  { source: "S-014", target: "D-008", polarity: "supports" },
  { source: "E-021", target: "D-008", polarity: "supports" },
  { source: "S-014", target: "D-011", polarity: "supports" },
  { source: "S-014", target: "D-013", polarity: "refutes" },
  { source: "E-021", target: "D-013", polarity: "refutes" },
];

export const GRAPH_NODE_MAP = Object.fromEntries(GRAPH_NODES.map((node) => [node.id, node]));

let cachedGraphEdges;
export function graphEdgesAll() {
  if (cachedGraphEdges) return cachedGraphEdges;
  const evidencePairs = new Set(GRAPH_EDGES.map((edge) => [edge.source, edge.target].sort().join(":")));
  const lineage = GRAPH_NODES.filter((node) => node.parent_id)
    .filter((node) => !evidencePairs.has([node.parent_id, node.id].sort().join(":")))
    .map((node) => ({ source: node.parent_id, target: node.id, polarity: "lineage" }));
  cachedGraphEdges = [...lineage, ...GRAPH_EDGES];
  return cachedGraphEdges;
}

export const PROJECTS = [
  { id: "P-01", name: "素数分布研究", question: "短区间素数密度是否服从修正泊松分布", nodes: 7, runs: 2, updated: "今天 14:06" },
  { id: "P-02", name: "神经算子外推", question: "PI-DeepONet 长时程外推的误差界", nodes: 21, runs: 9, updated: "昨天 18:44" },
  { id: "P-03", name: "蛋白质折叠采样", question: "受限玻尔兹曼机采样的混合时间上界", nodes: 13, runs: 5, updated: "周一 09:12" },
];

export const SEED_AGENTS = [
  { id: "AG-01", name: "研究助手", runtime: "Codex · ACP", instructions: "围绕钉住的节点上下文推进实验;所有结论必须引用 artifact。", model: "gpt-5.6-codex", thinking: "高", skills: ["agent-creation", "benchmark-design", "codebase-design"], advanced: { permission: "工作区写入", concurrency: "2", env: ["PYTHONPATH=src", "DATA_DIR=/data/e021"], mcp: ["openaiDeveloperDocs", "anysearch"] } },
  { id: "AG-02", name: "独立复核", runtime: "Claude Code · CLI", instructions: "不读取主执行的中间结论,主动寻找反例与边界条件。", model: "claude-sonnet-4.6", thinking: "中", skills: ["code-review", "grilling"], advanced: { permission: "只读", concurrency: "1", env: [], mcp: [] } },
];

export function makeAgent(id, mode) {
  const draft = mode === "draft";
  return { id, name: draft ? "AI 起草 · 实验审查员" : "未命名 Agent", runtime: "Codex · ACP",
    instructions: draft ? "审查实验产物,逐项核对输入范围、随机种子与统计口径,输出证据与失败原因。" : "",
    model: draft ? "claude-sonnet-4.6" : "gpt-5.6-codex", thinking: draft ? "高" : "中",
    skills: draft ? ["code-review", "grilling"] : [],
    advanced: { permission: "只读", concurrency: "1", env: [], mcp: [] } };
}
