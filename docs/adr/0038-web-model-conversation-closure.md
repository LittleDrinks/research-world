---
status: accepted
sources:
  - id: issue-215
    title: 规格：真实网页模型对话闭环
    url: https://github.com/LittleDrinks/research-world/issues/215
    accessed: 2026-08-31
  - id: stripe-idempotency
    title: Stripe Idempotent requests
    url: https://docs.stripe.com/api/idempotent_requests
    accessed: 2026-08-31
  - id: tanstack-chat-persistence
    title: TanStack AI Client Persistence
    url: https://github.com/TanStack/ai/blob/main/docs/persistence/client-persistence.md
    accessed: 2026-08-31
  - id: fastapi-sse
    title: FastAPI Server-Sent Events
    url: https://fastapi.tiangolo.com/reference/sse/
    accessed: 2026-08-31
  - id: penguin-v0.2.9
    title: Penguin Harness v0.2.9
    url: https://github.com/Prism-Shadow/penguin-harness/releases/tag/v0.2.9
    accessed: 2026-08-31
supersedes:
  - "0033: Penguin process lifecycle and physical credential delivery"
---
# 网页模型对话闭环
## Session 与主 Run
浏览器为 Session 和 Message 生成稳定 UUID 幂等键。Kernel 对同一 Project、标识和内容返回原对象，参数冲突明确失败。创建顺序固定为 Kernel 持久化 Session 后 Runtime Launch；Launch 失败保留可重试 Session，重复创建请求不生成第二个 Session 或主 Run。
Runtime 在根 Run 持久记录中保存唯一 `session_id`。相同 Session 与 Agent 快照重复 Launch 返回原 Run，快照冲突失败；Child Run 不带 Session。主对话 Submit 只接收 Session 与已持久化 Message，Runtime 内部解析根 Run；相同 Session 与 Message 重复 Submit 返回原 Turn。
未绑定 Session、跨 Session Message 与 Child Run 目标在 Runtime Adapter 启动和 Trace 写入前失败。服务器组合层拥有当前唯一主 Agent 定义，Agent 只含角色提示词、Skill 与 Tool。Runtime 绑定 Penguin Harness Adapter 并拥有模型访问配置；浏览器和 Agent 不选择 Adapter、模型或凭证。
## 投影与恢复
对话协调顺序固定为持久化用户 Message、Runtime Submit、观察主 Turn、幂等投影主 Turn 非空 `completed` 或 `limit` 回答。重复观察不重复回答；Child、cancelled 和 error 终态不写 Session。
自动断线重连使用 SSE `id` 与 `Last-Event-ID`。整页刷新先按稳定 Session 身份从 Kernel 水合对话；未回答 Message 以原 id 重复 Submit，复用原 Turn并重新订阅 Trace，不依赖浏览器保存执行状态，也不再次执行模型。
## Penguin
Compose 管理 Penguin Harness Adapter 的固定 v0.2.9 server 进程、数据根与 readiness。Runtime Adapter 独占 bearer token、Run 到 Penguin Session 映射、Turn 到 Penguin Task 映射及 HTTP/SSE 协议；浏览器和 Kernel 不接触该 server。
Runtime 独占模型访问配置，Compose 不向 Penguin Server 注入模型凭证或仓库根 `.env`，也不调用其模型、受管 Project、Agent 或 Task API。Runtime Trace、Session、健康响应、异常、日志和 Web 均不包含模型凭证或 Penguin token。成功终态同时要求非空 assistant 文本、根请求完成与随后 Task idle。
