---
status: accepted
sources:
  - id: issue-235
    title: Runtime Transport：HTTP Launch 与 Submit 纵向闭环
    url: https://github.com/LittleDrinks/research-world/issues/235
    accessed: 2026-09-01
  - id: issue-215
    title: 规格：真实网页模型对话闭环
    url: https://github.com/LittleDrinks/research-world/issues/215
    accessed: 2026-09-01
  - id: fastapi-lifespan
    title: FastAPI Lifespan Events
    url: https://fastapi.tiangolo.com/advanced/events/
    accessed: 2026-09-01
  - id: fastapi-status
    title: FastAPI Response Status Code
    url: https://fastapi.tiangolo.com/tutorial/response-status-code/
    accessed: 2026-09-01
  - id: httpx-async
    title: HTTPX Async Support
    url: https://www.python-httpx.org/async/
    accessed: 2026-09-01
  - id: httpx-transports
    title: HTTPX Transports
    url: https://www.python-httpx.org/advanced/transports/
    accessed: 2026-09-01
  - id: pydantic-models
    title: Pydantic Models
    url: https://pydantic.dev/docs/validation/latest/concepts/models/
    accessed: 2026-09-01
---
# Runtime HTTP Launch And Submit
## 决策
Runtime HTTP 只暴露 `POST /api/v1/runtime/launch` 与 `POST /api/v1/runtime/submit`。Launch 请求为 `{agent_spec, session_id?}`，Submit 请求为 `{session_id, message}`；Submit 不接受 Run id。Launch 成功返回 `200`，Submit 成功返回 `202`；路由只调用现有五动作核心的 `launch` 与 `submit`，成功响应直接返回核心的规范 Run/Turn view，不在 transport 复制执行、持久化或幂等行为。
请求模型拒绝未知字段。请求校验失败返回 `422 {"code":"invalid_request","detail":...}`；核心对象不存在返回 `404 {"code":"not_found","detail":...}`；核心对象归属或快照冲突返回 `409 {"code":"conflict","detail":...}`。客户端将这些状态和错误体保留为 `RuntimeHttpError`，成功体解析为只读的 `RunView` 或 `TurnView`。
内部存储错误返回 `500 {"code":"internal_error","detail":"internal server error"}`，不暴露存储异常详情；输入错误仍返回 422。
Research World 的 `RuntimeHttpClient` 为每个实例创建一个 scoped `httpx.AsyncClient`，所有命令复用它；`close()` 由应用生命周期调用并释放连接。测试通过 HTTPX ASGI transport 连接真实 FastAPI 应用与可控 Adapter，不读取 Runtime 私有存储。
## 取代范围
范围仅包括 Launch/Submit JSON transport。Subscribe、Cancel、Delegate、Penguin、生产 Runtime factory、Compose 与浏览器认证仍由各自 issue 负责；不保留旧 ACP 路由或兼容路径。
