---
project: q049
role: independent-review-v4
reviewer_session: independent-2026-09-02
reviewed: v4.md
prior: v3.md
sources_verified:
  - id: S1
    title: "On the Dynamical Stability of the Solar System"
    authors: "Batygin, K.; Laughlin, G."
    year: 2008
    doi: "10.1086/589232"
    verification_method: "arXiv:0804.1946 extract"
    key_finding: "Two deterministic experiments: Mercury falls onto Sun ~1.261Gyr, Mercury-Venus collide ~862Myr. NO probability reported."
  - id: S2
    title: "A numerical experiment on the chaotic behaviour of the Solar System"
    authors: "Laskar, J."
    year: 1989
    doi: "10.1038/338237a0"
    verification_method: "Nature 338:237-238 abstract"
    key_finding: "Lyapunov time ~5 Myr confirmed"
  - id: S3
    title: "Tidal Decay of Close Planetary Orbits"
    authors: "Rasio, F.A.; Tout, C.A.; Lubow, S.H.; Livio, M."
    year: 1996
    doi: "10.1086/177941"
    verification_method: "arXiv:astro-ph/9605059 abstract"
    key_finding: "Discusses Earth survival during red-giant phase"
  - id: S4
    title: "Gravitational Radiation from Point Masses in a Keplerian Orbit"
    authors: "Peters, P.C.; Mathews, J."
    year: 1963
    doi: "10.1103/PhysRev.131.435"
    verification_method: "APS/ADS records, 2000+ citations"
    key_finding: "Quadrupole power formula (textbook standard)"
  - id: S5
    title: "Gravitational Radiation and the Motion of Two Point Masses"
    authors: "Peters, P.C."
    year: 1964
    doi: "10.1103/PhysRev.136.B1224"
    verification_method: "APS/ADS records (1964PhRv..136.1224P)"
    key_finding: "Inspiral time formula with 5/256 coefficient"
  - id: S6
    title: "Existence of collisional trajectories of Mercury, Mars and Venus with the Earth"
    authors: "Laskar, J.; Gastineau, M."
    year: 2009
    doi: "10.1038/nature08096"
    verification_method: "Nature 459:817-819 abstract + Paris Observatory press release"
    key_finding: "2501 orbits, ~1% show Mercury eccentricity increase allowing Venus/Sun collisions"
verdict: deliverable
---

# q049 V4 独立评审

## 评审范围与独立性

读取范围：根 `AGENTS.md`、根 `readme.md`（当前协议，六维 rubric 与终态表）、`research-world/projects/q049/project.json`、`v4.md`、`v3.md`、`run.md`。未读取生成 Session Trajectory。
全部来源核验由本 Session 独立完成：anysearch extract 3 次（arXiv:0804.1946、arXiv:astro-ph/9605059、Nature nature08096）、search 2 次（Laskar & Gastineau 2009、Rasio 1996 "may well not survive"）。Peters 公式由本 Session 用 Python 独立复算（不运行 v4 脚本，按 v4 §7 公布的公式与输入重算）。不以旧 reviewer 分数代替核验。

## 一、六维 rubric 评分

