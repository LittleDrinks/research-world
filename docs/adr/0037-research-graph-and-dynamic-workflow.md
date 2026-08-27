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
supersedes:
  - 0020 graph evidence and Session retention scope
  - 0021 review and write-gate scope
  - 0026 Runtime and Trajectory ownership scope
  - 0027 Research Kernel ownership scope
  - 0032 fixed Pipeline and Auto scope
  - 0036 report-input scope
---
# 研究图谱与动态 Workflow
## 决策
采用 Research Graph 替代 Danus 式 Fact Graph：它保留 Direction 与失败 Experiment，报告只选择具有证据闭包的 Claim。Summary 与 Trajectory 不因编排便利而成为研究对象。
Workflow 由主 Agent 动态决定 Child Agent 的继续、复审、并行与转向。主 Agent 与人类可调用 Graph CLI，Child Agent 只读；双审留在主 Agent Skill/prompt，CLI 不耦合审核。撤销先显示节点及全部依赖后继，确认后使它们不再可用并保留历史。
固定 Pipeline、Stage、Auto、准入状态机与把 Trace 当作领域状态的设计不进入目标模型。
## 取舍
一个尚未验证的 Direction 若只留在 Child Agent Trajectory，主 Agent 新开 Session 时会丢失已探索路线；若把它写成已验证事实，又会让报告把猜想当结论。Research Graph 保留该 Direction，但报告只读取有证据闭包的 Claim。
Child Agent 因 Tool 失败结束时没有 Summary。Runtime 以结束原因和 Trajectory 尾窗暴露该失败；不建立复制摘要文本的 Handoff 实体，代价是主 Agent 必须在需要时展开日志。
一篇 Source 被撤回时，硬删除会抹去依赖关系与原有判断；级联撤销保留历史并使后继不再可用，代价是恢复必须新建 Research Graph 对象。
禁止 Child Agent 直接写图，放弃它们的直接写图速度，换取主 Agent Skill 在一次写入前集中执行双审；固定 Pipeline 不能表达“审查后继续原 Agent”与“审查后另开方向”的不同决定。
## 取代范围
ADR 0020 中图谱只含已准入事实、删除原始 Session 的范围由 Research Graph 与 Trajectory 边界替代。ADR 0021 中强制准入 Gate 与固定双审写入门由主 Agent Skill/prompt 替代。ADR 0026 中 Kernel/Pipeline 持有 Runtime Trace 的范围由 Agent Runtime 拥有 Session 与 Trajectory 替代。ADR 0027 中 Research Kernel 统一写入与编排的范围由 Graph CLI 和动态 Workflow 替代。ADR 0032 中固定 Pipeline、Stage、Auto 的范围由动态 Workflow 替代。ADR 0036 中以 admitted 状态选择报告输入的范围由证据闭包替代。
上述 ADR 与现有代码保留为遗留实现和历史设计记录，不描述目标架构。
