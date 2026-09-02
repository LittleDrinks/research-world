---
project: q049
artifact: receipt-v8
role: independent-audit
auditor_session: 01a05fb1-087d-7090-8261-a8e0a465c753
reviewer_session: 01a05fa3-b792-7822-8037-fe839e48a01c
reviewed:
  - v7.md
  - review-v7.md
supersedes: receipt-v7.md
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
verdict: deliverable
---
# q049 V7 核验结果
- 六维各 2 分，合计 12/12；S1-S6 的题名、作者、年份与 DOI 为 6/6 匹配。
- 输入 SHA-256：`v7.md` `dde87b3fe5779ced4a23b3f28eb00bf68bdc1251e190c7eeb0ec67e1f1420287`；`review-v7.md` `c921e44571c6d83078376745c10227671d0cd2f3b9ce938822dd9d94a67fb3c1`。
- Peters 两体圆轨道对照：Earth-Sun `t=3.373993930366e30 s`、`P=196.290559982 W`；条件质量损失给出 `Δa/a=+0.005000250013%`，`0.005%` 在声明精度下成立。
- 边界：executed 仅为 Earth-Sun 引力波计算；planned 为 N 体积分、广义相对论与质量损失对照、潮汐建模和蒙特卡洛评估。
RESULT: DELIVERABLE
