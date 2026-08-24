# Issue 落地状态
代码基线：`07ea3e9`。Research Kernel 与 Agent Runtime 是仅有的两个深模块。
| Issue | 验收结论 | 落地事实 |
|---|---|---|
| #12 | 完成 | 原子 claim、证据、verdict 逐条持久化 |
| #13 | 完成 | 重合候选进入独立 reflect Session，ghost 只提供最小上下文 |
| #14 | 完成 | reflect direction 绑定父 direction 与同谱系；PR #37 不合并 |
| #15 | 已关闭 | Kernel 保留证据边方向，前端不再改写 |
| #16 | 已关闭，过时 | ActivityPage 删除，科研日志只投影 Research event |
| #17 | 已关闭 | Thread 消息统一 Markdown 渲染 |
| #18 | 已关闭，过时 | 全量 NodeRail 删除，Thread 只展示显式钉入节点 |
| #19 | 完成 | Submission 默认 pending，只有 Admission 可产生 verdict 与 life state 变化 |
| #20 | 已关闭，设计替代 | 节点使用稳定不透明 id，内容相似性属于 Admission |
| #21 | 完成 | 执行凭据、不可变 SHA-256 Artifact、复跑哈希均在活路径持久化 |
| #22 | 完成 | 计划按单个 Action 审核，批准后幂等创建一次执行 |
| #23 | 设计替代 | 机制审核与证据审核使用不同 contract 和独立 Session，不重复同一 prompt |
| #24 | 完成 | ghost 仅进入 Admission 相似性上下文，不进入查询、Thread、报告或执行 |
| #25 | 完成 | Runtime 独占 Endpoint、模型、凭证与同模型 failover |
| #26 | 已关闭 | 对话只属于 Project Thread，地图 NodeChat 删除 |
| #27 | 设计替代并完成 | Lean4 作为 Agent Connector，与数据库和外部工具共用 Runtime seam |
| #28 | 已关闭，不做 | pre-experiment 不在当前闭环 |
| #29 | 设计替代并完成 | 人工 gate 负责决策；结果经 Artifact、observation、Admission 入图，不设湿实验专用分支 |
| #30 | 完成 | 交付状态由 Kernel 推导；admitted source 支持 BibTeX 校验与导出 |
| #31 | 设计替代并完成 | AgentSpec 编辑 Runtime 识别的 Endpoint、Model、Skill、Tool、Connector 与执行选项 |
| #32 | 已关闭，不做 | 多机 GPU 与通用故障降级不在当前单机边界 |
| #33 | 已关闭，不做 | 保留可变实验环境与不可变 Artifact 冲突 |
| #34 | 不做 opencli | 外部数据走 Connector；结果登记 Artifact 后提交 observation；公共目录隐藏 location/config |
| #35 | 完成 | claim/action 审核依据显式保存，支持/挑战 argument 分离，候选选择不使用模型自报 quality |
| #36 | 完成 | Report Skill 只消费 admitted projection、BibTeX export 与 delivery validation |
## 附加验收
| 要求 | 结果 |
|---|---|
| 图谱连线不穿过节点 | ELK edge section 路由；浏览器几何断言覆盖所有 life state |
| 节点短标题 | Pipeline Agent 必须返回标题；确定性 12-token 上限；服务端拒绝缺失、空值、类型错误与超限 |
| 地图引用节点 | 删除发起对话；Inspector 复制完整 `node_id`；Chat 通过 `@node_id` 搜索并钉入 |
| Research Kernel | `205 passed` |
| Agent Runtime | `63 passed` |
| Web | `61 passed`；生产构建通过 |
| 静态检查 | Ruff 全模块通过 |
| Compose | control、runtime、runner-controller 健康；worker 运行 |
| 真实 API | Connector 脱敏、Agent 保存、Artifact 隔离、Admission、报告投影与 BibTeX 导出通过 |
