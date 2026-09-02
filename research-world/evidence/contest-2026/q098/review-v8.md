---
project: q098
role: independent-review
reviewed: v8.md
prior: v7.md
verdict: deliverable
reviewer: q098-v8-reviewer
method: NCBI efetch + Crossref API direct verification
---

# q098 V8 独立科学评审

## Rubric 评分（readme.md:64-73）

| 维度 | 分数 | 依据 |
|---|:---:|---|
| 问题理解 | 2/2 | 对象（睡眠）、范围（健康影响）、争议（机制不确定性）、知识缺口（横断面 vs 因果证据）准确呈现，未继承错误前提 |
| 文献证据 | 2/2 | 8/8 来源经 NCBI PMID / Crossref API 逐条核验（见下方详表）；S5、S7、S8 元数据修正后与权威记录一致；S3 pages 为预存错误（非 v7→v8 回归）；关键断言（HOMA-IR 0.28、疫苗研究设计差异、类淋巴清除速率、三相耦合）均获确认 |
| Direction 质量 | 2/2 | 三个机制层面真正不同：突触稳态（神经可塑性）、类淋巴清除（代谢废物）、免疫-代谢调节（炎症/激素通路）；各含支持证据、限制/反证、区分性预测和实施负担；选择理由基于可行性而非证伪 |
| 科学推理 | 2/2 | 结论强度不超过证据：观察性设计显式声明不能建立因果；反向因果已承认；S6 青少年数据显式标注不用于成人样本量；负面对照分析纳入；失败路径（脱落、残余混杂）已处理 |
| 研究计划 | 2/2 | 数据（腕动计、血液标志物）、方法（ANCOVA、敏感性分析）、对照（DAG 协变量、负面对照）、判断方式（效应量、置信区间）、产物（可行性估计、方差）、资源（IRB、实验室）和风险（脱落、残余混杂）完整；所有项目为 planned，无 executed |
| 表达与追溯 | 2/2 | 问题→证据→三机制→选择→计划→局限形成单一主线；S1-S8 标识符可追溯至 frontmatter；V7→V8 变更说明记录版本谱系；artifact_stage 正确标记为 revision_candidate |

**总分：12/12**
**0 分项：无**

## S1-S8 来源逐条核验

### S1 — Tononi & Cirelli (2014)

| 字段 | v8 frontmatter | Crossref (DOI 10.1016/j.neuron.2013.12.025) | 结论 |
|---|---|---|---|
| Title | Sleep and the price of plasticity… | Sleep and the Price of Plasticity: From Synaptic and Cellular Homeostasis to Memory Consolidation and Integration | ✓ |
| Authors | Tononi G, Cirelli C | Tononi G, Cirelli C | ✓ |
| Journal | Neuron | Neuron | ✓ |
| Volume/Issue | 81/1 | 81/1 | ✓ |
| Pages | 12-34 | 12-34 | ✓ |
| Year | 2014 | 2014-01 | ✓ |

### S2 — Xie et al. (2013)

| 字段 | v8 frontmatter | Crossref (DOI 10.1126/science.1241224) | 结论 |
|---|---|---|---|
| Title | Sleep drives metabolite clearance from the adult brain | Sleep Drives Metabolite Clearance from the Adult Brain | ✓ |
| Authors | Xie L, Kang H, Xu Q, et al. | Xie L, Kang H, Xu Q, Chen MJ, Liao Y, Thiyagarajan M, O'Donnell J, Christensen DJ, Nicholson C, Iliff JJ, Takano T, Deane R, Nedergaard M (13 authors; et al. correct) | ✓ |
| Journal | Science | Science | ✓ |
| Volume/Issue | 342/6156 | 342/6156 | ✓ |
| Pages | 373-377 | 373-377 | ✓ |
| Year | 2013 | 2013-10 | ✓ |

### S3 — Fultz et al. (2019)

| 字段 | v8 frontmatter | Crossref (DOI 10.1126/science.aax5440) | NCBI PMID 31672896 | 结论 |
|---|---|---|---|---|
| Title | Coupled electrophysiological, hemodynamic, and cerebrospinal fluid oscillations in human sleep | ✓ identical | ✓ identical | ✓ |
| Authors | Fultz NE, Bonmassar G, Setsompop K, et al. | Fultz NE, Bonmassar G, Setsompop K, Stickgold RA, Rosen BR, Polimeni JR, Lewis LD (7 authors; et al. correct) | ✓ | ✓ |
| Journal | Science | Science | Science | ✓ |
| Volume/Issue | 366/6465 | 366/6465 | 366/6465 | ✓ |
| **Pages** | **623-630** | **628-631** | **628-631** | ⚠ 预存错误（见 L1） |
| Year | 2019 | 2019-11 | 2019 | ✓ |

### S4 — Besedovsky, Lange & Born (2012)

