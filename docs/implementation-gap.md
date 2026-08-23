# Issue 落地状态
代码基线：`596560e`；未提交工作树不计入完成。状态只描述已提交事实与剩余验收条件。
| Issue | 状态 | 处置 |
|---|---|---|
| #12 | 已实现，待整体验收 | `1838174` 已保存原子 claim、逐条结论与证据；回归通过后关闭 |
| #13 | 已实现，待整体验收 | `1838174` 已用独立 reflect Session 处理重合候选并限制披露；回归通过后关闭 |
| #14 | 已实现，待整体验收 | `1838174` 已把 reflect direction 绑定父 direction 与同谱系；关闭 PR #37，不合并 |
| #15 | 已关闭 | 极性边按 Kernel 投影方向渲染，`orientEvidence` 已删除 |
| #16 | 已关闭，过时 | ActivityPage 已删除，科研日志只投影 Research event |
| #17 | 已关闭 | Thread 消息统一经 ReactMarkdown 渲染 |
| #18 | 已关闭，过时 | 全量 NodeRail 已删除，Thread 只展示显式钉入节点 |
| #19 | 部分实现 | 删除 Life state 旁路；补齐默认 pending、Kernel `resolve_admission` 与不可伪造 Verdict 的接口验收 |
| #20 | 已关闭，设计替代 | 节点使用稳定不透明 id，内容相似性属于 Admission |
| #21 | 已实现，待整体验收 | `0286131`、`53f1089` 已保存完整执行凭据、不可变 Artifact 与复跑哈希 |
| #22 | 已实现，待整体验收 | `1838174` 已按单个 Action 审核并幂等创建执行 |
| #23 | 设计替代，待关闭 | 机制审核与证据审核使用独立 contract 和 Session，不实现原规格的重复 prompt 双审 |
| #24 | 已实现，待整体验收 | ghost 只进入 Admission 相似性上下文，执行端只收最小阻断理由 |
| #25 | 已实现，待 E2E | Runtime 识别 Endpoint，AgentSpec 选择模型并在同模型 Endpoint 间故障切换；compose 验收后关闭 |
| #26 | 已关闭 | 对话只属于 Project Thread，地图 NodeChat 已删除 |
| #27 | 设计替代，待 E2E | Lean4 作为 Agent 设置的可选 Connector 接入，与外部数据库和工具共用 Runtime seam，不新增 Kernel 分支 |
| #28 | 已关闭，不做 | pre-experiment 不在当前闭环 |
| #29 | 部分实现 | 人工 observation 登记 Artifact 后显式 Submission，经默认 pending 与 `resolve_admission` 入图 |
| #30 | 部分实现 | 补齐 Runtime 推导 Endpoint 可用性、admitted source 关联 Artifact 的 BibTeX 导出与语法校验 |
| #31 | 设计替代，待 E2E | Agent 设置只编辑 Runtime 识别的 Endpoint、Skill、Tool、Connector；Lean4、数据库与外部工具统一注册 |
| #32 | 已关闭，不做 | 多机 GPU 与通用故障降级不在当前单机边界 |
| #33 | 已关闭，不做 | 保留可变实验环境与不可变 Artifact 冲突 |
| #34 | 部分实现 | Connector 结果先登记 Project Artifact，再显式提交 observation；公共投影不得泄漏 location/config |
| #35 | 部分实现 | 已保存逐项审核证据；删除 brainstorm 模型自报 quality，候选选择只用 Kernel 确定性特征 |
| #36 | 部分实现 | report Skill 只调用报告投影、BibTeX 导出与交付校验，且只消费 admitted 引用 |