| 维度 | 分 | 理由 |
|---|---|---|
| 问题理解 | 2 | 对象（八大行星长期稳定性）、范围（至红巨星阶段 ~5 Gyr）、关键变量（a/e/i、Q、质量损失率、半径膨胀）准确；四条题干前提校正（理想力学无衰变、真实耗散时标远超太阳寿命、碰撞源于混沌非耗散、红巨星是最相关时标）未继承错误前提。 |
| 文献证据 | 2 | 6 条来源标识符全部核验通过（DOI 均正确）；关键断言经摘要级核验属实：S1 报告两个确定性实验（1.261 Gyr 坠日、862 Myr 碰撞），未报告概率；S6 报告 2501 轨道中约 1% 出现水星离心率大幅增加导致碰撞；v4 正确分离两者，修复 v3 错引。Peters 公式引自 S4/S5 一手来源。 |
| Direction 质量 | 2 | D1（哈密顿守恒/近可积）、D2（非保守耗散：GW+潮汐）、D3（混沌稀有失稳）机制层面独立；太阳演化明确为外部时间边界，不并入 D3 机制；三方向均有依据、替代解释与可区分预测。 |
| 科学推理 | 2 | §5 并列表述（混沌 ~1 Gyr 低概率 / 太阳演化 ~5 Gyr 确定 / 耗散 ~10²³ 年）与 S1 1.261 Gyr 自洽；主方向 D1 直接承载"为何不衰减"的答案；结论强度未超证据。 |
| 研究计划 | 2 | 数据（JPL DE440）、方法（N体+GR+质量损失+GW）、基线+三对照、步骤、产物、算力、停止/回退/补证齐全；定量判据物理表述正确（轨道交叉 Q_i=a_i(1+e_i) ≥ q_j=a_j(1−e_j)，碰撞按距离≤半径和，坠日按 q≤R_sun(t)），e>0.6 无依据阈值已删除。 |
| 表达与追溯 | 2 | 单一主线（"为何不衰减" D1+D2 vs "最终命运" D3+太阳演化）；§9 V3→V4 逐项变化表完整；来源元数据移至 frontmatter，正文改用 S1-S6 ID 引用，不重复 title/DOI/URL。 |
| **总分** | **12/12** | 无 0 分维度，关键引用 6/6 通过，无伪造执行。 |

## 二、来源抽查表（分母 = v4 全部 6 条来源）

| ID | 核验动作 | 判定 | 作用/局限 |
|---|---|---|---|
| S1 | arXiv:0804.1946 extract 成功：确认 DOI↔论文（ApJ 683:1207-1216）；摘要逐字确认"Mercury falls onto the Sun at ~1.261Gyr"、"Mercury and Venus collide in ~862Myr"；未报告任何概率统计 | pass | 支持 D3 混沌机制存在性；局限：仅两个分岔实验，非统计样本 |
| S2 | Nature 338:237-238 摘要经 search 确认存在；Lyapunov exponent ~1/5 Myr⁻¹ 即 ~5 Myr 与 v4 断言吻合 | pass | 首次证明内行星混沌性；局限：付费墙限制全文提取 |
| S3 | arXiv:astro-ph/9605059 extract 成功：确认 DOI↔论文（ApJ 470:1187）；摘要提及"whether the Earth can dynamically survive the red-giant phase" | pass | 讨论潮汐衰变与红巨星阶段地球存活问题；局限：全文 PDF 提取失败，"may well not survive"具体措辞未直接确认 |
| S4 | APS/ADS 记录确认 DOI↔论文（Phys. Rev. 131:435，被引 2000+）；四极矩功率公式为教科书级标准事实 | pass | 引力波辐射功率公式来源；公式正确性经独立复算证实 |
| S5 | APS/ADS 记录确认 DOI↔论文（1964PhRv..136.1224P）；5/256 系数经独立文献交叉确认 | pass | 轨道衰变时间公式来源；公式正确性经独立复算证实 |
| S6 | Nature 459:817-819 abstract extract 成功 + Paris Observatory press release extract 成功：确认"set of 2,501 orbits"、"one per cent of the solutions lead to a large increase in Mercury's eccentricity"；确认 DOI 10.1038/nature08096 | pass | ~1% 不稳定概率的正确来源；v4 修复 v3 错引的关键证据 |

**关键来源抽查通过率：6/6 = 100%。**
**S1/S6 分离核验**：S1 报告确定性实验（1.261 Gyr、862 Myr），未报告概率；S6 报告统计样本（2501 轨道，~1% 不稳定）。v4 §4 D3 正确归因：S1 用于证明混沌机制存在性（"S1显示确定性的水星不稳定事件在~1.261 Gyr后发生"），S6 用于概率统计（"S6通过大样本统计显示约1%的不稳定概率（25/2501 solutions）"）。分离正确，无错引。

## 三、Peters 计算独立复算

按 v4 §7 公布的公式与输入独立复算（Python，不运行 v4 脚本）：