| 字段 | v8 frontmatter | Crossref (DOI 10.1007/s00424-011-1044-0) | NCBI PMID 22071480 | 结论 |
|---|---|---|---|---|
| Title | Sleep and immune function | ✓ identical | ✓ identical | ✓ |
| Authors | Besedovsky L, Lange T, Born J | Besedovsky L, Lange T, Born J | ✓ | ✓ |
| Journal | Pflugers Arch | Pflügers Archiv - European Journal of Physiology | Pflugers Arch | ✓ |
| Volume/Issue | 463/1 | 463/1 | 463/1 | ✓ |
| Pages | 121-137 | 121-137 | 121-137 | ✓ |
| Year | 2012 | 2011-11 (online) / 2012-01 (print) | 2012 | ✓ |

### S5 — Spiegel et al. (2004) ★ NCBI PMID 15583226

| 字段 | v8 frontmatter | NCBI efetch PMID 15583226 | Crossref (DOI 10.7326/0003-4819-141-11-200412070-00008) | 结论 |
|---|---|---|---|---|
| Title | Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite | Brief communication: Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite | ✓ identical (case) | ✓ |
| **Authors** | **Spiegel K, Tasali E, Penev P, Van Cauter E** | **Spiegel K, Tasali E, Penev P, Van Cauter E** | **Spiegel K, Tasali E, Penev P, Van Cauter E** | **✓ v8 修正正确** |
| Journal | Ann Intern Med | Annals of internal medicine / Ann Intern Med | Annals of Internal Medicine | ✓ |
| Volume/Issue | 141/11 | 141/11 | 141/11 | ✓ |
| Pages | 846-850 | 846-850 (MedlinePgn: 846-50) | 846-850 | ✓ |
| DOI | 10.7326/0003-4819-141-11-200412070-00008 | ✓ identical | ✓ identical | ✓ |
| Year | 2004 | 2004-12 | 2004-12-07 | ✓ |

**v7 错误**：作者为 "Spiegel K, Leproult R, Van Cauter E"（3人，含 Leproult）。NCBI 确认正确作者为 Spiegel K, Tasali E, Penev P, Van Cauter E（4人，无 Leproult）。v8 修正正确。

### S6 — Matthews et al. (2012)

| 字段 | v8 frontmatter | Crossref (DOI 10.5665/sleep.2112) | 结论 |
|---|---|---|---|
| Title | Sleep duration and insulin resistance in healthy black and white adolescents | Sleep Duration and Insulin Resistance in Healthy Black and White Adolescents | ✓ |
| Authors | Matthews KA, Dahl RE, Owens JF, Lee L, Hall M | Matthews KA, Dahl RE, Owens JF, Lee L, Hall M | ✓ |
| Journal | Sleep | Sleep | ✓ |
| Volume/Issue | 35/10 | 35/10 | ✓ |
| Pages | 1353-1358 | 1353-1358 | ✓ |
| Year | 2012 | 2012-10 | ✓ |

### S7 — Lange et al. (2003) ★ NCBI PMID 14508028

| 字段 | v8 frontmatter | NCBI efetch PMID 14508028 | 结论 |
|---|---|---|---|
| Title | Sleep enhances the human antibody response to hepatitis A vaccination | Sleep enhances the human antibody response to hepatitis A vaccination. | ✓ |
| Authors | Lange T, Perras B, Fehm HL, Born J | Lange T, Perras B, Fehm HL, Born J | ✓ |
| **Journal** | **Psychosomatic Medicine** | **Psychosomatic medicine / Psychosom Med** | **✓ v8 修正正确** |
| **Volume/Issue** | **65/5** | **65/5** | **✓ v8 修正正确** |
| **Pages** | **831-835** | **831-835 (MedlinePgn: 831-5)** | **✓ v8 修正正确** |
| **DOI** | **10.1097/01.psy.0000091382.61178.f1** | **✓ identical** | **✓ v8 修正正确** |
| PMID | 14508028 | 14508028 | ✓ |
| Year | 2003 | 2003 Sep-Oct | ✓ |

**v7 错误**：期刊为 "JAMA"，volume=290, issue=12, pages="1593-1594", DOI="10.1001/jama.290.12.1593"。NCBI 确认该论文发表于 Psychosomatic Medicine, vol 65, issue 5, pages 831-835, DOI 10.1097/01.psy.0000091382.61178.f1。v8 全面修正正确。

### S8 — Prather et al. (2012) ★ NCBI PMID 22851802

