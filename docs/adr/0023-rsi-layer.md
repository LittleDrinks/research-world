---
sources:
  - id: gepa
    title: "GEPA: Reflective Prompt Evolution"
    url: https://arxiv.org/abs/2507.19457
  - id: dgm
    title: "Darwin-Gödel Machine"
    url: https://arxiv.org/abs/2505.22954
  - id: hgm
    title: "Huxley-Gödel Machine"
    url: https://arxiv.org/abs/2510.21614
  - id: reflexion
    title: "Reflexion"
    url: https://arxiv.org/abs/2303.11366
  - id: intrinsic-self-correction
    title: "Large Language Models Cannot Self-Correct Reasoning Yet"
    url: https://arxiv.org/abs/2310.01798
  - id: ssr
    title: "Self-Play SWE-RL"
    url: https://arxiv.org/abs/2512.18552
  - id: absolute-zero
    title: "Absolute Zero"
    url: https://arxiv.org/abs/2505.03335
---
# RSI 上层化：变异文本资产，冻结 benchmark 准入
RSI 是 harness 之上的独立层，只变异 Agent State 文本资产（提示词、skill、装配策略），不动模型权重（资源约束）。变异用 GEPA 式反思 [gepa]；每个候选过冻结 benchmark 确定性打分闸，严格更优才接受，否则回滚；全部版本入 archive 保留祖先——去 archive 性能腰斩 [dgm]，且即时分数与长期改进弱相关，选变异对象看历史后代收益而非最近得分 [hgm]。
失败触发（双审驳回、打分下降、命中金标模式）加每 N 任务兜底体检：无外部反馈的自纠常净亏 [intrinsic-self-correction]，失败触发是唯一有实践共识的方案 [reflexion]。变异循环 token 占任务 token 的移动占比封顶 10–15%，超限冻结变异——"绝大多数时候不变异"是不变量，不是口号。
executor 与 reviewer 错开变异（一方变异时另一方冻结）。reviewer 的红队集为金标错误语料（AgentRx 73 条、TELBench 错误段），永不进反思上下文。红皇后的防护不是双方停止变强，而是把"强"锚在博弈外的固定标尺：确定性测试与执行器 [ssr; absolute-zero]。
## Considered Options
- 权重微调：4×A5000 与学生券预算不支持——拒绝。
- reviewer 用 executor 失败语料改进：过拟合当前 executor 的错误分布（Goodhart）——拒绝，只用金标语料与人工裁决。
- 周期连续变异：无证据支持且违反预算不变量——拒绝。
