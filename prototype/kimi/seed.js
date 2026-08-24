// THROWAWAY PROTOTYPE: derived seed for the 10 kimi variants. In-memory only.
import { prototypeTasks, PROTOTYPE_GROUPS } from "../../research-world/web/src/prototype/prototypeSeed";

export { PROTOTYPE_GROUPS };

export const kimiTasks = prototypeTasks();

export const kimiProjects = [
  { id: "prime-distribution", name: "素数分布研究", question: "素数分布中的特殊规律", nodes: 33, running: 5, pending: 6, updated: "12 分钟前", lead: true },
  { id: "orbits-49", name: "轨道共振-49", question: "小行星带共振间隙的长期稳定性", nodes: 18, running: 2, pending: 1, updated: "3 小时前" },
  { id: "turbulence-intermittency", name: "湍流间歇性", question: "高雷诺数下耗散率的间歇标度", nodes: 11, running: 0, pending: 2, updated: "昨天" },
];

const ago = ["09:12", "09:41", "10:03", "10:27", "10:58", "11:14", "11:36", "11:52", "12:08", "12:21", "12:33", "12:47", "13:02", "13:18"];

export const kimiActivity = [
  ["Codex", "完成实验", "E-005 表示数计算", "完成", "输出效应量与置信区间，已写入证据"],
  ["Claude Code", "提交方向", "D-019 素数末位模式", "运行", "等待双审准入"],
  ["Pi", "运行中", "E-001 间隔数据扫描", "运行", "已扫描 6.2M / 10M 素数"],
  ["Qwen Researcher", "请求审查", "R-001 统计显著性审查", "排队", "多重比较阈值待确认"],
  ["Orchestrator", "编排", "D-010 局部密度波动", "运行", "生成 workflow：扫描→基线→复验"],
  ["Codex", "入图", "D-001 素数间隔计数", "已入图", "双审通过"],
  ["Claude Code", "失败重试", "D-014 素数间隔游程", "失败", "保留完整 trace"],
  ["Pi", "锁定", "D-002 短区间素数密度", "已锁定", "配置冻结，禁止再编辑"],
  ["Qwen Researcher", "起草", "D-013 素数四元组", "空闲", "草稿待审"],
  ["Orchestrator", "支持", "D-008 素数倒数和", "已支持", "证据链完整"],
  ["Codex", "排队", "D-007 对数积分偏差", "排队", "等待 ACP runtime"],
  ["Claude Code", "完成审查", "R-003 反例与边界审查", "完成", "未发现反例，边界区间已覆盖"],
  ["Pi", "运行中", "R-002 跨尺度复现审查", "运行", "3 个数量级复现中"],
  ["Orchestrator", "提示", "D-018 素数数字根", "空闲", "待审超过 24h，建议分流"],
].map(([actor, action, target, state, detail], i) => ({ id: `A-${i + 1}`, time: ago[i], actor, action, target, state, detail }));

export const kimiChat = [
  { role: "user", text: "把素数间隔相关性的实验跑起来，超过显著阈值再进双审。" },
  { role: "orchestrator", text: "已读取 D-003 相邻间隔相关性。当前证据不足：仅 1 个区间复现。建议先执行 E-003 孪生模式复验的同款复验流程，再提交 R-001。", nodes: ["D-003", "E-003", "R-001"] },
  { role: "user", text: "同意，顺便把模六剩余类也排进队列。" },
  { role: "orchestrator", text: "已编排 workflow：D-016 模六剩余类 → E-004 剩余类抽样 → R-004 证据链完整性。预计 3 个 runtime，排队中。", nodes: ["D-016", "E-004", "R-004"] },
  { role: "orchestrator", text: "提醒：D-014 素数间隔游程执行失败，trace 已保留。是否重试或标记为边界案例？", nodes: ["D-014"] },
];

export const kimiMetrics = {
  total: kimiTasks.length,
  running: kimiTasks.filter((t) => t.executionState === "运行").length,
  queued: kimiTasks.filter((t) => t.executionState === "排队").length,
  failed: kimiTasks.filter((t) => t.executionState === "失败").length,
  pending: kimiTasks.filter((t) => t.scienceState === "待审查").length,
  verified: kimiTasks.filter((t) => t.scienceState === "待验证").length,
  supported: kimiTasks.filter((t) => t.scienceState === "已支持").length,
  locked: kimiTasks.filter((t) => t.authoringState === "已锁定").length,
};

export function childrenOf(id) {
  return kimiTasks.filter((t) => t.parent === id);
}

export function taskById(id) {
  return kimiTasks.find((t) => t.id === id);
}
