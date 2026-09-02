---
project: q089
artifact: review-v12
role: independent-review
reviewer_session: "01a05fd9-1280-7692-9ab8-4eff803e5d85"
author_session: "01a05fd4-8be5-7713-83b1-0c1372b9a18e"
reviewed: v9.md
verdict: revise
sources:
  - role: reviewed-candidate
    path: research-world/evidence/contest-2026/q089/v9.md
  - role: previous-baseline
    path: research-world/evidence/contest-2026/q089/v8.md
  - role: prior-independent-review
    path: research-world/evidence/contest-2026/q089/review-v11.md
  - role: run-record
    path: research-world/evidence/contest-2026/q089/run.md
  - role: original-question
    path: research-world/projects/q089/project.json
  - role: primary-doi-check
    id: S3
    url: "https://www.nature.com/articles/s41586-022-04473-y"
---
# q089 独立核验
## 六维评分
| 维度 | 分数 | 依据 |
|---|---:|---|
| 问题界定 | 2/2 | 原题列出的 PV、热电、压电和 TPV 均被覆盖，并把热力学、器件、实验记录和商业效率分开。 |
| 来源 | 1/2 | S3 的题名与 41.1% +/- 1%、1.4/1.2 eV、2,400 C 条件获 Nature 一手页面支持；LONGi HIBC 27.81%（2025 年 4 月、ISFH）没有与 S1-S8 中的具体一手来源关联。 |
| Direction 与比较 | 2/2 | PV 光谱管理、TPV 光子回收和热电输运分别给出机制、反证、替代解释、可区分预测和不确定性；主方向与两个对照的取舍明确。 |
| 科学推理 | 2/2 | SQ 的适用条件、TPV 的温度边界、器件效率与系统效率的区别，以及 R_sub 消融的因果主张相互一致。 |
| 计划 | 1/2 | 消融、敏感性、停止和回退条件具备，但 0.74 eV TPV 基线没有冻结发射体温度和光谱、视场因子、反射率、器件结构或详细平衡计算口径，不能复现或解释 R_sub 的量化差异。 |
| 表达与追溯 | 1/2 | 核心论证可追溯，但新增的产物表述不是纯删除，且受审候选尚未被终态所有者选为 final。 |
| 合计 | 9/12 | 两项交付阻塞仍未解决。 |
## 机械核验
基线与候选的最小差异为 5 行新增、29 行删除。问题界定、S1-S8 条目、数值、三个 Direction、横向比较和步骤逐字不变；版本标识、标题版本、阶段词和历史变更说明被移除或更新。
产物项从仓库路径替换为 TPV 光谱-温度响应表、R_sub 消融结果和敏感性分析报告。该替换与既有步骤一致，未改变机制、数值或来源，却新增了计划表述；核心科学零漂移成立，但“只删除自指内容”的机械断言不成立。
## 执行与终态边界
趋势分析、SQ 曲线复现、R_sub 消融和系统级外推仍为 planned，未见新的仿真、实验、数值输出或执行凭据。终态由运行记录所有者裁决；该记录当前选择较早候选及其评审为 final 和 final_review，评审 verdict 不能把受审候选提升为终态。
## 修订条件
1. 为 LONGi/ISFH 的 27.81% 记录补入并在主张处关联一手来源，或删除该精确主张。
2. 冻结 TPV 基线的发射体温度和光谱、几何或视场、背反射率、器件结构、效率定义与计算实现，并把 R_sub 比较预先定义为可复核判据。
3. 要么恢复纯删除性质，要么将产物项的改写显式作为计划正文变更；随后由运行记录所有者在独立通过后更新 final 选择。
RESULT: REVISE
