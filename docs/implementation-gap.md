# Issue 落地状态
代码基线：`6da47ad`。状态只描述当前代码事实与本轮验收条件。
| Issue | 当前事实 | 处置 |
|---|---|---|
| #12 | review 只给整体 verdict | Admission 拆分原子 claim，逐条保存结论与证据 |
| #13 | 重合候选 ghost 后没有 reflect Session | 相似命中创建独立 reflect Session，只披露相关切片与最小理由 |
| #14 | reflect direction 的 parent 是 experiment | 改为父 direction，同谱系；从 PR #37 只移植该修复 |
| #15 | `orientEvidence` 已删除，极性边按服务端方向渲染 | 已实现，回归测试后关闭 |
| #16 | ActivityPage 已删除，科研日志只投影领域事件 | 已过时，关闭 |
| #17 | Thread 消息统一经 ReactMarkdown 渲染 | 已实现，前端构建后关闭 |
| #18 | 全量 NodeRail 已删除，Thread 只展示显式钉入节点 | 已过时，关闭 |
| #19 | HTTP 仍可直接创建带状态节点并 PATCH Life state | 所有适配器改走 Kernel command，状态迁移只由 Admission 执行 |
| #20 | 节点使用稳定的不透明 id；内容相似性属于 Admission | 原规格已被术语与准入决策替代，关闭 |
| #21 | runner 活路径没有完整执行凭据、Artifact 哈希与复跑校验 | Kernel 保存凭据与不可变 Artifact，结果审核校验输入边界和复跑哈希 |
| #22 | plan 一次落库全部 steps，执行前无行动审核 | 每次只提交一个 Action，审核通过后幂等创建一次执行 |
| #23 | 两次相同 prompt 充当双审 | 机制审核与证据审核使用独立 contract 和 Session |
| #24 | ghost 已进入部分查重，但没有完整最小披露路径 | ghost 只进入 Admission 相似性上下文，执行端只收最小阻断理由 |
| #25 | 凭证与 embedding 已收进 Runtime；端点仍是单实例 | Runtime 识别 endpoint，按 AgentSpec 选择并在同模型端点间故障切换 |
| #26 | 地图 NodeChat 已删除；对话只属于 Project Thread | 已决策并实现，关闭 |
| #27 | 无 Lean4 执行能力 | 作为 Agent 设置可选 MCP Connector 接入，不新增 Kernel 分支 |
| #28 | pre-experiment 不在当前闭环 | 不做，关闭 |
| #29 | 无人工湿实验 observation 提交路径 | 人工 observation 作为 source/experiment Submission 经同一 Admission 入图 |
| #30 | 无引用完整性和交付等级检查 | 报告投影校验 claim-source 引用、来源等级与检查时间 |
| #31 | AgentSpec 已支持模型/Instructions/Skills/Tools/MCP，设置页能力不足 | 设置页编辑识别结果；搜索与外部工具统一用 Connector |
| #32 | 多机 GPU 与通用故障降级不在当前单机边界 | 不做，关闭 |
| #33 | 保留实验环境与当前不可变 Artifact 模型冲突 | 不做，关闭 |
| #34 | source 没有统一外部数据获取凭据 | 数据库、浏览器登录态与采集工具经 Connector 使用，结果登记为 source Artifact |
| #35 | verdict 缺逐项证据，评分与 review 混合 | Admission 保存正反论据、依据引用和分维度 verdict；确定性评分独立 |
| #36 | 无人类可读报告规程 | 新增 report Skill，报告只消费 Kernel 投影与已准入引用 |
