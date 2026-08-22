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
| 识别 | workspace | 可用 Runtime、模型、Skill、Tool、MCP | `runtime/discover` extension |
| 启动 | AgentSpec、workspace、parent、mode | session_id | `runtime/launch` extension |
| 发送 | session_id、内容块 | 实时 session update、终止原因 | `session/prompt` |
| 检查 | session_id | 从 Trace 投影的消息、Turn、Tool 树 | `runtime/inspect` extension |
| 向量化 | endpoint、texts | vectors | `runtime/embed` extension |
ACP Python SDK 负责连接、schema 与 HTTP/WebSocket 传输。Web 通过 Research Kernel 使用同一 ACP Client；Runtime 不暴露第二套 REST 会话协议。
## 内部所有权
`providers` 处理 OpenAI 兼容端点与 Codex CLI；`skills` 解析 `SKILL.md`；`mcp` 解析工作区配置并执行所选 server；`tools` 执行文件与渐进披露工具；`trace` 写入并重放 Session；`acp` 只翻译外部协议。外部调用方不感知这些目录。
本机 Codex 0.149.0 没有 ACP 子命令，作为 Runtime 内部 CLI adapter 使用 `codex exec --json`；它不是新的外部边界。
## Session 与 Trace
Trace 是 Session 的唯一事实源，不建消息数据库。凡进入模型的内容都写入 Trace；凭证、授权头与私有环境变量永不写入。事件为 `session_meta`、`turn_start`、`model_request`、`model_response`、`tool_call`、`tool_result`、`child_session`、`turn_end`、`error`。
每条事件编码成单行 JSON 后一次写入；读取时丢弃断裂尾行并截断到最后一条完整记录。Session 恢复与 UI 投影只重放 Trace。
Thread 只在 Research Kernel 保存 `project_id + session_id` 指针。新建 Thread 启动新 Session；归档 Thread 不删除 Trace。
## Pipeline Run
PipelineSpec 由 Research Kernel 从 YAML 识别并校验。数据库只保存 `pipeline_id + definition_snapshot`，没有固定 kind；模板修改不影响在途 run。run event 只记录 stage、gate、人工决策与 session_id，模型消息和工具细节留在 Runtime Trace。
## 渐进披露
Skill 与节点正文默认不进入模型请求。模型只看到名称、描述和 `@node_id`；调用 `read_skill` 或 `read_resource` 后，读取结果才进入 Trace 与后续模型请求。MCP tool schema 只在 AgentSpec 选择对应 server 后暴露。
