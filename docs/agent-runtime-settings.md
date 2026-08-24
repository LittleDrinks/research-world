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
    url: https://github.com/multica-ai/multica/tree/v0.4.32
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
    version: 0.82.0
    url: https://www.conductor.build/changelog/0.82.0-conductor-mcp
    product_url: https://www.conductor.build/
    screenshot_source: https://www.conductor.build/
    screenshot: research-world/web/screenshots/issue63-competitor-conductor.png
    evidence_boundary: version comes from the fixed changelog entry; the homepage screenshot proves only the visible product shell captured on 2026-08-24
    license: proprietary product interface; screenshot retained as research evidence only
  - id: codex-app
    title: ChatGPT desktop app
    product: ChatGPT desktop app with Codex
    version: official documentation accessed 2026-08-24; Codex CLI repository v0.149.1
    url: https://learn.chatgpt.com/docs/app
    worktrees: https://learn.chatgpt.com/docs/environments/git-worktrees
    skills: https://learn.chatgpt.com/docs/build-skills
    repository: https://github.com/openai/codex
    screenshot_source: https://openai.com/index/introducing-the-codex-app/
    screenshot: research-world/web/screenshots/issue63-competitor-codex-app.png
    evidence_boundary: screenshot is an official launch-page capture, not a locally reproduced session; interaction claims are limited to current official documentation
    license: Apache-2.0 covers Codex CLI repository code, not the app interface or OpenAI assets
  - id: kimi-code
    title: Kimi Code CLI
    product: Kimi Code CLI
    version: '@moonshot-ai/kimi-code@0.38.0'
    url: https://github.com/MoonshotAI/kimi-code
    release: https://github.com/MoonshotAI/kimi-code/releases/tag/%40moonshot-ai%2Fkimi-code%400.38.0
    documentation: https://moonshotai.github.io/kimi-code/en/
    screenshot: null
    evidence_boundary: repository README and fixed release only; no Web UI screenshot or kimi-cli documentation is attributed to this generation
    license: MIT
  - id: kimi-cli
    title: Kimi CLI Web UI
    product: Kimi CLI
    version: 1.49.0
    url: https://github.com/MoonshotAI/kimi-cli
    release: https://github.com/MoonshotAI/kimi-cli/releases/tag/1.49.0
    documentation: https://moonshotai.github.io/kimi-cli/en/reference/kimi-web.html
    screenshot_source: https://moonshotai.github.io/kimi-cli/en/reference/kimi-web.html
    screenshot: research-world/web/screenshots/issue63-competitor-kimi-cli-web.png
    evidence_boundary: repository README marks migration to kimi-code and gradual wind-down; Web claims and screenshot apply only to kimi-cli 1.49.x
    license: Apache-2.0 for repository code; documentation and product assets retained as research evidence only
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
    url: https://github.com/LittleDrinks/ai4sci/issues/41
  - id: issue-43
    title: Tool Runtime and explicit provisioner
    url: https://github.com/LittleDrinks/ai4sci/issues/43
  - id: issue-54
    title: Source researcher preset
    url: https://github.com/LittleDrinks/ai4sci/issues/54
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
| Conductor 0.82.0 | workspace 列表和线程，并行运行多种 coding agent | 官方 docs 列出 Claude、Codex、Cursor、OpenCode harness | 0.82.0 changelog 增加 Conductor MCP；不把 MCP 当 Agent Profile | 每个 task 独立 workspace、branch、files、terminal、diff 与 review path | Workspace 是执行边界；变更与审阅紧邻会话 |
| ChatGPT desktop app with Codex | 当前官方 docs 支持 project、chat、folder 与 Codex 入口 | 官方 docs 分离本地、worktree 与 cloud environment | 当前官方 docs 单独定义 Skills 与 Plugins | worktree 用于并行隔离；权限与 sandbox 独立配置 | 只采用当前 docs 可直接证明的层次；旧 launch screenshot 不作为实测交互证据 |
| Kimi Code CLI 0.38.x | 官方 README 证明终端 TUI、session 与 subagent，不归因 Web UI | Kimi Code OAuth 或 Moonshot API key；ACP 独立入口 | plugin marketplace 提供 Skill、MCP 与 data source | single-binary 安装、workspace 与 lifecycle hooks | 新一代事实只来自 `kimi-code` 仓库/0.38.x release；无 Web screenshot |
| Kimi CLI 1.49.x | 旧 Web UI 提供 session 列表、创建与恢复 | provider/model/login 属旧 Python 实现；配置有效不等于认证 | 旧仓库支持 MCP 与 Agent/Skill 目录 | README 明示向 Kimi Code CLI 迁移并逐步停止维护 | Web 文档与截图只证明旧 `kimi-cli`，不得转用于 `kimi-code` |
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
以下 host inventory 是 `2026-08-24T14:23:05Z` 的点时 probe 结果，不是产品固定版本或长期保证。Codex version argv 固定为 `['codex', '--version']`；Kimi Code version argv 固定为 `['kimi', '--version']`，不登记或执行 Kimi 认证 probe，不运行 `doctor`、读取配置或访问 secret。
| Realm | CLI | `path` | `resolved_path` | `source` | Version | 认证事实与结论 |
|---|---|---|---|---|---|---|
| `wsl:ubuntu` | Codex CLI | `~/.local/bin/codex` | `~/.codex/packages/standalone/releases/0.149.1-x86_64-unknown-linux-musl/bin/codex` | `installer` | 0.149.1 | 当前固定 version probe 与既有安全 status 事实支持 ready；probe 输出解析后丢弃 |
| `wsl:ubuntu` | Claude Code | `~/.local/bin/claude` | `~/.local/share/claude/versions/2.1.237` | `installer` | 2.1.237 | 官方 JSON status 报告 OAuth 已登录；Runtime Adapter 未实现，unsupported |
| `wsl:ubuntu` | Pi Coding Agent | `~/.nvm/versions/node/v24.14.0/bin/pi` | 用户 NVM package 的 `dist/cli.js` | `npm` | 0.84.2 | 当前版本无已确认安全认证 status argv；found/`auth_probe_unavailable` |
| `wsl:ubuntu` | Kimi Code CLI | `~/.kimi-code/bin/kimi` | 同入口 | `installer` | 0.38.0 | `doctor config` 只证明配置语法有效；认证 unknown，found/`auth_probe_unavailable` |
| `wsl:ubuntu` | DeepSeek Harness | `~/.volta/bin/dsh` | Homebrew Volta shim | `npm` | 0.1.1-rc.1 | 无独立认证 probe 且无 Runtime Adapter，unsupported/`adapter_unavailable` |
| `wsl:ubuntu` | Gemini CLI、OpenCode | null | null | `path` | null | missing/`not_on_path` |
| `windows:host` | Claude Code | `C:\\nvm4w\\nodejs\\claude.cmd` | NVM npm package `@anthropic-ai/claude-code/bin/claude.exe` | `npm` | 2.1.160 | Windows PATH 实际命中 npm shim；未探测认证，found/`realm_mismatch` |
| `windows:host` | Pi Coding Agent | `C:\\nvm4w\\nodejs\\pi.cmd` | NVM npm package `@earendil-works/pi-coding-agent/dist/cli.js` | `npm` | 0.84.2 | 未探测认证，found/`realm_mismatch` |
| `windows:host` | Kimi Code CLI | Windows 用户目录 `.kimi-code\\bin\\kimi.exe` | 同入口 | `installer` | 0.38.0 | 未探测认证，found/`realm_mismatch` |
| `windows:host` | Codex、dsh、Gemini、OpenCode | null | null | `path` | null | missing/`not_on_path` |
Windows 另有 WinGet Claude Code 2.1.150，但不是当前 `claude` 命令的首选 PATH 入口，不能覆盖 npm shim 2.1.160 descriptor。宿主为 WSL2 Ubuntu；WSL 与 Windows 独立判定。probe 仅使用 `command -v`/`where.exe`、路径解析、`--version` 与官方非交互 status；未安装、更新、登录、刷新认证、读取 token/secret 或发起模型请求。个人绝对路径已脱敏。
OpenCLI 1.8.6 与 Chrome extension 1.0.22 只证明 `browser.opencli` Tool 和 WebUI QA 环境；它不进入上述 inventory、runtime selection、version/auth/login/readiness/prepare，也不推断任何 Agent 可用性。
## 信息架构
### Agent 列表
顶栏提供搜索、readiness 筛选、导入和新建。行字段为 `name`、`id`、Preset 来源、Runtime、model、Skills/Tools 数量、readiness、最近修改时间；行操作为选择编辑、复制、导出、删除。删除先展示引用该 Profile 的 Pipeline/Thread 数量并二次确认。
### 新建与草稿
新建入口只提供 `Preset`、`空白`、`描述目标` 三种模式。三种结果共享完整可编辑 AgentSpec 表单：name/id、runtime、Endpoint、model、Instructions、Skills、Tools、MCP 来源、reasoning、sandbox 与 workspace policy；同时展示字段级推荐理由、readiness 与 unresolved。空白模式不预填 runtime、Endpoint、model、Skill、Tool 或 MCP 能力。自然语言模式消费 #41 orchestrator 草稿，不在此范围实现模型调用。缺 runtime/Endpoint/model、secret unknown/missing/invalid 或能力未就绪时不可保存为 ready。任何模式都不得 prepare、登录、安装或启动 Agent。
### Profile 详情
固定 header 显示名称、stable id、来源、保存状态和聚合 readiness；tab 为 `Profile`、`Runtime`、`模型`、`Skills`、`Tools 与 MCP`、`诊断`。编辑工作副本与最后保存 snapshot 独立，dirty 由两者显式深比较；页面 footer 仅在 dirty 时出现 Cancel 与 Save。Cancel 恢复最后保存 snapshot，Save 写入新 snapshot 后清除 dirty。
### Runtime
Runtime inventory 行展示 product、realm、executable、version、source、path、resolved path、status/reason、last checked 和 capabilities。刷新是只读操作并显式呈现 `loading`、`refreshing`、`empty`。状态全集为 `found`、`ready`、`auth-required`、`missing`、`error`、`unsupported`。
`runtimeKey(id, realm) = JSON.stringify([id, realm])` 是 runtime option value、React key 与选择回读 key。选择和 Profile snapshot 同时保存 `id`、`realm`；禁止只按 `id` 查找或回退到第一个 realm。
### 模型与 Endpoint
先选择 execution runtime，再选择其支持的 Endpoint 与 model；endpoint URL 默认只显示 origin，凭证只显示 `configured`、`missing`、`invalid`、`not-required`，永不显示值。reasoning、service tier 等只在 Adapter 声明 capability 后出现。
### Skills
Skill 行展示 stable id、名称、完整描述、scope、来源和 path；搜索覆盖描述与路径。Profile 仅保存 Skill id；更新来源不会静默改变已保存 Profile，保存前展示 diff。
### Tools 与 MCP
Tool 行展示 stable Tool id、名称、描述、readiness 和来源 badge；`MCP` 是来源/adapter badge，不是独立 AgentSpec 数组。OpenCLI 显示为 `browser.opencli` Tool，能力描述为真实 Chrome 浏览器审计与交互；其安装或认证不得改变 Agent CLI readiness。
### Workspace、环境与 Secret
Profile 保存 workspace policy，不保存任意宿主绝对路径。环境变量只列允许的名称、来源和状态，不展示值；secret 只显示 provider、scope、last checked 与状态。继承 login shell、WSL、Windows 与 container 来源必须可区分。
### Readiness 与诊断
聚合 readiness 分解为 Runtime、Endpoint/model、Skills、Tools、workspace 和 secrets 六组。secret `configured`、`not-required` 映射为 `ready`，`missing`、`invalid` 映射为 `blocked`，仅 `unknown` 映射为 `unknown`；缺失或无效的 reason code 可见并阻止保存与 Launch。诊断可复制脱敏摘要，原始 stdout/stderr、环境值与 token 不进入 UI。
### 显式 Prepare
CLI 的 `查看准备计划` 先生成只读 plan：目标、受控 action、版本/来源、预计文件与进程变化、权限、网络、可回滚边界。状态机为 `plan -> confirm -> running -> succeeded | failed | cancelled`；failed/cancelled 可 retry，重试追加日志而不覆盖既有记录。Tool prepare 消费 #43，不进入 CLI prepare。Discovery、页面进入、保存 Profile 与 Chat 起草均不得触发 prepare。
## 响应式规格
桌面为 264px Agent rail + minmax detail；详情最大宽度 1180px，字段标签与值按 180px/minmax 两列。390px 将 rail 变为顶部 Agent selector，tab 横向滚动，字段单列；44px 最小点击区域。固定 footer 不能覆盖最后一个字段。
路径、model id 和 Skill 描述使用 `overflow-wrap:anywhere`；可复制字段最多三行预览并可展开。状态 badge 不隐藏；窄屏把 reason 放到下一行。表格在 760px 以下改为 definition rows，不产生页面横向滚动。
视觉沿用现有 `--surface-*`、`--text-*`、`--line-*` 与 `--state-*` token。卡片圆角不超过 8px；状态同时使用图标、文本与颜色。页面无装饰渐变、嵌套卡片或 viewport 字号缩放。
## 字段到深模块
| UI 字段/动作 | Owner | Contract | 当前缺口 |
|---|---|---|---|
| Profile id、name、instructions、runtime、endpoint、model、skills、tools、options | Agent Runtime `types`/`catalog` | AgentSpec snapshot | schema 尚无稳定 `runtime`；MCP 需归一到 Tool id |
| Preset 来源与参数 | Agent Runtime `presets` | Preset -> AgentSpec draft | 已有固定草稿；缺通用参数元数据与导入导出 |
| CLI inventory 全字段 | Agent Runtime `runtimes/discovery` | ADR 0030 `(id, realm)` descriptor | 模块与 API 投影缺失 |
| Endpoint、model、reasoning | Agent Runtime `endpoints` | EndpointDescriptor + model catalog | 当前 readiness 粗粒度，CLI 与 Endpoint 混放 |
| Skill id、描述、scope、path | Agent Runtime `skills` | SkillDescriptor | 缺 scope、diff、刷新状态与 UI 搜索投影 |
| Tool、MCP 来源 | Agent Runtime `tools` | #43 ToolDescriptor；MCP 为 adapter source | #43 未实现；MCP 不能进入独立 Profile 字段 |
| workspace policy | Agent Runtime `workspace` | WorkspaceDescriptor/policy | 当前只传 workspace path，缺 realm 与 policy 投影 |
| env/secret 状态 | Agent Runtime `config`/`endpoints` | redacted ConfigStatus | 缺仅状态 API 与 reason code |
| 聚合 readiness、诊断 | Agent Runtime `service` | ReadinessReport | 当前只有阻塞字符串，缺分项、时间与脱敏导出 |
| orchestrator 草稿 | Research Kernel orchestrator -> Agent Runtime validation | AgentSpec draft + rationale + unresolved | #41 未完成自然语言路径 |
| import、export、copy、delete | Agent Runtime `catalog` | AgentSpec document operations | 缺引用检查、确认和可移植格式 |
## Prototype
唯一交互原型路由为 `/prototype/agent-runtime`，实现位于 `research-world/web/src/prototype/agent-runtime/`。fixture 同时包含 WSL/Windows Codex descriptor，并覆盖 Profile snapshot dirty/Cancel/Save、三种完整草稿、secret missing/invalid 阻断、六种 CLI 状态、loading/refreshing/empty、prepare 全状态与日志保留，以及长 path/model/Skill；fixture 不代表本机实时事实。
可复现验收为 `research-world/web/tests/issue63-agent-runtime-prototype.spec.js`。截图为 `research-world/web/screenshots/issue63-prototype-desktop.png`、`issue63-prototype-mobile-390.png`、`issue63-prototype-mobile-skills-390.png` 与 `issue63-prototype-mobile-model-390.png`。验收只证明 prototype，不是 #41、#43、#54 或生产实现的独立 QA。
## Implementation Subissues
依赖顺序：1 -> 2 -> 3 -> 4；5 依赖 1/4；6 依赖 2/3/4 并消费 #41/#54。#43 是 3 的 Tool catalog 上游，不由任何草案重做。
### 1. Discovery contract 与双 realm probe
范围：实现 ADR 0030 descriptor、固定 argv、WSL/Windows realm、隔离错误、60 秒 cache 与手动刷新；不实现 AgentSpec、安装或 prepare。前端可观察验收：Runtime inventory 展示 `(id, realm)`、path/resolved path/source、六态与 loading/refreshing/empty。独立 QA：Compose WebUI 触发只读刷新并与脱敏 host probe 对照；确认 Profile snapshot 未变化，不调用模型。
### 2. AgentSpec runtime binding
依赖：1。范围：schema/types/validate/catalog 增加稳定 `(runtime id, realm)` 绑定，Endpoint/model 保持独立；不实现 discovery、Profile CRUD 或兼容迁移。前端可观察验收：只可选择当前 realm ready runtime，保存与回读绑定一致，跨 realm/missing/unsupported 阻断。独立 QA：WebUI 新建、保存、重开并检查 API 投影与阻断诊断。
### 3. Skill 与 MCP projection
依赖：2、#43 Tool catalog。范围：补齐 Skill scope/description/path；消费 #43 Tool descriptor，把 MCP 作为 Tool adapter source 投影，Profile 仍只保存 Skill/Tool id；不实现 Tool lifecycle、transport 或 provision。前端可观察验收：搜索、选择、移除、理由、unresolved、长字段和 MCP badge 可见，`browser.opencli` 只在 Tool catalog。独立 QA：WebUI 保存回读 payload，不出现 MCP 数组、transport、secret 或 OpenCLI runtime。
### 4. Readiness diagnostics
依赖：1/2/3。范围：投影 Runtime、Endpoint/model、Skill、Tool、workspace、secret 六组诊断、稳定 reason code、检查时间与脱敏导出；不修改认证或准备资源。前端可观察验收：ready/unknown/blocking 独立，Kimi config valid 不成为 authenticated，secret 只显示状态。独立 QA：用缺 secret、缺 Tool、probe error、realm mismatch fixture 验证阻断与导出内容。
### 5. CLI-only prepare
依赖：1/4。范围：仅实现 Agent CLI plan/confirm/run/cancel/retry 与 append-only 脱敏日志；Tool provision 完整消费 #43，不进入本范围。前端可观察验收：plan、confirm、running、succeeded、failed、cancelled、retry 全可见，失败/取消日志保留；页面进入、discovery、Profile 保存零副作用。独立 QA：无副作用 CLI fixture 跑成功、失败、取消与重试，核对目标 realm 和日志保留。
### 6. Pure Profile CRUD
依赖：2/3/4、#41 Preset/orchestrator 草稿、#54 source-researcher。范围：Profile list/create/edit/copy/delete/import/export/reference check 与 snapshot persistence；只消费上游完整草稿，不定义 Preset、调用 orchestrator、实现 source researcher 或 Tool provision。前端可观察验收：列表显示 Preset/model/runtime/Skills/Tools/readiness，三类上游草稿可编辑并在 ready 后保存，复制独立、删除可确认。独立 QA：OpenCLI 驱动 desktop/390 CRUD 和三草稿回读；#41/#54 仍各自独立验收。
## 未决事实
Kimi Code CLI 0.38.0 没有确认到安全、非交互认证状态命令；`doctor config` 成功不能写成已认证。DeepSeek Harness 的认证边界与 Agent Runtime Adapter 尚未定义。Conductor 没有公开源码许可。Multica 自定义 License 的附加商业限制需要法务判断后才能复用代码；prototype 只提炼交互模式。#41 自然语言 orchestrator、#43 Tool provision 与 #54 独立 QA 仍未完成。
