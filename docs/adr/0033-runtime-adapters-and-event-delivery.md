---
sources:
  - id: issue-145
    title: Runtime 深 Module
    url: https://github.com/LittleDrinks/research-world/issues/145
    accessed: 2026-08-29
  - id: issue-147
    title: 架构落地：决策记录与 TDD 证据约定
    url: https://github.com/LittleDrinks/research-world/issues/147
    accessed: 2026-08-29
  - id: pi-rpc
    title: Pi RPC mode
    url: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md
    accessed: 2026-08-30
  - id: open-design-adapters
    title: Open Design Agent Adapters
    url: https://github.com/nexu-io/open-design/blob/main/docs/agent-adapters.md
    accessed: 2026-08-30
status: accepted
supersedes:
  - "ADR 0026: Research Kernel/Runtime 对 Session、Trace、Thread 的旧所有权和会话接口"
  - "ADR 0027: Kernel 直接编排 Pipeline run 的旧接口范围"
  - "ADR 0032: 固定 Pipeline、Stage、Auto 执行入口的旧范围"
  - "ADR 0036: thread_id 持久化和 HTTP Thread 权威路径的范围"
  - "ADR 0037: 与 Run、Turn、Trace 和 Runtime delegation 冲突的 Thread/Trajectory/Workflow 范围"
---
# Runtime Adapters And Event Delivery
Runtime 拥有 Run、Turn、Trace、Skills、Tools、delegation、Runtime Adapters 及 Agent 执行快照（Adapter、model、instructions、skills、tools、params）；Research Kernel 拥有 Project、Session、Artifact、Research Graph 记录与关系以及 LocalMap。Session 是用户可读的 Kernel 对话，与 Runtime Run 和 Trace 分离。
## 决策
Runtime 对外只提供 Launch、Submit、Subscribe、Cancel 与 Delegate。Submit 从已持久化的 Kernel Session 用户消息创建或幂等返回 Turn，并立即返回 Turn 标识；Subscribe 以 Turn 标识和最后已见序号独立读取 Trace，断线后可按序号重连，不会再次执行提交。
Launch 时 Runtime 冻结 Agent 执行快照：Adapter、model、instructions、skills、tools、params；快照属于 Runtime，不进入 Kernel Session 或 Research Graph。
每个活跃 Turn 拥有 Adapter 执行句柄；不支持 multiple writers 的 Adapter 同时只允许一个活跃 Turn，Runtime 在调用 start 前拒绝同一 Adapter 的重叠 Turn。支持 multiple writers 的 Adapter 可以共享底层 harness，但取消共享执行时必须接收目标 Turn 身份。每个 Turn 创建时冻结其 Run 先前的终态上下文，也不把其他活跃 Turn 的输入或生成内容加入快照。并发 Turn 的完成顺序不改变回答与起始用户消息的配对关系。
Trace 是按 Turn 追加的 Runtime 执行事实。Runtime 先持久化事件再发布，事件序号用于订阅和重连；取消、错误与终态只改变目标 Turn。Cancel 只取消一个 Turn，重连只读取既有事件。
Runtime Adapter 只负责识别、启动、提交、取消和产生规范化事件；Run 恢复、Trace 持久化、上下文快照、delegation 与事件重连由 Runtime 负责。Adapter 的位置、协议、生命周期、配置和凭证不越过 Runtime 边界。
transport/session.py 是 Kernel 与 Runtime 之间的无状态协调层，不是第三深模块；顺序是持久化用户消息 -> Runtime Submit -> 将主 Agent 终态回答投影到同一消息。HTTP 的 Session 读取和发消息由 transport/session.py 负责，Runtime Turn 订阅、取消和 Run 查询由 transport/runtime.py 负责，Kernel Project、Artifact、图谱和 LocalMap 由 transport/kernel.py 负责；提交、订阅、取消和 Session 读取保持为分离路径。
Pi Adapter 只在开发端从宿主机进程 PATH 定位并运行已安装的 Pi，复用宿主机的安装、认证和偏好；当前支持并验证 Pi `0.84.3`，使用 `pi --mode rpc --no-session`，不把 Run 或 Turn 映射为 Pi Session，不读取或写入 Pi Session 文件。模型、thinking 和 system prompt 只有 Agent 执行快照明确提供时才进入 argv；子进程只继承 HOME、Pi 配置目录、PATH、locale 及 Pi 的无遥测设置，不继承 Runtime 或 Endpoint 凭证。Pi 的 prompt response 只作接受确认，Adapter 持续消费 JSONL，在 `agent_settled` 且已有成功 `agent_end` 后返回 AdapterResult；文本增量映射为 `{type: "delta", data: {text}}`，thinking 生命周期映射为 `reasoning`，tool execution 生命周期映射为 `tool`；协议、配置、进程和模型错误显式失败，未知事件不静默忽略。Pi 不支持 multiple writers，按 Turn 的取消先发 `abort`，再有界收敛该执行句柄。正常交付使用 Compose，Docker 不包含也不支持 Pi。Penguin Harness Adapter 是未来与 Pi 同级的 Runtime Adapter，由 Runtime 直接启动并使用用户提供的模型访问配置；不加入占位、fallback 或模拟实现。
## 取代范围
上述取代只覆盖与新所有权和事件边界冲突的旧决定：ADR 0026 中 Runtime 拥有 Session、Kernel 保存 Thread 指针以及一次会话式 prompt/inspect 的范围；ADR 0027 中 Kernel 直接解释 Pipeline run 的范围；ADR 0032 中固定 Pipeline、Stage、Auto 执行入口及其 Runtime 绑定的范围；ADR 0036 中持久化 `thread_id` 并以 HTTP Thread 路径作为报告或会话权威入口的范围；ADR 0037 中以 Thread、Trajectory 或 Workflow 驱动执行会话的范围。ADR 0036 的报告投影、渲染、Artifact 和持久化规则不因会话关联方式改变；会话权威由 Session projection 提供，执行和事件关联由 Submit/Subscribe 按 Turn 标识提供。各 ADR 未与 Run、Turn、Trace、Adapter、Session 所有权冲突的研究图谱、报告和发现细节仍是历史记录，不重写。
