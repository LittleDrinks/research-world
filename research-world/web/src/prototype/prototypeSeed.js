// THROWAWAY PROTOTYPE DATA: dense enough to expose navigation and canvas behavior.
const rows = [
  row("Q-001", "question", "素数分布中的特殊规律", "寻找素数分布中可计算、可复现且可证伪的特殊规律。", null, "已入图", "已配置", "运行", "Codex", "ACP", "研究问题"),
  row("D-001", "direction", "素数间隔计数", "统计不同区间长度内素数间隔的频数与偏差。", "Q-001", "已入图", "已配置", "完成", "Codex", "ACP", "基础计数"),
  row("D-002", "direction", "短区间素数密度", "比较短区间内实际素数数与对数积分预测。", "Q-001", "已入图", "已锁定", "运行", "Pi", "CLI", "基础计数"),
  row("D-003", "direction", "相邻间隔相关性", "检验连续素数间隔是否存在可计算相关性。", "Q-001", "已入图", "已配置", "完成", "Claude Code", "ACP", "基础计数"),
  row("D-004", "direction", "最大间隔增长", "拟合给定范围内最大素数间隔的增长趋势。", "Q-001", "待审", "草稿", "空闲", "Qwen Researcher", "CLI", "基础计数"),
  row("D-005", "direction", "间隔模分布", "分析素数间隔对小模数的取值分布。", "Q-001", "已支持", "已配置", "完成", "Codex", "CLI", "基础计数"),
  row("D-006", "direction", "素数计数误差", "计算素数计数函数与近似公式之间的误差。", "Q-001", "已入图", "已锁定", "完成", "Pi", "ACP", "解析与估计"),
  row("D-007", "direction", "对数积分偏差", "比较 π(x) 与 li(x) 在不同尺度的偏差方向。", "Q-001", "已入图", "已配置", "排队", "Claude Code", "CLI", "解析与估计"),
  row("D-008", "direction", "素数倒数和", "观察素数倒数和的增长与理论渐近项差异。", "Q-001", "已支持", "已锁定", "完成", "Qwen Researcher", "ACP", "解析与估计"),
  row("D-009", "direction", "素数幂次贡献", "分离素数幂对切比雪夫函数的不同贡献。", "Q-001", "待审", "草稿", "空闲", "Codex", "ACP", "解析与估计"),
  row("D-010", "direction", "局部密度波动", "检测局部素数密度的周期性或异常波动。", "Q-001", "已入图", "已配置", "运行", "Pi", "CLI", "解析与估计"),
  row("D-011", "direction", "孪生素数频率", "统计孪生素数对在尺度变化下的出现频率。", "Q-001", "已入图", "已锁定", "完成", "Claude Code", "ACP", "计算实验"),
  row("D-012", "direction", "素数三元组", "比较不同素数三元组模式的相对频率。", "Q-001", "已支持", "已配置", "完成", "Codex", "CLI", "计算实验"),
  row("D-013", "direction", "素数四元组", "搜索高阶素数间隔模式并估计其稀疏程度。", "Q-001", "待审", "草稿", "空闲", "Qwen Researcher", "ACP", "计算实验"),
  row("D-014", "direction", "素数间隔游程", "研究相同间隔连续出现形成的游程长度。", "Q-001", "已入图", "已配置", "失败", "Pi", "CLI", "计算实验"),
  row("D-015", "direction", "可加结构搜索", "寻找素数间隔序列中的简单可加结构。", "Q-001", "已支持", "已锁定", "完成", "Claude Code", "ACP", "计算实验"),
  row("D-016", "direction", "模六剩余类", "比较素数在模六两个剩余类中的分布差异。", "Q-001", "已入图", "已配置", "完成", "Codex", "ACP", "结构规律"),
  row("D-017", "direction", "小模数剩余类", "扩展到模三十并比较允许剩余类的频率。", "Q-001", "已支持", "已锁定", "排队", "Qwen Researcher", "CLI", "结构规律"),
  row("D-018", "direction", "素数数字根", "检验素数数字根序列是否偏离随机基线。", "Q-001", "待审", "草稿", "空闲", "Pi", "ACP", "结构规律"),
  row("D-019", "direction", "素数末位模式", "分析十进制素数末位组合及其转移频率。", "Q-001", "已入图", "已配置", "运行", "Claude Code", "CLI", "结构规律"),
  row("D-020", "direction", "素数和的表示", "统计素数作为两个素数之和的表示数量。", "Q-001", "已支持", "已锁定", "完成", "Codex", "ACP", "结构规律"),
  row("E-001", "experiment", "间隔数据扫描", "扫描前一千万个素数并生成间隔统计表。", "D-001", "已入图", "已配置", "运行", "Codex", "CLI", "实验节点"),
  row("E-002", "experiment", "密度基线对照", "用随机模型和对数积分分别建立对照基线。", "D-002", "已支持", "已锁定", "完成", "Pi", "ACP", "实验节点"),
  row("E-003", "experiment", "孪生模式复验", "在独立区间重复孪生素数频率测试。", "D-011", "已入图", "已配置", "排队", "Claude Code", "CLI", "实验节点"),
  row("E-004", "experiment", "剩余类抽样", "对模六与模三十剩余类执行分层抽样。", "D-016", "待审", "草稿", "空闲", "Qwen Researcher", "ACP", "实验节点"),
  row("E-005", "experiment", "表示数计算", "计算素数和表示数并检验尺度稳定性。", "D-020", "已支持", "已锁定", "完成", "Codex", "CLI", "实验节点"),
  row("R-001", "review", "统计显著性审查", "检查候选规律是否超过多重比较后的显著阈值。", "D-005", "待审", "已配置", "排队", "Pi", "ACP", "审查节点"),
  row("R-002", "review", "跨尺度复现审查", "验证候选规律能否在多个数量级稳定复现。", "D-010", "已入图", "已锁定", "运行", "Claude Code", "CLI", "审查节点"),
  row("R-003", "review", "反例与边界审查", "主动搜索反例、边界区间和算法误差来源。", "D-015", "已支持", "已配置", "完成", "Qwen Researcher", "ACP", "审查节点"),
  row("R-004", "review", "证据链完整性", "检查数据、代码、参数和结论之间的可追溯性。", "D-020", "待审", "草稿", "空闲", "Codex", "CLI", "审查节点"),
];


