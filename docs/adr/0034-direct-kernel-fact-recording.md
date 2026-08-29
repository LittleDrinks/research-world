---
sources:
  - id: issue-146
    title: Research Kernel 深 Module
    url: https://github.com/LittleDrinks/research-world/issues/146
    accessed: 2026-08-29
  - id: issue-147
    title: 架构落地：决策记录与 TDD 证据约定
    url: https://github.com/LittleDrinks/research-world/issues/147
    accessed: 2026-08-29
status: accepted
supersedes:
  - "ADR 0026: Runtime/Kernel 混合 Session、Trace、Thread 与 Pipeline 的旧所有权"
  - "ADR 0027: command/query、准入和 Pipeline 驱动的旧 Kernel 写入范围"
  - "ADR 0032: Kernel 持有固定 Pipeline 与 Auto 的旧范围"
  - "ADR 0037: 与直接记录、Session 投影和 Kernel LocalMap 冲突的 Workflow/Trajectory 范围"
---
# Direct Kernel Fact Recording
Research Kernel 是 Project 研究状态的唯一深模块，拥有 Project、Session、Artifact、Research Graph 记录与关系以及 LocalMap；Runtime 不绕过 Kernel Interface 写入这些对象。
## 决策
Kernel Interface 只接受 Project、Session、Artifact、Record、Connect、Remove 与 LocalMap 领域输入。Record 只校验内容完整和 Project 归属，写入后立即可被地图、LocalMap 和 Agent 使用；不设置准入状态、审核 Gate 或自动拒绝。Connect 只连接同一 Project 的既有记录和有效关系；Remove 记录时同时移除其直接关系，但不删除关联 Artifact；Remove 关系不影响记录。
Session 先持久化用户消息，再由对话协调层把主 Agent 的最终回答投影回同一消息位置。重复提交同一消息只关联已有 Turn；Child Agent 不直接写用户 Session；Submit 创建 Turn 前失败时保留用户消息而不投影回答。Session 投影是用户可读对话来源，Trace 仍只保存 Runtime 执行事实。
LocalMap 直接由 Kernel 按 Project 隔离、文本或节点引用和数量限制检索，返回匹配记录、与匹配记录相邻的直接关系和匹配记录关联的 Artifact；查询只接受一个非空 `text` 或 `record_id` 及正整数 `limit`，记录按创建顺序返回且不自动去重。它不调用 MMR、复核或删除，也不把全图交给调用方。MMR 是 Runtime 提供、由 Brainstorm Skill 选择调用的确定性 Tool operation；Runtime 只能通过 Kernel Interface 使用图谱能力，Kernel 不实现 MMR。
Kernel 当前使用 SQLite；SQLite FTS5 只提供词法全文检索，用于候选检索，不是向量余弦语义检索。后续候选检索以 embedding 语义候选替换 FTS5，是 Kernel 内部的私有演进/TODO，不改变 LocalMap Interface，也不自动去重。
## 取代范围
上述取代只覆盖与直接事实记录和所有权冲突的旧决定：ADR 0026 中 Kernel/Runtime 对 Session、Trace、Thread 与研究状态的混合范围；ADR 0027 中动态 command/query、准入、Pipeline 和 Kernel 编排作为写入前提的范围；ADR 0032 中由 Kernel 持有固定 Pipeline、Stage、Auto 和人工 Gate 的范围；ADR 0037 中以 Workflow、Trajectory 或旧 Session 作为 Research Graph 写入前提的范围。其余 Research Graph 的对象语义、证据关系和报告闭包规则保持不变。
