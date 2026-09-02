---
project: q049
artifact: review-v8
role: independent-review
reviewer_session: 01a05fd9-122e-7bc1-ab3c-513690287236
author_session: 01a05fd4-8bd4-7484-afd1-8ca2105ac4cb
reviewed:
  - research-world/evidence/contest-2026/q049/v8.md
  - research-world/evidence/contest-2026/q049/v7.md
verdict: deliverable
sources:
  - id: issue-249
    type: issue
    title: "首批五案例验证证据-假设-反驳-计划-修订"
    url: "https://github.com/LittleDrinks/research-world/issues/249"
    used_for: "six-dimension acceptance rubric"
  - id: original-question
    type: local-file
    path: research-world/evidence/contest-2026/deep-cases.md
    sha256: "982682ec85784d4085ca09c7fc3a5ad45941a57cd8901e44bf21bba16a42ff35"
    used_for: "q049 original question and expected evidence chain"
  - id: run-record
    type: local-file
    path: research-world/evidence/contest-2026/q049/run.md
    sha256: "70c028552dbee65d4283b9df5d3743253ecf30f618a22d31c8b26c67df4693dc"
    used_for: "execution boundary, provenance, and terminal ownership"
  - id: prior-artifact
    type: local-file
    path: research-world/evidence/contest-2026/q049/v7.md
    sha256: "dde87b3fe5779ced4a23b3f28eb00bf68bdc1251e190c7eeb0ec67e1f1420287"
    used_for: "mechanical scientific-drift baseline"
  - id: candidate-artifact
    type: local-file
    path: research-world/evidence/contest-2026/q049/v8.md
    sha256: "e0a6d83a65ae80f11c585f2b0c63053923b9e60b1fc8240cfb0f6627ebe65643"
    used_for: "rubric assessment target"
  - id: prior-independent-review
    type: local-file
    path: research-world/evidence/contest-2026/q049/review-v7.md
    sha256: "c921e44571c6d83078376745c10227671d0cd2f3b9ce938822dd9d94a67fb3c1"
    used_for: "prior source, numerical, and rubric evidence"
  - id: S1
    type: cited-publication
    title: "On the Dynamical Stability of the Solar System"
    authors: "Batygin, Konstantin; Laughlin, Gregory"
    year: 2008
    doi: "10.1086/589232"
    url: "https://doi.org/10.1086/589232"
    used_for: "retained cited-source inventory"
  - id: S2
    type: cited-publication
    title: "A numerical experiment on the chaotic behaviour of the Solar System"
    authors: "Laskar, Jacques"
    year: 1989
    doi: "10.1038/338237a0"
    url: "https://doi.org/10.1038/338237a0"
    used_for: "retained cited-source inventory"
  - id: S3
    type: cited-publication
    title: "Tidal Decay of Close Planetary Orbits"
    authors: "Rasio, Frederic A.; Tout, Christopher A.; Lubow, Stephen H.; Livio, Mario"
    year: 1996
    doi: "10.1086/177941"
    url: "https://doi.org/10.1086/177941"
    used_for: "retained cited-source inventory"
  - id: S4
    type: cited-publication
    title: "Gravitational Radiation from Point Masses in a Keplerian Orbit"
    authors: "Peters, P. C.; Mathews, J."
    year: 1963
    doi: "10.1103/PhysRev.131.435"
    url: "https://doi.org/10.1103/PhysRev.131.435"
    used_for: "retained cited-source inventory"
  - id: S5
    type: cited-publication
    title: "Gravitational Radiation and the Motion of Two Point Masses"
    authors: "Peters, P. C."
    year: 1964
    doi: "10.1103/PhysRev.136.B1224"
    url: "https://doi.org/10.1103/PhysRev.136.B1224"
    used_for: "retained cited-source inventory"
  - id: S6
    type: cited-publication
    title: "Existence of collisional trajectories of Mercury, Mars and Venus with the Earth"
    authors: "Laskar, Jacques; Gastineau, Mickaël"
    year: 2009
    doi: "10.1038/nature08096"
    url: "https://doi.org/10.1038/nature08096"
    used_for: "retained cited-source inventory"
  - id: schroder-connon-smith-2008
    type: primary-publication
    title: "Distant future of the Sun and Earth revisited"
    authors: "Schröder, K.-P.; Connon Smith, R."
    year: 2008
    journal: "Monthly Notices of the Royal Astronomical Society"
    volume: "386"
    issue: "1"
    pages: "155-163"
    doi: "10.1111/j.1365-2966.2008.13022.x"
    url: "https://academic.oup.com/mnras/article-pdf/386/1/155/2998239/mnras0386-0155.pdf"
    used_for: "solar-evolution source verification"
  - id: johnstone-et-al-2015
    type: primary-publication
    title: "Stellar winds on the main-sequence I. Wind model"
    authors: "Johnstone, C. P.; Güdel, M.; Lüftinger, T.; Toth, G.; Brott, I."
    year: 2015
    journal: "Astronomy and Astrophysics"
    volume: "577"
    article: "A27"
    doi: "10.1051/0004-6361/201425300"
    url: "https://www.aanda.org/articles/aa/pdf/2015/05/aa25300-14.pdf"
    used_for: "conditional solar-wind mass-loss input verification"
