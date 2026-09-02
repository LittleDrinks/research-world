---
project: q049
artifact: review-v6
role: independent-review
reviewer_session: 01a05f71-605a-72f2-8794-c212a321d464
reviewed: v6.md
supersedes: review-v5.md
prior_review: review-v5.md
verdict: deliverable
sources:
  - id: S1
    title: "On the Dynamical Stability of the Solar System"
    authors: "Batygin; Laughlin"
    year: 2008
    doi: "10.1086/589232"
  - id: S2
    title: "A numerical experiment on the chaotic behaviour of the Solar System"
    authors: "Laskar"
    year: 1989
    doi: "10.1038/338237a0"
  - id: S3
    title: "Tidal Decay of Close Planetary Orbits"
    authors: "Rasio; Tout; Lubow; Livio"
    year: 1996
    doi: "10.1086/177941"
  - id: S4
    title: "Gravitational Radiation from Point Masses in a Keplerian Orbit"
    authors: "Peters; Mathews"
    year: 1963
    doi: "10.1103/PhysRev.131.435"
  - id: S5
    title: "Gravitational Radiation and the Motion of Two Point Masses"
    authors: "Peters"
    year: 1964
    doi: "10.1103/PhysRev.136.B1224"
  - id: S6
    title: "Existence of collisional trajectories of Mercury, Mars and Venus with the Earth"
    authors: "Laskar; Gastineau"
    year: 2009
    doi: "10.1038/nature08096"
---
# q049 V6 独立核验
## 结论
六维均为 2 分，总分 **12/12**；S1-S6 的题名、作者、年份与 DOI 均匹配，**6/6**。未发现 Major 或 Critical 缺陷；`v6.md` 可交付。
## 版本边界
V5 至 V6 的差异限于 artifact 与 supersedes 元数据、标题、去除自我指涉、planned/executed 表述和规范措辞；科学主张、S1-S6、概率归因和已公开的 Earth-Sun 凭据未漂移。第 9 节表格保留 V4 至 V5 的历史修正，V6 的实际变化以直接差异为准。
## 六维评分
| 维度 | 分 | 依据 |
|---|---:|---|
| 问题理解 | 2 | 对象、范围、变量、争议与题干前提校正完整；保守动力学、耗散、混沌和太阳演化的边界明确。 |
| 文献证据 | 2 | S1-S6 均有可解析 DOI，来源作用和局限与关键陈述相连。 |
| Direction 质量 | 2 | D1、D2、D3 分别对应保守动力学、非保守耗散和混沌失稳，机制、替代解释与不确定性可区分。 |
| 科学推理 | 2 | 守恒、微弱耗散、低概率混沌失稳和太阳演化时间边界没有互相替代或越界归因。 |
| 研究计划 | 2 | 数据、方法、基线、对照、判据、产物、资源、风险和停止条件齐全；模拟仍标为 planned。 |
| 表达与追溯 | 2 | 来源 ID、版本关系、方向比较、计划和已执行的引力波计算形成可回读主线。 |
| **总分** | **12/12** | 无 0 分维度。 |
## S1-S6 核验
| ID | 书目信息 | 结果 |
|---|---|---|
| S1 | Batygin; Laughlin (2008), `10.1086/589232` | match |
| S2 | Laskar (1989), `10.1038/338237a0` | match |
| S3 | Rasio; Tout; Lubow; Livio (1996), `10.1086/177941` | match |
| S4 | Peters; Mathews (1963), `10.1103/PhysRev.131.435` | match |
| S5 | Peters (1964), `10.1103/PhysRev.136.B1224` | match |
| S6 | Laskar; Gastineau (2009), `10.1038/nature08096` | match |
25/2501 的约 1% 水星不稳定统计归于 S6；S1 只用于构造的约 1.261 Gyr 失稳轨迹，归因未混淆。
## Peters 与条件质量损失
公式为 `t=(5/256)(c^5/G^3)(a^4/(m1*m2*(m1+m2)))`，秒到 Julian year 的换算为 `31557600 s`。
| 计算 | 独立结果 | 对照 |
|---|---|---|
| V6 Earth-Sun | `t=3.373993930366e30 s=1.069154159494e23 yr`；`P=196.290559982 W` | 与 `3.374e30 s`、`1.069e23 yr`、`196.291 W` 的显示精度一致。 |
| Earth-Sun | `t=3.374197216379e30 s=1.069218576945e23 yr` | 匹配记录的两组输入结果。 |
| Mercury-Sun | `t=1.370536799260e30 s=4.342969044731e22 yr` | 匹配记录的两组输入结果。 |
条件输入 `(1e-14 M_sun/yr)(5e9 yr)` 给出 `Delta M/M=5e-5`；绝热近似的 `Delta a/a` 为约 `+0.005000%`，精确的一阶外修正为 `+0.005000250013%`，故 `0.005%` 在声明精度下成立。
## 四类主源
| 类别 | 主源 | 绑定 |
|---|---|---|
| 引力辐射 | Peters (1964), `10.1103/PhysRev.136.B1224` | 两组圆轨道 Peters 计算。 |
| 太阳系动力学 | Laskar; Gastineau (2009), `10.1038/nature08096` | 2501 条 5 Gyr 积分与约 1% 水星高偏心率结果。 |
| 太阳演化 | Schroder; Connon Smith (2008), `10.1111/j.1365-2966.2008.13022.x` | 巨星阶段质量损失和轨道外移边界。 |
| 恒星风 | Johnstone; Gudel; Luftinger; Toth; Brott (2015), `10.1051/0004-6361/201425300` | `1e-14 M_sun/yr` 的取整条件输入；不作为五十亿年外推。 |
上述两组计算、条件算术和四类主源属于同题数值对照的独立复核，不改变 `v6.md` 的 S1-S6 计数或已执行边界。
RESULT: DELIVERABLE
