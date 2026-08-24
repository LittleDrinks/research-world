---
sources:
  - id: issue-64
    title: 调研 Agent Harness 轨迹界面并设计 Trace 页面重构
    url: https://github.com/LittleDrinks/ai4sci/issues/64
    accessed: 2026-08-24
  - id: issue-65
    title: Chat 研究运行入口改为跳转轨迹页，移除内联浮层
    url: https://github.com/LittleDrinks/ai4sci/issues/65
    accessed: 2026-08-24
  - id: deepseek-harness
    title: DeepSeek Harness official repository
    url: https://github.com/deepseek-ai/deepseek-harness/tree/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-trajectory
    title: DeepSeek Harness Trajectory UI
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/client/ui-trajectory/README.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-tool
    title: DeepSeek Harness Tool UI
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/client/ui-tool/README.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-deliverables
    title: DeepSeek Harness Deliverables UI
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/client/ui-deliverables/README.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-subagents
    title: DeepSeek Harness Subagents UI
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/client/ui-subagents/README.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-guide
    title: DeepSeek Harness user guide
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/user/guide/index.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: deepseek-providers
    title: DeepSeek Harness provider settings
    url: https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/user/guide/providers.md
    version: dsh-v0.1.1-rc.2
    accessed: 2026-08-24
  - id: langsmith-traces
    title: LangSmith view traces
    url: https://docs.langchain.com/langsmith/view-traces
    version: hosted UI
    accessed: 2026-08-24
  - id: langsmith-cost
    title: LangSmith cost tracking
    url: https://docs.langchain.com/langsmith/cost-tracking
    version: hosted UI
    accessed: 2026-08-24
  - id: langsmith-manage
    title: LangSmith manage a trace
    url: https://docs.langchain.com/langsmith/manage-trace
    version: hosted UI
    accessed: 2026-08-24
  - id: langsmith-search
    title: LangSmith trace query syntax
    url: https://docs.langchain.com/langsmith/trace-query-syntax
    version: hosted UI
    accessed: 2026-08-24
  - id: langsmith-privacy
    title: LangSmith trace masking
    url: https://docs.langchain.com/langsmith/mask-inputs-outputs
    version: hosted UI
    accessed: 2026-08-24
  - id: phoenix-traces
    title: Phoenix tracing
    url: https://arize.com/docs/phoenix/learn/tracing
    version: current documentation
    accessed: 2026-08-24
  - id: phoenix-cost
    title: Phoenix cost tracking
    url: https://arize.com/docs/phoenix/tracing/how-to-tracing/cost-tracking
    version: current documentation
    accessed: 2026-08-24
  - id: phoenix-query
    title: Phoenix extract data from spans
    url: https://arize.com/docs/phoenix/tracing/how-to-tracing/extract-data-from-spans
    version: current documentation
    accessed: 2026-08-24
  - id: phoenix-sessions
    title: Phoenix sessions
    url: https://arize.com/docs/phoenix/tracing/how-to-tracing/sessions
    version: current documentation
    accessed: 2026-08-24
  - id: phoenix-redaction
    title: Phoenix custom span processor
    url: https://arize.com/docs/phoenix/tracing/how-to-tracing/advanced/modifying-spans
    version: current documentation
    accessed: 2026-08-24
  - id: temporal-ui
    title: Temporal Web UI
    url: https://docs.temporal.io/web-ui
    version: v2.53.3
    accessed: 2026-08-24
  - id: temporal-release
    title: Temporal UI v2.53.3
    url: https://github.com/temporalio/ui/releases/tag/v2.53.3
    version: v2.53.3
    accessed: 2026-08-24
  - id: temporal-history-test
    title: Temporal UI event history integration tests
    url: https://github.com/temporalio/ui/blob/v2.53.3/tests/integration/workflow-event-history.spec.ts
    version: v2.53.3
    accessed: 2026-08-24
  - id: temporal-timeline-test
    title: Temporal UI timeline integration tests
    url: https://github.com/temporalio/ui/blob/v2.53.3/tests/integration/workflow-timeline.spec.ts
    version: v2.53.3
    accessed: 2026-08-24
  - id: current-trace-ui
    title: Research World Trace implementation
    path: research-world/web/src/pages/TracesPage.jsx
    version: issue-64 parent
    accessed: 2026-08-24
  - id: current-runtime-trace
    title: Agent Runtime Trace implementation
    path: runtime/runtime/trace.py
    version: issue-64 parent
    accessed: 2026-08-24
  - id: current-runtime-service
    title: Agent Runtime service
    path: runtime/runtime/service.py
    version: issue-64 parent
    accessed: 2026-08-24
  - id: current-kernel-schema
    title: Research Kernel schema
    path: research-world/server/db.py
    version: issue-64 parent
    accessed: 2026-08-24
  - id: current-opencli-desktop
    title: Current Trace complete state desktop screenshot
    path: docs/adr/assets/0029-trace-ui/current/trace-desktop.png
    capture: OpenCLI Chrome 1440x900
    accessed: 2026-08-24
  - id: current-opencli-mobile
    title: Current Trace complete state mobile screenshot
    path: docs/adr/assets/0029-trace-ui/current/trace-mobile-390.png
    capture: OpenCLI Chrome 390x844
    accessed: 2026-08-24
  - id: current-opencli-failed
    title: Current Trace failed state desktop screenshot
    path: docs/adr/assets/0029-trace-ui/current/trace-failed-desktop.png
    capture: OpenCLI Chrome 1440x900
    accessed: 2026-08-24
  - id: prototype-opencli-desktop
    title: Trace prototype desktop
    path: docs/adr/assets/0029-trace-ui/prototype/trace-desktop-opencli.png
    capture: OpenCLI Chrome 1440x900
    accessed: 2026-08-24
  - id: prototype-opencli-mobile
    title: Trace prototype mobile
    path: docs/adr/assets/0029-trace-ui/prototype/trace-mobile-390-opencli.png
    capture: OpenCLI Chrome 390x844
    accessed: 2026-08-24
  - id: prototype-opencli-inspector
    title: Trace prototype mobile inspector
    path: docs/adr/assets/0029-trace-ui/prototype/trace-mobile-inspector-390-opencli.png
    capture: OpenCLI Chrome 390x844 after Tool row selection
    accessed: 2026-08-24
  - id: prototype-opencli-diff
    title: Trace prototype mobile diff
    path: docs/adr/assets/0029-trace-ui/prototype/trace-mobile-diff-390-opencli.png
    capture: OpenCLI Chrome 390x844 after Diff tab selection
    accessed: 2026-08-24
  - id: prototype-playwright-desktop
    title: Trace prototype desktop geometry check
    path: docs/adr/assets/0029-trace-ui/prototype/trace-desktop-playwright.png
    capture: Playwright Chromium 1440x900
    accessed: 2026-08-24
  - id: prototype-playwright-mobile
    title: Trace prototype mobile geometry check
    path: docs/adr/assets/0029-trace-ui/prototype/trace-mobile-390-playwright.png
    capture: Playwright Chromium 390x844
    accessed: 2026-08-24
  - id: prototype-playwright-inspector
    title: Trace prototype mobile inspector geometry check
    path: docs/adr/assets/0029-trace-ui/prototype/trace-mobile-inspector-390-playwright.png
    capture: Playwright Chromium 390x844 after Tool row selection
    accessed: 2026-08-24
