---
sources:
  - id: open-design-agent-adapters
    title: OpenDesign Agent Adapters
    url: https://github.com/nexu-io/open-design/blob/35edb37d60c8ec73e34174f1608f8833f461f8b4/docs/agent-adapters.md
  - id: open-design-pi-definition
    title: OpenDesign Pi Runtime definition
    url: https://github.com/nexu-io/open-design/blob/35edb37d60c8ec73e34174f1608f8833f461f8b4/apps/daemon/src/runtimes/defs/pi.ts
  - id: open-design-pi-rpc
    title: OpenDesign Pi RPC transport
    url: https://github.com/nexu-io/open-design/blob/35edb37d60c8ec73e34174f1608f8833f461f8b4/apps/daemon/src/agent-protocol/pi-rpc/session.ts
  - id: pi-coding-agent
    title: Pi Coding Agent 0.84.3
    url: https://github.com/earendil-works/pi/tree/bfb004d4418ff05c6f909eaaab856cbe75c1fde0/packages/coding-agent
---
# Pi Native Runtime Adapter
## 边界
Pi CLI 拥有模型调用、原生 Tool、认证、上下文压缩和原生 Session。Runtime Adapter 由只含启动事实的 Pi definition、RPC command/ack client 与无 I/O event parser 组成；通用 Runtime 生命周期负责 probe、spawn、cancel 和进程收敛。Runtime 不实现第二套 Agent loop，不读取、复制、转换或注入 Pi 凭据。Pi definition 不声明 auth probe；readiness 只确认 executable、固定版本和 RPC Adapter，账户或模型权限错误在 Turn 中显式返回。
## 调用
Runtime image 固定 Pi `0.84.3`。每个 Turn 在 Project workspace 启动 `pi --mode rpc --session-id <runtime-session-id>`，通过 stdin 发送一个 `prompt` command，只包含最新 user turn。`prompt success` 只代表接受；`agent_end` 才结束 Turn。完成后关闭 stdin 并有界终止仍存活的 RPC 进程。
AgentSpec 的逻辑 Endpoint 为 `pi`，model 为 `default`；`default` 不生成 `--model`，Pi 本地配置决定 provider、model、base URL 与 API key。reasoning 映射到 `--thinking`。Pi Agent 不声明 Runtime Tool；Pi 原生 Tool lifecycle 只投影为 provider item。
## Session
Runtime Session id 与 Pi native session id 相同，不扫描文件时间、不猜 continuation、不用 `new_session.parentSession` 创建逐轮分叉。Pi 原生 JSONL 是 continuation source，Trajectory 是 Web inspect 与 UI projection；Runtime restart 后用相同 id 恢复。宿主终端继续原生 Session 后，下一次 Web prompt 继承新增上下文，但 Web 不反向补录终端消息。同一 native Session 只允许一个活跃 writer。
Thread restart 创建新 Runtime/Pi Session；旧 Pi Session 与 Trajectory 均保留。Pi session path、native id、配置路径与凭据不进入公共投影。
## Compose
Runtime 与宿主 Pi 读写共享同一个 Pi agent directory，Pi 子进程使用宿主 UID/GID 写入。Pi child environment 只保留运行所需的 HOME、Pi directory、locale 与固定 PATH，不继承 Runtime Endpoint 凭据。容器内 workspace path 与宿主不同时，`/resume` 在 All Sessions 中按名称或首条消息查找。
## 失败
版本不匹配、RPC ack 拒绝、invalid JSON、缺少 `agent_end`、模型错误、extension error、retry exhausted、timeout 与进程异常均显式失败，不切换 Runtime、不重放完整 Trajectory、不新建替代 Session。取消先发送 RPC `abort`，再有界终止进程组。
