---
project: q049
role: independent-review
reviewer_model: contest-qwen/gpt-5.6-sol
reviewed: [baseline.md, v1.md]
date: 2026-09-01
verdict: revise
---
# q049 V1 独立评审

## 评审范围与独立性
- 读取范围严格限于：`research-world/projects/q049/project.json`、`readme.md` 第 56-88 行（rubric 与终态表）、`baseline.md`、`v1.md`。未读取 V1 Trajectory、历史 `orbits-49` 产物与任何后续版本。
- 所有引用核验由本 Session 用 anysearch 独立完成（5 次 batch_search + 3 次 extract，覆盖 arXiv、ADS、IOP、ScienceDirect、Wikipedia、UCL 讲义等），不把 V1 运行记录中的"成功提取 1 个 DOI"当证据。
- 抽查范围：V1 全部 5 条来源；baseline 全部 5 条来源中承载关键精确数值的 3 条逐项核数值，另 2 条通用 Wikipedia 背景来源核存在性。

## 一、六维 rubric 评分

### baseline（direct-answer，contest-qwen/qwen3-max）
| 维度 | 分 | 理由 |
|---|---|---|
| 问题理解 | 2 | 明确校正题干"最终螺旋坠入太阳"的误导前提，区分引力波、混沌、潮汐、太阳演化各机制，对象与范围准确。 |
| 文献证据 | 2 | 关键精确数值（200 W、~10¹³ 倍宇宙年龄、Lyapunov 2-230 Myr、7.5%、60 倍、2501 次模拟、~1% 概率）全部独立核验通过；Nature 论文 DOI/卷页正确。缺陷仅一处：Ghosh 文中"每天 10⁻¹⁵ m"取自不可提取的 PDF 正文，unverifiable。 |
| Direction 质量 | 0 | 直接回答形态，无任何 Direction 结构。 |
| 科学推理 | 2 | 结论强度与证据匹配；GR 稳定化、混沌概率、太阳演化主导等论断均被核验支持；未越界。 |
| 研究计划 | 0 | 无研究计划。 |
| 表达与追溯 | 2 | 单一主线清晰，来源列表含 URL/DOI，检索限制如实记录。 |
| **总分** | **8/12** | 作为直接回答质量高，但缺 Direction 与计划两个维度结构性为 0。 |

### V1（Workflow，contest-qwen/qwen3-max）
| 维度 | 分 | 理由 |
|---|---|---|
| 问题理解 | 2 | 研究对象、范围、关键变量（a/e/i、Q、质量损失率）与四条题干前提校正均准确。 |
| 文献证据 | 1 | 5 条来源中 3 条核验失败：来源 5 的 DOI 实际属于另一篇论文（伪造标识符，V1 自承"未直接检索到"）；来源 4 arXiv 号错误；来源 3 的关键结论被反向转述。仅来源 1、2 通过。不满足"无错引或虚构引用"。 |
| Direction 质量 | 2 | 三个方向在机制层面清晰可区分（混沌动力学 / 耗散累积 / 太阳演化），各有依据、反证、可区分预测与不确定性，横向比较（时间尺度/确定性/观测支持）成立。 |
| 科学推理 | 1 | 存在实质科学错误：§2 与 D2 称地球-太阳引力波功率"~10⁻²⁰ W 量级"，实际约 200 W，错约 22 个数量级；对 Rasio et al. 1996 的引用结论反向。主线结论（耗散可忽略、太阳演化主导）方向正确，但定量骨架有错。 |
| 研究计划 | 1 | 数据、方法、基线/三组对照、步骤、产物、停止/回退条件齐全；但定量判据"dE/dt < 10⁻²⁰ W 视为可忽略"物理错误——按此判据，地球实际约 200 W 的引力波辐射将被误判为"不可忽略"，足以误导实施。 |
| 表达与追溯 | 2 | planned/executed 明确分开，运行记录如实（4 次搜索、2 次 DOI 提取失败），主线单一。唯一小缺口：§2 与 D1 内联引用 "Laskar, 1989" 未进 §3 来源记录。 |
| **总分** | **9/12** | 无 0 分维度，但 <10 且关键引用抽查失败。 |

## 二、引用抽查表

