---
sources:
  - id: dsh-architecture
    title: DeepSeek Harness architecture
    url: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
---
# AgentSpec
AgentSpec 是一次 Agent 执行所需能力的声明：Runtime、模型、Instructions、Skills、Tools、MCP 与执行参数。它不是独立的“能力装配”模块。
Runtime 先识别当前工作区可用的模型、Skills、Tools 与 MCP；编辑器只能选择识别结果。AgentSpec 启动时编译并快照进 `session_meta`，运行中不可修改；修改后启动新 Session。
Skill 由目录中的 `SKILL.md` 识别。系统提示只注入名称与描述，正文由 `read_skill` 按需读取。节点以 `@node_id` 引用，正文由 `read_resource` 按需读取。MCP 由工作区配置识别，AgentSpec 只保存 server id。
Builder 只生成 AgentSpec 草稿；JSON Schema、识别结果校验与人工确认共同决定是否可启动。
