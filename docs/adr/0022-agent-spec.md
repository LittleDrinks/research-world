---
sources:
  - id: dsh-architecture
    title: DeepSeek Harness architecture
    url: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
  - id: claude-science
    title: Claude for Life Sciences
    url: https://www.anthropic.com/research/claude-for-life-sciences
  - id: mcp
    title: Model Context Protocol
    url: https://docs.anthropic.com/en/docs/mcp
---
# AgentSpec
AgentSpec 是一次 Agent 执行所需能力的声明：Endpoint、模型、Instructions、Skills、Tools、Connectors 与执行参数。它不是独立的“能力装配”模块。
Runtime 先识别当前工作区可用的 Endpoint、模型、Skills、Tools 与 Connectors；编辑器只能选择识别结果。AgentSpec 启动时编译并快照进 `session_meta`，运行中不可修改；修改后启动新 Session。
Skill 由目录中的 `SKILL.md` 识别。系统提示只注入名称与描述，正文由 `read_skill` 按需读取。节点以 `@node_id` 引用，正文由 `read_resource` 按需读取。Connector 由 Runtime 注册或从工作区识别，AgentSpec 只保存 Connector id。
Skill 表达可复用科研规程，Tool 是 Runtime 内置动作，Connector 是以 MCP server 接入的外部数据库、科学软件、搜索服务或实验设施。Connector 配置和凭证由 Runtime 持有；Agent 设置只选择 Connector id，Kernel、Pipeline、Trace 与 Artifact 不保存密钥。
Lean4 与 PubMed、UniProt、PDB、私有实验数据库、HPC 使用同一 Connector 路径。新增能力只需注册 Connector 并在 AgentSpec 选择；Kernel 不增加 backend 枚举，Pipeline 不增加专用 stage。
Builder 只生成 AgentSpec 草稿；JSON Schema、识别结果校验与人工确认共同决定是否可启动。
