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
  - id: scienceagentbench
    title: "ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery"
    url: https://arxiv.org/abs/2410.05080
  - id: mlagentbench
    title: "MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation"
    url: https://arxiv.org/abs/2310.03302
  - id: paperbench
    title: "PaperBench: Evaluating AI's Ability to Replicate AI Research"
    url: https://arxiv.org/abs/2504.01848
  - id: ai-scientist-v2
    title: "The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search"
    url: https://arxiv.org/abs/2504.08066
  - id: agent-laboratory
    title: "Agent Laboratory: Using LLM Agents as Research Assistants"
    url: https://aclanthology.org/2025.findings-emnlp.320/
verified: 2026-09-01
---
# 2026 挑战杯阿里云榜题 XH-202619
赛道一·科学发现，方向 1A·科学假设生成与研究计划设计；基座使用 Qwen 系列。
## 提交约束
- 技术方案 PPT/PDF 不超过 20 页。模板 P1 的“不超过30页”与首页说明、P20 自检冲突，采用两处一致且更严格的 20 页。
- 作品简介、Qwen 与 AI 技术说明各不超过 300 字；模板未设其他总字数上限。填写系统报名作品名、最终作品名、赛道方向和可选宣传材料链接。
- 团队信息按模板粘贴盖章报名表第一页、第二页截图；报名所需个人信息按模板提交，非必需个人信息脱敏。
- 方向 A 保留官方 125 题逐题输出；失败、证据不足和需人工判断的题目不得省略。
- 交付源码、环境、依赖、运行方法、Qwen 调用方式及凭证或截图、125 题输出、代表案例输入与有次序的 V1、评审、最终版及必要日志、测试 API、示例请求和可交互前端。
- 演示视频可选，不超过 10 分钟；视频经夸克网盘提交分享链接。
- 候选假设和研究计划仍需研究者审查，不得表述为已验证科学发现；受限数据与密钥不得进入交付物，Qwen 调用凭证或截图不得暴露 API 密钥。
## 模板结构
- Word 元数据：21 页、1125 词、6415 字符、7525 个含空格字符。
- 正文：封面加 P1-P20，161 个段落、26 张表；唯一图片位于正文第 6 段，为 P1 两页盖章报名表截图；脚注、尾注和嵌入附件均为空。
- 版式：Letter 纸张，四边 1 英寸页边距，首页独立页眉；模板自身 21 页不改变提交材料 20 页上限。
- 必需图示：P2 总体思路、P6 真实架构、P7 真实上下文结构、P12 真实工作流程。
- P1-P20 可按真实内容合并，不要求逐页对应或填满 20 页；完整案例位于 P14-P17，P18 至少一种同条件比较。
- 较长代码、日志和数据表进入允许的附件，不挤占论证正文。
## 展示 Project
采用 1 个旗舰加 4 个差异化验证，覆盖数值计算、计算材料、冲突文献、湿实验规划和时序数据；Project 身份只使用小写 `qNNN`。每例以 V1→独立评审→最终版、证据完整性、Trajectory 和明确终态为验收，不用节点数量代理。
| 层级 | Project | 科学问题 | 验证形态 | 完成边界 | issue |
|---|---|---|---|---|---|
| 旗舰 | `q049` | Why don’t the orbits of planets decay and cause them to crash into each other? | 文献约束、数值积分、复跑哈希、正反证据、报告与导出 | 完整 Workflow；V1/最终版可比较；当前 `q049` 的 Trajectory/Artifact 独立于历史 `orbits-49` | #59 |
| 次级 | `q089` | How can we break the current limit on energy-conversion efficiencies? | Matbench 真实数据、计算材料、支持与否证路径 | 既有 quantity-unit 负例与不泄露标签的正例均保留 | #111 |
| 次级 | `q021` | Can we ever overcome antibiotic resistance? | 文献冲突、来源质量、检索失败恢复 | 冲突证据不压成肯定结论；来源不足显式保留 | #60 |
| 次级 | `q112` | Can we create an environmentally friendly replacement for plastics? | 结构化湿实验计划、风险与人工 Gate | 不伪造实验结果；外部执行缺失时结束为 `waiting_human` | #61 |
| 次级 | `q098` | Why do we need sleep? | Sleep-EDF、时序分析、人体数据边界 | #62 先修复跨题文本；人体可穿戴数据缺失时结束为 `waiting_human` | #104 |
`research-world/projects/q049/project.json` 与已删除的 `orbits-49/project.json` 经空白规范化后 title、full_text 完全相同；唯一 Project identity 为 `q049`。`research-world/evidence/orbits-49-*` 仅保留 2026-08-11 历史 Artifact/Trajectory。
## 运行方法
科研主线为“问题界定→一手文献与知识缺口→三个机制或路线不同的 Direction→证据与替代解释比较→研究计划→V1→独立评审→最终版”。研究计划说明数据或材料、方法、对照或基线、判断方式、产物、资源和伦理条件；可检验性是质量项，不是唯一门槛。候选和计划不表述为已验证发现。
### 版本与 Session
- V1 Session：全新 Pi Session，只读取 canonical Project、任务协议和检索能力，不读取评审或其他候选正文。
- Review Session：全新 Pi Session，只读取 canonical Project、V1、V1 来源记录和统一 rubric，不读取 V1 Trajectory；输出逐项分数、引用核验、具体缺陷和修改要求。
- Revision Session：全新 Pi Session，读取 canonical Project、V1、来源记录和 review；生成 V2。未通过时，每次修订继续使用全新 Session 并保留 V3、V4；提交叙事固定展示 V1→评审→最终版，不覆盖旧版本。
- Session 归属固定为 Project 加版本或职责；RESULT 记录实际 Session id、模型、调用和 token。正式案例至少保留一组 Qwen 结果；其他上游模型可用于评审、修订或鲁棒性比较。模型变更后的提升不归因于 Workflow。
### 深度案例 rubric
每项 0、1、2 分：0 为缺失或不可用，1 为存在但有实质缺陷，2 为可直接进入提交材料。最终版须总分至少 10/12、无 0 分、关键引用抽查通过、无伪造执行结果，并由独立 reviewer 判定可交付。
| 维度 | 2 分条件 |
|---|---|
| 问题理解 | 对象、范围、争议和知识缺口准确，未继承错误前提 |
| 文献证据 | 关键陈述有可核验来源，来源作用与局限明确，无错引或虚构引用 |
| Direction 质量 | 三个方向在机制或路线层面不同，依据、替代解释和不确定性可比较 |
| 科学推理 | 结论强度不超过证据，反对证据和失败路径真实影响方向选择 |
| 研究计划 | 数据、方法、对照、判断方式、产物、资源和风险足以让研究者继续实施 |
| 表达与追溯 | 问题、证据、方向、取舍和计划形成单一主线，来源与版本可回读 |
### 终态
按表中顺序裁决，命中即停止；每个 Project 恰好一个终态。
| 终态 | 判定 |
|---|---|
| `waiting_human` | 继续运行需要领域裁决、受限数据权限、安全或伦理决定；记录待决问题，不伪造替代结果 |
| `failed` | 不需要人类裁决，但模型、传输或 Tool 经一次重试后仍无可用产物，或返回内容在科学上不可用；重试不得覆盖原 Session |
| `completed` | 最终版通过 rubric、引用抽查和独立评审，计划项与已执行项明确分开 |
| `partial` | 未命中以上终态且已形成有用研究材料，但来源不足、争议未解或截止前未达到 rubric；保留具体缺口 |
### Benchmark
q049 在相同问题、模型、检索权限和近似输出预算下比较直接回答与 Workflow V1，报告六维 rubric、引用有效率、Direction 差异、计划可用性和 token。深度案例比较 V1 与最终版的分数变化、缺陷修复率、新增代价、调用和 token。Q001-Q125 报告四类终态、结构完整率、引用抽查通过率、领域分布、调用和 token。外部 benchmark 只提供评价方法，不冒充本项目成绩。
### Herdr 任务协议
- `MISSION`：固定 Project id、原始问题、任务协议版本、Session 职责、模型、来源权限、输出位置和禁止项。
- `BACKBRIEF`：调用模型前复述 Project、问题边界、计划检索、预期文件、Session 职责、模型和已知限制；Project、版本或职责不一致时停止。
- `RESULT`：形成终态后报告终态、模型、Session id、调用和 token、来源、版本产物、rubric、失败和未解决项；Herdr 的 `idle`、`done`、`blocked` 不是科研 RESULT。
- 计划与执行分开表述。实际执行保存输入、命令或方法、输出、退出状态、数据或文件哈希和限制；未执行步骤明确标为 planned，不用模拟结果填充。
- API key 和其他凭证只存在于 Runtime 环境，不得进入 prompt、Tool I/O、Trajectory、Artifact、清单、截图或失败输出。发现泄漏立即停止发布、隔离受影响产物、脱敏并重新运行；含密钥版本不得作为证据。
## P1-P20 证据矩阵
设计 ADR 只证明约定；历史 Artifact/Trajectory 只证明对应历史运行；科学结果必须由当前 Project 中具有证据闭包的 Claim、关联 Source/Experiment/Artifact、Trajectory 和评价记录共同支持。
| 章节 | 模板要求字段 | 所需系统能力/科学结果 | 证据位置 | 当前状态 | 缺口 issue |
|---|---|---|---|---|---|
| P1 | 盖章报名表第 1、2 页截图；系统报名作品名、最终作品名、赛道方向、300 字作品简介、300 字 Qwen/AI 说明、可选宣传链接；具体问题、核心方法、代表结果 1/2（对象、口径、结果）、主要局限；API/前端、代表案例、报告、源码、Qwen 调用凭证/截图、125 题输出、可选 10 分钟视频 | 汇总经核验的作品身份、方法、两项科学结果与限制；从 Project/报告投影生成可追溯摘要；报名所需个人信息按模板提交，非必需个人信息脱敏，受限数据、密钥不交付 | 原模板 `docs/赛道一-方向1A-科学假设生成与研究计划设计-提交要求及模板.docx`；代表案例 `project.json`；后续报告投影、Artifact、提交入口 | 案例输入存在；q098 canonical 文本仍待修复，报名字段、两项代表结果和交付入口未形成 | 报名信息由团队提供；#36、#44、#59、#60、#61、#104、#111、#112 |
| P2 | 现有方法的具体不足、实际解决范围；已实现的科学问题理解、证据组织、候选生成、比较筛选、研究计划、反馈修订；总体思路图；主要输出；125 题实际测试；与直接大模型问答的差异 | 形成“问题→知识缺口→证据→候选→筛选→计划→反馈”闭环并逐项证明已实现功能、实际输出、全量结果和同条件直接问答差异 | `docs/adr/0037-research-graph-and-dynamic-workflow.md`；`research-world/projects/q001` 至 `q125` | Research Graph、动态 Workflow 和报告投影有设计/代码；125 项仅有输入，未形成总体思路成图、全量输出或直接问答实测 | #45、#47、#50、#59、#60、#61 |
| P3 | 对事实/文献解释/模型推断、知识缺口转候选、可检验/证伪、反对证据/替代解释、候选非结论五项分别填写实际做法与理由；说明识别缺口的信息、约束假设的证据及支持/削弱/否定结果 | Claim 与 Source/Experiment/Artifact 的证据闭包、Direction、supports/refutes 关系和独立审核；展示代表案例中每项原则的实际输入、判据和 verdict | `CONTEXT.md`；`docs/adr/0037-research-graph-and-dynamic-workflow.md` | 五项原则有领域设计；五个案例尚无同口径实跑结果证明实际采用及效果 | #12、#23、#35、#59、#60、#61、#104、#111 |
| P4 | 每条实际资料的名称、获得/使用方式、对假设的作用、局限；来源可用性判断；证据不足/冲突处理；引用与证据对应；只列实际使用内容 | 获取全文、核验 authors/year/identifier/license/hash 并归档 Source；Claim 绑定来源与 Artifact，冲突保留 supports/refutes 关系 | `docs/submission-reference-manifest.json`；远端 `/data/zsm/ai4s/references/issue-53/`；历史 `research-world/evidence/orbits-49-run.json` | Q021/Q049/Q112 各一份官方全文的书目、许可、URL、PDF 属性、哈希和归档路径已核验；尚未成为当前案例的 Source/Claim 证据链，Q089/Q098 来源未固定 | #30、#54、#59、#60、#61、#104、#111 |
| P5 | 每项评价内容、具体方法、对象/样本、结果如何影响后续；评价重点与理由；程序/模型/团队/专家主体；V1 与最终版口径是否一致及变化原因；继续、停止、转人工条件 | 从 Trajectory、Artifact 和版本结果计算过程指标，冻结样本与 rubric；评价结果触发修订、停止或人工判断，报告口径变化 | `benchmarks/README.md`、`benchmarks/literature_bench/reuse_selection.md`、`docs/benchmarks/design.md`；已关闭 Benchmark #55；已完成 Benchmark #56、#57；`docs/adr/0019-evaluation.md`、`docs/adr/0024-deterministic-metrics.md` | #56、#57 的官方全量 Benchmark 已完成并通过独立验收；SciFact dev 300、top-3 的 Hit one 0.8467、Hit all 0.8333 可写为组件指标；五个案例的评价表、版本间口径和处理结果未形成 | #47、#59、#60、#61、#104、#111 |
| P6 | 真实架构图；科学问题理解、证据获取组织、候选生成、核验筛选、计划/反馈五模块各自输入、核心处理、输出、下一模块关系；说明非一次问答及进入后续版本的中间结果 | Research Graph、Agent Runtime 与主 Agent 分责；Question、Source、Direction、Experiment、Trajectory、Artifact 和反馈构成动态 Workflow | `docs/adr/0026-agent-runtime.md`、`docs/adr/0037-research-graph-and-dynamic-workflow.md` | 模块职责和数据流有设计/代码；提交版真实架构图及五模块逐格运行证据未形成 | #45、#50、#59、#60、#61 |
| P7 | 实际 Qwen 模型/调用方式、具体任务、单次上下文、结构化输出/格式约束、检索/代码/Tool 协作；真实上下文结构图含问题、已有/反对证据、关键约束、历史结果、反馈；抑制无依据生成措施、更新/多次调用触发、实际变化 | AgentSpec 快照模型与 Tool；独立 Session、来源引用和独立审核；Trajectory 证明真实上下文、调用次数、触发条件和前后结果 | `docs/adr/0022-agent-spec.md`、`docs/adr/0026-agent-runtime.md`；历史 `research-world/evidence/orbits-49-run.json` | 历史 q049 可证明 `qwen3.7-flash`、20 请求、657082 token；不能作为当前五个案例的模型、上下文和效果证据，真实上下文图未形成 | #44、#103、#106、#109、#110、#113 |
| P8 | 识别对象/范围、条件/关键变量、已有认识/争议/未知、可处理知识缺口四步的实际做法、中间结果、对假设生成的用途；一题真实中间结果示例 | 主 Agent 把 Question 解析为约束与可引用知识缺口，并将结果交给 Direction 生成 | 代表案例 Project 输入；后续研究对象与 Trajectory | 只有原始科学问题；对象、变量、认识/争议/未知、缺口及用途尚无当前运行结果 | #59、#60、#61、#104、#105、#111 |
| P9 | 从缺口形成解释、多个可区分候选、纳入支持/反对证据、控制重复/空泛/不可检验、统一表达五项实际做法及解决的问题；每条候选含核心陈述、依据、正反证据、预测、替代解释、不确定性 | 主 Agent 生成三个不同 Direction，检索与独立审核控制重复并保留完整比较；给出真实候选数量和内容 | `docs/adr/0037-research-graph-and-dynamic-workflow.md`；历史 q049 Trajectory/Artifact | 生成、查重和修订有历史样例；五个案例没有按模板字段形成的当前候选结果 | #13、#20、#24、#59、#60、#61、#104、#111 |
| P10 | 相关性、证据一致性、冲突/错引、可检验/证伪、候选重复、是否进入计划六项的判断与处理结果；说明保留、合并、降级、淘汰规则；给出一组选/不选实例 | 独立 review 产生逐项 verdict，主 Agent 决定保留、合并、降级或淘汰 Direction，并保留对比候选及理由 | `docs/adr/0037-research-graph-and-dynamic-workflow.md`；历史 `research-world/evidence/orbits-49-run.json` | 审核 contract 和历史 reviewer 事件存在；五个案例的六项结果及选/不选对照未形成 | #12、#23、#35、#59、#60、#61、#104、#111 |
| P11 | 待验证预测、所需数据/资料/实验条件、研究步骤/分析方法、各结果支持/反对对象、停止/回退/补证条件；具体/可复核检查；已具备执行条件与建议项；禁止“进一步研究”空话 | 研究计划明确 planned 与 executed；实际执行保存输入、方法、输出、退出状态、数据或文件哈希和限制，主 Agent 按证据决定继续、修订、停止或转人工 | `docs/adr/0020-graph-and-evidence.md`、`docs/adr/0037-research-graph-and-dynamic-workflow.md` | 计划、执行凭据和终止语义有设计/代码；五个案例无按字段生成的计划或当前执行凭据 | #21、#22、#59、#60、#61、#104、#111 |
| P12 | 真实全流程图及反馈返回点；至少三项实际反馈/失败的情况、发现、处理、后续影响；自动反馈、人工调整、保留的前后变化 | 动态 Workflow 串联接题、候选、计划、执行、review、revision；V1、评审、最终版和失败 Trajectory 区分自动与人工反馈 | `benchmarks/README.md`；历史 q049 Trajectory/Artifact；Q21 worker 恢复记录 | Q21 恢复和 q049 历史闭环可写为既有验收事实；当前五个案例的完整 Workflow、三项失败表、前后变化及流程图未形成 | #45、#50、#59、#60、#61、#104、#108、#111 |
| P13 | 125 题单题运行方式、共同输出、总体评价、证据不足/失败/人工判断保留；案例领域/特点、选择理由、展示能力、不能代表的题目/条件 | 对 125 个 canonical Project 使用同一任务协议和评价并保留全部终态；按研究形态选择案例且声明外推边界 | `docs/questions.json`；`research-world/projects/q001` 至 `q125`；`readme.md` 的展示 Project 记录 | Q001-Q125 identity 连续唯一，1+4 案例选择理由已记录；125 题共同输出/评价未运行，案例边界待实证 | #45、#48、#62、#91 |
| P14 | 案例问题原文、对象/变量、已有认识/主要证据、知识缺口、不确定性/争议；第一轮证据/约束、生成目标、模型/方法设置、评价口径 | 将 canonical Question、Source 和约束投影为 V1 输入快照，保存模型、方法和 rubric | 代表案例 `project.json`；`docs/submission-reference-manifest.json`；后续 V1/Trajectory | 案例输入存在；q098 canonical 文本和 Q089/Q098 primary Source 未固定，其余科学内容与第一轮设置没有当前运行证据 | #54、#59、#60、#61、#62、#104、#111 |
| P15 | H-01/H-02/H-03 的依据、反证/替代、预测、第一轮处理结果；三步计划内容及每步可支持/反对/区分对象；保留重复、证据不足、不可检验和不具体的原始结果 | V1 保留全部 Direction、review verdict 和计划，不以人工精选覆盖原结果 | 历史 q049 Trajectory/报告仅作旧系统 Artifact；后续当前 Project 研究对象/Trajectory | 历史 Artifact 存在；当前展示案例没有可填入第一轮表的真实候选和计划 | #59、#60、#61 |
| P16 | 至少三项第一轮具体问题、判断依据、科学结论/计划影响、第二轮实际调整；触发证据/评价/人工意见；增删改、不变项及理由、预期改善 | 独立 review 绑定问题与修改要求，Revision Session 引用触发证据并保留未改项 | 历史 q049 Trajectory 的 revise/reviewer 反馈；后续版本与 Session lineage | 历史 revise 可作机制样例；当前案例无逐项第一轮问题、触发依据和第二轮调整 | #50、#59、#60、#61 |
| P17 | V1 与最终版的证据、Direction、筛选、计划、不确定性/边界及变化原因/结果；改善、未改善/新代价、停止或继续理由 | 以同一 rubric 比较有次序的 V1 和最终版，Trajectory/Artifact/Session lineage 证明变化；不新增 Round 领域对象 | 历史 q049 report/review；后续 V1、review、最终版和报告投影 | 历史 review 有范围限制；当前案例尚无两版可比结果或停止/继续结论 | #50、#59、#60、#61 |
| P18 | 至少一种同条件对照/消融：对象、相同条件、评价方法、本作品结果、对照结果、结论/代价；分别说明科学逻辑、技术方法、结果改善及未改善/成本 | 冻结输入、模型/预算与评价口径执行对照，保存两侧 Trajectory/Artifact 和确定性指标 | `benchmarks/README.md`；已完成 Benchmark #56、#57；`docs/adr/0019-evaluation.md`、`docs/adr/0024-deterministic-metrics.md` | #56、#57 的官方全量 Benchmark 已完成并通过独立验收；这些 Benchmark 与 SciFact 指标可写技术评测，不能冒充展示 Project 同条件对照；模板要求的结果表未形成 | #47、#59、#60、#61 |
| P19 | 125 题完整形成、部分/证据不足、无法处理/需人工、重复运行/稳健性的数量/比例、判断口径、表现/原因；至少三类失败/边界的表现、原因、当前能力；可选外部泛化来源/方法/结果；候选与计划仍需研究者审查 | 汇总全部 Project 状态并保留失败；复跑计算稳健性；披露输入串位、适用边界和人工审查，不把结构合法当语义正确 | `docs/questions.json`；125 个 Project 输入；后续全量输出/评价；跨题文本串位事实 #62 | 仅能证明 Q001-Q125 identity/结构连续，不能报告完成率；Q098、Q107/Q109、Q118/Q121 等跨题文本串位作为边界披露 | #45、#62、#91 |
| P20 | 源码/环境/依赖/运行方法；Qwen 模型/调用及不含密钥的凭证或截图；125 题逐题输出；案例 V1、评审、最终版、必要日志；测试 API/示例请求/交互前端；可选视频；≤20 页、事实一致、125 题不省略、案例不代替总体、入口可核验、候选非结论、敏感信息妥善处理自检 | 形成自包含交付包与可复现入口；逐项校验文件、服务、调用证据、输出、日志、API/前端和隐私；报名所需个人信息按 P1 模板交付，非必需个人信息脱敏，受限数据/密钥排除 | 仓库源码；`research-world/README.md`；原模板；后续 125 题输出、案例 Trajectory/Artifact、API/前端入口 | 原模板、源码和 Compose 说明存在；服务未启动，Qwen 调用证明、125 输出、V1/评审/最终版、API/前端实测、视频与最终自检未完成 | #44、#46、#50、#59、#60、#61 |
## 当前阻塞
- #244 完成 Herdr 任务协议与独立验收后启动 #249。
- #249 五个深度案例达到可交付质量并通过独立评审后启动 #245；达到质量前不请求用户验收。
- #245 形成 125 个唯一终态后启动 #247；失败、部分完成和人工等待不得省略。
- #247 只使用实际运行与可回读 Artifact 填写 P13-P19；#56、#57 和外部 benchmark 只作组件或方法证据，不冒充完整系统成绩。