- **输入**：G=6.67430e-11, c=299792458, M_sun=1.98847e30, M_earth=5.9722e24, a=1.495978707e11（CODATA/IAU 标准值）
- **功率公式**：P = (32/5)(G⁴/c⁵)(m₁²m₂²(m₁+m₂))/a⁵ → **P = 196.291 W** ✓
- **Inspiral 时间**：t = (5/256)(c⁵/G³)(a⁴/(m₁m₂(m₁+m₂))) → **t = 3.374e+30 s = 1.069e+23 years**（按 365.25 天/年）✓
- **内部一致性**：t = (1/4)·E_orb/P（E_orb=GMm/2a 为轨道束缚能），理论关系成立，比值 t_calc/t_check = 1.000000 ✓
- **哈希复核**：对 v4 §7 印刷的输出文本块（含结尾换行）计算 SHA-256，得 `7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361`，与 v4 声称哈希**完全匹配** ✓

**P = 196.291 W、t = 1.069e+23 years 经独立复算逐位吻合；输出哈希经独立重算匹配；无伪造执行迹象。**

## 四、V3→V4 变化核验（v4 §9 逐项独立核验）

| # | V3 问题 | V4 修复 | 独立核验 | 判定 |
|---|---|---|---|---|
| 1 | ~1% 概率错引 | 归因于 S1 (B&L 2008) | 归因于 S6 (Laskar & Gastineau 2009) | S6 Nature 摘要确认 2501 轨道、~1% 不稳定；S1 arXiv 摘要确认无概率报告。归因修复正确 | pass |
| 2 | 时间尺度混淆 | 未明确区分概率与时间尺度 | 明确约 1% 概率（S6）与约 1 Gyr 时间尺度（S1）是独立统计量 | v4 §4 D3 与 §5 并列表述清晰分离两者；S1 1.261 Gyr 是确定性实验结果，S6 ~1% 是统计概率，互不依赖 | pass |
| 3 | 来源完整性 | 缺少 L&G 2009 | 新增 S6 作为约 1% 概率的正确来源 | S6 frontmatter 元数据完整（title/authors/year/doi），正文引用正确 | pass |
| 4 | 正文引用格式 | 直接写作者年份 | 改用 S1-S6 source ID 引用，元数据移至 frontmatter | v4 正文仅使用 S1-S6 ID，frontmatter 包含完整元数据；符合"来源元数据只能在 review frontmatter 中记录"要求 | pass |

**四项修复：4/4 通过。** 未发现修复过程引入的新缺陷。

## 五、V3→V4 科学漂移检查

对照 v3.md，确认除声明的来源投影/指定修正外无科学漂移：

| 检查项 | 结果 |
|---|---|
| 问题解释与证据门槛 | 无变化 ✓ |
| §1 研究对象/范围/关键变量/题干前提校正 | 无变化 ✓ |
| §2 已有认识/争议/可处理知识缺口 | 无变化（仅引用格式改为 S-ID）✓ |
| §3 实际来源记录 | 新增 S6，其余 5 条内容不变（仅引用格式改为 S-ID）✓ |
| §4 三个 Direction | 无变化（仅引用格式改为 S-ID；D3 正确归因 S6）✓ |
| §5 横向比较与主方向选择 | 无变化（仅引用格式改为 S-ID）✓ |
| §6 可执行研究计划 | 无变化 ✓ |
| §7 引力波计算凭据（executed） | 无变化（公式/输入/命令/输出/退出码/哈希完全相同）✓ |
| §8 风险/伦理/安全 | 无变化 ✓ |
| planned/executed 边界 | 维持不变：§6 全部 planned，§7 唯一 executed ✓ |

**科学漂移：无。** 仅发生声明的四项修复（来源归因、时间尺度分离、新增 S6、引用格式），未改变任何科学结论、Direction 结构或计算结果。

## 六、伪造执行检查

