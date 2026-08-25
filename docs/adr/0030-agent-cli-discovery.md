---
sources:
  - id: issue-63
    title: Agent UI research and redesign
    url: https://github.com/LittleDrinks/ai4sci/issues/63
    accessed: 2026-08-24
  - id: multica-runtime
    title: Multica v0.4.32
    url: https://github.com/multica-ai/multica/tree/v0.4.32
    accessed: 2026-08-24
  - id: kimi-code
    title: Kimi Code CLI 0.38.0
    url: https://github.com/MoonshotAI/kimi-code/releases/tag/%40moonshot-ai%2Fkimi-code%400.38.0
    accessed: 2026-08-24
---
# Agent CLI Discovery
## 决策
Agent Runtime 在实际启动 Agent 的进程与 execution realm 内只读识别 Agent CLI。浏览器、Research Kernel 与 Tool Adapter 不探测可执行文件。`runtime/discover` 返回 inventory；发现结果不写 AgentSpec、Profile 或 Preset，不安装、不登录、不启用、不调用模型。
OpenCLI 是浏览器自动化 Tool Adapter，只能以 `browser.opencli` 进入 Tool catalog 或驱动 WebUI QA；不属于 Agent CLI、execution runtime、认证来源或 prepare 目标。
## Descriptor
| 字段 | 类型 | 语义 |
|---|---|---|
| `id` | stable string | Runtime 内置产品 id，如 `codex`、`claude`、`pi`、`kimi-code`；不由路径生成 |
| `realm` | stable string | 执行边界 id，如 `wsl:ubuntu`、`windows:host`、`container:runtime` |
| `display_name` | string | 产品展示名 |
| `executable` | string | 固定 probe 使用的命令名 |
| `version` | string/null | 固定 version probe 解析后的版本 |
| `source` | enum | 发现机制：`path`、`win_get`、`npm`、`installer`、`explicit`、`container_image` |
| `path` | string/null | 发现入口；PATH 命中的 shim、symlink、`.cmd` 或 executable 路径 |
| `resolved_path` | string/null | 在该 realm 内解析后的最终 executable；缺失项为 null |
| `status` | enum | `found`、`ready`、`auth-required`、`missing`、`error`、`unsupported` |
| `reason` | object/null | `code`、可展示 `message` 与失败 `probe`；不含 stdout、stderr、环境值或凭证 |
| `last_checked_at` | RFC 3339 | 该 descriptor 最近完成探测的时间 |
| `capabilities` | string[] | Adapter 已确认的能力 id；缺省为空，不从产品名推断 |
同一产品在不同 realm 返回独立 descriptor，以 `(id, realm)` 唯一标识。UI 使用 `runtimeKey(id, realm) = JSON.stringify([id, realm])` 作为 option value、React key 与选择回读 key；选择和 Profile snapshot 始终同时保存 `id`、`realm`，不按 `id` 回退查找。`path` 不跟随 symlink、shim 或 wrapper；`resolved_path` 完成 realm 内解析。`source` 只表示发现来源，不编码 realm、文件类型或 readiness。
`capabilities` 使用 Runtime 内置词表：`interactive`、`non-interactive`、`streaming`、`resume`、`model-select`、`reasoning-select`、`workspace`、`auth-probe`。Profile 选择的 Skill、Tool 与 MCP 来源不进入该数组。
## 状态与错误
| 状态 | 判定 |
|---|---|
| `found` | executable 与 version 已确认，认证或 Adapter readiness 无法安全确认 |
| `ready` | executable、兼容版本、Adapter 与必需认证全部确认；不表示 Profile 已启用 |
| `auth-required` | executable、版本与 Adapter 可用，安全认证 probe 明确报告未登录、过期或缺凭证 |
| `missing` | 固定候选在目标 realm 的 PATH 与显式位置均不存在 |
| `error` | executable 存在，但固定 probe 超时、崩溃或返回不可解析结果 |
| `unsupported` | executable 存在，但平台、版本或 Runtime Adapter 明确不兼容 |
稳定 reason code 为 `not_on_path`、`auth_missing`、`auth_expired`、`auth_probe_unavailable`、`probe_timeout`、`probe_failed`、`probe_invalid_output`、`version_incompatible`、`adapter_unavailable`、`realm_mismatch`、`unsupported_platform`。`missing` 不伪造 `path`；wrapper 无法解析时返回 `error/probe_invalid_output`；跨 realm descriptor 只能是 `found/realm_mismatch`，不能参与当前 realm readiness。
## Probe
Runtime 对每个内置候选执行固定 argv allowlist，不经过 shell。定位、路径解析、版本与认证 probe 分进程运行；单步 2 秒、单候选累计 5 秒，stdout 与 stderr 各截断到 16 KiB，解析后丢弃。进程组超时终止；一个候选失败不改变其他结果。
固定 version argv 包含 Codex `['codex', '--version']` 与 Kimi Code `['kimi', '--version']`。Kimi 不登记认证 argv；version probe 不运行 `doctor`、读取配置或访问 secret。
认证只使用官方、非交互、无敏感输出的状态命令。没有这种命令时返回 `found/auth_probe_unavailable`，不得读取配置文件、环境变量值或 token。配置语法有效不等于已认证；Kimi `doctor config` 成功仍保持认证 unknown。probe 不执行 install、update、login、token refresh、doctor 修复、付费模型调用或任意用户命令。
## Realm 与缓存
`wsl`、`windows` 与 `container` 是独立 execution realm。Runtime 只把当前 launch realm 的 descriptor 用于 AgentSpec readiness；其他 realm 仅作为 inventory 事实展示。
结果按 `(workspace_id, realm, runtime_build)` 缓存 60 秒；key 不含 host path、Profile id 或认证值。页面进入读取缓存；手动刷新绕过缓存。首次无缓存为 `loading`，刷新时旧 snapshot 保持可读并标记 `refreshing`，候选 catalog 为空为 `empty`。刷新失败返回本次各 descriptor 的稳定错误并保留上次 snapshot 供对照，不把旧结果标记为本次成功。
## Readiness 与准备
`found != ready != enabled`。AgentSpec 只保存用户确认的稳定 `runtime` 引用；Profile readiness 由 runtime、Endpoint/model、Skills、Tools、workspace 与 secret status 联合投影。secret `configured`、`not-required` 投影为 `ready`，`missing`、`invalid` 投影为 `blocked`，只有 `unknown` 投影为 `unknown`；`missing`、`invalid` 的 reason code 可见并阻止保存与 Launch。inventory 不嵌入 Profile snapshot，刷新不得改变 Profile/Preset。
Profile 编辑使用与最后保存 snapshot 分离的工作副本。dirty 由两者显式深比较得出；仅 dirty 时显示 Cancel/Save，Cancel 恢复最后保存 snapshot，Save 写入新的独立 snapshot 后清除 dirty。
CLI 缺失或不兼容时，UI 可请求 `runtime/prepare/plan` 生成 CLI-only 计划；二次确认后才执行。Tool provision 始终由 #43 Tool catalog/Provisioner 负责，Discovery 不调用 Tool prepare。保存 Profile、页面进入与 Chat 草稿均不得触发 CLI prepare。
## API 投影
```json
{
  "agent_clis": [{
    "id": "codex",
    "realm": "wsl:ubuntu",
    "display_name": "Codex CLI",
    "executable": "codex",
    "version": "0.149.1",
    "source": "installer",
    "path": "~/.local/bin/codex",
    "resolved_path": "~/.codex/packages/standalone/releases/0.149.1-x86_64-unknown-linux-musl/bin/codex",
    "status": "ready",
    "reason": null,
    "last_checked_at": "2026-08-24T14:23:05Z",
    "capabilities": ["non-interactive", "streaming", "resume", "model-select", "reasoning-select", "workspace", "auth-probe"]
  }],
  "cache": {"realm": "wsl:ubuntu", "runtime_build": "0.1.0", "ttl_seconds": 60, "stale": false}
}
```
## AgentSpec 边界
AgentSpec 增加稳定 `runtime` 引用；`endpoint` 与 `model` 继续描述模型服务选择。descriptor 是 Runtime inventory，不嵌入 Profile。CLI、Endpoint、Tool、Skill、Preset 与 Profile 分属不同实体；MCP 只作为 Tool Adapter 来源，OpenCLI 只可由稳定 Tool id `browser.opencli` 选择。
