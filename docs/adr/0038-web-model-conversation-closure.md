---
status: accepted
sources:
  - id: issue-219
    title: Governance：固定 Web 模型连接与凭证边界
    url: https://github.com/LittleDrinks/research-world/issues/219
    accessed: 2026-08-31
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
未绑定 Session、跨 Session Message 与 Child Run 目标在 Runtime Adapter 启动和 Trace 写入前失败。服务器组合层拥有当前唯一主 Agent 定义，Agent 只含角色提示词、Skill 与 Tool。Research World 设置 facade 只转发模型设置管理请求；Penguin 持久拥有模型访问配置，浏览器和 Agent 不选择 Adapter、模型或凭证。
## 模型设置
Web 模型设置属于本闭环范围。模型访问配置是部署级设置，不随 Project、Session、Agent、Run、Turn 或 Trace 复制。Web 设置页的管理操作固定为测试、保存、掩码读取、替换、清除：测试只验证连接而不持久化；保存与替换提交完整的 provider、model id、baseurl、apikey；掩码读取只返回 provider、model id、base URL、默认模型与密钥状态；清除移除配置。
Research World 设置 facade 只转发上述操作，Runtime Settings 管理面不属于五动作执行接口；Penguin 是唯一持久所有者。明文 apikey 可短暂进入 Web password input 和明确的测试、保存或替换请求；请求结束即清空，不进入 storage、URL、console、其他 DOM、日志或响应。
未配置模型时 Compose 和应用仍保持健康；Chat 不提交模型 Turn，只显示设置引导。
## 投影与恢复
对话协调顺序固定为持久化用户 Message、Runtime Submit、观察主 Turn、幂等投影主 Turn 非空 `completed` 或 `limit` 回答。重复观察不重复回答；Child、cancelled 和 error 终态不写 Session。
自动断线重连使用 SSE `id` 与 `Last-Event-ID`。整页刷新先按稳定 Session 身份从 Kernel 水合对话；未回答 Message 以原 id 重复 Submit，复用原 Turn并重新订阅 Trace，不依赖浏览器保存执行状态，也不再次执行模型。
## Penguin
Compose 管理 Penguin Harness Adapter 的固定 v0.2.9 server 进程、数据根与 readiness。Penguin 每次启动铸造新的 bearer token，并以 `0600` 写入专用数据根的 token 文件；Runtime 是唯一外部调用方，每次新请求重新读取 token 文件。control/Web 不获得 token，Penguin 的启动替换承担唯一的 token 生命周期，不设计外部生成或手工轮换。
Runtime Adapter 独占 Run 到 Penguin Session、Turn 到 Penguin Task 的映射及 HTTP/SSE 协议；浏览器和 Kernel 不接触该 server。Runtime Trace、Session、健康响应、异常、日志和 Web 设置管理响应均不包含明文模型凭证或 Penguin token；Web password input 仅在明确请求期间暂存明文 apikey。仓库根环境文件不注入模型凭证。成功终态同时要求非空 assistant 文本、根请求完成与随后 Task idle。
