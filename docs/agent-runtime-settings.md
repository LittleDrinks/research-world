---
title: Agent Runtime Settings
status: proposed
accessed: 2026-08-24
canonical_for: issue-63 research, UI specification, prototype acceptance, implementation subissues
sources:
  - id: opendesign
    title: OpenDesign
    product: OpenDesign
    version: open-design-v0.20.2
    url: https://github.com/nexu-io/open-design
    product_url: https://open-design.ai
    screenshot_source: https://raw.githubusercontent.com/nexu-io/open-design/main/docs/screenshots/product-tour/home.png
    screenshot: research-world/web/screenshots/issue63-competitor-opendesign.png
    license: Apache-2.0 for repository code; product name, hosted service, screenshots and trademarks are not relicensed by this review
  - id: multica
    title: Multica
    product: Multica
    version: v0.4.32
    url: https://github.com/multica-ai/multica
    product_url: https://multica.ai
    screenshot_source: https://raw.githubusercontent.com/multica-ai/multica/main/apps/docs/public/images/docs/tutorial-runtime-detail.webp
    screenshot: research-world/web/screenshots/issue63-competitor-multica.png
    license: Multica License; Apache-2.0 terms plus hosted and embedded commercial restrictions, retained branding and attribution requirements
  - id: cc-switch
    title: CC Switch
    product: CC Switch
    version: v3.20.0
    url: https://github.com/farion1231/cc-switch
    product_url: https://ccswitch.io
    screenshot_source: https://raw.githubusercontent.com/farion1231/cc-switch/main/assets/screenshots/main-en.png
    screenshot: research-world/web/screenshots/issue63-competitor-cc-switch.png
    license: MIT for repository code; product name, website and screenshots remain their owners' assets
  - id: conductor
    title: Conductor
    product: Conductor
    version: 0.81.0 latest visible changelog entry
    url: https://www.conductor.build/docs
    product_url: https://www.conductor.build/
    screenshot_source: https://www.conductor.build/
    screenshot: research-world/web/screenshots/issue63-competitor-conductor.png
    license: proprietary product interface; screenshot retained as research evidence only
  - id: codex-app
    title: Introducing the Codex app
    product: Codex app
    version: product page dated 2026-02-02; Codex CLI repository v0.149.1
    url: https://openai.com/index/introducing-the-codex-app/
    repository: https://github.com/openai/codex
    screenshot_source: https://openai.com/index/introducing-the-codex-app/
    screenshot: research-world/web/screenshots/issue63-competitor-codex-app.png
    license: Apache-2.0 covers Codex CLI repository code, not the app interface or OpenAI assets
  - id: kimi-code
    title: Kimi Code CLI Web UI
    product: Kimi Code CLI
    version: v0.38.0
    url: https://github.com/MoonshotAI/kimi-cli
    documentation: https://moonshotai.github.io/kimi-cli/en/reference/kimi-web.html
    screenshot_source: https://moonshotai.github.io/kimi-cli/en/reference/kimi-web.html
    screenshot: research-world/web/screenshots/issue63-competitor-kimi.png
    license: MIT for repository code; documentation and product assets retained as research evidence only
  - id: claude-squad
    title: Claude Squad
    product: Claude Squad
    version: v1.0.20
    url: https://github.com/smtg-ai/claude-squad
    screenshot_source: https://raw.githubusercontent.com/smtg-ai/claude-squad/main/assets/screenshot.png
    screenshot: research-world/web/screenshots/issue63-competitor-claude-squad.png
    license: AGPL-3.0
  - id: issue-41
    title: Agent Profile Preset orchestration
    url: https://github.com/Intelligent-Internet/ai4sci/issues/41
  - id: issue-43
    title: Tool Runtime and explicit provisioner
    url: https://github.com/Intelligent-Internet/ai4sci/issues/43
  - id: issue-54
    title: Source researcher preset
    url: https://github.com/Intelligent-Internet/ai4sci/issues/54
qa:
  tool: OpenCLI browser with real Chrome
  tool_version: 1.8.6
  chrome_extension: 1.0.22
  target: http://127.0.0.1:8095
