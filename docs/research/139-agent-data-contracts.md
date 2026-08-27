---
sources:
  - id: temporal-child
    title: Temporal Go SDK child workflow API
    url: https://github.com/temporalio/sdk-go/blob/9e67f43b78c6f0174e06009a2eded936829de59c/workflow/doc.go
    version: commit 9e67f43b78c6f0174e06009a2eded936829de59c
    format: source
    accessed: 2026-08-27
  - id: langgraph-routing
    title: LangGraph Send and Command
    url: https://github.com/langchain-ai/langgraph/blob/bdb8a9c7a4aa1390af225f6a5d292e5088659bd5/libs/langgraph/langgraph/types.py
    version: commit bdb8a9c7a4aa1390af225f6a5d292e5088659bd5
    format: source
    accessed: 2026-08-27
  - id: langgraph-checkpoint
    title: LangGraph SQLite checkpoint saver
    url: https://github.com/langchain-ai/langgraph/blob/bdb8a9c7a4aa1390af225f6a5d292e5088659bd5/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py
    version: commit bdb8a9c7a4aa1390af225f6a5d292e5088659bd5
    format: source
    accessed: 2026-08-27
  - id: openai-handoff
    title: OpenAI Agents SDK handoffs
    url: https://github.com/openai/openai-agents-python/blob/10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e/docs/handoffs.md
    version: commit 10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e
    format: source
    accessed: 2026-08-27
  - id: openai-session
    title: OpenAI Agents SDK sessions
    url: https://github.com/openai/openai-agents-python/blob/10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e/docs/sessions/index.md
    version: commit 10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e
    format: source
    accessed: 2026-08-27
  - id: openai-result-trace
    title: OpenAI Agents SDK results and tracing
    url: https://github.com/openai/openai-agents-python/blob/10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e/docs/results.md
    version: commit 10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e
    format: source
    accessed: 2026-08-27
  - id: openai-trace
    title: OpenAI Agents SDK tracing
    url: https://github.com/openai/openai-agents-python/blob/10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e/docs/tracing.md
    version: commit 10cdae4a3c30a29c6e96c8ec14e6bf1c5f02940e
    format: source
    accessed: 2026-08-27
  - id: prov-dm
    title: W3C PROV-DM
    url: https://www.w3.org/TR/prov-dm/
    version: W3C Recommendation 2013-04-30
    format: web specification
    accessed: 2026-08-27
  - id: otel-genai
    title: OpenTelemetry GenAI agent spans
    url: https://github.com/open-telemetry/semantic-conventions-genai/blob/5f5ae69e52464c56eea4389fb793c2690caaea78/docs/gen-ai/gen-ai-agent-spans.md
    version: commit 5f5ae69e52464c56eea4389fb793c2690caaea78
    format: source
    accessed: 2026-08-27
  - id: pi-compaction
    title: Pi compaction and branch summarization
    url: https://github.com/earendil-works/pi/blob/e86823096c5bad39e1ca282ec24bc5eb9bec745b/packages/coding-agent/docs/compaction.md
    version: commit e86823096c5bad39e1ca282ec24bc5eb9bec745b
    format: source
    accessed: 2026-08-27
  - id: pi-session
    title: Pi session JSONL format
    url: https://github.com/earendil-works/pi/blob/e86823096c5bad39e1ca282ec24bc5eb9bec745b/packages/coding-agent/docs/session-format.md
    version: commit e86823096c5bad39e1ca282ec24bc5eb9bec745b
    format: source
    accessed: 2026-08-27
  - id: pi-protocol
    title: Pi session protocol
    url: https://github.com/earendil-works/pi/blob/e86823096c5bad39e1ca282ec24bc5eb9bec745b/packages/protocol/README.md
    version: commit e86823096c5bad39e1ca282ec24bc5eb9bec745b
    format: source
    accessed: 2026-08-27
  - id: claude-subagents
    title: Claude Code subagents
    url: https://code.claude.com/docs/en/sub-agents
    version: Claude Code v2.1.247
    format: web documentation
    accessed: 2026-08-27
