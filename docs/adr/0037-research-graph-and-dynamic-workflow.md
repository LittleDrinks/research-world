---
sources:
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
