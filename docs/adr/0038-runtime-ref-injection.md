---
status: accepted
decided: 2026-09-02
---
# Runtime Ref Injection
AgentSpec 的 `runtime` ref 所有权归 control：`agents/*.yaml` 不写 `runtime` 字段；control 在 RuntimeClient 边界（`launch` 与 `validate_agent` 出口）为缺 ref 的 agent_spec 注入默认 `{id: openai-compatible, realm: container:runtime}`；已有 ref 原样透传，注入值不回写、不落盘，agent create/save 保存原始声明。runtime 的 `agent.schema.json` 保持 `runtime` 必填不放宽；注入后仍校验失败的 spec 照常拒绝并记错误日志。
## 取舍
让 yaml 携带 ref 会把运行拓扑重复声明进 control 配置，一处漂移即新建对话 400、restart 同断；由 runtime 默认补全或放宽 schema 会把 ref 所有权移进 runtime，掩盖 control 配置漂移并削弱启动校验。边界注入单点收敛，thread create/restart 与 agent create/save 全路径共享同一出口。