---
# Agent Runtime Settings
## 名称消歧
| 用户称呼 | 官方名称与证据 | 排除候选 | 结论 |
|---|---|---|---|
| Open Design | `nexu-io/open-design` 的产品字标为 `OpenDesign`，release 使用 `Open Design`，官方域名为 `open-design.ai` | `opendesigner.io` 自称 fan-made；`OpenCoworkAI/open-codesign` 是独立 Open CoDesign | 研究对象写作 `OpenDesign`；用户口语 `Open Design` 可追溯到同一官方仓库 |
| Multica | 官方站、仓库 `multica-ai/multica` 与产品 UI 均为 `Multica` | 未发现同类官方候选 | 拼写确认，无未决歧义 |
| CC Switch | 官方仓库 `farion1231/cc-switch`、官网 `ccswitch.io` 与界面为 `CC Switch`；slug、binary 可写 `cc-switch` | `syntax-syndicate/cc-switch-ai-tool` 与 `SaladDay/cc-switch-cli` 是其他项目 | 产品名写 `CC Switch`，代码标识写 `cc-switch` |
## 竞品矩阵
| 产品 | Agent/创建 | Runtime、模型与认证 | Skills、Tools、MCP | Workspace、环境与诊断 | 可取模式 |
|---|---|---|---|---|---|
| OpenDesign | Home 按项目和任务启动设计 Agent，非 Profile 管理器 | PATH 自动发现多种本机 Agent CLI，支持本机 CLI 或 BYOK | Skill、CLI、MCP 作为插件/能力来源 | working directory 显式，主界面低密度 | CLI 自动识别与工作目录放在发送前；不复制营销化大画布 |
| Multica | Agent 列表、空白创建、Build with AI、详情和归档 | machine + CLI 构成 Runtime；显示 command、path、version、在线与外部登录要求 | Agent 详情分 Skills、MCP、环境；Skill 可导入并快照到 workspace | Runtime 日志、重启、停止、自定义 Runtime；任务有执行日志与重试 | 最接近目标：Inventory 与 Profile 分离，空白/AI 草稿并列，详情按深模块分组 |
| CC Switch | 以 Claude、Codex、Gemini 工具切换为入口，不管理 Agent Profile | Provider 列表、endpoint、模型、测速、代理、故障切换、用量 | 统一 MCP、prompts、Skills；GitHub/zip 安装与双向同步 | 首启导入、备份、云同步、deep-link 确认 | Provider 密度、当前使用状态、导入导出与危险操作确认 |
| Conductor | workspace 列表和线程，多个 coding agent；模式控制模型、reasoning、plan、fast | 复用已安装 Claude、Codex、Cursor、OpenCode 的登录 | 可复用 Skills；未把 MCP 做成独立 Agent 选择实体 | branch、files、terminal、diff；setup/run/archive scripts；login-shell 环境与 local secrets | Workspace 是执行边界；secret 仅显示本地状态；变更与审阅紧邻会话 |
| Codex app | Project、thread、worktree 管理并行 Agent；变更审阅 | 继承 Codex CLI/IDE session history 和配置 | 专门的 Skill 创建管理界面；Automation 进入 review queue | worktree 隔离，安全默认和可配置权限 | 列表用任务状态而非大卡片；Skill 管理与 Agent 运行分层 |
| Kimi Code Web | session 列表、搜索、新建、归档、导出和恢复 | provider manager、模型选择、登录独立；Web 与 CLI session 同步 | Markdown Agent、Skill 目录优先级和自动/手动调用 | working directory、文件引用、错误恢复、诊断 | 长路径可搜索可换行；失败保留恢复动作，不把认证和配置有效混为一谈 |
| Claude Squad | TUI 会话列表，新建、删除、暂停、恢复、attach | Profile 保存 program command，可运行 Claude、Codex、Gemini、Aider 等 | 无完整 Skills、Tool、MCP 设置面 | 每会话 git workspace 与 tmux；状态高度紧凑 | Profile 是启动命令模板，不等于 Agent；列表状态与快捷操作足够密集 |
## 设计结论
Agent 列表、Profile、Preset、Runtime inventory 与 Capability catalog 分开。Profile 是已保存的 AgentSpec；Preset 是可复用草稿；Runtime inventory 是只读事实；Skill 与 Tool 是 Profile 选择；MCP 只作为 Tool 来源与 transport 诊断展示。
页面优先回答三个问题：当前选了什么、现在能否启动、不能启动时下一项显式动作是什么。发现、认证、兼容性、Profile 启用和 prepare 不能合成一个绿色状态。
列表使用紧凑行显示名称、stable id、Preset 来源、Runtime、模型和 readiness。详情用单层 section 和 tab，不嵌套卡片。长 path、模型 id 与 Skill 描述允许换行并保留复制动作；不以省略号作为唯一读取方式。
## 当前实现审计
| 范围 | 状态 | 证据 |
|---|---|---|
| Profile 列表、详情编辑、Preset 草稿、readiness 阻塞 | 已有 | 当前 Agent 页面可选 `math-proof`、`source-researcher`，可编辑 endpoint、model、skills、tools、instructions 与限制 |
| Chat 起草 Agent | 已有草稿流程 | Chat 的“起草 Agent”可选 Preset 并进入可取消、可确认的表单 |
| 自然语言 orchestrator | 缺失 | #41 仍为 open；当前只能从固定 Preset 起草 |
| Tool catalog 与显式 Provisioner | 缺失 | #43 仍为 open；当前没有 prepare plan、二次确认和日志 |
| source-researcher Preset | 实现中，未独立验收 | #54 最新修复在独立分支，issue 仍 open 并等待第二次 Compose/OpenCLI QA；不得写成完成 |
| CLI discovery、MCP 来源、secret 状态、诊断、导入导出、复制/删除 | 缺失 | 当前 Agent 页面没有对应入口 |
当前桌面截图为 `research-world/web/screenshots/issue63-current-agents-desktop.png` 与 `issue63-current-chat-draft-desktop.png`；390px 截图为 `issue63-current-agents-mobile-390.png` 与 `issue63-current-chat-draft-mobile-390.png`。桌面表单可用但 Preset 与 Profile 视觉权重接近；移动端 Preset 区过长，首屏无法看到当前 Agent 关键 readiness，draft 中模型和能力落到较深滚动位置。
## 本机只读 CLI Probe
| Realm | CLI | 入口与来源 | Version | 认证事实 | Discovery 结论 |
|---|---|---|---|---|---|
| WSL PATH | Codex CLI | `~/.local/bin/codex` symlink，用户安装 | 0.149.0 | 官方 status 报告 API-key 方式已配置；未记录任何 key 内容 | executable、version、认证与现有 Adapter 可确认 |
| WSL PATH | Claude Code | `~/.local/bin/claude` symlink，用户安装 | 2.1.237 | 官方 JSON status 报告已登录、OAuth；未记录凭证 | executable、version、认证可确认，Runtime Adapter 尚未实现 |
| WSL PATH | Pi Coding Agent | 用户 NVM bin symlink，用户安装 | 0.84.2 | 对 Google、OpenAI Codex、Anthropic 的无刷新检查均报告 credentials not configured | executable、version 可确认，认证未就绪 |
| WSL PATH | Kimi Code CLI | `~/.kimi-code/bin/kimi`，用户安装 | 0.38.0 | `doctor config` 只证明配置有效；没有找到安全非交互认证 status | executable、version 可确认，认证未决，不得写 ready |
| WSL PATH | DeepSeek Harness | 用户 Volta shim | 0.1.1-rc.1 | launcher help 没有独立认证 probe | executable、version 可确认，Runtime Adapter 与认证语义未决 |
| WSL PATH | Gemini CLI | 未找到 | - | 未探测 | missing |
| WSL PATH | OpenCode | 未找到 | - | 未探测 | missing |
| Windows PATH | Claude Code | WinGet package | 未执行跨 realm 启动 | 未探测 | found in Windows realm；不能作为 WSL ready |
| Windows PATH | Kimi Code CLI | Windows 用户目录 | 未执行跨 realm 启动 | 未探测 | found in Windows realm；不能作为 WSL ready |
| Windows PATH | Codex、Pi、dsh、Gemini、OpenCode | `where.exe` 未找到 | - | 未探测 | missing in Windows PATH |
宿主为 WSL2 Ubuntu，不是容器；PATH 同时含 Linux 与 Windows 挂载目录。所有已找到的 Linux CLI 均为用户安装，没有系统安装事实。探测只使用 `command -v`/`where.exe`、官方 version/help、配置目录存在性和非敏感认证 status；未安装、更新、登录、读取 token/secret 或发起模型请求。个人绝对路径已归一为 `~`、用户 NVM、用户 Volta 或 Windows 用户目录。
OpenCLI 1.8.6 与 Chrome extension 1.0.22 只证明浏览器 Tool 和本次 WebUI QA 环境可用；它不在上表，不参与 Agent/Profile/认证 readiness，也不从安装状态推断任何 Agent Runtime 能力。
## 信息架构
### Agent 列表
顶栏提供搜索、readiness 筛选、导入和新建。行字段为 `name`、`id`、Preset 来源、Runtime、model、readiness、最近修改时间；行操作为复制、导出、删除。删除先展示引用该 Profile 的 Pipeline/Thread 数量并二次确认。
### 新建与草稿
新建入口只提供 `Preset`、`空白`、`描述目标` 三种模式。Preset 与空白立即建立未保存草稿；自然语言模式先由 orchestrator 生成 AgentSpec draft、字段级理由与未决项，用户逐项编辑后显式确认。任何模式都不得 prepare、登录、安装或启动 Agent。
### Profile 详情
固定 header 显示名称、stable id、来源、保存状态和聚合 readiness；tab 为 `Profile`、`Runtime`、`模型`、`Skills`、`Tools 与 MCP`、`诊断`。页面 footer 仅在 dirty 时出现取消与保存。
### Runtime
Runtime inventory 行展示 product、executable、version、source/path、status/reason、last checked 和 capabilities。刷新是只读操作并显式呈现 `loading`、`refreshing`、`empty`。状态全集为 `found`、`ready`、`auth-required`、`missing`、`error`、`unsupported`。
### 模型与 Endpoint
先选择 execution runtime，再选择其支持的 Endpoint 与 model；endpoint URL 默认只显示 origin，凭证只显示 `configured`、`missing`、`invalid`、`not-required`，永不显示值。reasoning、service tier 等只在 Adapter 声明 capability 后出现。
### Skills
Skill 行展示 stable id、名称、完整描述、scope、来源和 path；搜索覆盖描述与路径。Profile 仅保存 Skill id；更新来源不会静默改变已保存 Profile，保存前展示 diff。
### Tools 与 MCP
Tool 行展示 stable Tool id、名称、描述、readiness 和来源 badge；`MCP` 是来源/adapter badge，不是独立 AgentSpec 数组。OpenCLI 显示为 `browser.opencli` Tool，能力描述为真实 Chrome 浏览器审计与交互；其安装或认证不得改变 Agent CLI readiness。
### Workspace、环境与 Secret
Profile 保存 workspace policy，不保存任意宿主绝对路径。环境变量只列允许的名称、来源和状态，不展示值；secret 只显示 provider、scope、last checked 与状态。继承 login shell、WSL、Windows 与 container 来源必须可区分。
### Readiness 与诊断
聚合 readiness 分解为 Runtime、Endpoint/model、Skills、Tools、workspace 和 secrets 六组。每项给稳定 reason code、可执行下一步和最近检查时间；未知保持 unknown，不用绿色代替。诊断可复制脱敏摘要，原始 stdout/stderr、环境值与 token 不进入 UI。
### 显式 Prepare
`查看准备计划` 先生成只读 plan：目标、受控 action、版本/来源、预计文件与进程变化、权限、网络、可回滚边界。用户二次确认后才执行；日志逐步显示 queued、running、succeeded、failed、cancelled。失败保留计划和脱敏日志；Discovery、页面进入、保存 Profile 与 Chat 起草均不得触发 prepare。
## 响应式规格
桌面为 264px Agent rail + minmax detail；详情最大宽度 1180px，字段标签与值按 180px/minmax 两列。390px 将 rail 变为顶部 Agent selector，tab 横向滚动，字段单列；44px 最小点击区域。固定 footer 不能覆盖最后一个字段。
路径、model id 和 Skill 描述使用 `overflow-wrap:anywhere`；可复制字段最多三行预览并可展开。状态 badge 不隐藏；窄屏把 reason 放到下一行。表格在 760px 以下改为 definition rows，不产生页面横向滚动。
视觉沿用现有 `--surface-*`、`--text-*`、`--line-*` 与 `--state-*` token。卡片圆角不超过 8px；状态同时使用图标、文本与颜色。页面无装饰渐变、嵌套卡片或 viewport 字号缩放。
## 字段到深模块
| UI 字段/动作 | Owner | Contract | 当前缺口 |
|---|---|---|---|
| Profile id、name、instructions、runtime、endpoint、model、skills、tools、options | Agent Runtime `types`/`catalog` | AgentSpec snapshot | schema 尚无稳定 `runtime`；MCP 需归一到 Tool id |
| Preset 来源与参数 | Agent Runtime `presets` | Preset -> AgentSpec draft | 已有固定草稿；缺通用参数元数据与导入导出 |
| CLI inventory 全字段 | Agent Runtime `runtimes/discovery` | ADR 0030 `agent_clis[]` | 模块与 API 投影缺失 |
| Endpoint、model、reasoning | Agent Runtime `endpoints` | EndpointDescriptor + model catalog | 当前 readiness 粗粒度，CLI 与 Endpoint 混放 |
| Skill id、描述、scope、path | Agent Runtime `skills` | SkillDescriptor | 缺 scope、diff、刷新状态与 UI 搜索投影 |
| Tool、MCP 来源、prepare | Agent Runtime `tools` | ToolDescriptor、prepare plan/run | #43 未实现；MCP 不能进入独立 Profile 字段 |
| workspace policy | Agent Runtime `workspace` | WorkspaceDescriptor/policy | 当前只传 workspace path，缺 realm 与 policy 投影 |
| env/secret 状态 | Agent Runtime `config`/`endpoints` | redacted ConfigStatus | 缺仅状态 API 与 reason code |
| 聚合 readiness、诊断 | Agent Runtime `service` | ReadinessReport | 当前只有阻塞字符串，缺分项、时间与脱敏导出 |
| orchestrator 草稿 | Research Kernel orchestrator -> Agent Runtime validation | AgentSpec draft + rationale + unresolved | #41 未完成自然语言路径 |
| import、export、copy、delete | Agent Runtime `catalog` | AgentSpec document operations | 缺引用检查、确认和可移植格式 |
## Prototype
唯一交互原型路由为 `/prototype/agent-runtime`，实现位于 `research-world/web/src/prototype/agent-runtime/`。fixture 覆盖六种 CLI 状态、空/loading/refreshing、长 path、长 model、长 Skill 描述、secret 状态、prepare plan/log、三种草稿模式与 orchestrator 确认；fixture 不代表本机实时事实。
验收截图为 `research-world/web/screenshots/issue63-prototype-desktop.png`、`issue63-prototype-mobile-390.png`、`issue63-prototype-mobile-skills-390.png` 与 `issue63-prototype-mobile-model-390.png`。验收只证明 prototype 的布局与交互，不是 #41、#43、#54 或生产实现的独立 QA。
## Implementation Subissues
### 1. Agent CLI discovery descriptor 与 probe
范围：实现 ADR 0030 的 WSL/Linux execution realm、固定候选、隔离 probe、缓存和手动刷新；不实现安装。前端验收：Runtime tab 显示六种状态、reason、source/path、version、last checked，刷新有 loading/refreshing/empty。独立 QA：Compose 启动后只用 OpenCLI WebUI 触发刷新，核对脱敏诊断；不得调用业务 API/DB 或模型。
### 2. AgentSpec runtime 与 catalog API
范围：在 AgentSpec/ADR/schema/API 中加入稳定 execution runtime 引用，分离 CLI runtime 与 Endpoint/model，迁移不在范围内。前端验收：Profile 可选择 ready Runtime，unsupported/missing 不可保存，保存后回读一致。独立 QA：通过 WebUI 新建、刷新、重开 Profile 验证；不得将 OpenCLI 列为 Runtime。
### 3. Capability catalog 统一 Tool/MCP/Skill
范围：补齐 Skill scope/描述/path 与 Tool source/readiness；MCP 只投影为 Tool adapter source，加入 `browser.opencli` Tool。前端验收：长描述与路径可读可复制，Profile payload 只含 Skill id 与 Tool id。独立 QA：OpenCLI WebUI 检查搜索、选择、保存和回读，不读取本机 secret。
### 4. Redacted readiness 与诊断
范围：实现 Runtime、Endpoint/model、Skill、Tool、workspace、secret 分项 ReadinessReport、稳定 reason code 和脱敏导出。前端验收：unknown、blocking、ready 不互相替代；secret 仅显示状态。独立 QA：构造缺凭证、缺 Tool、probe error 三个 fixture，通过 WebUI 验证诊断与无敏感输出。
### 5. 显式 prepare plan 与 run log
范围：实现受控 CLI/Tool prepare plan、二次确认、取消与日志；页面进入、discovery、保存均禁止隐式执行。前端验收：确认前无变更，计划显示来源/权限/网络/影响，失败可重试。独立 QA：用无副作用 fixture 在 Compose WebUI 完成计划、取消、失败、成功四条路径。
### 6. Agent CRUD、Preset 与 orchestrator 草稿确认
范围：实现 Profile 搜索/筛选、copy/import/export/reference-aware delete，统一 Preset/空白/自然语言 draft；自然语言只生成待确认 AgentSpec。前端验收：三种草稿均可取消且不落库，确认后字段回读一致，删除展示引用。独立 QA：OpenCLI WebUI 覆盖 desktop 与 390px；#54 需单独 QA，不沿用本 issue 结论。
## 未决事实
Kimi Code CLI 没有确认到安全、非交互认证状态命令；不能把配置有效写成已认证。DeepSeek Harness 的认证边界与 Agent Runtime Adapter 尚未定义。Conductor 没有公开源码许可。Multica 自定义 License 的附加商业限制需要法务判断后才能复用代码；本原型仅提炼交互模式。#54 仍等待独立 QA，任何页面标记都应为实现中。