---
# Trace 页面
## 决策
Trace 页面采用“运行摘要 + 因果时间轴 + 事件检查器”三层结构。Research Kernel 提供 Pipeline run、Stage、Step、Admission、Review、Artifact 与 lineage 投影；Agent Runtime 提供 Session、Turn、模型事件与 Tool I/O。页面组合两个投影，不复制事实、不把 Runtime 事件写回 Kernel。
运行列表回答“哪个 run 值得看”，运行摘要回答“发生了什么”，时间轴回答“何时、由谁、因何发生”，检查器回答“具体输入输出是什么”。默认只展开异常、当前执行路径与用户选中项；原始 JSON 是检查器视图，不是主导航。
Chat composer 只保留恒定高度的“研究运行 N”入口。入口携带 Project、Thread 与原 thread URL 进入独立 Trace 页面；Trace 按 Project/Thread 显示恰好关联的 Pipeline runs，并提供返回原对话。composer 上方不渲染 run panel、popover、list 或详情组件。
`completed`、`failed`、`paused`、`waiting_human` 与 `running` 沿用 Pipeline run 状态；Runtime `cancelled` 只用于 Turn。Run 级 cancelled 在 Kernel 支持取消并持久化前显示为不可用状态，不由前端推断。
## DeepSeek Harness 消歧
唯一可确认对象是 DeepSeek 官方 GitHub 组织 `deepseek-ai` 下的 `deepseek-harness`，仓库主页指向 DeepSeek 官方域名，Web 包直接包含 Trajectory、Tool、Deliverables 与 Subagents UI。核验版本为 `dsh-v0.1.1-rc.2`、commit `b150a551b8d465e31e418e1b2eaf5e79bbb7d28e`。
“DeepSeek Harness 界面”对应该仓库 Web 应用中的 Trajectory UI，不对应第三方同名仓库。官方仓库、官方域名与包边界三项证据一致，没有需要并列保留的候选。受 Compose-only 约束，未启动该仓库；界面结论来自固定 commit 的官方 README、源码和测试，不声称实机操作。
## 来源矩阵
| 产品 | 类型 | 版本/访问日 | 页面来源 | 实际操作/截图 |
|---|---|---|---|---|
| DeepSeek Harness | coding agent harness | `dsh-v0.1.1-rc.2` / 2026-08-24 | `deepseek-*` 固定 commit 的官方仓库文档、源码、测试 | 未启动；未复用截图 |
| LangSmith | agent trace / hosted observability | hosted UI / 2026-08-24 | `langsmith-*` 官方文档 | 未登录；官方页面图文，不复用截图 |
| Phoenix | agent trace / OSS observability | current docs / 2026-08-24 | `phoenix-*` 官方文档 | 未启动；官方页面图文，不复用截图 |
| Temporal UI | workflow/run observability | `v2.53.3` / 2026-08-24 | `temporal-*` 官方文档、release、固定 tag 测试 | 未启动；未复用截图 |
| Research World | Deep Research Kernel + Agent Runtime | issue-64 parent / 2026-08-24 | `current-*` 本地实现 | OpenCLI 真实 Chrome；三张本地截图 |
## 竞品拆解
### 导航与首屏
| 产品 | 导航 | 首屏信息 | 结构视图 |
|---|---|---|---|
| DeepSeek Harness | Session 内 Trajectory，行选择后就地检查；Subagents 可切换后代与同级 | Turn 边界、Step 标记、事件类型、事件序号、运行态 | 事件账本 + 固定 Overview timing；Subagents 独立 lineage 树 |
| LangSmith | Project 的 Threads/Traces/Runs，选中后侧栏保持上下文 | conversation、输入输出、reasoning、Tool、subagent、token/cost/model | Messages、Turns、Details；child run 嵌套，parallel Tool 分组 |
| Phoenix | Project traces、Sessions、span 详情 | latency、status、token/cost、模型、span 属性 | trace/span 父子树；Session 为聊天式时序 |
| Temporal UI | Workflow 列表进入 execution；History/Workers/Relationships/Pending/Call Stack/Queries/Metadata | status、start/close/duration、Workflow/Run ID、task queue、parent、history size | Timeline、All、Compact、JSON；Relationships 父子树 |
结论：首屏必须同时保留“运行健康度”和“当前选择内容”，不能要求用户从顶层逐层盲开。父子树表达因果，时间条表达并行；二者不是可互换的装饰视图。
### 内容与折叠
| 产品 | 折叠 | Prompt/Response/Thinking | Tool I/O、文件与 Artifact |
|---|---|---|---|
| DeepSeek Harness | Turn 粗分隔、事件行折叠、只加载当前窗口 | User/Assistant 可选；token、Input/Output/Timing 在检查器；运行中不伪造 duration | ToolCallTree 递归 subcall；terminal/read/diff/search/web 专用渲染；成功写入文件形成 deliverable chips |
| LangSmith | Turn card 展开/折叠；thought 默认折叠；subagent 嵌套返回 | Messages/Turns/Details 分层，Details 保留 input/output/error/metadata | Tool message 自动展开；child run 保持上下文；无通用代码文件交付物语义 |
| Phoenix | span 树折叠，选中 span 看属性 | LLM span 输入输出和属性；provider 数据按 OpenTelemetry 语义 | Tool span 作为子 span；Artifact 与文件 diff 不是产品核心语义 |
| Temporal UI | event 展开；Compact 逻辑分组；JSON 独立 | Workflow input/result，无模型 thinking 语义 | Activity input/result；无模型 Tool、文件 diff、Artifact 语义 |
结论：Research World 复用 Runtime 的 Session/Turn/Tool call 与 Kernel Artifact，不引入新的执行层级。Markdown、JSON、diff、终端输出按内容类型选择 renderer；未知类型回退为纯文本和原始 JSON。
### 指标、失败与操作
| 产品 | 状态/耗时/token/cost/model | 错误/重试 | 搜索/筛选 | 复制/导出/实时 |
|---|---|---|---|---|
| DeepSeek Harness | selected event token/duration；Overview 支持 actual/duration/sequence、TTFT/decoding；运行中 duration 留空 | Tool 状态区分 running/success/fail/interrupted；旧记录加载与 tail follow | 当前已加载窗口搜索/折叠 | follow tail；用户上滚后暂停；选择内容可复制，缺少稳定深链 |
| LangSmith | run timing、token、cost、model；父级聚合 | error 位于 Details；可并排比较 trace | query language 覆盖时间、token、error、metadata、文本 | run link、share、compare、logs；导出由 API/SDK 提供 |
| Phoenix | span/trace/session/project latency、token、cost、model/provider | error span 沿父子树定位 | UI filter bar 与 Python 表达式；可导出 dataframe | span 查询导出；采集流更新 |
| Temporal UI | status、start/close/duration、history size、attempt/retry 属性 | 失败 event 展开；Task Failures saved view；支持 reset/cancel/terminate | Search Attributes、filter builder、raw query、saved views | Run ID 复制；完整 History JSON 下载；运行详情刷新 |
结论：指标只在事实源存在时显示。Duration 由相邻事实时间戳派生；token 可聚合；cost、retry attempt 和 Run 级取消均不可由现有事实可靠推断，显示“未记录”并进入独立 schema/API subissue。
### 隐私与响应式
| 产品 | 脱敏 | 桌面 | 移动 |
|---|---|---|---|
| DeepSeek Harness | Provider key write-only、显示 redacted | 账本与检查器并置，Overview 固定 | responsive scroller 给 composer 留空间；长行独立滚动 |
| LangSmith | SDK 可隐藏/变换 input、output、metadata，支持正则匿名化与禁用采集 | 多视图和侧栏适合宽屏 | 官方资料未给出可验收的 390px 契约 |
| Phoenix | client span processor 可在发送前删除、修改或遮蔽 span | 树、表、详情协同 | 官方资料未给出可验收的 390px 契约 |
| Temporal UI | Codec Server 解码受保护 payload | workflow 元数据、tab、详情 | 官方资料未给出可验收的 390px 契约 |
结论：秘密在写 Trace 前移除，UI 不能把 CSS 遮挡当脱敏。每个隐藏内容显示“已脱敏”标记；没有标记时不声称安全。桌面三栏，390px 只保留一条主轴，运行列表进入抽屉，检查器进入全宽 sheet，所有代码内容横向滚动。
## 当前 WebUI 审计
### 环境与路径
运行中的 `http://127.0.0.1:8095` 由既有 Compose 服务提供，未重启。OpenCLI 路径为 `/projects` → `Q49 行星轨道稳定性` → `/map` → `轨迹` → `/traces/run%3A6c9d9d0d1a3b7d0d0f5b92b8`。complete run 为 `run:6c9d9d0d1a3b7d0d0f5b92b8`；failed run 通过左侧运行列表进入 `/traces/run%3A0443196fc76402d8b5cf9c2b`。
### 可见字段
| 层级 | 当前可见 |
|---|---|
| Run | pipeline name/id、node 短 id、当前 stage、created_at、status、payload.error、event count |
| Stage | id、type、agent/tool、推导 status |
| Step | ordinal、payload command/summary/title、status、raw payload/output JSON |
| Session | 短 session id、actor、model、status |
| Turn | 序号、status、Tool 次数、prompt text、output |
| Event | model response raw JSON、Tool name/arguments/result、error |
complete run 首屏为“规划与验证”、节点 `6038aad`、当前 stage `complete`、26 events；展开 plan 后可见 planner、`gpt-5.6-sol`、完整中文 prompt 与原始 JSON response。execute 展开后有 3 个执行 Step。failed run 首屏只增加 `Connection closed`，没有失败事件定位或错误分类。
### 缺口
1. 树层级正确但首屏没有 duration、token 汇总、model 汇总、Session 数、Tool 数、错误位置和完成进度，运行列表只能靠短 id 与状态辨认。
2. Stage、Session、Turn、Event 都用同形缩进；并行、父子 Session 与 Kernel lineage 无视觉区分，时间与因果不可扫读。
3. 长 prompt、shell command、JSON 与 output 直接进入纵向树，单个节点支配页面；没有 Markdown、JSON tree、diff、终端专用视图。
4. 没有搜索、类型筛选、仅异常、全部展开/折叠、复制稳定 id、深链、导出、Artifact、Admission、Review 或 node 返回入口。
5. Bootstrap 每 5 秒整体轮询；Session inspect 只在 Session id 列表变化时读取。运行中 Session 的新增事件不会持续更新；一次读取失败显示“会话不可用”，没有局部重试。
6. failed 首屏把自由文本错误放在 header，无法跳到失败事件、复制上下文或识别是否曾重试。
7. 390px 下左侧导航残留窄条，主标题左侧裁切，Stage meta 截断；桌面实屏出现 `Failed to fetch` toast，覆盖运行内容且不指明失败请求。
## 用户任务
1. 从项目运行列表在 10 秒内找到正在运行、等待人工处理或失败的 run。
2. 从 Chat 的紧凑入口进入当前 Project/Thread 的关联 runs，并返回同一 thread URL。
3. 在首屏确认 run 的 Pipeline、node、lineage、状态、耗时、模型、token、错误摘要与当前执行位置。
4. 沿 Stage → Step/Session → Turn → event 定位因果；同时识别重叠执行，不把时间重叠误称为父子关系。
5. 对比 prompt、response、thinking、Tool 参数与结果，阅读 Markdown、JSON、终端输出和 diff。
6. 打开 Source、Artifact、Admission、Direction、Review 与相关 node，复制稳定 id 或当前选择深链。
7. 运行中保持当前位置接收新增事件；上滚或选择历史项时暂停自动跟随。
8. 在 390px 完成从 Chat 进入/返回、查找失败、查看 Tool I/O、复制 id 四项任务。
## 信息架构
| 区域 | 内容 | 桌面 | 390px |
|---|---|---|---|
| Run rail | Project/Thread scope、关联数量、搜索、状态筛选、run rows | 248px 固定栏 | 顶部按钮打开抽屉 |
| Header | breadcrumb、标题、稳定 id、status、返回原对话与 node | 主区顶部 | 两行紧凑布局 |
| Summary | duration、Stage 进度、Session/Tool、token、model、cost 状态 | 单行指标带 | 两列网格 |
| Overview | 全程时间条、并行 lane、当前时间/尾随 | 树上方 112px | 横向滚动 84px |
| Trace tree | Stage、Step、Session、Turn、event | 主列，最小 480px | 单列全宽 |
| Inspector | Overview/Input/Output/Artifact；Markdown/JSON/diff/raw | 420px sticky | 全宽 sheet |
| Relation strip | node、lineage、Admission、Review、Artifact | Header 下方 | 横向滚动 |
## 组件
| 组件 | 职责 |
|---|---|
| `RunRail` | Project/Thread scope、关联数量、状态/文本筛选、run 选择、运行态更新，不加载 Session 内容 |
| `RunHeader` | run identity、状态、错误摘要、复制、返回原 thread 与 node |
| `RunSummary` | 只展示现有或可派生指标；缺失字段显示“未记录” |
| `RelationStrip` | Kernel node、lineage、Admission、Review、Artifact 关系入口 |
| `TraceOverview` | 共享时间尺度、Stage/Session lane、重叠区间、tail follow |
| `TraceTree` | 因果层级与折叠；选中项由 URL query 保存 |
| `TraceRow` | type、label、status、start、duration、token、错误标记 |
| `TraceInspector` | 选中项 tabs、内容 renderer、复制、原始 JSON |
| `ContentRenderer` | text/Markdown/JSON/terminal/diff；未知类型纯文本回退 |
| `TraceToolbar` | 搜索、类型/状态筛选、仅异常、折叠、时间模式 |
## 状态模型
| 状态 | 页面行为 |
|---|---|
| empty | 空运行列表显示启动入口语义；不渲染空树 |
| loading | rail 与 summary 固定尺寸 skeleton；已载入树不因局部 loading 消失 |
| queued | header 显示排队，overview 保留待开始位置，duration 为空 |
| running | 当前路径展开，未结束项 duration 显示进行中而非估算；默认跟随尾部 |
| waiting_human | 当前 gate 展开，保留已有安全操作；动作成功后原位刷新 |
| completed | summary 固定最终值，默认折叠成功的低层事件 |
| failed | header 错误摘要可跳至首个失败项；树展开失败路径，成功同级折叠 |
| paused | 显示暂停原因与可用动作，不等同失败 |
| cancelled | Runtime Turn 可显示；Run 级只在 Kernel 持久化后启用 |
| partial | Kernel run 已载入但一个 Session inspect 失败；该 Session 局部错误和重试，不遮挡其他内容 |
## 交互
1. 行点击选中并更新 `?item=`；折叠按钮只改变展开态，不改变选中。
2. Trace 接收 `project_id`、`thread_id` 与 `from`；`from` 只允许当前 Project 的 thread URL。运行列表先按 Project 隔离，再按 Thread 关联过滤；缺 Thread 时显示 Project 全部 runs。
3. 返回对话使用原 `from`；缺失或无权访问时回到当前 Project 的 Chat，不从浏览器 referrer 推断。
4. 搜索匹配 label、id、Tool name 与已加载文本；结果保留祖先并标亮，未加载内容不宣称已搜索。
5. 类型、状态与仅异常筛选可组合；筛选后空态显示清除筛选。
6. Overview 点击区间滚动并选中对应行；拖动只缩放时间范围，不修改因果树。
7. running 默认 tail follow；用户上滚、展开历史项或选中项后暂停，显式按钮恢复。
8. `Copy` 复制当前 tab 的可见原文；复制 id 与复制深链分开；导出只在服务端提供 canonical trace 导出后启用。
9. Inspector tabs 保留各自滚动位置。超过 200 行的 JSON 默认折叠；超过 256 KiB 的内容显示截断标记和 Artifact 打开动作，不能静默裁剪。
10. Markdown 禁止执行内嵌 HTML；外链明确域名。diff 保留行号、增删色和独立横向滚动；颜色不是唯一状态信号。
## 字段映射
`已有`表示当前 schema/API 直接给出；`可派生`表示不新增事实即可确定计算；`缺失`表示必须先改 owner 的 schema/API。
| UI 字段 | 状态 | 事实源/规则 |
|---|---|---|
| run id/project/node/lineage/pipeline | 已有 | `pipeline_runs` |
| Pipeline 定义与 Stage 顺序 | 已有 | `definition_snapshot` |
| run status/current stage/error | 已有 | run `status/stage/payload.error` |
| run start/end | 已有 | `created_at/updated_at`，updated 仅在终态作为 end |
| run duration | 可派生 | 终态 `updated_at-created_at`；运行态 `now-created_at` 并标进行中 |
| Step id/ordinal/status/input/output/time | 已有 | `pipeline_steps` |
| Kernel event actor/type/payload/time | 已有 | `pipeline_events` |
| Session id/stage/actor/usage | 已有 | `agent_session` event；usage 可能为空 |
| Session parent | 已有 | Runtime `session_meta.parent`，当前 UI 未投影 |
| Session child catalog | 缺失 | ADR 0026 声明 `child_session`，当前 Runtime 未写该 event，Kernel run 也无统一 child 投影 |
| 并行区间 | 可派生 | Session/Turn/event 时间区间重叠；只表达重叠，不推断因果 |
| Turn input/output/status | 已有 | Runtime inspect projection |
| prompt/model response/model/endpoint | 已有 | `model_request/model_response/session_meta.agent_spec` |
| thinking | 缺失 | 没有 normalized response part；provider-specific message 字段不能作为稳定 UI contract |
| Tool name/arguments/result/error | 已有 | `tool_call/tool_result` |
| Tool duration | 可派生 | call/result `time` 差；缺 result 时为空 |
| token | 已有/可派生 | response 与 turn_end usage；按 Turn/Session/run 聚合并避免双计 |
| cost | 缺失 | 需要 model/provider pricing revision 与逐 response cost，不能按当前价格回算历史 |
| model 汇总 | 可派生 | Session spec 与 model_request 去重 |
| retry/attempt/previous run | 缺失 | Pipeline/Runtime 均无 typed attempt 与 predecessor relation |
| error location/class | 部分已有 | Runtime `error` 有 exception text；Kernel 只有 payload text，缺 typed class 与关联 event id |
| Artifact id | 可派生 | Tool capture result 的 `artifact_id`；必须按既有 Tool result contract 解码 |
| Artifact media type/size/preview | 缺失 | Kernel store 有记录，run projection 没有通用 Artifact metadata/read endpoint |
| file diff | 缺失 | Tool result 没有 normalized diff content block；不能从 shell 文本猜测 |
| Admission | 已有/缺投影 | node `life_state/rejection_reason/rebuttal` 已有；run detail 缺 typed relation |
| Review | 已有/缺投影 | Pipeline Step/output/event 保存审核结果；run detail 缺统一 Review relation |
| node/lineage | 已有 | run 与 node schema；页面可深链现有 node route |
| Thread→run association | 缺失 | Thread 只有 `project_id + session_id`，Pipeline run payload 可接收 `thread_id` 但缺稳定关联投影与数量 query；由 #65 实现 |
| Project/Thread filter | 缺失 | run list 现按 Project；需要 Kernel query 接收并校验 `thread_id`，不由前端过滤跨 Project 数据 |
| return thread URL | 可派生 | 入口提供受控 `from`，Trace 校验 Project/Thread 后保留 |
| search/filter | 可派生/缺分页 | 已加载投影可本地筛选；大 Trace 需要 cursor 与服务端条件 |
| copy | 可派生 | 已加载原文与稳定 id |
| canonical export | 缺失 | 没有 run + Runtime sessions 的一致快照导出接口 |
| live update | 部分已有 | bootstrap 5 秒 polling；Session inspect 一次性，缺 session 增量 cursor/stream |
| redaction | 缺失 | ADR 0026 禁止写凭证；实现没有 Tool I/O 内容脱敏与 `redacted` provenance，UI 不显示虚假安全标记 |
## 隐私
1. API key、authorization header、cookie、private env 与数据库凭证在进入 Trace writer 前删除；渲染层二次遮罩只作纵深防御。
2. `redacted: true`、规则 id 与原始字节数进入 event metadata，不保存原值；UI 显示已脱敏和规则，不允许展开。
3. Tool I/O、prompt、response、Artifact preview 默认继承 Project 访问边界。复制、导出和外链打开均记录明确目标，不自动复制隐藏内容。
4. Markdown 禁止脚本、事件属性、iframe 与不受控图片；JSON key 命中敏感名时二次遮罩并显示非事实性保护提示。
## Prototype
入口为 `/prototype/agent-runtime?view=trace&project_id=project:q49&thread_id=thread:orbital&from=/chat/thread:orbital`，文件只位于 `research-world/web/src/prototype/agent-runtime/`。prototype 使用静态场景演示独立 Trace 页面、Project/Thread scope、返回原对话、布局与交互；不包含 Chat composer 或图中浮层。cost、retry、Run cancelled、thinking、Thread→run query 与完整 Artifact metadata 明确显示“未记录/待 API”，不冒充现有数据。
验收场景覆盖 completed、running、failed、cancelled、empty 与 loading；覆盖 Stage、并行 Session、Turn、Tool I/O、JSON、Markdown、diff、Artifact id、Admission、Review、token、error 与 lineage。prototype 截图进入 `docs/adr/assets/0029-trace-ui/prototype/`。
### Prototype 自验
Compose project `issue64-trace` 在 host `8195/8198` 构建并通过 healthcheck；prototype URL 带 `project_id=project:q49`、`thread_id=thread:orbital` 与 `from=/chat/thread:orbital`。
OpenCLI 真实 Chrome 完成运行选择、Tool 行选择、移动 inspector 打开和 Diff tab 切换。Playwright Chromium 断言 1440px 的 body/root scroll width 均为 1440px，390px 均为 390px；移动 inspector bounds 为 `x=0,y=53,width=390,height=791`；桌面 Trace row 无相邻列重叠。
状态交互覆盖 failed、Turn cancelled、empty、loading、running；搜索命中 `graph_query`；全部折叠显示 3 个 Stage，全部展开显示 14 行；移动 Run rail 开闭后仍无页面级横向溢出。该结果是设计实现自验，不是独立事实或规格 QA。
## 实施 subissue 草案
Chat 紧凑入口、Project/Thread filter、关联数量和返回原对话已由 #65 跟踪，不重复起草。下列 Trace subissue 消费 #65 的导航上下文与关联投影。
### 1. Kernel run detail projection
范围：新增单个 run 的聚合 query，返回 run、Stage、Step、event、node/lineage、Admission/Review 关系和关联 Session id；接受 #65 已校验的 Project/Thread scope，不包含 Runtime message 内容。
前端可见验收：Trace 首屏一次请求得到稳定 header、summary、relation strip；字段缺失以 null 表达，不解析自由文本。
Schema/API 依赖：Research Kernel query 与 HTTP GET；沿用现有表，不新增状态。
独立 OpenCLI QA：从项目运行列表进入 complete/failed/waiting_human 各一项，核对 node、Stage、错误和关系入口。
### 2. Runtime incremental inspect projection
范围：为 Session inspect 增加 event cursor、typed content parts、parent/child catalog、错误类别、redaction metadata；保留 Trace JSONL 为事实源。
前端可见验收：运行中 Session 原位追加事件；thinking 不存在时不显示 tab；child Session 可定位父项。
Schema/API 依赖：Agent Runtime ACP extension；Tool I/O 写前脱敏；不改 Kernel 数据库。
独立 OpenCLI QA：观察运行中 Session 两次增量、取消 Turn、失败 Tool 与 child Session，确认无重复事件。
### 3. Trace shell and run summary
范围：实现 Run rail、header、summary、relation strip、empty/loading/partial/terminal states；消费 #65 的 Project/Thread/from 上下文。
前端可见验收：1440px 首屏可识别 scope、关联数量、status、duration、Stage 进度、Session/Tool、token、model、cost 未记录和首个错误；可返回原对话。
Schema/API 依赖：subissue 1、#65；token/model 使用 subissue 2 投影。
独立 OpenCLI QA：只走 WebUI 从 Chat 进入 scoped Trace，按状态筛选并切换 run，复制完整 run id，返回原 thread，局部 Session 失败不遮挡 run。
### 4. Causal tree and timeline overview
范围：实现 Stage/Step/Session/Turn/event 因果树、共享时间尺度、并行 lane、选中与折叠。
前端可见验收：重叠 Session 显示在不同 lane；parent/child 有连线；运行中未结束项不显示伪造 duration。
Schema/API 依赖：subissue 1、2 的时间戳与 parent/child；不新增执行层级。
独立 OpenCLI QA：选择 overview 区间定位行，折叠同级不改变选中，刷新后 `?item=` 恢复。
### 5. Trace content inspector
范围：实现 Input/Output/Artifact/raw tabs 与 text/Markdown/JSON/terminal/diff renderer。
前端可见验收：长 JSON 可折叠和复制，Markdown 安全渲染，diff 行号与增删可读，Artifact id 可打开，截断有明确标记。
Schema/API 依赖：subissue 2 typed content；Artifact metadata/read endpoint 另由 subissue 1 暴露 Project-scoped projection。
独立 OpenCLI QA：分别打开 prompt、response、Tool、terminal、diff、Artifact；核对复制内容与横向滚动。
### 6. Trace search, filters and canonical export
范围：实现文本/类型/状态/仅异常筛选、匹配祖先保留、稳定深链和一致快照导出。
前端可见验收：搜索结果说明加载范围；空结果可一键清除；导出包含 run 与引用 Session 的固定 cursor 快照。
Schema/API 依赖：大 Trace cursor/filter query；Kernel 协调 Runtime snapshot token，禁止前端拼接竞态快照。
独立 OpenCLI QA：组合 Tool+failed 筛选，复制深链重开同一事件，下载后核对 run/session ids。
### 7. Trace responsive and live behavior
范围：实现 tail follow、暂停/恢复、局部重试、390px drawer/sheet 与键盘焦点。
前端可见验收：390px 无页面横向溢出、标题裁切或控件重叠；代码区独立横向滚动；新增事件不抢走历史选择。
Schema/API 依赖：subissue 2 cursor/stream；不增加第二套实时协议。
独立 OpenCLI QA：桌面与 390px 运行中截图；上滚暂停、恢复跟随、Session 局部重试、键盘完成筛选和复制。
## 不采纳
不把所有事件画成一张自由缩放 graph：密集文本的主要任务是定位与阅读，graph 只保留可证实的 parent/child 与并行关系。
不从 timestamps 推断 parent/child，不从 shell 文本推断 file diff，不按当前模型价格回算历史 cost，不把 provider 私有字段固定成 thinking schema。
不在 Chat composer 上方展开 run panel、popover、list 或 Trace 详情；Chat 不复制运行查询和详情组件。
不复刻竞品术语或建立第二套 Session/Artifact/Review；Deep Research Kernel 与 Agent Runtime seam 保持不变。