---
# 独立审查
## 判定
可交付。六维均为 2 分，合计 12/12；没有 0 分维度。
## 六维评分
| 维度 | 分 | 依据 |
|---|---:|---|
| 问题界定 | 2 | 将题干的普遍衰变断言分解为保守动力学、弱耗散、混沌失稳和太阳演化边界；对象、范围、变量和可处理缺口均明确。 |
| 来源与数值 | 2 | S1-S6 的书目信息与既有独立核验记录一致；地球-太阳 Peters 复算为 196.290559982415 W、3.373993930366e30 s、1.069154159494e23 yr，匹配展示精度；25/2501 为 0.999600159936%。 |
| Direction 与比较 | 2 | 三条方向分别检验保守近可积、非保守耗散和混沌稀有失稳；每条均给出支持、替代解释、可区分预测和不确定性，横向比较按时间尺度、确定性和观测支持选择主方向。 |
| 研究计划 | 2 | 数据、N 体方法、三项对照、轨道交叉/碰撞/坠日判据、预期解释、产物、资源及停止、回退、补证条件形成可执行链。 |
| planned/executed 与终态所有权 | 2 | N 体积分、相对论、质量损失、潮汐和蒙特卡洛均明确为 planned；仅限 Peters 计算标注为 executed 并保留输入、公式、命令、输出、退出码和哈希；项目级终态未由科学稿声明，deliverable 仅为独立评审判断。 |
| 表达、追溯与内容守恒 | 2 | 原题、来源、机制取舍、计划和限定计算连成单一可追溯主线；允许项归一化后的两侧 SHA-256 均为 c20112e37a520803d5a20ae58959962f354c09f53f596464ba3cff4e31905742，科学正文没有替换、新增或删除。 |
## 来源核验
Schröder 与 Connon Smith (2008) 的题名、年份和 DOI 10.1111/j.1365-2966.2008.13022.x 由 OUP 出版记录核对；Johnstone、Güdel、Lüftinger、Toth 与 Brott (2015) 的题名、作者、年份、A&A 577 A27 和 DOI 10.1051/0004-6361/201425300 由 A&A 出版物核对。后者给出约 1.4e-14 M_sun/yr 的模型太阳风质量损失率，因此既有的 1e-14 M_sun/yr 是取整的条件输入，不是五十亿年外推。
## 残余风险
本轮未重读 S1-S6 原文；其元数据与证据角色依据保留的来源记录和既有独立核验。OUP PDF 的全文未能由提取服务读取，故仅核对其出版元数据，未以此替代对具体物理断言的全文复核；这构成核验范围限制，不构成来源失效。
RESULT: DELIVERABLE
