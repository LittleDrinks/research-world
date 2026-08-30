---
status: accepted
sources:
  - id: issue-169
    title: MVP 规格：主 Agent 协作研究闭环与双深 Module 切换
    url: https://github.com/LittleDrinks/research-world/issues/169
    accessed: 2026-08-31
  - id: adr-practice
    title: Maintain an architecture decision record
    url: https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record
    accessed: 2026-08-31
  - id: madr
    title: Markdown Architectural Decision Records
    url: https://adr.github.io/madr/
    accessed: 2026-08-31
  - id: html-sse
    title: HTML Standard server-sent events
    url: https://html.spec.whatwg.org/multipage/server-sent-events.html
    accessed: 2026-08-31
  - id: ai-sdk-resume
    title: AI SDK resume streams
    url: https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams
    accessed: 2026-08-31
  - id: ai-sdk-chat-source
    title: AI SDK Chat source
    url: https://github.com/vercel/ai/blob/main/packages/ai/src/ui/chat.ts
    accessed: 2026-08-31
  - id: pydantic-ai-ui
    title: Pydantic AI UI overview
    url: https://pydantic.dev/docs/ai/integrations/ui/overview/
    accessed: 2026-08-31
  - id: sse-starlette
    title: sse-starlette
    url: https://github.com/sysid/sse-starlette
    accessed: 2026-08-31
  - id: rq-abandoned-jobs
    title: RQ exceptions and abandoned jobs
    url: https://python-rq.org/docs/exceptions/
    accessed: 2026-08-31
supersedes:
  - "0017: Thread and fixed Pipeline execution assumptions"
  - "0022: Agent execution configuration and capability validation"
  - "0026: Runtime ownership, execution context, Session/Trace distinction, and event delivery"
  - "0029: Chat Thread to Runtime Session delivery and return-path assumptions"
  - "0030: Agent CLI discovery's Runtime binding scope"
  - "0032: fixed Pipeline/Auto execution entry and adapter binding"
  - "0036: HTTP Thread authority for session and report paths"
  - "0037: Thread/Trajectory/Workflow execution scope"
---
# Runtime Adapters And Event Delivery
## 决策
Research Kernel 拥有 Project、Session、Artifact、Record、Relation 与 LocalMap；Runtime 拥有模型访问配置、Run、Turn、Trace、Skill、Tool、委派、Runtime Adapter 与执行快照。Agent 配置只包含角色提示词、选中的 Skill 与 Tool，不包含模型访问配置或 Adapter 绑定。
Runtime 对外只提供 Launch、Submit、Subscribe、Cancel 与 Delegate。Submit 在 Kernel Session 已持久化用户消息后创建或幂等返回 Turn，并立即返回 Turn 标识；浏览器不选择或传递 Run id。Subscribe 以 Turn 标识和最后已见序号独立读取 Trace，断线后按序号重连，不会再次执行提交。
Launch 时 Runtime 冻结 Agent 执行快照和 Adapter 绑定；快照属于 Runtime，不进入 Kernel Session 或 Research Graph。一个 Run 可同时承载多个活跃 Turn，每个 Turn 都有独立的 Adapter 执行句柄和 Trace。Adapter 可以为 Turn 提供独立 harness 句柄，也可以使用能按 Turn 身份寻址的共享执行；Runtime 不得因为底层 harness 的实现方式把同一 Run 的重叠 Turn 改为互斥或拒绝。Turn 创建时只冻结 Run 先前的终态上下文，不读取其他活跃 Turn 的输入或生成内容，完成顺序不改变回答与起始用户消息的配对关系。
Trace 是按 Turn 追加的 Runtime 执行事实。Runtime 先持久化事件再发布，`seq` 用于订阅和重连；取消、错误与终态只改变目标 Turn。Delegate 创建独立 Child Run；Child Turn 终态以包含 Child Run、Child Turn、状态和结果的 `child_result` 事件追加到父 Turn Trace，不写入用户 Session。普通 parent 终态等待已启动 Child Turn 的结果，显式 Cancel 只终止目标 parent，不取消其他 Child Turn。
Runtime Adapter 只负责识别、启动、提交、取消和产生规范化事件；Run 恢复、Trace 持久化、上下文快照、委派与事件重连由 Runtime 负责。Adapter 的位置、协议、生命周期、配置和凭证不越过 Runtime 边界。
transport/session.py 是 Kernel 与 Runtime 之间的无状态协调层，不是第三深模块；顺序是持久化用户消息 -> Runtime Submit -> 将主 Agent 终态回答投影到同一消息。Session 读取、Submit、Subscribe、Cancel 使用分离的 HTTP 路径，transport 不拥有 Project、Run 或 Trace。
HTTP 事件订阅使用标准 SSE。Server 将 Trace `seq` 写入 SSE `id`，`Last-Event-ID` 与可选 `after_seq` 映射到 Subscribe 游标；浏览器为每个活跃 Turn 建立独立 EventSource，关闭订阅只结束订阅，不取消 Turn。刷新先读取 Kernel Session；没有最终回答的 Message 以相同 Message id 重复 Submit，Runtime 返回原 Turn 后重放 Trace，transport 只投影一次终态回答。
`@ai-sdk/react useChat` 不拥有产品的 Agent 或 Chat 状态；Pydantic AI UI Adapter 不进入请求执行链。两者的 UI 或执行语义不能取代 Runtime 的 Submit、Subscribe、Cancel 与 Turn 归属。
Pi Adapter 只在开发端从宿主机运行已安装的 Pi，复用宿主机安装、认证和偏好；正常交付使用 Compose，Docker 不包含或支持 Pi。Penguin Harness Adapter 是与 Pi 同级的托管 Runtime Adapter，由 Runtime 直接启动并使用用户提供的模型访问配置，是 Docker/MVP 默认交付 Adapter。Adapter 失败显式结束，不静默切换、占位或模拟另一个 Adapter。
## 取代范围
`supersedes` 列出的旧 ADR 只在所列范围内保留历史记录，不再作为当前 Runtime、Session、Run、Turn、Trace、Adapter 或事件边界的实施依据。ADR 0036 的报告投影、渲染、Artifact 与持久化规则不因 Session 关联方式改变；其他未与当前边界冲突的研究图谱、报告和发现细节保持历史语义。