### V1（全部分母 = 5 条来源）
| # | 来源 | 判定 | 核验 URL | 断言核验 |
|---|---|---|---|---|
| 1 | Batygin & Laughlin 2008, DOI 10.1086/589232 | pass | https://arxiv.org/abs/0804.1946 ；https://iopscience.iop.org/article/10.1086/589232 | DOI↔论文正确（ApJ 683:1207）。断言"20 Gyr 无严重不稳定；分岔实验水星 ~1.26 Gyr 坠入太阳、~862 Myr 与金星碰撞"与摘要逐字吻合（1.261 Gyr / 862 Myr）。 |
| 2 | Laskar et al. 2004, DOI 10.1051/0004-6361:20041335 | pass | http://ui.adsabs.harvard.edu/abs/2004A&A...428..261L/abstract | DOI↔论文正确（A&A 428:261-285）。具体数字"60 Myr 后不可预测 / 250 Myr 最规则成分"属正文级断言，摘要级无法确认（unverifiable 子断言，不影响来源判定）。 |
| 3 | Rasio et al. 1996, DOI 10.1086/177941 | **fail** | http://ui.adsabs.harvard.edu/abs/1996ApJ...470.1187R/abstract ；https://arxiv.org/pdf/astro-ph/9605059 | DOI↔论文正确（ApJ 470:1187），但 V1 断言"地球可能在太阳红巨星阶段幸存"被原文反向：原文为 "the Earth may well **not** survive after all"。错引（结论反向转述）。 |
| 4 | Lecar et al. 2001, arXiv:astro-ph/0111602 | **fail** | https://arxiv.org/abs/astro-ph/0111602 | astro-ph/0111602 实为 Murray & Holman "The role of chaotic resonances in the solar system"；Lecar et al. "Chaos in the Solar System" 的正确 arXiv 号为 **astro-ph/0111600**。标识符错误，按所给 ID 不可回读。 |
| 5 | Deienno & Nesvorný 2014, DOI 10.1016/j.icarus.2014.04.029 | **fail** | https://www.sciencedirect.com/science/article/abs/pii/S0019103514002218 | 该 DOI 属于 Pires et al. "The evolution of a Pluto-like system during the migration of the ice giants"（Icarus 246）。未检索到任何 2014 年 Deienno & Nesvorný 题为 "Long-term evolution of the solar system" 的 Icarus 论文；V1 自承"未直接检索到，基于领域知识引用"。视为伪造/错配标识符。 |

**V1 有效率：2/5 = 40%**（分母为全部 5 条来源；来源 2 含 1 条 unverifiable 子断言）。

### baseline（关键精确数值来源分母 = 3）
| # | 来源 | 判定 | 核验 URL | 断言核验 |
|---|---|---|---|---|
| 1 | Ghosh 2016, IJAR 4(12):673-678 | pass | https://www.journalijar.com/article/13816/ | 文章存在（DOI 10.21474/IJAR01/2445）；摘要明确 "inspiral time of the earth's orbit … ~10¹³ times greater than the age of the universe"，支持 baseline "3×10¹³ 倍"（同数量级）。200 W 独立旁证：UCL 讲义 "For the Earth-Sun orbital system, the amount of gravitational radiation expected is 200 W"（https://www.mssl.ucl.ac.uk/~mjp/diploma/highen_13_gravwaves_notes.pdf）。"每天 10⁻¹⁵ m" 取自 PDF 正文，unverifiable 子断言。注：IJAR 为低门槛期刊，其具体数值非主流文献交叉确认。 |
| 2 | Laskar & Gastineau 2009, Nature 459:817-819, DOI 10.1038/nature08096 | pass | http://ui.adsabs.harvard.edu/abs/2009Natur.459..817L/abstract ；https://observatoiredeparis.psl.eu/mercury-mars-venus-and-the.html | DOI↔论文、卷页正确；2501 次模拟、约 1% 概率水星危险轨道（20/2501）、5 Gyr 窗口均获 Wikipedia 条目与巴黎天文台发布交叉确认。 |
| 3 | Wikipedia "Stability of the Solar System" | pass | https://en.wikipedia.org/wiki/Stability_of_the_Solar_System | 逐项命中：Lyapunov 2-230 Myr；水星 1-2% 概率；GR 贡献水星近日点进动 7.5%（引 Park et al. 2017）；无 GR 时不稳定率高 60 倍。 |
| 4 | Wikipedia "Gravitational wave" | pass（背景来源，无关键精确数值） | https://en.wikipedia.org/wiki/Gravitational_wave | 存在，仅用于通用机制表述。 |
| 5 | Wikipedia "Orbital decay" | pass（背景来源，无关键精确数值） | https://en.wikipedia.org/wiki/Orbital_decay | 存在，仅用于通用机制表述。 |

**baseline 关键精确数值来源有效率：3/3 = 100%**（含全部 5 条来源则为 5/5；Ghosh 的 "10⁻¹⁵ m/day" 为 unverifiable 子断言，不改变来源级判定）。

## 三、同条件对照（同题、同模型族、同检索权限）

| 项 | baseline | V1 |
|---|---|---|
| Direction 差异 | 无 Direction 结构 | 三方向机制可区分（混沌/耗散/太阳演化），满足模板 H-01/02/03 要求 |
| 计划可用性 | 无计划 | 计划要素齐全但含物理错误判据，研究者按现判据实施会得出错误筛选结论 |
| 来源质量 | 3 条 Wikipedia（三级）+ 低门槛 IJAR + 1 条 Nature 一手；但所引数值全部核验通过 | 全部标注一手/预印本，姿态更高；但 3/5 核验失败，含 1 条伪造 DOI、1 条结论反向、1 条错误标识符 |
| 科学错误 | 未发现 | 引力波功率错约 22 个数量级（10⁻²⁰ W vs 实际 ~200 W）；Rasio 结论反向 |
| 近似输出预算 | 单篇直接回答，约 1.5k 词，无检索失败记录 | 约 2.5k 词结构化报告，4 次搜索 + 3 次 DOI 提取（2 失败），成本高于 baseline |
| 不可归因因素 | 两侧文件均未记录 Session id 与 token；baseline 无运行记录，无法确认其检索路径；V1 自述模型与 baseline 同为 contest-qwen/qwen3-max 但无凭证可回读；两侧模型一致性、预算等价性不可归因 | 同左 |

