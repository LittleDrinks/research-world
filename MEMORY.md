# 项目状态
## 已确认目标
- Research Graph 保存 Question、Source、Direction、Experiment、Artifact 与证据关系；研究地图是其 UI 投影，报告只使用具有证据闭包的 Claim。
- Research Kernel 拥有 Project、Session、Artifact、Research Graph 记录与关系以及 LocalMap；Session 是 Project 下用户可读的对话，保存用户消息和主 Agent 最终回答。
- Runtime 拥有 Run、Turn、Trace、Skills、Tools、delegation、Runtime Adapters 以及 Agent 执行快照（Adapter、model、instructions、skills、tools、params）。Session 与 Run 分离；Turn 创建时冻结 Run 先前的终态上下文，并按起始用户消息固定并发回答位置。
- 主 Agent 直接与用户对话并通过 Runtime Delegation 创建 Child Agent Run；Child Agent 可通过 Kernel Interface 读写 Research Graph 记录与关系，但不直接写用户 Session。
- Graph CLI 供主 Agent 与人类读写或删除 Research Graph；复核是 Agent 或人的行为，不是 Kernel Gate。删除记录时移除直接关系并保留关联 Artifact；LocalMap 由 Kernel 直接检索，MMR 是 Runtime 提供的确定性 Tool operation。
- Pi Adapter 只在宿主机用于开发端到端验证；正常交付使用 Compose，Docker 不包含也不支持 Pi。Penguin Harness Adapter 是未来同级 Adapter，当前不提供 fallback。
## 当前实现
- 当前生产代码处于架构切换前的遗留实现，不能作为目标边界或交付完成证据。
- 服务从 `research-world/` 使用 `docker compose up --build -d` 启动；凭证只在仓库根 `.env` 的 `apikey`、`baseurl`。
- 基座模型为 Qwen；开发最多三天，其余时间用于真实运行、证据整理和提交。
## 进行中
- #139 / draft PR #140 是多 Agent 数据契约调研，等待资料归档与独立验收。
- #141 / PR #142 已将 Research Graph 术语和目标边界落库；生产代码尚未迁移。
