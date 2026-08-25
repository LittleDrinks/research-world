---
sources:
  - id: aliyun-contest
    title: 2026 挑战杯阿里云榜题
    url: https://university.aliyun.com/action/tzbjbgs2026
    accessed: 2026-08-26
  - id: codex-cli
    title: Codex CLI reference
    url: https://developers.openai.com/codex/cli/reference
    accessed: 2026-08-26
  - id: claude-cli
    title: Claude Code CLI reference
    url: https://code.claude.com/docs/en/cli-usage
    accessed: 2026-08-26
  - id: pi-cli
    title: Pi agent toolkit
    url: https://github.com/earendil-works/pi
    accessed: 2026-08-26
  - id: kimi-cli
    title: Kimi Code CLI
    url: https://github.com/MoonshotAI/kimi-cli
    accessed: 2026-08-26
status: accepted
---
# Contest Loop And Bounded Auto
## 决策
赛题六阶段是现有 Research Kernel 事实的有序投影，不新增 KnowledgeGap、Evidence 或 Research Round 实体。
| 赛题阶段 | Kernel 表达 | 完成证据 |
|---|---|---|
| 问题理解 | question payload 与 Claim | 对象、范围、变量、约束、争议和知识缺口可回读 |
| 知识整合 | admitted source、Claim、Artifact | primary Source 全文、元数据、引用和局限可核验 |
| 候选假设生成 | 多个 Direction | 至少 3 个非同义候选，预测、替代解释和不确定性明确 |
| 证据梳理 | supports / refutes 与 Admission / Review | 正反证据不被压平，冲突和不足保留 |
| 研究计划输出 | experiment payload 与执行凭据 | 数据、变量、对照、方法、判据、停止和回退条件可执行 |
| 反馈修正 | 有序 Pipeline run 的研究版本投影 | V1 / V2 差异绑定证据、评价或人工反馈 |
Auto 由 Research Kernel 持有。启动时冻结最大 Pipeline run 数、token、墙钟时间、并发和无改进轮数；支持暂停、恢复和停止。每次执行只记录一个终止原因：`completed`、`run_budget`、`token_budget`、`time_budget`、`no_improvement`、`waiting_human`、`stopped` 或 `failed`。冲突证据、湿实验、伦理约束和授权缺失进入人工 Gate，不能由 Auto 批准。现有无界 reflect 级联删除。
Agent Runtime 继续通过 ACP 对外，内部按产品稳定接口实现 Adapter：Codex 使用 `codex exec --json`，Claude 使用 print / stream-json，Pi 使用 RPC / JSON，Kimi 使用原生 ACP。AgentSpec 显式保存 `runtime: {id, realm}`；Runtime、Endpoint 与模型互相独立，不从 Endpoint 推断 Runtime，不做跨 Adapter fallback。Instructions、Skills、Tools 与 Runtime readiness 在 Launch 前冻结，缺失即失败。
报告和 Project export 都从 Kernel 投影。报告 Agent 只能组织 admitted Claim、Source 与关联 Artifact；Pipeline run 只用于版本次序和反馈来源，不把 Runtime Trace 当作科学事实或报告内容。导出包增加 manifest、checksum 与 Kernel 持有的 Session 引用；Runtime Trace 作为独立运行审计文件交付，不参与报告事实投影。凭证、绝对路径和临时文件不进入任何投影。
## 实现顺序
1. AgentSpec Runtime schema、Catalog、readiness 与 Profile UI。
2. Codex、Claude、Pi、Kimi Adapter。
3. 六阶段 Pipeline 与有限 Auto Kernel 状态机。
4. Auto 工作台、研究版本差异与人工 Gate。
5. 报告、Project export 与代表案例。
6. Q001–Q125 轻量运行与提交包。
## 非目标
通用 Tool Provisioner、完整 Project File 导入或同步、外部 Benchmark 扩张、远端或 GPU 基建、100+ 节点规模化布局不阻塞本里程碑。
