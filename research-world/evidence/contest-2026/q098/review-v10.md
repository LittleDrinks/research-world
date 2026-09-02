---
project: q098
artifact: v10
reviewer: q098-v10-final-reviewer
reviewer_session: 01a05edc-80ec-717a-a4d2-81b799ea5e7a
reviewer_marker: ATTR-Q098-R10-550059
role: independent-review
reviewed: v10.md
prior: v9.md
prior_review: review-v9.md
verdict: deliverable
method: NCBI efetch + Crossref API direct verification + structural diff
---

# q098 V10 终审

## 一、S5 完整题名权威核验（本轮核心修复项）

### NCBI efetch PMID 15583226

| 字段 | NCBI XML 原文 | v10 frontmatter | 判定 |
|---|---|---|---|
| ArticleTitle | `Brief communication: Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite.` | `Brief communication: Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite` | ✓ 一致（仅省略句号，符合引用格式） |
| Authors | Spiegel K, Tasali E, Penev P, Van Cauter E | `Spiegel K, Tasali E, Penev P, Van Cauter E` | ✓ |
| Volume | 141 | `volume: 141` | ✓ |
| Issue | 11 | `issue: 11` | ✓ |
| Pages | StartPage 846, EndPage 850 | `pages: "846-850"` | ✓ |
| DOI | `10.7326/0003-4819-141-11-200412070-00008` | `doi: "10.7326/0003-4819-141-11-200412070-00008"` | ✓ |
| Journal | Ann Intern Med | `journal: "Ann Intern Med"` | ✓ |
| Year | 2004 | `year: 2004` | ✓ |

### Crossref API `GET /works/10.7326/0003-4819-141-11-200412070-00008`

```
title: ['Brief Communication: Sleep Curtailment in Healthy Young Men Is Associated with Decreased Leptin Levels, Elevated Ghrelin Levels, and Increased Hunger and Appetite']
author: [('Spiegel', 'Karine'), ('Tasali', 'Esra'), ('Penev', 'Plamen'), ('Cauter', 'Eve Van')]
volume: 141
issue: 11
page: 846-850
DOI: 10.7326/0003-4819-141-11-200412070-00008
journal: ['Annals of Internal Medicine']
year: [[2004, 12, 7]]
```

**注**：Crossref 将末位作者解析为 `family="Cauter", given="Eve Van"`，但 NCBI efetch XML 明确为 `<LastName>Van Cauter</LastName><ForeName>Eve</ForeName>`。v10 采用 NCBI 权威格式 `Van Cauter E`，正确。

**结论：v10 S5 title 补全"Brief communication: "前缀与 NCBI PMID 15583226 完全一致。v9 的 S5 标题缺少"Brief communication: "前缀，v10 已修正。**

## 二、S3/S7/S8 v9 修复保持核验

| 来源 | 字段 | v10 值 | NCBI 权威值 | 保持 |
|---|---|---|---|---|
| S3 | pages | "628-631" | PMID 31672896: pages 628-631 | ✓ |
| S3 | DOI | "10.1126/science.aax5440" | PMID 31672896: 同 | ✓ |
| S3 | volume/issue | 366/6465 | PMID 31672896: 同 | ✓ |
| S7 | journal | "Psychosomatic Medicine" | PMID 14508028: Psychosom Med | ✓ |
| S7 | vol/issue/pages | 65/5/831-835 | PMID 14508028: 65/5/831-5 | ✓ |
| S7 | DOI | "10.1097/01.psy.0000091382.61178.f1" | PMID 14508028: 同 | ✓ |
| S8 | vol/issue/pages | 35/8/1063-1069 | PMID 22851802: 35/8/1063-9 | ✓ |
| S8 | DOI | "10.5665/sleep.1990" | PMID 22851802: 同 | ✓ |
| S8 | PMID/PMCID | 22851802/PMC3397812 | PMID 22851802: 同 | ✓ |
| S8 | authors (7 full) | Prather AA, Hall M, Fury JM, Ross DC, Muldoon MF, Cohen S, Marsland AL | PMID 22851802: 同 | ✓ |

**结论：v9 三项修复（S3 pages、S7/S8 DOI 与元数据）在 v10 中完整保持，零回退。**

## 三、V9→V10 全量 Diff

### YAML frontmatter（3 处变更，全部预期内）

| 变更项 | v9 | v10 | 预期 |
|---|---|---|---|
| artifact | v9 | v10 | ✓ 版本递进 |
| supersedes | v8.md | v9.md | ✓ 指向更新 |
| S5 title | `Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite` | `Brief communication: Sleep curtailment in healthy young men is associated with decreased leptin levels, elevated ghrelin levels, and increased hunger and appetite` | ✓ 核心修复：补全"Brief communication: "前缀 |

YAML 其余 82 行逐字节一致（S1–S4、S6–S8 全部元数据、project/stage 声明）。

