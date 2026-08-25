---
sources:
  - id: prov
    title: "PROV-DM: The PROV Data Model"
    url: https://www.w3.org/TR/prov-dm/
  - id: micropublications
    title: "Micropublications: a semantic model for claims, evidence, arguments and annotations in biomedical communications"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC4530550/
  - id: nanopublications
    title: "Nanopublication Guidelines"
    url: https://nanopub.net/guidelines/working_draft/
  - id: graphmind
    title: "GraphMind: Interactive Novelty Assessment System for Accelerating Scientific Discovery"
    url: https://arxiv.org/abs/2510.15706
  - id: exploration-narrowing
    title: "AI Research Agents Narrow Scientific Exploration"
    url: https://arxiv.org/abs/2605.27905
  - id: verbalized-sampling
    title: "Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity"
    url: https://arxiv.org/abs/2510.01171
  - id: divalign
    title: "DivAlign: MMR-style de-homogenization for ideation"
    url: https://arxiv.org/abs/2607.28087
  - id: trrack
    title: "Trrack: A Library for Provenance-Tracking in Web-Based Visualizations"
    url: https://doi.org/10.1109/vis47514.2020.00030
---
# research-world 重设计：图谱主屏、Pipeline、auto 闭环
research-world 从多页控制平面改为知识图谱主屏加三视图，闭环为“命题→实验→反思→新命题”。
## 数据模型
- 节点固定四类：question / source / direction / experiment。result 并入 experiment 负载；claim 不独立成类——它是审计单位而非节点：review 启动时把 direction 的主张文本与 experiment 的结果文本拆成逐条原子断言，审计结果回写 direction 状态机与极性边。
- direction 带状态机 `proposed→supported/refuted`，必须承载完整证据链；边带 supports/refutes 极性。
- pending 虚线节点：agent 开工前 goal 先入图；完工后 admitted 填内容，驳回变幽灵（淡化并保留理由）。被拒 direction 与失败 experiment 全部留图。
PROV 记录生产过程 [prov]，Micropublications 与 Nanopublications 记录主张、证据和发布信息 [micropublications; nanopublications]；前者不推出后者。因此以少量工作流节点保存事实和来源，以 direction 的状态和极性边保存科学论证，不另造 result 或自由 claim 层。
## Pipeline 模板
Pipeline 是 `prompt/tool/spawn` stage 序列，policy 修饰算法，on 路由出口。启动时把 YAML 定义快照进 run；数据库与解释器不含 kind 枚举。
- brainstorm：生成 N 候选（可叠 Verbalized Sampling）→ embedding 查重（余弦 >0.8 转 reflect/合并并渐进披露阻断理由；0.6–0.8 LLM 成对裁决；<0.6 入池）→ MMR 贪心入池（质量分 − 0.2·max_sim）→ pending direction 入图 → review。
- research：plan → 执行 experiment → review（机械证据审计加质量/多样性分；双审冲突升级人，rebuttal 格式沉淀）→ reflect 产新 direction 候选。
GraphMind 将新颖性审核放在交互式图谱中 [graphmind]；实证研究显示复杂 Agent 仍会收缩探索空间 [exploration-narrowing]。Verbalized Sampling 只能提供生成多样性 [verbalized-sampling]，MMR 式去同质化才把多样性放入入池目标 [divalign]，故相似度阈值只是当前运营门槛，须随语料校准，不能成为节点语义。
## 恢复
- Control 只把人工闸门决策写入 run 并重新排队；Worker 是唯一 Pipeline 解释器驱动者。
- Worker 对 `running` run 续期；租约过期后其他 Worker 可原子领取并从 run 快照继续。
- stage 内每次产生节点、审查结论或实验计划后更新 `_pipeline` 检查点；恢复只执行检查点之后的动作。
- 实验步骤以 `(run_id, ordinal)` 幂等创建；已完成步骤读取持久输出，未完成步骤重新执行。
- run 失败时终结其创建的 pending 节点为 ghost，原始作用节点只解除 working。
- runner 将非法输入记录为非零执行结果；run 进入终态前，所有已启动 step 必须进入 completed 或 failed。
## 三视图（其余删除）
- 地图（主屏）：知识图谱式 kanban；科研日志是地图的时间视图；非 admitted 节点淡化。
- 对话：Project 下的 Thread；节点通过 `@node_id` 作为资源引用钉入，不拥有消息。
- 轨迹：从 run 下钻 Session、Turn 与 Tool；消息和工具细节来自 Runtime Trace。
Trrack 展示同一溯源状态可生成时间线、分支和聚合视图 [trrack]，所以地图、对话和活动是同一图谱的读模型；时间顺序、worker 状态和研究结论不互相替代。
## 变化
- 不保留向后兼容：旧节点类型、四页路由、审核/报告数据流直接删。
- 模型与 embedding 凭证只进入 Agent Runtime；Research Kernel 只持 ACP 地址。
