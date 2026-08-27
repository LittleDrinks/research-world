# 项目状态
## 已确认目标
- Research Graph 保存 Question、Source、Direction、Experiment、Artifact 与证据关系；研究地图是其 UI 投影，报告只使用具有证据闭包的 Claim。
- Agent Runtime 拥有 Session 与 Trajectory。正常结束的 Agent 在 Trajectory 结尾输出 Summary；异常结束时主 Agent 读取结束原因和尾窗，按需展开完整日志；Summary 不是 Research Graph 事实。
- 主 Agent 动态编排 Workflow，可继续、复审、并行或转向；不使用固定 Pipeline、Stage、Auto 或图谱状态机。
- 主 Agent 与人类可调用 Graph CLI，Child Agent 只读；双审留在主 Agent Skill/prompt。Source 失效时以显式确认的级联撤销保留历史。
## 当前实现
- `origin/main` 仍运行旧 Research Kernel、准入、Pipeline、Stage、Auto 与 Trace；它们是遗留实现，不能作为目标模型或交付完成证据。
- 服务从 `research-world/` 使用 `docker compose up --build -d` 启动；凭证只在仓库根 `.env` 的 `apikey`、`baseurl`。
- 基座模型为 Qwen；开发最多三天，其余时间用于真实运行、证据整理和提交。
## 进行中
- #138 正在把文档引用与数据契约一手来源归档为本地 PDF、Markdown 与源码/网页快照。
- #139 / draft PR #140 是多 Agent 数据契约调研，等待资料归档与独立验收。
- #141 / PR #142 将术语和目标边界落库；生产代码尚未迁移。
