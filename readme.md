---
sources:
  - id: issue-53
    url: https://github.com/LittleDrinks/ai4sci/issues/53
  - id: submission-template
    title: 赛道一-方向1A-科学假设生成与研究计划设计-提交要求及模板.docx
    sha256: 430ef9a8ec504a3b693e00653a8c3b55a34e00c888ebd616cc06cea7f75c2884
  - id: official-questions
    path: docs/questions.json
  - id: reference-manifest
    path: docs/submission-reference-manifest.json
verified: 2026-08-24
---
# 2026 挑战杯阿里云榜题 XH-202619
赛道一·科学发现，方向 1A·科学假设生成与研究计划设计；基座使用 Qwen 系列。
## 提交约束
- 技术方案 PPT/PDF 不超过 20 页。模板 P1 的“不超过30页”与首页说明、P20 自检冲突，采用两处一致且更严格的 20 页。
- 作品简介、Qwen 与 AI 技术说明各不超过 300 字；模板未设其他总字数上限。填写系统报名作品名、最终作品名、赛道方向和可选宣传材料链接。
- 团队信息处粘贴盖章报名表第一页、第二页截图。
- 方向 A 保留官方 125 题逐题输出；失败、证据不足和需人工判断的题目不得省略。
- 交付源码、环境、依赖、运行方法、Qwen 调用方式及凭证或截图、125 题输出、代表案例输入与两轮结果及必要日志、测试 API、示例请求和可交互前端。
- 演示视频可选，不超过 10 分钟；视频经夸克网盘提交分享链接。
- 候选假设和研究计划仍需研究者审查，不得表述为已验证科学发现；密钥、受限数据和个人信息不得进入交付物。
## 模板结构
- Word 元数据：21 页、1125 词、6415 字符、7525 个含空格字符。
- 正文：封面加 P1-P20，161 个段落、26 张表、1 张页眉图片；脚注、尾注和嵌入附件均为空。
- 版式：Letter 纸张，四边 1 英寸页边距，首页独立页眉；模板自身 21 页不改变提交材料 20 页上限。
- 必需图示：P2 总体思路、P6 真实架构、P7 真实上下文结构、P12 真实工作流程。
- P1-P20 可按真实内容合并，不要求逐页对应或填满 20 页；完整案例位于 P14-P17，P18 至少一种同条件比较。
- 较长代码、日志和数据表进入允许的附件，不挤占论证正文。
## 展示 Project
选择覆盖文献证据、数值计算和结构化实验计划三种报告形态；Project 身份只使用小写 `qNNN`。
| Project | 科学问题 | 报告覆盖理由 | 所需 Profile / Tool | 预计 Pipeline run | 主要风险与缺口 |
|---|---|---|---|---|---|
| `q021` | Can we ever overcome antibiotic resistance? | 文献密集且涉及全球监测、冲突证据和政策边界；覆盖 P4、P5、P12、P19。仓库已有 Q21 worker 中断恢复的 UI 证据，可展示失败恢复但不能代替科学结果。 | 文献研究员；一手检索、浏览器/PDF、PubMed/WHO、Project Files。 | 1 次 brainstorm；每个 admitted direction 进入 research/review，证据变化后 reflect；实际次数由 `admitted >=100` 停止条件决定。 | 文献研究员与 Tool readiness 未完成：#43、#54；正向研究结果和 100+ 节点未完成：#48。 |
| `q049` | Why don’t the orbits of planets decay and cause them to crash into each other? | 可形成文献约束、数值积分、复跑哈希、支持/反驳和反思；覆盖 P7、P11、P12、P14-P18。 | 文献研究员、数值研究 Agent；一手检索、Python scientific stack、SymPy、Project Files。 | 1 次 brainstorm；选中方向逐一 research/review；数值 Artifact 复跑后 reflect；实际次数由 `admitted >=100` 停止条件决定。 | `orbits-49` 运行只作历史 Trace/Artifact，不能证明当前 `q049` 完成；#48。 |
| `q112` | Can we create an environmentally friendly replacement for plastics? | 同时要求材料来源、工艺变量、实验条件、统计优化和规模化边界；覆盖 P4、P8-P11、P18、P19，并能明确湿实验需人工返回。 | 文献研究员、实验规划 Agent；一手检索、PDF/表格抽取、Python 统计、Project Files、人工 gate。 | 1 次 brainstorm；候选材料路线分别 research/review；计划与人工反馈后 reflect；实际次数由 `admitted >=100` 停止条件决定。 | 不得把论文既有实验写成系统执行结果；真实 Pipeline、人工反馈和 100+ 节点未完成：#48、#54。 |
`research-world/projects/q049/project.json` 与已删除的 `orbits-49/project.json` 经空白规范化后 title、full_text 完全相同；唯一 Project identity 为 `q049`。`research-world/evidence/orbits-49-*` 仅保留 2026-08-11 历史 Artifact/Trace。
## P1-P20 证据矩阵
“可写事实”仅表示现有文件能支持该句；设计 ADR 不证明运行完成，历史 Artifact/Trace 不证明当前 Pipeline 完成。
| 章节 | 模板字段 | 现有系统证据 | 当前可写事实 | 缺口 issue |
|---|---|---|---|---|
| P1 | 团队/作品信息、核心问题、方法、两项代表结果、局限、官网提交项 | `research-world/projects/q021|q049|q112/project.json` | 三个 Project 输入和报告覆盖选择已固定；无代表结果可写。 | 团队字段人工填写；结果 #48 |
| P2 | 实际解决的问题、已完成功能、总体思路图、125 题测试、与直接问答差异 | `docs/adr/0017-research-world-redesign.md`、`docs/adr/0027-research-kernel.md`、125 个 Project 输入 | 图谱、Pipeline、准入与报告投影已有设计和代码证据；125 题只有输入，不是输出。 | #45、#48 |
| P3 | 事实/解释/推断区分、知识缺口、可检验/证伪、反证、候选非结论 | `CONTEXT.md`、`docs/adr/0017-research-world-redesign.md`、`docs/adr/0021-review-pipeline.md` | claim 审计、Direction 状态和 ghost 隔离是当前领域设计；三题尚无统一实跑证据。 | #12、#23、#48 |
| P4 | 实际来源、获得与使用、作用、局限、冲突处理、引用对应 | `docs/submission-reference-manifest.json`；`research-world/evidence/orbits-49-run.json` 为历史 Trace | 三份一手全文已远端归档并校验；当前三题尚无 admitted Source 链。 | #30、#48、#54 |
| P5 | 评价内容、方法、样本、主体、轮次口径、继续/停止/人工判断 | `benchmarks/README.md` 的冻结指标与边界；#55 已完成 SciFact dev 300、top-3 | 可写 SciFact Hit one 0.8467、Hit all 0.8333 及已有组件指标边界；不能据此评价三个展示 Project。 | #47、#56、#57 |
| P6 | 真实架构图、模块输入/处理/输出、非一次问答闭环 | `docs/adr/0017-research-world-redesign.md`、`docs/adr/0026-agent-runtime.md`、`docs/adr/0027-research-kernel.md` | Research Kernel 与 Agent Runtime 的职责和事件流可写；无提交版架构截图。 | #48、#50 |
| P7 | Qwen 模型/调用、任务、上下文、结构约束、Tool 协作、真实上下文图 | `docs/adr/0022-agent-spec.md`；历史 `orbits-49-run.json` 记录 `qwen3.7-flash`、20 请求、657082 token | 只能把该模型与用量写成历史 Artifact 事实，不能写成当前三题调用结果。 | #41、#43、#44、#48、#54 |
| P8 | 对象/范围、变量、已有认识/争议/未知、知识缺口及真实中间结果 | 三个 `project.json` 只含原始问题 | 可写原始问题；无当前 Pipeline 解析结果。 | #48 |
| P9 | 多候选、支持/反对证据、重复控制、统一假设表达 | `docs/adr/0017-research-world-redesign.md`；历史 q049 Trace 含多轮 revise | 生成、查重和 reflect 是设计事实；三题候选数量与质量不可写。 | #13、#20、#24、#48 |
| P10 | 相关性、证据一致性、冲突引用、可检验/证伪、重复、筛选 | `docs/adr/0021-review-pipeline.md`；历史 q049 Trace 含双 reviewer | 可写审核 contract 和历史审核事件；当前三题筛选结果不可写。 | #12、#23、#35、#48 |
| P11 | 预测、数据/条件、步骤/分析、支持/反对判据、停止/回退/补证 | `docs/adr/0021-review-pipeline.md`、`docs/adr/0020-graph-and-evidence.md` | Action 审核、执行凭据和 Artifact 是设计/代码事实；三题无当前计划和执行凭据。 | #21、#22、#46、#48 |
| P12 | 一次完整运行图、反馈返回点、失败处理、自动/人工反馈、前后变化 | 历史 q049 Trace；`benchmarks/README.md` 记录 Q21 worker 恢复和 Q49 UI 闭环 | Q21 恢复与 Q49 历史闭环可写为既有验收事实；均未达到本次三题验收。 | #45、#48、#50 |
| P13 | 125 题全量方法、共同输出、总体评价、失败保留、案例选择理由 | `docs/questions.json`；`research-world/projects/q001` 至 `q125` | 125 个连续输入存在，三题按报告覆盖选择；没有 125 题逐题输出。 | #45、#48 |
| P14 | 案例原文、变量、认识/证据、缺口、不确定性、第一轮设置 | `q021/q049/q112 project.json` 与三份全文 manifest | 案例输入和首份来源已固定；尚无第一轮真实设置。 | #48、#54 |
| P15 | 第一轮 H-01..03、依据、反证/替代、预测、处理结果、三步计划 | 历史 q049 报告/Trace 仅作旧系统 Artifact | 只能说明历史 Artifact 存在；不能填入当前第一轮表。 | #48 |
| P16 | 第一轮问题、判断依据、影响、第二轮调整、触发证据/人工意见 | 历史 q049 Trace 记录 revise 与 reviewer 反馈 | 可引用历史 revise 机制示例；当前案例没有第一轮问题分析。 | #48、#50 |
| P17 | 两轮证据/假设/筛选/计划/边界变化、改善、代价、停止原因 | 历史 q049 报告及 report review | 可写历史 report review 明示的范围限制；当前两轮对照不可写。 | #48、#50 |
| P18 | 至少一种同条件对照/消融、评价、结果、优势、代价 | `benchmarks/README.md` 含已冻结组件对照 | 组件对照可写入技术评测，不可冒充展示 Project 的同条件对照。 | #47、#56、#57 |
| P19 | 125 题完成/部分/失败/稳健性数量，失败原因，边界，泛化 | 125 个输入文件；项目语料存在跨题文本串位 | 可披露输入完整但输出未运行，并把语料串位列为数据边界；无完成率可写。 | #45、#48 |
| P20 | 源码/环境/运行、Qwen 凭证、125 输出、案例日志、API/前端、视频、自检 | 仓库源码、`research-world/README.md`、历史 q049 Artifact/Trace | 源码和 Compose 入口存在；本次未启动服务，不能写“可正常核验”。 | #44、#46、#48、#50 |
## 当前阻塞
- #48 尚未通过 WebUI 真实运行 `q021`、`q049`、`q112` 到各自 `admitted >=100`，所以 P1、P8-P17、P19 不得填入结果性陈述。
- #54 尚未提供文献研究员 Preset；三份远端全文只是引用准备，不是 Source Admission。
- #56、#57 尚未完成官方全量 Benchmark；#55 的完整 SciFact 检索指标仍是组件指标，不得写成完整系统分数。
- 125 题输入存在跨题文本串位，当前没有独立修复 issue；#45/#48 运行时须原样披露，不能静默改题或省略失败。