## 四、Findings（按严重度排序）

1. **[Critical] V1 §3 来源 5 伪造标识符**：DOI 10.1016/j.icarus.2014.04.029 属于 Pires et al.（Icarus 246，Pluto 系统迁移），目标论文未检索到存在证据，V1 自承未检索而凭"领域知识"引用。违反"禁止虚构引用"，触发关键引用抽查失败。
2. **[Critical] V1 §2"已有认识"、§4 D2 反对证据、§6 定量判据**：地球-太阳引力波功率写作 "~10⁻²⁰ W 量级"，实际约 200 W，错约 22 个数量级；计划判据 "dE/dt < 10⁻²⁰ W 视为可忽略" 物理错误，按此判据真实耗散会被误判为显著。耗散机制结论（可忽略）方向正确，但定量依据与判据均错。
3. **[Major] V1 §3 来源 3 结论反向转述**：Rasio et al. 1996 原文结论为地球"may well not survive"红巨星阶段，V1 记为"地球可能幸存"；该错误同时渗入 §4 D3 支持证据。
4. **[Major] V1 §3 来源 4 arXiv 号错误**：astro-ph/0111602 → 应为 astro-ph/0111600（Lecar, Franklin, Holman & Murray, "Chaos in the Solar System"）。按所给标识符不可回读。
5. **[Minor] V1 内联引用未入来源记录**：§2 与 D1 使用 "Laskar, 1989"（真实文献，Nature 338:237）但未列入 §3，追溯链断裂。
6. **[Minor] baseline 两处次级瑕疵**：Ghosh 摘要为 "~10¹³ 倍"，baseline 写 "3×10¹³ 倍"（同数量级，正文未核）；"每天 10⁻¹⁵ m" 不可核验；2501 次模拟实际完成于 2008 年（论文 2009 年发表），baseline 表述为"2009 年进行"。

## 五、Direction 保留/改写/淘汰意见
- **D1 轨道混沌主导论：保留**。机制独立、证据经核验（Batygin & Laughlin 断言逐字命中摘要）；仅需把 Laskar 1989 补入来源记录并修正 Lecar arXiv 号。
- **D2 微弱耗散累积论：改写保留**。作为被否证方向有方法论价值（题干前提正对应此方向），但必须以正确量级（~200 W、inspiral 时间 ~10²³ 年）重写支持/反对证据，并修正 Rasio 引用方向。
- **D3 太阳演化决定论：保留为主方向**。时间尺度论证与恒星演化共识一致；需删除对 Rasio "幸存"结论的依赖，改为引用其"质量损失加速潮汐衰减"的真实结论。
- 无淘汰项。

## 六、V2 最小必改清单
1. 删除来源 5（Deienno & Nesvorný 2014）；如需太阳质量损失的一手来源，替换为实际检索核验过的文献（候选：Schröder & Connon Smith 2008），禁止凭领域知识补 DOI。
2. 修正引力波功率为 ~2×10² W（地球-太阳），重写 §2、D2 与 §6 判据；判据改为时间尺度比较（inspiral 时间 vs 太阳主序寿命）而非功率阈值。
3. 修正 Rasio et al. 1996 的转述：太阳质量损失加速潮汐衰减，地球"may well not survive"；同步修正 §4 D3 支持证据。
4. 修正来源 4 arXiv 号为 astro-ph/0111600（或改引其正式刊版 Annu. Rev. Astron. Astrophys. 2001）。
5. 将 Laskar 1989 补入 §3 来源记录（含 DOI/卷页），或删除该内联引用。

**必须标为 planned 的事项**：§6 研究计划全部执行步骤（REBOUND 实现、复现 Batygin & Laughlin、蒙特卡洛模拟）保持 planned，不得出现模拟结果；V2 若新增数值计算，必须附输入/命令/输出/哈希，否则标 planned。
**必须标为 waiting_human 的事项**：无。本题为纯理论天体物理，无受限数据、伦理或安全 Gate；付费全文无法核验的子断言（如 Ghosh 正文数值）标 unverifiable，不升级为 waiting_human。

## 七、Verdict
**revise**。V1 总分 9/12（<10），关键引用抽查失败（来源 5 伪造 DOI、来源 3 结论反向、来源 4 标识符错误，有效率 2/5），且含 22 个数量级的物理错误。无伪造执行（planned/executed 分离如实）。baseline 8/12，引用 3/3 通过但缺 Direction 与计划结构，不能替代 Workflow 产物。
