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
每个 Turn 创建时冻结其 Run 先前的终态上下文；活跃 Turn 不共享可变的原生 harness 会话，也不把其他活跃 Turn 的输入或生成内容加入快照。并发 Turn 的完成顺序不改变回答与起始用户消息的配对关系。
Trace 是按 Turn 追加的 Runtime 执行事实。Runtime 先持久化事件再发布，事件序号用于订阅和重连；取消、错误与终态只改变目标 Turn。Cancel 只取消一个 Turn，重连只读取既有事件。
Runtime Adapter 只负责识别、启动、提交、取消和产生规范化事件；Run 恢复、Trace 持久化、上下文快照、delegation 与事件重连由 Runtime 负责。Adapter 的位置、协议、生命周期、配置和凭证不越过 Runtime 边界。
Pi Adapter 只在开发端从宿主机定位并运行已安装的 Pi，复用宿主机的安装、认证和偏好；正常交付使用 Compose，Docker 不包含也不支持 Pi。Penguin Harness Adapter 是未来与 Pi 同级的 Runtime Adapter，由 Runtime 直接启动并使用用户提供的模型访问配置；不加入占位、fallback 或模拟实现。
## 取代范围
上述取代只覆盖与新所有权和事件边界冲突的旧决定：ADR 0026 中 Runtime 拥有 Session、Kernel 保存 Thread 指针以及一次会话式 prompt/inspect 的范围；ADR 0027 中 Kernel 直接解释 Pipeline run 的范围；ADR 0032 中固定 Pipeline、Stage、Auto 执行入口及其 Runtime 绑定的范围；ADR 0036 中持久化 `thread_id` 并以 HTTP Thread 路径作为报告或会话权威入口的范围；ADR 0037 中以 Thread、Trajectory 或 Workflow 驱动执行会话的范围。ADR 0036 的报告投影、渲染、Artifact 和持久化规则不因会话关联方式改变；会话权威由 Session projection 提供，执行和事件关联由 Submit/Subscribe 按 Turn 标识提供。各 ADR 未与 Run、Turn、Trace、Adapter、Session 所有权冲突的研究图谱、报告和发现细节仍是历史记录，不重写。
