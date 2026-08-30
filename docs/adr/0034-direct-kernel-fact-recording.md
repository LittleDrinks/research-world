---
status: accepted
sources:
  - id: issue-169
    title: MVP 规格：主 Agent 协作研究闭环与双深 Module 切换
    url: https://github.com/LittleDrinks/research-world/issues/169
    accessed: 2026-08-31
  - id: issue-146
    title: Research Kernel 深 Module
    url: https://github.com/LittleDrinks/research-world/issues/146
    accessed: 2026-08-29
  - id: issue-147
    title: 架构落地：决策记录与 TDD 证据约定
    url: https://github.com/LittleDrinks/research-world/issues/147
    accessed: 2026-08-29
supersedes:
  - "0017: fixed Pipeline and admission scope"
  - "0020: graph evidence and admission scope"
  - "0021: review Pipeline and write-gate scope"
  - "0026: mixed Runtime/Kernel Session, Trace, Thread and Pipeline ownership"
  - "0027: command/query, admission and Pipeline-driven Kernel writes"
  - "0032: Kernel-owned fixed Pipeline, Stage, Auto and human Gate"
  - "0037: Workflow, Trajectory and old Session as Research Graph write prerequisites"
---
# Direct Kernel Fact Recording
Research Kernel 是 Project 研究状态的唯一深模块，拥有 Project、Session、Artifact、Record、Relation 与 LocalMap；Runtime 不绕过 Kernel Interface 写入这些对象。
## 决策
Kernel Interface 只接受 Project、Session、Artifact、Record、Connect、Remove 与 LocalMap 领域输入。Record 只校验内容完整、Project 归属和 Project-owned Artifact 引用，写入后立即可被地图、LocalMap 和 Agent 使用；不持有准入、pending、admitted、ghost、审核意见、人工裁决或 Pipeline 状态。Connect 只连接同一 Project 的既有 Record 和有效 Relation；Remove Record 时同时移除其直接 Relation，但不删除关联 Artifact；Remove Relation 不影响两端 Record。
Session 先持久化用户消息，再由对话协调层把主 Agent 的最终回答投影回同一消息位置。重复 Submit 同一消息只关联已有 Turn；Child Agent 不直接写用户 Session；Submit 创建 Turn 前失败时保留用户消息而不投影回答。Session 是用户可读对话来源，Trace 只保存 Runtime 执行事实。
LocalMap 直接由 Kernel 按 Project 隔离、文本或 Record 引用和数量限制检索，返回匹配 Record、直接 Relation 和关联 Artifact；它不调用 MMR、复核或删除，也不把全图交给调用方。MMR 是 Runtime 提供、由 Brainstorm Skill 选择调用的确定性 Tool operation；Runtime 只能通过 Kernel Interface 使用图谱能力，Kernel 不实现 MMR。
Kernel 当前使用 SQLite；闭环阶段的词法候选检索只用于先完成 Record、LocalMap 与页面功能。功能闭环通过后，语义候选检索以 Embedding 替换词法路径，不改变 LocalMap Interface，不自动去重，也不保留双检索路径。
## 取代范围
`supersedes` 列出的旧 ADR 只在所列范围内保留历史记录，不再把准入、审核、Pipeline、Auto、Workflow 或旧 Session 作为 Record、Connect、Remove、LocalMap 的写入前提。其余 Research Graph 对象语义、证据关系和报告闭包规则保持历史语义。
