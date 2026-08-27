---
sources:
  - id: danus-fact-graph
    title: Danus fact graph data model
    url: https://github.com/frenzymath/Danus/blob/7a51336e53cd1d558d0e766a61eb0fed46ebb05b/danus/core/DATA_MODEL.md
    version: commit 7a51336e53cd1d558d0e766a61eb0fed46ebb05b
  - id: pi-session
    title: Pi session format and compaction
    url: https://github.com/earendil-works/pi/tree/e86823096c5bad39e1ca282ec24bc5eb9bec745b/packages/coding-agent/docs
    version: commit e86823096c5bad39e1ca282ec24bc5eb9bec745b
  - id: claude-subagents
    title: Claude Code subagents
    url: https://code.claude.com/docs/en/sub-agents
    version: Claude Code v2.1.247
  - id: prov-dm
    title: W3C PROV-DM
    url: https://www.w3.org/TR/prov-dm/
    version: W3C Recommendation 2013-04-30
status: accepted
---
# 研究图谱与动态 Workflow
Research Graph 记录 Question、Source、Direction、Experiment、Artifact 与证据关系；它不是 Danus 式只含已验证事实的 Fact Graph。研究地图是其 UI 投影，报告只从具有证据闭包的 Claim 生成结论。
Agent Runtime 拥有 Session 与 Trajectory。Child Agent 在 Trajectory 最后一段输出 Summary；主 Agent 默认读取尾窗，需要时展开完整 Trajectory。Summary 用于编排，不能直接写入 Research Graph。
Workflow 由主 Agent 动态决定 Child Agent 的继续、复审、并行与转向，不使用固定 Pipeline、Stage 或状态机。主 Agent 与人类独占 Graph CLI；双审由主 Agent Skill/prompt 执行，CLI 不耦合审核。撤销在执行前展示目标及全部依赖后继，确认后使它们不再可用并保留历史。
现有 Research Kernel、准入、Pipeline、Stage、Auto、Trace 与相关实现是遗留实现，不代表本 ADR 已在生产代码中落地。
## 取舍
一个尚未验证的 Direction 若只留在 Child Agent Trajectory，主 Agent 新开 Session 时会丢失已探索路线；若把它写成已验证事实，又会让报告把猜想当结论。Research Graph 保留该 Direction，但报告只读取有证据闭包的 Claim。
Child Agent 因 Tool 失败结束时没有 Summary。Runtime 以结束原因和 Trajectory 尾窗暴露该失败；不建立复制摘要文本的 Handoff 实体，代价是主 Agent 必须在需要时展开日志。
一篇 Source 被撤回时，硬删除会抹去依赖关系与原有判断；级联撤销保留历史并使后继不再可用，代价是恢复必须新建 Research Graph 对象。
主 Agent 独占 Graph CLI，放弃 Child Agent 的直接写图速度，换取双审 Skill 可在一次写入前集中执行；固定 Pipeline 不能表达“审查后继续原 Agent”与“审查后另开方向”的不同决定。
## 取代范围
本 ADR 取代 ADR 0027、0032 中对目标模型的 Research Kernel、Fact Graph、Pipeline、Stage、Auto 与 Trace 术语；它们保留为遗留实现和历史设计记录，不描述目标架构。
