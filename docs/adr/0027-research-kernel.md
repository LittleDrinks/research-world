# Research Kernel
系统只有 Research Kernel 与 Agent Runtime 两个深模块。Research Kernel 是 Project 研究状态的唯一写入门；HTTP、CLI、Worker Host 是适配器，不能直接访问 World、PipelineEngine 或数据库。
## 接口
`command(command)` 接收提交节点、人工裁决、启动/取消 Pipeline 等状态变更；`query(query)` 返回项目、图谱、运行、日志等投影；`run(run_id)` 解释一个已领取的 Pipeline run。接口使用领域命令和值对象，不暴露表结构、事务或内部服务。
## 准入
节点提交统一经过 `submit -> pending -> review -> admitted | ghost`。Kernel 在 command 事务内调用 Admission；HTTP PATCH、CLI 与 Pipeline 不得直接改 Life state。
Admission 内部按顺序运行 `AdmissionPolicy`：结构校验、相似性、主张审计、机制审核、证据审核。Policy 接收只读 Submission 与 Context，返回结构化 Verdict；它不能写数据库或启动执行。Kernel 聚合 Verdict、处理双审分歧并一次提交节点状态、rebuttal、claims 与事件。
## 运行
Pipeline run 生命周期、行动审核、执行凭据、Artifact 与 Research event 由 Kernel 维护。模型执行只经 ACP 调用 Agent Runtime；计算执行只经 Runner Adapter。Runtime Trace、模型凭证和 Connector 凭证不进入 Kernel。
## 投影
地图、科研日志、运行详情和报告从 Kernel 事实确定性投影。适配器只能请求投影，不能拼接跨表业务状态。
