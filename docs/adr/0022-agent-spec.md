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
  - id: openai-agents-tools
    title: OpenAI Agents SDK Tools
    url: https://openai.github.io/openai-agents-python/tools/
  - id: zotero-metadata
    title: Zotero Retrieve PDF Metadata
    url: https://www.zotero.org/support/retrieve_pdf_metadata
---
# AgentSpec
AgentSpec 是一次 Agent 执行所需能力的声明：Endpoint、模型、Instructions、Skills、Tool id 与执行参数。它不是独立模块，也不包含 transport、位置、凭证或安装配置。
Runtime 先识别当前工作区可用的 Endpoint、模型、Skill 与 Tool；编辑器只能选择识别结果。AgentSpec 启动时编译为 Endpoint、Skill 与 Tool operation 的不可变快照写入 `session_meta`；运行中定义漂移时明确失败并要求新 Session。
Skill 由 `SKILL.md` 识别，系统提示只注入名称与描述，正文由 `read_skill` 按需读取。节点以 `@node_id` 引用，正文由 `read_resource` 按需读取。
Tool 是科研人员选择的能力，一个 Tool 可展开多个 operation。内置函数、Lean4、PubMed、UniProt、PDB、私有数据库、浏览器、GPU 与实验环境走同一 Tool 路径；MCP、HTTP、SSE、stdio、CLI 与数据库驱动只属于 Tool Adapter 实现。Kernel 不增加 backend 枚举，Pipeline 不增加专用 stage。
Preset 是可复用 AgentSpec 草稿，只引用 Tool id。Agent 设置可手动应用 Preset；对话 orchestrator 可生成草稿，但安装、配置、保存与启动都需人工确认。应用后 AgentSpec 独立保存，不随 Preset 更新漂移。
标准 Preset 引用的 Tool 在标准 Compose 环境中必须开箱即用。草稿可保留未就绪 Tool，Launch 必须返回缺失 Tool id、原因与可执行的安装或配置动作；orchestrator 不生成命令、URL 或凭证。
`source-researcher` 是稳定 Runtime Preset：固定引用随 Runtime 发布的 `crossref`、`openalex`、`arxiv`、`pubmed`、`project_files` 与 `source-research` Skill；额外搜索、OpenCLI/browser 与 Zotero 只在当前 catalog 已识别相应稳定 id 时加入推荐。每项推荐携带用途、status 与 reason；任何非 ready 推荐阻止保存和 Launch，应用 Preset 不调用 prepare。
文献 Tool 按科研能力分组而非按 operation 展开：Crossref/OpenAlex 核验书目与开放获取位置，arXiv/PubMed 检索一手来源并读取可得全文，Project Files 将完整正文登记为 Project scoped Artifact。元数据记录、摘要与全文 Artifact 分开，附件存在不推导书目正确，书目正确也不推导全文可用。
AgentSpec 创建与更新必须携带 Project id；Research Kernel 在落盘前按该 Project workspace 的 Runtime catalog 重检 Tool readiness，未就绪时返回 Tool id、状态与原因。
创建与更新是显式区分的两个操作：POST 创建新 AgentSpec，PUT 只更新已存在 id，不做 upsert；id 非法或重复、名称或 Instructions 为空时返回可读错误且不落盘。新建的默认 Endpoint、模型与执行选项来自 Runtime 识别结果与规范默认值，不引入第二套配置格式。
