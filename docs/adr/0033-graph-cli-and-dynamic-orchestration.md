---
sources:
  - id: danus
    title: "Danus: Orchestrating Mathematical Reasoning Agents with Fact-Graph Memory"
    authors: "Jihao Liu et al."
    arxiv: "2607.06447"
    url: https://arxiv.org/abs/2607.06447
    accessed: 2026-08-27
status: accepted
---
# 图谱 CLI 与动态编排
## 决策
Research Kernel 只拥有 Fact Graph 与 Graph CLI。Graph CLI 查询、写入和删除节点或关系；它不嵌入审核策略，不维护 Workflow 状态，也不启动 Agent。
主 Agent 保留用户意图、方向选择和最终综合，按需要并行委派探索 Agent、委派审核 Agent，或根据返回结果继续同一方向。子 Agent 的 Session 与 Trajectory 属于各自的 Agent Runtime；Workflow 以这些 Trajectory 的父子关系和主 Agent 的决策显现，不由 Kernel 状态机解释。
审核是主 Agent 的 Skill。审核结果提供意见、依据和不确定性，主 Agent 决定是否调用 Graph CLI；审核不生成节点准入状态，不限制 Graph CLI 的写入或删除。
`pending`、`admitted`、`ghost`、强制双审、Direction 状态机、Kernel Auto 和固定 Pipeline stage 均不存在。交付报告从指定 Fact Graph 快照及两个有序 Pipeline run 切点生成；V1/V2 不是研究流程。
## 边界
Fact Graph 保存当前研究对象及其关系，不保存 Session 对话、工具输入输出或 Workflow 执行状态。Trajectory 保存工作过程，不充当科研结论。删除图谱内容不产生替代状态；对应 CLI 调用仍留在发起 Agent 的 Trajectory 中。[danus]
