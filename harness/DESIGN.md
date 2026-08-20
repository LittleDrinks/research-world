# Harness 设计

独立进程服务，HTTP 契约即公共接口；research-world 是第一个调用方。稳定性优先：任何单点故障表现为一条错误记录，而不是进程崩溃或状态丢失。

## 资源模型

- **Session**：有状态执行上下文。字段：id、role_prompt、model、tools、status、created_at。消息历史持久化，进程重启后 turn 可继续。
- **Turn**：一次 prompt 驱动。字段：id、session_id、prompt、status（running/completed/limit/error）、result_text、usage、started_at、completed_at。
- **Trace**：append-only jsonl，评测与排障的唯一事实来源。
- **Benchmark**：一组 case + 可重复执行 + 结构化打分。

## API

| 路由 | 说明 |
| --- | --- |
| GET /health | {"ok": true} |
| POST /sessions | body {role_prompt?, model?, tools?, prompt_segments?} → session。prompt_segments 依次拼接到 role_prompt 之后，作为 system 消息随 session 持久化。tool 两种：`{"type":"fs"}`（内建文件工具）；`{"type":"webhook","name","description","parameters","url","headers"?}`（回调调用方） |
| GET /sessions/{id} | session + 消息数 + 累计 usage |
| POST /sessions/{id}/turns | body {prompt, max_rounds?=12, timeout_seconds?=600, token_budget?=200000} → turn（同步执行完返回） |
| POST /sessions/{id}/turns/stream | 同上执行，但响应为 SSE：`data: {"delta": "..."}` 逐段，结束 `data: {"done": true, "turn": {...}}` |
| GET /sessions/{id}/turns/{turn_id} | turn 详情 |
| GET /sessions/{id}/trace | jsonl 全文 |
| POST /benchmarks | body {name, cases:[{id, prompt, tools?, expect?}]} → benchmark |
| POST /benchmarks/{bid}/runs | body {role_prompt?, model?, tools?} → 逐 case 建独立 session 执行 |
| GET /benchmarks/{bid}/runs/{rid} | 每 case 指标 + 聚合 |

## Trace schema

每行一个 JSON：`{"ts", "session_id", "turn_id", "seq", "kind", "data", "usage"?}`。
kind ∈ `turn_start | model_request | model_response | tool_call | tool_result | turn_end | error`。
usage 只在 model_response 上：`{"prompt_tokens", "completion_tokens"}`。
流式 turn 的 model_response 是拼装后的完整消息；delta 不进 Trace。

## 执行循环（稳定性契约）

1. user 消息落库 → 循环 max_rounds 次：调模型 → response 落库 → 无 tool_calls 则 completed；有则逐个分发。
2. 工具抛任何异常 → 捕获为该 tool_call 的错误 tool_result，循环继续。
3. 模型调用：429/5xx/网络超时指数退避重试 3 次（0.5s/1s/2s）；4xx 立即失败，turn 记 error。
4. 超 timeout 或 token_budget → turn 记 limit，正常返回已有 result_text，不抛栈。
5. 禁止全局可变状态、禁止改 os.environ；并发 turn 之间零共享。
6. fs 工具（read_file / grep / glob）限制在 session workspace 内，路径逃逸返回错误而非异常。

## 存储

SQLite（stdlib sqlite3，WAL）。表：sessions、turns、messages（session_id, seq, role, content, tool_calls, tool_call_id）、benchmarks、cases、benchmark_runs、case_results。workspace 在 `{HARNESS_DATA:-./data}/workspaces/{session_id}/`。

## 模型与工具

- 模型：OpenAI 兼容 POST {HARNESS_API_BASE}/chat/completions，Bearer HARNESS_API_KEY；默认 model 环境变量 HARNESS_MODEL。流式路径带 `stream: true` + `stream_options.include_usage`，逐 chunk 解析 delta；429/5xx/传输错误只在连接建立前按 backoff 重试，流开始后的传输错误直接记 turn error。
- webhook 工具：POST url，body {"tool","arguments","session_id","turn_id"}，headers 透传，60s 超时；非 2xx → 错误 tool_result。

## 打分（结构化，不用 LLM judge）

每 case：status、rounds、tool_error_count、wall_ms、prompt_tokens、completion_tokens；expect.contains 时加 substring 命中布尔。聚合：完成率、平均轮次、平均 token、总耗时。