| 字段 | v8 frontmatter | NCBI efetch PMID 22851802 | 结论 |
|---|---|---|---|
| Title | Sleep and antibody response to hepatitis B vaccination | Sleep and antibody response to hepatitis B vaccination. | ✓ |
| **Authors** | **Prather AA, Hall M, Fury JM, Ross DC, Muldoon MF, Cohen S, Marsland AL** | **Prather AA, Hall M, Fury JM, Ross DC, Muldoon MF, Cohen S, Marsland AL** (7 authors) | **✓ v8 修正正确** |
| Journal | Sleep | Sleep | ✓ |
| **Volume/Issue** | **35/8** | **35/8** | **✓ v8 修正正确** |
| **Pages** | **1063-1069** | **1063-1069 (MedlinePgn: 1063-9)** | **✓ v8 修正正确** |
| **DOI** | **10.5665/sleep.1990** | **✓ identical** | **✓ v8 修正正确** |
| PMID | 22851802 | 22851802 | ✓ |
| **PMCID** | **PMC3397812** | **PMC3397812** | **✓ v8 新增正确** |
| Year | 2012 | 2012 Aug | ✓ |

**v7 错误**：volume=35, issue=5, pages="601-606", DOI="10.5665/sleep.1808", 作者为 "Prather AA, Hall M, Fury JM, et al."。NCBI 确认正确为 volume=35, issue=8, pages=1063-1069, DOI=10.5665/sleep.1990, PMID=22851802, PMCID=PMC3397812, 7位作者全名列出。v8 全面修正正确。

**分母/通过率：8/8（100%）— 所有 DOI 解析正确，所有标题/作者/期刊/卷期/DOI 经权威源确认**

## V7→V8 漂移检查

| 检查项 | 方法 | 结果 |
|---|---|---|
| 科学正文 | `diff` of body text (YAML 之后) | **空输出 — 零漂移** |
| 三机制内容 | 突触稳态、类淋巴清除、免疫-代谢调节 | 逐字一致 |
| HOMA-IR 定量 | 0.28 单位/小时、Fisher-z 精度基准、120 完成者 | 一致 |
| 纳入/排除标准 | 18-45 岁、STOP-Bang 0-2、无糖尿病等 | 一致 |
| planned/executed 状态 | 所有项目仍为 planned，无 executed 项 | 一致 |
| 观察性边界声明 | "无法确立因果关系"等表述 | 一致 |
| 疫苗研究修正 | S7 实验性 vs S8 观察性 | 一致 |
| 历史错引删除 | Cappuccio、Ford 已删除 | 确认 |
| 新增科学内容 | 无 | — |
| 新增来源 | 无 | — |

**结论：v7→v8 仅 YAML frontmatter 元数据修正（S5 作者、S7 期刊/卷期页/DOI、S8 卷期页/DOI/PMID/PMCID/作者展开），科学正文零漂移。**

## V7→V8 YAML 变更核验

| 变更项 | v7 值 | v8 值 | NCBI/Crossref 权威值 | 判定 |
|---|---|---|---|---|
| S5 authors | Spiegel K, Leproult R, Van Cauter E | Spiegel K, Tasali E, Penev P, Van Cauter E | Spiegel K, Tasali E, Penev P, Van Cauter E (PMID 15583226) | ✓ 修正正确 |
| S7 journal | JAMA | Psychosomatic Medicine | Psychosomatic Medicine (PMID 14508028) | ✓ 修正正确 |
| S7 volume | 290 | 65 | 65 | ✓ 修正正确 |
| S7 issue | 12 | 5 | 5 | ✓ 修正正确 |
| S7 pages | 1593-1594 | 831-835 | 831-835 | ✓ 修正正确 |
| S7 DOI | 10.1001/jama.290.12.1593 | 10.1097/01.psy.0000091382.61178.f1 | 10.1097/01.psy.0000091382.61178.f1 | ✓ 修正正确 |
| S7 PMID | (无) | 14508028 | 14508028 | ✓ 新增正确 |
| S8 volume | 35 | 35 | 35 | 不变 |
| S8 issue | 5 | 8 | 8 | ✓ 修正正确 |
| S8 pages | 601-606 | 1063-1069 | 1063-1069 | ✓ 修正正确 |
| S8 DOI | 10.5665/sleep.1808 | 10.5665/sleep.1990 | 10.5665/sleep.1990 | ✓ 修正正确 |
| S8 PMID | (无) | 22851802 | 22851802 | ✓ 新增正确 |
| S8 PMCID | (无) | PMC3397812 | PMC3397812 | ✓ 新增正确 |
| S8 authors | Prather AA, Hall M, Fury JM, et al. | Prather AA, Hall M, Fury JM, Ross DC, Muldoon MF, Cohen S, Marsland AL | 7 authors (PMID 22851802) | ✓ 展开正确 |

## 单一正文检查

- v8.md 共 282 行，YAML frontmatter 由恰好 2 个 `---` 行界定
- `REVISION_RESULT: CANDIDATE` 出现 1 次（文件末尾）
- 科学正文 H1 标题：`# 睡眠时长与免疫-代谢健康：前瞻性队列研究计划（V8）`，仅 1 个
- 无重复正文块

