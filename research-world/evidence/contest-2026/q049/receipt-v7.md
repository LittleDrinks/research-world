---
project: q049
artifact: receipt-v7
role: independent-audit
auditor_session: 01a05f7d-eb58-73d3-91a7-3f25f4e9ba70
reviewer_session: 01a05f71-605a-72f2-8794-c212a321d464
reviewed:
  - v6.md
  - review-v6.md
supersedes: receipt-v6.md
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
# q049 V6 独立审计
- 六维各 2 分，合计 12/12；S1-S6 的题名、作者、年份与 DOI 6/6 匹配。
- 输入 SHA-256：候选稿 `c44f3bd614585fd702b3fade7403164957627ab638080b8680b7fbfddb294ffe`；独立核验输入 `f9a3a74da25a983886f37f52d03a5fb9e5ed7276363f1c848bcd77e8f028d79e`。
- Peters 对照给出 Earth-Sun `t=3.373993930366e30 s`、`P=196.290559982 W`；条件质量损失的绝热外移约 `+0.005000%`，`0.005%` 在声明精度下成立。
- 边界：N 体积分、广义相对论与质量损失对照、蒙特卡洛评估为 planned；仅 Earth-Sun 引力波计算标为 executed。
RESULT: DELIVERABLE
