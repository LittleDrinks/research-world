---
issue: 152
repository: LittleDrinks/research-world
status: research
accessed: 2026-08-30
sources:
  issue_152: https://github.com/LittleDrinks/research-world/issues/152
  context: ../../CONTEXT.md
  adr_0033: ../adr/0033-runtime-adapters-and-event-delivery.md
  runtime_seam: ../../runtime/runtime/runtime.py
  pi_rpc: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md
  pi_rpc_mode: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/modes/rpc/rpc-mode.ts
  pi_jsonl: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/modes/rpc/jsonl.ts
  pi_rpc_types: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/modes/rpc/rpc-types.ts
  pi_args: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/cli/args.ts
  pi_rpc_client: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/modes/rpc/rpc-client.ts
  pi_package: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/package.json
  pi_quickstart: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/quickstart.md
  pi_usage: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/usage.md
  pi_config: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/config.ts
  pi_settled: https://github.com/earendil-works/pi/issues/2110
  mcp_stdio: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/stdio.py
  mcp_client_docs: https://py.sdk.modelcontextprotocol.io/client/
  pi_binary_snapshot: ../../datasets/research-kernel-papers/snapshots/issue-139/pi-session-protocol.md
  pi_session_snapshot: ../../datasets/research-kernel-papers/snapshots/issue-139/pi-session-format.md
  pi_compaction_snapshot: ../../datasets/research-kernel-papers/snapshots/issue-139/pi-compaction.md
---
# Issue #152: Pi Runtime Adapter 研究记录
范围：为新 `runtime/runtime/runtime.py` 的 Adapter seam 提供实现参考；不把旧 Runtime service、ACP/server 入口或 Pi Session 文件纳入新 Adapter。
## 结论
- **启动参数**：Pi RPC 的入口是 `pi --mode rpc`；#152 的最小命令是 `pi --mode rpc --no-session`。`--offline`、`--provider`、`--model` 和 `--no-approve` 都需要明确的产品或 Agent snapshot 决策，不能隐式加入。
- **定位**：Adapter 从进程 `PATH` 定位名为 `pi` 的可执行文件，不硬编码 npm 包路径或 `node dist/cli.js`；fake Pi 使用同名可执行文件走同一查找逻辑。
- **版本**：上游当前 package 声明版本为 `0.84.4`；本机只读检查到 `/home/q2635/.nvm/versions/node/v24.14.0/bin/pi`，实际版本为 `0.84.3`。两者不构成兼容性承诺；版本或配置不满足时必须明确报错。
- **认证与偏好**：Pi 的 API key、默认 agent 目录和偏好属于宿主机 Pi 配置；Adapter 只将所需宿主环境传入子进程，不传入 Runtime/root `.env` 凭证，也不以 Pi Session 文件代替 Runtime Trace。
- **JSONL 传输**：RPC 通过 stdin 接收命令、通过 stdout 输出 response/event JSONL，一行一个 JSON 对象；stderr 仅作为诊断流。
- **提交与 ACK**：核心提交命令是 `{"type":"prompt","message":"..."}`。prompt response 只确认 accepted/queued/handled；模型、工具或重试错误继续通过事件流表达，ACK 不是 Turn 完成。
- **流式事件**：`message_update` 提供增量，`message_end.message` 是消息完整值。`agent_end` 代表一次低层 agent loop 结束，后面仍可能有 retry、compaction 或 queued continuation；`agent_settled` 才表示 session-level 没有自动后续工作。Adapter 将文本、thinking、tool 和错误映射为 `{type, data}`，不发 Runtime 保留的 `turn_end`。
- **取消**：取消命令是 `{"type":"abort"}`；Adapter 对目标 Pi handle 发 abort，并在子进程不响应时执行有界终止。`clear_queue` 是不同的交互语义，不能用 `session_id` 猜测目标 Turn。
- **错误**：找不到 `pi`、配置或认证失败、spawn 失败、非零退出、EOF、坏 JSON、未知或不合约事件和取消失败都必须成为明确 Adapter/Turn error，不切换 Penguin 或其他 Adapter。
## 与新 Runtime 的边界
- `RuntimeAdapter` 只有 `start(TurnRequest) -> handle`、`submit(handle, request, emit) -> AdapterResult`、`cancel(handle, request)`；Runtime 持有 Run/Turn、Trace、事件重连、委派、上下文快照和按 Turn 取消。Pi Adapter 不读写 Trace，不接触 Kernel Session，不维护 Runtime 私有锁/进程表。
- `supports_multiple_writers` 决定同一 Adapter 的并发 Turn；Pi 声明不支持 multiple writers，让 Runtime 拒绝重叠 Turn。
- 不把 `--session-id`、`--session-dir`、resume 或 Pi Session JSONL 当作 Runtime 身份或恢复机制；`--no-session` 与 Run/Turn 所有权边界一致。
## 进程适配对照
- MCP Python SDK 提供可复用的进程卫生模式：显式 argv/cwd/过滤 env、独立 stdin/stdout/stderr、增量解析、有界退出、POSIX 进程组 TERM/KILL 和错误上报。
- 只复用生命周期模式，不复用 MCP 的 `initialize`、JSON-RPC envelope 或 schema；Pi RPC 是另一套 JSONL 命令和事件协议。
## 仓库快照的使用边界
- `pi-session-protocol.md` 的 4-byte big-endian 加 CBOR 协议不是当前 `pi --mode rpc` 的 stdin/stdout JSONL，不用于 #152。
- `pi-session-format.md` 的 Pi Session 持久化、分支和 compaction entry 不能替代 Runtime TraceLedger，也不由 Adapter 解析、写入或用于重连。
- 旧 compaction 记录进一步说明不能把一次 `agent_end` 或一个 `turn_end` 当作 Runtime Turn 的唯一完成证据。
## 不应复用的旧 ACP 语义
- ACP `session_id`、session lifecycle、`PromptResponse(stop_reason)`、`session_update` 和 `cancel(session_id)` 都属于旧 ACP 边界；新 Adapter 只接收 opaque handle/`TurnRequest`，调用 Runtime 提供的 `emit({type, data})`，并返回 `AdapterResult`。
- 旧 `RuntimeAdapter` 的 descriptor、EndpointPool、`generate`、`provider_session_id` 以及把 `agent_end` 当作终态的逻辑不进入新三方法 seam。
## 验证边界
- 已确认本机 `PATH` 定位和 `pi --version`：`0.84.3`。
- 2026-08-30 通过公开 `Runtime`/`PiAdapter` seam，在空的临时 workspace 发起有界主 Agent RPC 回合；宿主 Pi `0.84.3` 正常完成，终态为 `status: completed`，`result_text` 精确为 `OK`，`error: null`。规范化事件类型仅为 `turn_start`、`reasoning`、`delta`、`turn_end`（`reasoning` 可重复）；证据保存在 `.scratch/tdd/152/real-pi-round5-deepseek.txt`。
- 本次验证未使用 Docker、Penguin fallback 或 Pi Session 文件。
