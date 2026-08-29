# 项目状态
## 已确认目标
- Research Graph 保存 Question、Source、Direction、Experiment、Artifact 与证据关系；研究地图是其 UI 投影，报告只使用具有证据闭包的 Claim。
- #145、#146、#147 已完成架构边界、领域术语和开发证据规范的记录；生产代码仍待架构切换。
## 当前实现
- 当前生产代码处于架构切换前的遗留实现，不能作为目标边界或交付完成证据。
- 服务从 `research-world/` 使用 `docker compose up --build -d` 启动；凭证只在仓库根 `.env` 的 `apikey`、`baseurl`。
- 基座模型为 Qwen；开发最多三天，其余时间用于真实运行、证据整理和提交。
## 进行中
- #139 / draft PR #140 是多 Agent 数据契约调研，等待资料归档与独立验收。
- #141 / PR #142 已将 Research Graph 术语和目标边界落库；生产代码尚未迁移。