function row(id, type, title, prompt, parent, scienceState, authoringState, executionState, agent, channel, group) {
  return { id, type, title, prompt, parent, scienceState, authoringState, executionState, agent, channel, group };
}


export function prototypeTasks() {
  const directions = rows.filter((item) => item.type === "direction");
  return rows.map((item) => enrich(item, directions));
}


function enrich(item, directions) {
  const position = nodePosition(item, directions);
  return { ...item, scienceState: scienceLabel(item), kind: kindLabel(item.type), position, goal: "形成可引用、可复现且可被反驳的研究结论。",
    model: item.agent === "Pi" ? "gpt-5.2" : "gpt-5.6-codex", provider: item.agent === "Qwen Researcher" ? "DashScope" : "OpenAI compatible",
    workspace: "/workspace/prime-distribution", permission: "按需确认", acceptance: ["记录输入、seed 与环境", "输出效应量与置信区间", "失败时保留完整 trace"],
    tools: ["graph-query", "filesystem", "python-runner"] };
}


function scienceLabel(item) {
  if (item.scienceState === "待审") return "待审查";
  if (item.scienceState !== "已入图") return item.scienceState;
  return item.type === "direction" ? "待验证" : "已采纳";
}


function nodePosition(item, directions) {
  if (item.type === "question") return { x: 20, y: 310 };
  if (item.type === "direction") return { x: 420, y: directions.findIndex((node) => node.id === item.id) * 190 };
  if (item.type === "experiment") return { x: 820, y: parentY(item.parent, directions) };
  return { x: 1220, y: parentY(item.parent, directions) };
}


function parentY(parent, directions) {
  return directions.findIndex((node) => node.id === parent) * 190;
}


function kindLabel(type) {
  return { question: "研究问题", direction: "方向", experiment: "实验", review: "审查" }[type];
}


export const PROTOTYPE_GROUPS = ["研究问题", "基础计数", "解析与估计", "计算实验", "结构规律", "实验节点", "审查节点"];
