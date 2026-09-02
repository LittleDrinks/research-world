---
project: q049
artifact: review-v7
role: independent-review
reviewer_session: 01a05fa3-b792-7822-8037-fe839e48a01c
reviewed: v7.md
supersedes: review-v6.md
prior_review: review-v6.md
verdict: deliverable
sources:
  - id: S1
    title: "On the Dynamical Stability of the Solar System"
    authors: "Batygin, Konstantin; Laughlin, Gregory"
    year: 2008
    doi: "10.1086/589232"
  - id: S2
    title: "A numerical experiment on the chaotic behaviour of the Solar System"
    authors: "Laskar, Jacques"
    year: 1989
    doi: "10.1038/338237a0"
  - id: S3
    title: "Tidal Decay of Close Planetary Orbits"
    authors: "Rasio, Frederic A.; Tout, Christopher A.; Lubow, Stephen H.; Livio, Mario"
    year: 1996
    doi: "10.1086/177941"
  - id: S4
    title: "Gravitational Radiation from Point Masses in a Keplerian Orbit"
    authors: "Peters, P. C.; Mathews, J."
    year: 1963
    doi: "10.1103/PhysRev.131.435"
  - id: S5
    title: "Gravitational Radiation and the Motion of Two Point Masses"
    authors: "Peters, P. C."
    year: 1964
    doi: "10.1103/PhysRev.136.B1224"
  - id: S6
    title: "Existence of collisional trajectories of Mercury, Mars and Venus with the Earth"
    authors: "Laskar, Jacques; Gastineau, Mickaël"
    year: 2009
    doi: "10.1038/nature08096"
---
# q049 V7 证据状态
## 结论
六维各 2 分，合计 12/12；S1-S6 的题名、作者、年份与 DOI 全部匹配，6/6。无 Major 或 Critical 缺陷，v7.md 可交付。
## 六维评分
| 维度 | 分 | 依据 |
|---|---:|---|
| 问题理解 | 2 | 对象、范围、变量、争议与四条题干前提校正完整；保守动力学、耗散、混沌与太阳演化边界清楚。 |
| 文献证据 | 2 | S1-S6 均有匹配 DOI；来源作用、局限和关键陈述相连，S1 的确定性轨迹与 S6 的概率统计未混用。 |
| Direction 质量 | 2 | D1、D2、D3 分别对应保守近可积动力学、非保守耗散与混沌稀有失稳，均含证据、替代解释、预测和不确定性。 |
| 科学推理 | 2 | 守恒、微弱耗散、低概率混沌失稳和太阳演化时间边界彼此区分；D1 直接回答不衰减，D2 补足实际耗散时标。 |
| 研究计划 | 2 | 数据、方法、基线、三个对照、判据、产物、资源、风险与停止条件齐全；模拟明确为 planned。 |
| 表达与追溯 | 2 | 问题、来源、方向、取舍、计划和唯一已执行计算构成单一主线，版本关系可回读。 |
| 总分 | 12/12 | 无 0 分维度。 |
## S1-S6 来源
| ID | 书目信息 | 结果 |
|---|---|---|
| S1 | Batygin; Laughlin (2008), 10.1086/589232 | match |
| S2 | Laskar (1989), 10.1038/338237a0 | match |
| S3 | Rasio; Tout; Lubow; Livio (1996), 10.1086/177941 | match |
| S4 | Peters; Mathews (1963), 10.1103/PhysRev.131.435 | match |
| S5 | Peters (1964), 10.1103/PhysRev.136.B1224 | match |
| S6 | Laskar; Gastineau (2009), 10.1038/nature08096 | match |
25/2501 的约 1% 水星不稳定统计归于 S6；S1 仅用于约 1.261 Gyr 的构造失稳轨迹。
## 版本差异
V6→V7 的变化限于 artifact、supersedes、标题、删除空白行及第 9 节版式。排除这些版本记录并规范化标题后，科学正文的全部非空行逐行一致，无科学漂移。
## Peters、0.005% 与四类主源
按第 7 节公开输入复算，Earth-Sun 圆轨道结果为 t=3.373993930366e30 s=1.069154159494e23 yr、P=196.290559982 W，与展示精度的 3.374e30 s、1.069e23 yr、196.291 W 一致。
条件输入 (1e-14 M_sun/yr)(5e9 yr)=5e-5；a∝M⁻¹ 给出 Δa/a=+0.005000250013%，故 0.005% 在声明精度下成立，且仅为条件算术而非五十亿年预测。
| 类别 | 主源 | 绑定 |
|---|---|---|
| 引力辐射 | Peters (1964), 10.1103/PhysRev.136.B1224 | 两体圆轨道衰变公式与 Earth-Sun 复算。 |
| 太阳系动力学 | Laskar; Gastineau (2009), 10.1038/nature08096 | 2501 条 5 Gyr 积分与约 1% 水星高偏心率结果。 |
| 太阳演化 | Schröder; Connon Smith (2008), 10.1111/j.1365-2966.2008.13022.x | 巨星阶段质量损失和轨道外移边界。 |
| 恒星风 | Johnstone; Güdel; Lüftinger; Toth; Brott (2015), 10.1051/0004-6361/201425300 | 1e-14 M_sun/yr 的取整条件输入，不作长期外推。 |
四类主源用于数值对照，不增减 S1-S6 的 6/6 计数。
## 执行边界
已执行：第 7 节 Earth-Sun 引力波计算保留输入、公式、命令、输出、退出码和哈希。planned：N 体积分、广义相对论与质量损失对照、潮汐建模和蒙特卡洛评估；未把模拟结果表述为已执行。
RESULT: DELIVERABLE
