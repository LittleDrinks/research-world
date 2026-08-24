---
sources:
  - id: crossref-rest
    title: Crossref REST API
    url: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
  - id: crossref-full-text
    title: Crossref Accessing full texts
    url: https://www.crossref.org/documentation/retrieve-metadata/rest-api/text-and-data-mining/
  - id: pmc-oai
    title: PMC OAI-PMH API
    url: https://pmc.ncbi.nlm.nih.gov/tools/oai/
---
# Research Kernel
系统只有 Research Kernel 与 Agent Runtime 两个深模块。Research Kernel 是 Project 研究状态的唯一写入门；HTTP、CLI、Worker Host 是适配器，不能直接访问 World、PipelineEngine 或数据库。
## 接口
`command(command)` 接收提交节点、人工裁决、启动/取消 Pipeline 等状态变更；`query(query)` 返回项目、图谱、运行、日志等投影；`run(run_id)` 解释一个已领取的 Pipeline run。接口使用领域命令和值对象，不暴露表结构、事务或内部服务。
`start_run` 只接受 `{node_id,pipeline_id,payload?}`；目标节点必须属于当前 Project 且 admitted。`payload` 只允许 `thread_id`、`instruction`、`mode`、`pins`，每个 pin 必须属于当前 Project 且 admitted，Thread 必须属于当前 Project；适配器不能注入游标、信号、execution id 或 Pipeline 内部状态。
## 准入
节点提交统一经过 `submit -> pending -> admitted | ghost`。Submission 后的 AdmissionPolicy 是纯、只读、可替换的内部 seam；策略返回结构化结论时 Kernel 立即落状态，默认策略返回 pending，不把未审核内容自动准入。
`resolve_admission` 是 pending 节点的唯一显式完成命令，只接收 node id、decision、reason 与 rebuttal；Kernel 构造 Verdict 并一次提交 Life state、驳回理由与 rebuttal。HTTP PATCH、CLI、Pipeline 和调用方构造的 Verdict 均不能改 Life state。Pipeline 的机制审核、证据审核与双审升级是 Kernel 内部策略，不扩大外部接口。
WebUI 的 Admission 操作只适配 `resolve_admission`；reject 要求非空理由，操作结果从 Kernel 投影刷新，界面不自行构造 Life state、驳回理由或证据边。
## 运行
Pipeline run 生命周期、行动审核、执行凭据、Artifact 与 Research event 由 Kernel 维护。模型执行只经 ACP 调用 Agent Runtime；计算执行只经 Runner Adapter。Runtime Trace、模型凭证和 Tool 凭证不进入 Kernel。
Artifact 在 Project 内按 SHA-256 寻址，读取、关联与复跑校验都携带 project id。Tool Runtime 只能通过 Artifact 与 observation port 提交结果；observation 继续经过 Admission，Tool 调用成功不等于研究事实准入。
文献 Pipeline 的 prompt stage 只产生 SourceCandidate，提交 stage 由 Kernel 校验结构、当前 Direction 和 Artifact 的 Project scope、media type、SHA-256 后形成 source。SourceCandidate 不进入图谱；source 先经过 Admission，pending 经既有 `resolve_admission` 变为 admitted 或 ghost，只有 admitted source 才建立 supports/refutes 边。
SourceCandidate 严格包含 title、authors、year、venue、DOI 或稳定 URL、source type、license、access status、全文 Artifact、与 Direction 的 use/relevance/claims/原文定位、检索 query/database、核验时间和未解决问题，不接受额外字段。全文可用时 Artifact 必须来自当前 Project 且包含 id、Project File、media type、SHA-256；`full_text_unavailable` 时 Artifact 为空、use 只能是 background、claims 为空。摘要字段不进入 SourceCandidate，不能支撑 supports/refutes。
Pipeline run 投影保留 SourceCandidate 与 source 的 Admission 状态；Project 图谱投影保留书目元数据、Artifact 和 Direction 关系。
Brainstorm 只要求模型返回候选内容，不接受模型自报 `quality`。候选选择只使用 Kernel 计算的确定性特征与多样性，审核证据另行保存。
Pipeline 创建的节点把 Agent 生成的简洁 `title` 与完整正文分开存于 payload：brainstorm、reconcile、reflect 返回 `{title,text}`，plan 返回 `{title,action}` 替代占位标题。`title` 硬上限 12 token；token 计量单位：每个 CJK 字符、每段连续 Latin/数字、每个其他非空白标点或符号各计 1。Kernel 拒绝缺失、空白、非字符串或超限的 title，不截断、不合成、不回退正文。
## 投影
地图、科研日志、运行详情和报告从 Kernel 事实确定性投影。适配器只能请求投影，不能拼接跨表业务状态；Agent 搜索、资源读取、Thread 钉入和 Pipeline 启动只消费 admitted 节点。
报告投影只包含 admitted claim、source 与关联 Artifact；Endpoint 可用性由 Kernel 查询 Runtime 识别结果后推导。BibTeX 只能从当前 Project 内 admitted source 关联的 Artifact 导出，返回内容前完成语法校验；调用方不能提交路径、内容或自报 Endpoint 状态。
