---
sources:
  - title: "ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery"
    url: https://arxiv.org/abs/2410.05080
  - title: "MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation"
    url: https://arxiv.org/abs/2310.03302
  - title: "PaperBench: Evaluating AI's Ability to Replicate AI Research"
    url: https://arxiv.org/abs/2504.01848
  - title: "The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search"
    url: https://arxiv.org/abs/2504.08066
  - title: "Agent Laboratory: Using LLM Agents as Research Assistants"
    url: https://aclanthology.org/2025.findings-emnlp.320/
status: accepted
---
# 赛题科研工作流
## 目标
Q001-Q125 逐题形成可审核的科学问题理解、文献证据、三个不同 Direction、方向比较和研究计划；q049、q089、q021、q112、q098 形成 V1、独立评审与 V2。候选和计划是研究起点，不表述为已验证发现。
## 科研主线
1. 界定问题：明确研究对象、已知范围、关键约束、争议和当前可处理的知识缺口；错误前提先纠正。
2. 获取证据：检索一手论文、预印本、官方数据或权威技术资料；二手资料只用于定位一手来源；记录来源类型、适用范围、冲突和不可访问项。
3. 生成方向：形成三个机制、数学结构或研究路线不同的 Direction；措辞变化不算新方向；至少一个方向体现替代解释、零假设或失败路线。
4. 比较方向：逐项检查问题相关性、证据一致性、与既有工作的差异、科学推理、主要风险和信息缺口；保留未选方向及理由。
5. 设计计划：为优先 Direction 给出所需数据或材料、研究步骤、分析方法、对照或基线、预期产物、判断方法、资源与伦理条件；可检验性是质量项，不是唯一门槛。
6. 形成版本：首次完整产物固定为 V1；独立 reviewer 只读取问题、V1、来源与统一 rubric，输出具体缺陷和修改要求；修订产物固定为 V2，禁止覆盖 V1。未通过时继续产生 V3、V4，但提交叙事仍明确展示 V1→评审→最终版。
7. 结束运行：记录 `completed`、`partial`、`failed` 或 `waiting_human`；来源不足、工具失败、伦理限制和未解决争议不得隐藏。
## 深度案例评价
每项按 0、1、2 分评审：0 为缺失或不可用，1 为存在但有实质缺陷，2 为可直接进入提交材料。
| 维度 | 2 分条件 |
|---|---|
| 问题理解 | 对象、范围、争议和知识缺口准确，未继承错误前提 |
| 文献证据 | 关键陈述有可核验来源，来源作用与局限明确，无错引或虚构引用 |
| Direction 质量 | 三个方向在机制或路线层面不同，依据、替代解释和不确定性可比较 |
| 科学推理 | 结论强度不超过证据，反对证据和失败路径真实影响方向选择 |
| 研究计划 | 数据、方法、对照、判断方式、产物、资源和风险足以让研究者继续实施 |
| 表达与追溯 | 问题、证据、方向、取舍和计划形成单一主线，来源与版本可回读 |
最终版须总分至少 10/12、无 0 分、关键引用抽查通过、无伪造实验结果，并由独立 reviewer 判定可交付。未达到时继续修订；客观来源、工具、安全或伦理阻断则保留当前版本并进入相应终态。
## Benchmark
| 比较 | 固定条件 | 指标 |
|---|---|---|
| q049 直接回答 vs Workflow V1 | 同一问题、模型、检索权限和近似输出预算 | 六维 rubric、引用有效率、Direction 差异、计划可用性、token |
| 深度案例 V1 vs 最终版 | 同一问题、来源边界和 rubric | 六维分数变化、缺陷修复率、新增代价、调用与 token |
| Q001-Q125 全量 | 同一任务协议版本 | 四类终态数量、结构完整率、引用抽查通过率、领域分布、调用与 token |
模型变更必须记录；更换模型后的提升不能归因于 Workflow。正式案例至少保留一组 Qwen 结果，其他上游模型可用于评审、修订或鲁棒性比较。
## Herdr 任务协议
`MISSION` 固定 Project id、原始问题、任务协议版本、模型、来源权限、输出位置和禁止项。深度案例 V1 不读取后续评审意见；任何运行不得写入凭证。
`BACKBRIEF` 在调用模型前复述 Project、问题边界、计划检索、预期文件、模型和已知限制；问题或 Project 不一致时停止。
`RESULT` 只在任务形成终态后输出，包含终态、模型、Session id、调用与 token、来源、产物位置、rubric、失败和未解决项；Herdr 的 `idle`、`done` 或 `blocked` 不是科研 RESULT。
## 产物
深度案例保留 `v1.md`、`review.md`、最终版本、直接回答对照或鲁棒性比较、紧凑运行清单；全量案例保留逐题结果和总清单。完整 Trajectory 作为运行审计保留，不进入正文，不自动成为 Claim，不进入凭证。
