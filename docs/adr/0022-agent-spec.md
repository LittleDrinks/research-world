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
Agent Runtime 先识别工作区能力，编辑器只能选择识别结果。AgentSpec 启动时把已选择能力编译为不可变快照写入 `session_meta`；任一能力缺失或运行中定义漂移时明确失败并要求新 Session。
Skill 由 `SKILL.md` 识别，系统提示只注入名称与描述，正文由 `read_skill` 按需读取。节点以 `@node_id` 引用，正文由 `read_resource` 按需读取。
Tool 是科研人员选择的能力，一个 Tool 可展开多个 operation。内置函数、Lean4、PubMed、UniProt、PDB、私有数据库、浏览器、GPU 与实验环境走同一 Tool 路径；MCP、HTTP、SSE、stdio、CLI 与数据库驱动只属于 Tool Adapter 实现。Research Kernel 不增加 backend 枚举，Workflow 不增加专用 stage。
Preset 是可复用 AgentSpec 草稿，只引用 Tool id。Agent 设置可手动应用 Preset；主 Agent 可生成草稿，但安装、配置、保存与启动都需人工确认。应用后 AgentSpec 独立保存，不随 Preset 更新漂移。
标准 Preset 引用的 Tool 在标准 Compose 环境中必须开箱即用。草稿可保留未就绪 Tool，Launch 必须返回缺失 Tool id、原因与可执行的安装或配置动作；主 Agent 不生成命令、URL 或凭证。
AgentSpec 创建与更新必须携带 Project id；Agent Runtime 在 Launch 前按该 Project workspace 重检 Tool readiness，未就绪时返回 Tool id、状态与原因。
创建与更新是显式区分的两个操作：POST 创建新 AgentSpec，PUT 只更新已存在 id，不做 upsert；id 非法或重复、名称或 Instructions 为空时返回可读错误且不落盘。新建默认值来自识别结果与规范默认值，不引入第二套配置格式。
