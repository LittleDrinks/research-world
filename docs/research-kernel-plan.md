---
sources:
  - title: The Last Human-Written Paper: Agent-Native Research Artifacts
    url: https://arxiv.org/abs/2604.24658
  - title: Agent-Native Research Artifact
    url: https://github.com/ARA-Labs/Agent-Native-Research-Artifact
---
# Research Kernel
## 核心对象
- Question：待解决的科学问题。
- Claim：可证伪的科学主张，一等对象。
- Investigation：验证 Claim 的方法，覆盖实验、证明、模拟、观察、统计分析与文献核验。
- Evidence：Investigation 产生或引用的证据。
- Artifact：代码、配置、数据、图表与实验记录等不可变产物。
- DecisionEvent：准入、驳回、转向、停止等状态变化及理由。
## 研究图
`Question -> Claim -> Investigation -> Evidence -> Claim` 构成固定科研循环；supports/refutes 表达证据极性，竞争路线纵向分叉，DecisionEvent 表达状态变化，外部 agent invocation 只作为执行标记。
## 真实论文语料
语料覆盖数学证明、计算 benchmark、数值模拟、观测数据、湿实验、临床或人工反馈六种研究模态，每类十篇。每篇收集公开全文、摘要、来源版本、许可证与内容哈希，生成可回放 Kernel fixture、缺失与推断清单；七篇种子论文保留章节级人工分解，其余论文先完成摘要级分解。论文未公开的研究过程不得补写，重建关系标记 explicit 或 inferred。
## 面板原型
同一批真实论文数据分别渲染阶段泳道图、Claim 中心图、探索树图。每种方案必须支持定位主张状态、追溯原始证据、查看失败路线、区分明确记录与推断、识别下一步行动、定位促成状态变化的外部执行。
## ARA 导出
ARA 是 Kernel 的确定性导出协议，不是内部存储模型。Project 与 Question 映射到 manifest 和 `logic/problem.md`；Claim 映射到 `logic/claims.md`；Investigation 映射到 `logic/experiments.md`；方法与约束映射到 `logic/solution/`；Artifact 与环境映射到 `src/`；DecisionEvent 与失败分支映射到 `trace/exploration_tree.yaml`；Evidence 映射到 `evidence/`；来源关系映射到 `logic/related_work.md`。冻结 project revision 后导出并通过当前 ARA Seal Level 1，缺失内容显式保留。
## 写作隔离
官方 `ara/PAPER.md` 保持根 manifest 语义，传统论文写入 `publication/PAPER.md`。写作 agent 只读挂载冻结的 `ara/`，禁止联网，唯一可写目标是 `publication/PAPER.md`；完成后检查新增主张、数字、引用和证据指针。
## 目录目标
`research-world/src/research_world/` 下按 kernel、application、execution、ara、control、worker 分模块；verticals 保存垂类资源、验证器与 agent profile；fixtures 保存论文和 project 数据；web 与 tests 独立。顶层 harness 在外部 runtime adapter 完成后删除，旧 server 按所有权拆分，125 题由单一 catalog 生成，已完成的 prototype 删除，当前状态只维护在 MEMORY.md。
## 实施顺序
术语与 ADR -> 真实论文语料 -> UI 原型 -> Kernel -> ARA 导出 -> 外部执行接口 -> 目录迁移与删除。Research Kernel、ARA 映射和真实数据面板通过评审前，不改生产架构。