---
# 多 Agent 数据契约
## 边界
| 项目术语 | 数据所有者 | 可回放内容 | 不是 |
|---|---|---|---|
| Session | Agent Runtime | 一次 AgentSpec 运行的 Trace | Thread、科研事实 |
| Trajectory | Agent Runtime | Trace 的有序事件、父子 Session、终态输出 | 可写入 Fact Graph 的结论 |
| 动态 Workflow | Research Kernel | Pipeline 对 Stage、spawn、gate、出口的结构化选择 | 由模型消息反推的流程图 |
| Fact Graph | Research Kernel | admitted 节点、Claim、关系、Artifact 引用 | Session 日志或 Agent 自报 |
| Artifact | Research Kernel | Project 内 SHA-256 不可变产物 | 裸路径、临时 Tool 输出 |
`Trajectory` 保存工作过程；其末尾输出或尾窗是给另一个 Agent 的低成本上下文投影。`Fact Graph` 保存已准入的科研事实；只有 Kernel 的 observation/Artifact 提交与 Admission 能把过程材料变成事实。
## 一手系统对照
| 系统/规范 | 动态编排 | 子 Agent/子任务结果 | Session/Trajectory | 持久状态 | Artifact/事实或审计记录 | 依据 |
|---|---|---|---|---|---|---|
| Temporal | 父 Workflow 调度子 Workflow，可并行等待 | `ChildWorkflowFuture.Get` 返回子执行结果；可单独等待启动 | Workflow History 供重放 | 服务端 History | History 的生命周期事件是执行审计，不声明领域事实 | `temporal-child` |
| LangGraph | `Send` 可带不同状态并行投递；`Command` 同时更新状态与路由 | 子图/节点产出归入图状态 | `StateSnapshot` 有 next、task、interrupt 与父 checkpoint | SQLite checkpoint 以 thread、namespace、checkpoint 为键保存状态和 writes | checkpoint 是执行状态，不是证据准入 | `langgraph-routing`、`langgraph-checkpoint` |
| OpenAI Agents SDK | handoff 是模型可调用的定向工具，输入可带 schema/过滤 | `RunResult.new_items` 保留 handoff、tool、approval 边界；`final_output` 属于最后 Agent | trace/span 覆盖 run、turn、agent、handoff、tool | Session 在 run 前读历史、run 后写新 item | rich run item/trace 用于 UI、审计与调试，不等同领域事实 | `openai-handoff`、`openai-session`、`openai-result-trace`、`openai-trace` |
| PROV-DM | Activity 可由计划和 Agent 关联，活动间可 informed-by | Entity 可由 Activity 生成、由其他 Entity 派生 | Activity 带时间；不规定对话存储 | Bundle 可封装一组 provenance 断言 | Entity/Activity/Agent、generation、usage、derivation 给出可审计谱系关系 | `prov-dm` |
| OpenTelemetry GenAI | `invoke_workflow` 与 `invoke_agent` 是不同操作语义 | agent/tool 调用为 span，保持 trace 父子关系 | conversation id 只在已有时关联，不能以 trace id 伪造 | 规范只定义遥测语义 | 输入/输出、Tool I/O 为 opt-in 遥测，不能替代事实准入 | `otel-genai` |
| Pi | session JSONL 的分支和 compaction 可重建上下文 | eval 将 final response 与 native Session 分开断言 | JSONL 以 id/parentId 成树；summary 是专门 entry | session 元数据、快照是权威；progress 仅 UI 提示 | native Session 附件用于评测；不把摘要称为科研事实 | `pi-compaction`、`pi-session`、`pi-protocol` |
| Claude Code | 子 Agent 隔离上下文、顺序或并行委派 | 子 Agent 完成后只将 summary 返回主对话 | 每个子 Agent 自有 context window | 文档未把 summary 规定为事实存储 | summary 是上下文控制与编排输出 | `claude-subagents` |
## 摘要与事实
Pi 将 compaction/branch summary 写为 Session 的专门条目，并用 summary 加最近消息重建下一次上下文；Claude Code 让隔离子 Agent 返回 summary；两者都把摘要用于容量控制，不赋予领域事实地位。OpenAI 的 rich item、Temporal 的 History、LangGraph checkpoint 也保留可审计过程，却都没有把子执行最终文本自动升格为业务事实。依据：`pi-compaction`、`pi-session`、`claude-subagents`、`openai-result-trace`、`temporal-child`、`langgraph-checkpoint`。
因此可检验的约束是：子 Agent prompt 要求最终摘要时，摘要仍是该 Session `Trajectory` 的最后一个终态模型输出；主 Agent 默认读取该 Session 的末尾窗口，按需展开完整 Trajectory。该读取不新增 handoff/result payload，也不把摘要复制进 Fact Graph。只有摘要指出的 Source、Experiment 或 Artifact 经 Kernel 准入后，Claim 与证据链才进入 Fact Graph。
## 最小候选
| 候选 | 最小契约 | 实现改变 | 评测证据 | 用户界面 |
|---|---|---|---|---|
| A. Session 引用加尾窗 | `child_session_id`、父子关系、终态 `event_id`；Runtime 由 Trace 投影 `tail(cursor, limit)` | Trace 写入 child_session 与稳定顺序；Launch/Stage 只传引用；不改 Kernel 图谱表 | 固定 Trace 重放能证明子 Session、终态、默认尾窗与全量读取一致；尾窗截断不得丢终态 | Trajectory 树显示子 Session；默认摘要卡来自尾窗，展开进入完整 Trace |
| B. 终态投影引用 | A 加 `terminal_output_ref = {session_id,event_id}`，它是查询投影而非存储 payload | Runtime inspect 提供终态输出选择；主 Agent 只接收 ref 展开的尾窗，不建立 handoff/result schema | 同一 Trace 两次投影得到相同 ref/文本；失败、取消、limit 无伪造终态摘要 | 子任务行显示 terminal、failed 或 unavailable；复制/展开均跳同一 Trajectory 事件 |
| C. 引用加准入出口 | B 加 Kernel 的 `artifact_id`/observation 草稿引用；Claim 仍经 Admission | Tool Runtime 经现有 Artifact/observation port 交 Kernel；摘要不能直接写节点 | 验证摘要本身不能生成 admitted Claim；带 SHA-256 Artifact 且审核通过时才形成可追溯证据链 | 摘要旁只显示已准入 Artifact/节点关系；未准入材料标为运行记录 |
三者都支持“最后摘要供编排、尾窗优先、全量可展开”。A 最少但要求主 Agent 从尾窗自行识别终态；B 固定终态定位而不复制文本；C 同时闭合科研事实入口。当前调研不选择其一。
## 不变量
- `Session` 与 `Trajectory` 属于 Agent Runtime，Kernel 只保存必要 Session 引用与 Pipeline run 结构事件。
- 动态 `Workflow` 只消费结构化引用和受控投影；不得解析自由文本来猜 parent/child、Artifact 或事实关系。
- 摘要、模型响应、Tool 成功和 checkpoint 都是过程材料；不得绕过 Admission 写入 Fact Graph。
- Fact Graph 的 Claim、source、experiment、Artifact 与 supports/refutes 才是报告、评测科研正确性和用户研究地图的事实输入。
