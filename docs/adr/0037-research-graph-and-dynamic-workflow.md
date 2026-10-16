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
## 决策
采用 Research Graph 替代 Danus 式 Fact Graph：它保留 Direction 与失败 Experiment，报告只选择具有证据闭包的 Claim。Summary 与 Trajectory 不因编排便利而成为研究对象。
Workflow 由主 Agent 动态决定 Child Agent 的继续、复审、并行与转向。主 Agent 与人类可调用 Graph CLI，Child Agent 只读；双审留在主 Agent Skill/prompt，CLI 不耦合审核。撤销先显示节点及全部依赖后继，确认后使它们不再可用并保留历史。
Herdr/Pi 可在平台外执行同一 Workflow 并保存 Session、Trajectory、Summary 与 Artifact；这些运行记录不自动成为 Research Graph 事实。后续平台主 Agent 可读取 Artifact，经审核后使用现有 Graph CLI 写入 Direction、Experiment、Claim 与证据关系；本次赛题运行不实现专用导入层。
固定 Pipeline、Stage、Auto、准入状态机与把 Trace 当作领域状态的设计不进入目标模型。
## 取舍
一个尚未验证的 Direction 若只留在 Child Agent Trajectory，主 Agent 新开 Session 时会丢失已探索路线；若把它写成已验证事实，又会让报告把猜想当结论。Research Graph 保留该 Direction，但报告只读取有证据闭包的 Claim。
正常结束的 Child Agent 在 Trajectory 末尾输出 Summary；Tool 失败时可能没有 Summary。Runtime 以结束原因和 Trajectory 尾窗暴露该失败；不建立复制摘要文本的 Handoff 实体，代价是主 Agent 必须在需要时展开日志。
一篇 Source 被撤回时，硬删除会抹去依赖关系与原有判断；级联撤销保留历史并使后继不再可用，代价是恢复必须新建 Research Graph 对象。
禁止 Child Agent 直接写图，放弃它们的直接写图速度，换取主 Agent Skill 在一次写入前集中执行双审；固定 Pipeline 不能表达“审查后继续原 Agent”与“审查后另开方向”的不同决定。