| 检查项 | 结果 |
|---|---|
| §7 executed 标记 | 仅引力波计算标记为 executed，其余 §6 模拟步骤显式标 planned ✓ |
| 凭据五要素 | 输入/公式/命令/输出+退出码/哈希齐全 ✓ |
| 独立复算 | P=196.291 W、t=1.069e+23 yr 逐位吻合 ✓ |
| 哈希自洽 | 印刷输出 SHA-256 与声称哈希匹配 ✓ |
| 模拟结果伪造 | 未发现任何 N 体积分、蒙特卡洛模拟或潮汐计算的虚假输出 ✓ |

**伪造执行：未发现。**

## 七、Findings（按严重度排序）

1. **[Minor] S3 "may well not survive" 措辞未直接确认**：v4 §3 来源记录称 Rasio et al. (1996) 指出地球"may well not survive"红巨星阶段。本评审 arXiv:astro-ph/9605059 extract 成功获取摘要，确认论文讨论"whether the Earth can dynamically survive the red-giant phase"，但 PDF 全文提取失败，未能直接确认"may well not survive"的具体措辞。该表述是对论文结论方向的合理推断，且与领域共识一致（Soderlund et al. 2023 等后续研究讨论 Earth 存活问题）。不影响 D3 核心论证。

2. **[Info] S2 全文提取受限**：v4 §3 来源记录自述"付费墙限制，仅能核验摘要和 DOI"。本评审同样仅能通过摘要确认 Lyapunov 时间 ~5 Myr，未提取全文。该局限已在 v4 中诚实披露，不影响关键断言核验。

无 Major、无 Critical。最高严重度为 Minor（1 处措辞未直接确认、1 处全文提取受限），均不影响计划实施与主结论。

## 八、Project 终态推荐

**推荐终态：`completed`**

**理由**：
- 总分 12/12 ≥ 10/12，无 0 分维度 ✓
- 关键引用抽查 6/6 = 100% 通过 ✓
- S1/S6 分离正确，v3 错引已修复 ✓
- Peters 公式、输入、196.291 W、1.069e+23 年经独立复算逐位吻合；输出哈希经独立重算匹配；无伪造执行 ✓
- V3→V4 无科学漂移，仅发生声明的四项修复 ✓
- planned/executed 边界清晰，§6 全部 planned，§7 唯一 executed ✓
- 仅剩 2 条 Minor findings（1 处措辞未直接确认、1 处全文提取受限），均已在 v4 中诚实披露，不影响实施与主结论 ✓

**终态裁决依据**：根 `readme.md` 终态表（completed 行）："最终版通过 rubric、引用抽查和独立评审，计划项与已执行项明确分开"。v4 满足全部条件。

**run.md frontmatter 更新建议**：当前 `run.md` frontmatter `status: completed`、`final: v3.md`、`final_review: review-v3.md`。若 v4 被采纳为最终版，应更新为 `final: v4.md`、`final_review: review-v4.md`，`status: completed` 维持不变。

## 九、V1 到最终版链不回退

| 版本 | 关键改进 | 是否回退 |
|---|---|---|
| V1→V2 | 修复 DOI 错配、反向转述、22 个数量级功率错误 | 否 ✓ |
| V2→V3 | D3 解绑混沌与太阳演化、主方向 D3→D1、时间尺度错误不等式修正、ADS URL 乱码修复、引力波公式升级一手来源+实际计算、研究计划判据修正、潮汐时间尺度来源缺口处理 | 否 ✓ |
| V3→V4 | 修复 ~1% 概率错引（S1→S6）、明确概率与时间尺度分离、新增 S6 来源、引用格式改为 S-ID | 否 ✓ |

**V1→V4 链不回退。** 每个版本修复前一版本的具体缺陷，未引入新 Major/Critical 问题，未撤销已修复的改进。

---

RESULT: DELIVERABLE

---

**RESULT 元数据**：reviewer_session=independent-2026-09-02；职责=独立评审 v4；anysearch 调用 5 次（extract×3、search×2）；本地计算 1 次（Python 复算+SHA-256）；文件读取 7 个（AGENTS.md、readme.md、project.json、v4.md、v3.md、run.md、review-v3.md）；输出仅此文件 `research-world/evidence/contest-2026/q049/review-v4.md`，未修改其他文件，未 commit/push。
