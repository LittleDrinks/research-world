---
sources:
  - id: acp-python
    title: Agent Client Protocol Python SDK
    url: https://github.com/agentclientprotocol/python-sdk
  - id: dsh-architecture
    title: DeepSeek Harness architecture
    url: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
  - id: penguin-traces
    title: Penguin Harness sessions and traces
    url: https://github.com/Prism-Shadow/penguin-harness
---
# Agent Runtime
系统只有两个深模块：Research Kernel 拥有项目、事实图谱、Thread、Pipeline 与评价；Agent Runtime 拥有 Agent 执行、模型凭证、能力识别、Session 与 Trace。Pipeline 解释和评价不进入 Runtime；它们通过相同的 Agent Runtime 接口启动普通 Session。
## 外部接口
| 动作 | 输入 | 输出 | ACP 映射 |
|---|---|---|---|
| 识别 | workspace | 可用 Endpoint、模型、Skill、Tool、Connector | `runtime/discover` extension |
| 启动 | AgentSpec、workspace、parent、mode | session_id | `runtime/launch` extension |
| 发送 | session_id、内容块 | 实时 session update、终止原因 | `session/prompt` |
| 检查 | session_id | 从 Trace 投影的消息、Turn、Tool 树 | `runtime/inspect` extension |
| 向量化 | endpoint、texts | vectors | `runtime/embed` extension |
ACP Python SDK 负责连接、schema 与 HTTP/WebSocket 传输。Web 通过 Research Kernel 使用同一 ACP Client；Runtime 不暴露第二套 REST 会话协议。
## 内部所有权
`endpoints` 识别 OpenAI 兼容服务与 Codex CLI，并在同模型 Endpoint 间故障切换；`skills` 解析 `SKILL.md`；`connectors` 注册或识别外部能力并执行所选能力；`tools` 执行文件与渐进披露工具；`trace` 写入并重放 Session；`acp` 只翻译外部协议。外部调用方不感知这些目录。
本机 Codex 0.149.0 没有 ACP 子命令，作为 Runtime 内部 CLI adapter 使用 `codex exec --json`；它不是新的外部边界。
## Connector
Connector 是 AgentSpec 的可选能力，不是第三个深模块。HTTP、SSE、stdio 与 MCP 都藏在 Runtime 内部 seam 后；同一注册、识别、选择和调用路径接入 Lean4、外部数据库、浏览器与实验设施。
Connector 公共投影只包含标识、名称、描述、transport、来源与可用性；URL、command、args、环境变量名、请求头和凭证不越过 Runtime seam。调用结果先返回 Runtime 内置工具，再由 Research Kernel 登记为 Project Artifact；Runtime 不直接写研究图谱。
## Session 与 Trace
Trace 是 Session 的唯一事实源，不建消息数据库。凡进入模型的内容都写入 Trace；凭证、授权头与私有环境变量永不写入。事件为 `session_meta`、`turn_start`、`model_request`、`model_response`、`tool_call`、`tool_result`、`child_session`、`turn_end`、`error`。
每条事件编码成单行 JSON 后一次写入；读取时丢弃断裂尾行并截断到最后一条完整记录。Session 恢复与 UI 投影只重放 Trace。
Thread 只在 Research Kernel 保存 `project_id + session_id` 指针。新建 Thread 启动新 Session；归档 Thread 不删除 Trace。
Project 创建只接收名称与研究问题；Research Kernel 在受控 projects 根目录内分配 workspace，Web 不提交文件系统路径。
## Pipeline Run
PipelineSpec 由 Research Kernel 从 YAML 识别并校验。数据库只保存 `pipeline_id + definition_snapshot`，没有固定 kind；模板修改不影响在途 run。AgentSpec Instructions 只保存跨任务稳定的角色约束，prompt stage 保存本次操作契约；prompt stage 的 `agent` 引用已保存 AgentSpec，Research Kernel 不临时改写 Endpoint、模型、Skill、Tool 或 Connector。启动时将完整 AgentSpec 交给 Runtime 快照。run event 只记录 stage、gate、人工决策与 session_id，模型消息和工具细节留在 Runtime Trace。
## 渐进披露
Skill 与节点正文默认不进入模型请求。模型只看到名称、描述和 `@node_id`；调用 `read_skill` 或 `read_resource` 后，读取结果才进入 Trace 与后续模型请求。Connector tool schema 只在 AgentSpec 选择对应 Connector 后暴露。
报告工具只请求 Research Kernel 的报告投影、BibTeX 导出与交付校验。Endpoint 可用性由 Kernel 查询 Runtime 识别结果后推导，Agent 和 HTTP 调用方不能自报。
