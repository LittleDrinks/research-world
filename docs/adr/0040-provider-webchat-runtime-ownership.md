---
status: accepted
sources:
  - id: issue-276
    title: 定稿：真实 Provider Web Chat 的 HTTP Runtime 与模型归属
    url: https://github.com/LittleDrinks/research-world/issues/276
    accessed: 2026-09-02
supersedes:
  - "0018: Agent-side endpoint binding scope"
  - "0033: Penguin-owned deployment model access config consumed through the Runtime Settings management plane, and the Docker/MVP default delivery status of the Penguin Harness Adapter"
  - "0038: the missing-model-config gate that blocks Chat Submit before Runtime without creating a Turn, and the Runtime Adapter → Penguin Session/Task → Penguin HTTP/SSE execution mapping for Provider Web Chat"
  - "0039: Launch/Submit-only HTTP transport scope deferring Subscribe"
---
# Provider Web Chat Runtime And Model Ownership
## 决策
真实 Provider Web Chat 的唯一永久路径是浏览器 → control → `runtime.runtime.Runtime` 的 HTTP Launch/Submit/Subscribe → Runtime 拥有的 OpenAI-compatible Adapter → Provider；control 的对话协调发起 Launch、Submit 与 Subscribe，不接触其他 Runtime 入口。ACP 与 `service.Runtime` 是被取代的遗留路径，不恢复。
保存的 Agent definition 只含角色提示词、Skill 与 Tool 选择，不携带 provider 或 model 选择。Runtime 在其进程内解析部署提供的 `RW_MODEL_NAME`、`baseurl` 与 `apikey`；OpenAI-compatible Adapter 属于 Runtime，模型调用与凭证使用不越过 Runtime 边界，Trace 只记录非机密的已解析模型标识。
`baseurl` 与 `apikey` 只进入 Runtime 进程，browser/control、公开 API、Trace 与日志不携带密钥。部署缺失 `baseurl` 或 `apikey` 时，Runtime 以可理解的错误显式失败受影响的 Turn，不静默降级、占位或切换 Adapter。
Pi Adapter、Delegate、Child Run 与 Tool 不参与 Provider Web Chat 模型访问路径；刷新对同一 Message 重复 Submit 并返回已有 Turn；WebUI API-key 设置不是模型访问配置的解析来源。