### 科学正文（YAML `---` 之后至变更说明之前）

```
diff v9_body v10_body
→ 唯一差异：H1 标题 V9→V10（第1行）
→ 其余 197 行科学正文逐字一致
```

**检查清单**：

| 检查项 | 结果 |
|---|---|
| 三机制内容（突触稳态/类淋巴/免疫-代谢） | 逐字一致 |
| HOMA-IR 定量（0.28 单位/小时、Fisher-z、120 完成者） | 一致 |
| 纳入/排除标准（18-45 岁、STOP-Bang 0-2） | 一致 |
| planned/executed 状态（全 planned，零 executed） | 一致 |
| 观察性边界声明（"无法确立因果关系"） | 一致 |
| 疫苗研究区分（S7 实验性 vs S8 观察性） | 一致 |
| 历史错引（Cappuccio/Ford 已删除） | 确认保持删除 |
| 新增科学内容 | 无 |
| 新增来源 | 无 |

**结论：科学正文零漂移。**

### 变更说明段落

v9 变更说明（2 条：S3 修复 + artifact 递进）→ v10 变更说明（2 条：S5 title 前缀补全 + artifact 递进）。仅元数据记录更新，不涉及科学主张。

## 四、六维评分（readme.md rubric）

| 维度 | 分数 | 依据 |
|---|:---:|---|
| 问题理解 | 2/2 | 与 v9 逐字一致；对象/范围/争议/知识缺口准确 |
| 文献证据 | 2/2 | 8/8 来源全经 NCBI/Crossref 核验（v9 review 已确认 S3/S7/S8，v10 仅补全 S5 title 前缀至权威值，其余 7 来源保持正确） |
| Direction 质量 | 2/2 | 三机制真正不同；各含支持/限制/区分性预测/实施负担；选择基于可行性 |
| 科学推理 | 2/2 | 观察性边界贯穿；反向因果已承认；S6 显式不用于样本量；负面对照纳入 |
| 研究计划 | 2/2 | 数据/方法/对照/判断/产物/资源/风险完整；全 planned 零 executed |
| 表达与追溯 | 2/2 | 单一主线；S1-S8 可追溯；V9→V10 变更说明清晰 |

**总分：12/12**

## 五、来源通过率

**8/8（100%）** — S1–S8 全部 DOI 解析正确，元数据与 NCBI/Crossref 权威记录一致。S5 title 现已包含"Brief communication: "前缀，与 PMID 15583226 完全匹配。

## 六、Planned/Executed 状态

所有研究步骤（腕动计发放、实验室采样、ANCOVA 分析、预注册等）标记为 planned。无 executed 项。无伪造数据、无模拟结果。

## 七、单一正文检查

| 检查 | 值 |
|---|---|
| 总行数 | 280 |
| `---` 分隔符 | 2（frontmatter 开/闭） |
| H1 标题 | 1（`# 睡眠时长与免疫-代谢健康：前瞻性队列研究计划（V10）`） |
| REVISION_RESULT | 1 次（`REVISION_RESULT: CANDIDATE`，文件末行） |
| 重复正文块 | 无 |

**结论：单一正文，无重复。**

## 八、V1→V10 链完整性

| 版本 | 分数 | 关键修复 |
|---|:---:|---|
| V1 | 7/12 | 初始候选；因果过度、疫苗事实和样本量错误 |
| V2 | 8/12 | 修复因果和疫苗；引入两条定量错引 |
| V3 | 9/12 | 改为 precision pilot；Xie 错述修复 |
| V4 | 11/12 | 修复六项缺陷；8/8 引用 |
| V5 | 12/12 | 最终候选；最小修订 |
| V6 | 12/12 | 终态收口为 waiting_human |
| V7 | 12/12 | 来源投影至 frontmatter；无科学漂移 |
| V8 | 12/12 | S5/S7/S8 元数据修正至 NCBI 权威记录 |
| V9 | 12/12 | S3 pages 修正至 628-631（NCBI+Crossref 双确认） |
| **V10** | **12/12** | **S5 title 补全"Brief communication: "前缀（NCBI PMID 15583226 确认）；科学正文零漂移** |

V1→V10 链不回退，分数单调递增或持平。

## 九、Findings

### Critical
无。

### High
无。

### Medium
无。

### Low
无。

## 十、终态建议

v10 是纯元数据修正版本，科学正文与 v9 零差异。8/8 来源元数据全部与 NCBI/Crossref 权威记录一致，零 open findings。建议 run owner：

1. **接受 v10 为 final artifact**
2. **更新 run.md**：`final: v10.md`、`final_review: review-v10.md`
3. **Project 终态保持 `waiting_human`**（仍需 IRB/知情同意/腕动计/实验室资源）

本 reviewer 不裁决 Project terminal；仅向 run owner 提供建议。

RESULT: DELIVERABLE
