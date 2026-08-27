---
sources:
  - docs-references.manifest.json
  - issue-139.sources.json
  - https://github.com/LittleDrinks/research-world/issues/139#issuecomment-5434636802
---
# 本地参考索引
按 `docs-references.manifest.json` 的 `id`、`status`、`format` 和路径检索；论文 PDF 在 `references/`，`opendataloader-pdf` 产出的 Markdown 在 `markdown/`，#139 固定来源在 `snapshots/issue-139/`。
## 主题入口
| 主题 | 本地材料 | 当前仓库结论 |
| --- | --- | --- |
| 研究状态与证据准入 | [论文 Markdown](markdown/)、[Research Kernel ADR](../../docs/adr/0027-research-kernel.md)、[竞赛循环 ADR](../../docs/adr/0032-contest-loop-and-bounded-auto.md) | Kernel 是研究状态唯一写入门；只有 admitted claim、source、artifact 进入报告投影。 |
| 路由、handoff 与子工作流 | [Temporal child workflow](snapshots/issue-139/temporal-child-workflow.go)、[LangGraph routing](snapshots/issue-139/langgraph-routing.py)、[Agents handoffs](snapshots/issue-139/openai-agents-handoffs.md) | 路由和委派产生可追踪的子执行边界，不能把临时会话直接当作研究事实。 |
| checkpoint、session 与压缩 | [LangGraph SQLite checkpoint](snapshots/issue-139/langgraph-sqlite-checkpoint.py)、[Agents sessions](snapshots/issue-139/openai-agents-sessions.md)、[Agents results](snapshots/issue-139/openai-agents-results.md)、[Pi session format](snapshots/issue-139/pi-session-format.md)、[Pi protocol](snapshots/issue-139/pi-session-protocol.md)、[Pi compaction](snapshots/issue-139/pi-compaction.md) | Session state 用于恢复执行；事实和模型交互仍由可审计 Trace 记录，压缩不应伪造原始事件。 |
| 溯源与可观测性 | [PROV-DM](snapshots/issue-139/w3c-prov-dm.md)、[GenAI agent spans](snapshots/issue-139/opentelemetry-genai-agent-spans.md)、[Agents tracing](snapshots/issue-139/openai-agents-tracing.md)、[Trace ADR](../../docs/adr/0029-trace-ui.md) | Trace 是 Session 的模型事实源；来源、事件和父子关系保持可回放，凭证和私有运行元数据不进入公开投影。 |
| 独立 agent 委派 | [Claude Code subagents](snapshots/issue-139/claude-code-subagents.md)、[Agents handoffs](snapshots/issue-139/openai-agents-handoffs.md)、[Agent Runtime ADR](../../docs/adr/0026-agent-runtime.md) | 子 agent 返回受限结果，主流程以明确边界接收；新 Session 承担恢复和权限隔离。 |
## 完整性
- `docs` 论文型来源：85 条，82 条同时有本地 PDF 和 Markdown，3 条保留失败原因与重试命令。
- #139 补充来源：13 条；固定源码记录 commit，网页记录规范或产品版本与访问日，格式和 SHA-256 在 manifest 中。
- 固定源码按原始快照校验；`pi-compaction.md` 的原始尾空格审计例外已在 manifest 明列，不作为下载失败。
- 设计说明中 17 条无原 URL 的题名-only 引用保留在 `unresolved_citations`；产品页、代码仓库、Issue 和未纳入清单的纯网页文档 96 条保留在 `excluded_sources`。
