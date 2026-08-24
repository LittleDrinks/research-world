---
sources:
  - id: issue-63
    title: Agent UI research and redesign
    url: https://github.com/Intelligent-Internet/ai4sci/issues/63
    accessed: 2026-08-24
  - id: multica-runtime
    title: Multica daemon and runtimes
    url: https://docs.multica.ai/concepts/daemon-and-runtimes
    accessed: 2026-08-24
  - id: kimi-cli
    title: Kimi Code CLI command reference
    url: https://moonshotai.github.io/kimi-cli/en/reference/kimi-command.html
    accessed: 2026-08-24
---
# Agent CLI Discovery
## 决策
Agent Runtime 在实际启动 Agent 的进程和 execution realm 内只读识别 Agent CLI。浏览器、Research Kernel 与 Tool Adapter 不探测可执行文件。`runtime/discover` 返回 `agent_clis`；发现结果不写 AgentSpec、不安装、不登录、不启用、不调用模型。
OpenCLI 是浏览器自动化 Tool/adapter，不是 Agent CLI、执行 Runtime 或认证 readiness 来源；它只进入 Tool catalog。
## Descriptor
| 字段 | 类型 | 语义 |
|---|---|---|
| `id` | stable string | Runtime 内置的产品 id，如 `codex`、`claude`、`pi`、`kimi`；不由路径生成 |
| `display_name` | string | 产品展示名 |
| `executable` | string | 实际探测的命令名 |
| `version` | string/null | 安全 `--version` 或等价命令解析后的版本 |
| `source` | enum | `user-path`、`system-path`、`shim`、`symlink`、`windows-path`、`container-path`、`explicit` |
| `path` | string/null | 选中 realm 内解析后的可执行文件路径 |
| `status` | enum | `found`、`ready`、`auth-required`、`missing`、`error`、`unsupported` |
| `reason` | object/null | 稳定 code、可展示 message、失败 probe；不含 stdout、stderr 或凭证 |
| `last_checked_at` | RFC 3339 | 该 descriptor 最近完成探测的时间 |
| `capabilities` | string[] | Adapter 已确认的能力 id；缺省为空，不从产品名推断 |
`capabilities` 使用 Runtime 内置词表：`interactive`、`non-interactive`、`streaming`、`resume`、`model-select`、`reasoning-select`、`workspace`、`auth-probe`。Profile 选择的 Skill、Tool 与 MCP 来源不进入该数组。
## 状态
| 状态 | 判定 |
|---|---|
| `found` | executable 与 version 已确认，认证或 Adapter readiness 尚不能安全确认 |
| `ready` | executable、兼容版本、Adapter 和必需认证全部确认；仍未表示 Profile 已启用 |
| `auth-required` | executable、版本与 Adapter 可用，安全认证 probe 明确报告未登录、过期或缺凭证 |
| `missing` | 已知候选在目标 realm 的 PATH 与显式位置均不存在 |
| `error` | executable 存在，但固定 probe 超时、崩溃或返回不可解析结果 |
| `unsupported` | executable 存在，但平台、版本或 Runtime Adapter 明确不兼容 |
稳定 reason code 为 `not_on_path`、`auth_missing`、`auth_expired`、`auth_probe_unavailable`、`probe_timeout`、`probe_failed`、`probe_invalid_output`、`version_incompatible`、`adapter_unavailable`、`realm_mismatch`、`unsupported_platform`。
## Probe
Runtime 对每个内置候选执行固定 argv allowlist，不经过 shell。定位、版本和认证 probe 分进程运行；单步 2 秒、单候选累计 5 秒、stdout 与 stderr 各截断到 16 KiB，并在完成解析后丢弃。进程组超时终止；一个候选失败不改变其他结果。
认证只使用官方、非交互、无敏感输出的状态命令。没有这种命令时返回 `found/auth_probe_unavailable`，不得读取配置文件、环境变量值或 token。probe 不执行 install、update、login、doctor 修复、付费模型调用或任意用户命令。
## Realm 与来源
`wsl`、`windows` 与 `container` 是独立 execution realm。Runtime 只把能在当前 launch 进程中直接执行的结果用于 `ready`；其他 realm 的发现结果保留来源并返回 `found/realm_mismatch`。shim 与 symlink 同时记录入口 `path` 和内部 `resolved_path`，UI 默认展示脱敏入口路径，诊断页按本地权限展开。
## 缓存与刷新
结果按 `workspace + realm + Runtime build` 缓存 60 秒。页面进入使用缓存并显示 `last_checked_at`；手动刷新绕过缓存并将 UI 置为 `refreshing`。首次无缓存为 `loading`，候选 catalog 为空为 `empty`。刷新只重新 probe，不改变 Agent、Preset、凭证、文件或进程配置。
## 准备与启用
`found != ready != enabled`。AgentSpec 只引用用户确认的 execution runtime；Profile readiness 由已保存选择和最新 descriptor 共同投影。缺失或需配置时，UI 可请求 `runtime/prepare/plan` 生成声明式计划；执行必须二次确认并进入独立 prepare 日志。Discovery 不调用 `runtime/tools/prepare`，也不隐式 prepare CLI。
## API 投影
```json
{
  "agent_clis": [{
    "id": "codex",
    "display_name": "Codex CLI",
    "executable": "codex",
    "version": "0.149.0",
    "source": "symlink",
    "path": "~/.local/bin/codex",
    "status": "ready",
    "reason": null,
    "last_checked_at": "2026-08-24T12:00:00Z",
    "capabilities": ["non-interactive", "streaming", "resume", "model-select", "reasoning-select", "workspace", "auth-probe"]
  }]
}
```
## AgentSpec 边界
AgentSpec 需要稳定 `runtime` 引用；`endpoint` 与 `model` 继续描述模型服务选择。CLI discovery descriptor 是 Runtime inventory，不嵌入 Profile。CLI、API Endpoint、Tool、Skill、Preset 与 Profile 分属不同实体；OpenCLI 仅可由 Profile 的稳定 Tool id 选择。