**结论：单一正文，无重复**

## 伪造执行检查

- 无模拟实验结果
- 无虚构数据
- 所有研究步骤标记为 planned
- 无 executed 项
- REVISION_RESULT: CANDIDATE 正确标记为候选

**结论：无伪造执行**

## 三机制核验

| 机制 | 核心来源 | 区分性 | 选择理由 | 结论 |
|---|---|---|---|---|
| 突触稳态 | S1 | 神经可塑性层面 | 需 EEG/神经影像，成本高 | 保留为比较方向 |
| 类淋巴清除 | S2 + S3 | 代谢废物清除层面 | 需侵入性采样，伦理限制大 | 保留为比较方向 |
| 免疫-代谢调节 | S4 + S5 + S6 | 炎症/激素通路层面 | 腕动计+血液采样可行 | 选为研究计划方向 |

三方向在机制层面真正不同，选择基于可行性而非证伪其他假说。符合协议要求。

## HOMA-IR 计划与观察性边界核验

- **主要终点**：6 个月 HOMA-IR，前瞻性设计
- **统计方法**：ANCOVA 回归，显式称为"关联"或"时间预测"，绝不称为"因果效应"
- **样本量**：精度导向（Fisher-z SE），显式声明不冒充调整模型功效
- **S6 使用**：仅作为背景参考，显式声明不用于成人样本量计算
- **局限性**：残余混杂、反向因果、腕动计局限、外推限制均已声明
- **观察性边界**：全文未出现因果推断语言，观察性设计约束贯穿始终

**结论：HOMA-IR 计划在观察性边界内，无越界**

## artifact_stage 与终态

- v8 artifact_stage = `revision_candidate`：版本阶段，不是 Project 终态
- run.md 当前 status = `waiting_human`：正确反映 Project 终态
- v8 不改变终态理由：仍需 IRB、知情同意、腕动计和实验室资源
- 若 v8 被接受为 final，run.md 应更新 `final: v8.md`、`final_review: review-v8.md`

## V1→最终链完整性

| 版本 | 分数 | 关键修复 |
|---|:---:|---|
| V1 | 7/12 | 初始候选；因果过度、疫苗事实错误、样本量错误 |
| V2 | 8/12 | 修复因果和疫苗；引入两条定量错引 |
| V3 | 9/12 | 改为 precision pilot；Xie 错述修复 |
| V4 | 11/12 | 修复六项缺陷；8/8 引用 |
| V5 | 12/12 | 最终候选；最小修订 |
| V6 | 12/12 | 终态收口为 waiting_human |
| V7 | 12/12 | 来源投影至 frontmatter；无科学漂移 |
| **V8** | **12/12** | **S5/S7/S8 元数据修正至 NCBI 权威记录；科学正文零漂移** |

V1→V8 链不回退，分数单调递增或持平。

## Findings

### Critical
无。

### High
无。

### Medium
无。

### Low

**L1. S3 pages 预存错误**：v8 frontmatter S3 pages="623-630"，但 Crossref 和 NCBI PMID 31672896 均确认为 628-631。此错误自 v7（及更早版本）继承，非 v7→v8 回归。v8 变更说明仅声明修正 S5/S7/S8，未声明修正 S3，因此不构成虚假声明。建议 run owner 在下一轮修订中修正。不影响任何科学断言（正文未引用 S3 具体页码）。

**L2. v7 S7 DOI 指向错误论文**：v7 的 S7 DOI 10.1001/jama.290.12.1593 实际指向一篇 JAMA 论文（非 Lange 2003 甲肝疫苗研究）。v8 已修正为正确 DOI 10.1097/01.psy.0000091382.61178.f1。review-v7 声称该 DOI 核验通过，属于 v7 reviewer 的遗漏。v8 已修复，无需进一步动作。

## 向 run owner 的建议

1. **S3 pages 修正**：下一轮修订将 S3 pages 从 "623-630" 修正为 "628-631"（Crossref + NCBI PMID 31672896 确认）。
2. **run.md 更新**：若 v8 被接受为 final，更新 `final: v8.md`、`final_review: review-v8.md`。
3. **无需进一步科学修订**：v8 科学正文零漂移，元数据修正经 NCBI 权威源确认，12/12 评分达标。

## Project Terminal Recommendation

**推荐终态：`waiting_human`**（与 run.md 当前 status 一致）

理由：
1. 研究计划已通过独立评审（12/12）
2. 继续执行需要 IRB 批准、参与者知情同意、腕动计设备和实验室资源
3. 观察性设计不能建立因果关系
4. 符合 readme.md `waiting_human` 判定："继续运行需要领域裁决、受限数据权限、安全或伦理决定"

本 reviewer 不裁决 Project terminal；仅向 run owner 提供建议。

RESULT: DELIVERABLE
