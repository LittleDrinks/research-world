---
project: q098
role: independent-review
reviewed: v9.md
prior: v8.md
verdict: deliverable
reviewer: q098-v9-final-reviewer
method: NCBI efetch + Crossref API direct verification + structural diff
---

# q098 V9 终审

## 一、S3 pages 权威核验（本轮核心修复项）

### NCBI efetch PMID 31672896

| 字段 | NCBI XML 原文 | v9 frontmatter | 判定 |
|---|---|---|---|
| StartPage | `<StartPage>628</StartPage>` | — | — |
| EndPage | `<EndPage>631</EndPage>` | — | — |
| MedlinePgn | `<MedlinePgn>628-631</MedlinePgn>` | `pages: "628-631"` | ✓ 一致 |
| Volume | `<Volume>366</Volume>` | `volume: 366` | ✓ |
| Issue | `<Issue>6465</Issue>` | `issue: 6465` | ✓ |
| DOI | `<ELocationID EIdType="doi">10.1126/science.aax5440</ELocationID>` | `doi: "10.1126/science.aax5440"` | ✓ |

### Crossref API `GET /works/10.1126/science.aax5440`

```
pages=628-631, volume=366, issue=6465
```

**结论：v9 S3 pages="628-631" 与 NCBI 和 Crossref 双源完全一致。review-v8 L1 finding 已闭合。**

## 二、S5/S7/S8 v8 修复保持核验

| 来源 | 字段 | v9 值 | NCBI/Crossref 权威值 | 保持 |
|---|---|---|---|---|
| S5 | authors | Spiegel K, Tasali E, Penev P, Van Cauter E | PMID 15583226: 同 | ✓ |
| S5 | DOI | 10.7326/0003-4819-141-11-200412070-00008 | Crossref: 同 | ✓ |
| S5 | vol/issue/pages | 141/11/846-850 | NCBI+Crossref: 同 | ✓ |
| S7 | journal | Psychosomatic Medicine | PMID 14508028: Psychosomatic medicine | ✓ |
| S7 | vol/issue/pages | 65/5/831-835 | NCBI: 同 | ✓ |
| S7 | DOI | 10.1097/01.psy.0000091382.61178.f1 | NCBI: 同 | ✓ |
| S8 | vol/issue/pages | 35/8/1063-1069 | PMID 22851802: 同 | ✓ |
| S8 | DOI | 10.5665/sleep.1990 | NCBI: 同 | ✓ |
| S8 | PMID/PMCID | 22851802/PMC3397812 | NCBI: 同 | ✓ |
| S8 | authors (7 full) | Prather AA, Hall M, Fury JM, Ross DC, Muldoon MF, Cohen S, Marsland AL | PMID 22851802: 同 | ✓ |

**结论：v8 三项修复（S5/S7/S8）在 v9 中完整保持，零回退。**

## 三、V8→V9 全量 Diff

### YAML frontmatter（3 处变更，全部预期内）

| 变更项 | v8 | v9 | 预期 |
|---|---|---|---|
| artifact | v8 | v9 | ✓ 版本递进 |
| supersedes | v7.md | v8.md | ✓ 指向更新 |
| S3 pages | "623-630" | "628-631" | ✓ 核心修复 |

YAML 其余 78 行逐字节一致（S1–S2、S4–S8 全部元数据、project/stage 声明）。

### 科学正文（YAML `---` 之后至变更说明之前）

```
diff /tmp/v8_body.md /tmp/v9_body.md
→ 唯一差异：H1 标题 V8→V9（第2行）
→ 其余 189 行科学正文逐字一致
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

v8 变更说明（4 条 S5/S7/S8 修正）→ v9 变更说明（2 条：S3 修复 + artifact 递进）。仅元数据记录更新，不涉及科学主张。

## 四、六维评分（readme.md rubric）

| 维度 | 分数 | 依据 |
|---|:---:|---|
| 问题理解 | 2/2 | 与 v8 逐字一致；对象/范围/争议/知识缺口准确 |
| 文献证据 | 2/2 | 8/8 来源全经 NCBI/Crossref 核验（v8 review 已逐条确认，v9 仅修正 S3 pages 至权威值，S5/S7/S8 保持正确） |
| Direction 质量 | 2/2 | 三机制真正不同；各含支持/限制/区分性预测/实施负担；选择基于可行性 |
| 科学推理 | 2/2 | 观察性边界贯穿；反向因果已承认；S6 显式不用于样本量；负面对照纳入 |
| 研究计划 | 2/2 | 数据/方法/对照/判断/产物/资源/风险完整；全 planned 零 executed |
| 表达与追溯 | 2/2 | 单一主线；S1-S8 可追溯；V8→V9 变更说明清晰 |

**总分：12/12**

## 五、来源通过率

**8/8（100%）** — S1–S8 全部 DOI 解析正确，元数据与 NCBI/Crossref 权威记录一致。

## 六、Planned/Executed 状态

所有研究步骤（腕动计发放、实验室采样、ANCOVA 分析、预注册等）标记为 planned。无 executed 项。无伪造数据、无模拟结果。

## 七、单一正文检查

| 检查 | 值 |
|---|---|
| 总行数 | 280 |
| `---` 分隔符 | 2（frontmatter 开/闭） |
| H1 标题 | 1（`# 睡眠时长与免疫-代谢健康：前瞻性队列研究计划（V9）`） |
| REVISION_RESULT | 1 次（`REVISION_RESULT: CANDIDATE`，文件末行） |
| 重复正文块 | 无 |

**结论：单一正文，无重复。**

## 八、V1→V9 链完整性

| 版本 | 分数 | 关键修复 |
|---|:---:|---|
| V1 | 7/12 | 初始候选；因果过度、疫苗事实错误、样本量错误 |
| V2 | 8/12 | 修复因果和疫苗；引入两条定量错引 |
| V3 | 9/12 | 改为 precision pilot；Xie 错述修复 |
| V4 | 11/12 | 修复六项缺陷；8/8 引用 |
| V5 | 12/12 | 最终候选；最小修订 |
| V6 | 12/12 | 终态收口为 waiting_human |
| V7 | 12/12 | 来源投影至 frontmatter；无科学漂移 |
| V8 | 12/12 | S5/S7/S8 元数据修正至 NCBI 权威记录 |
| **V9** | **12/12** | **S3 pages 修正至 628-631（NCBI+Crossref 双确认）；科学正文零漂移** |

V1→V9 链不回退，分数单调递增或持平。review-v8 L1 finding 已闭合。

## 九、Findings

### Critical
无。

### High
无。

### Medium
无。

### Low
无。（review-v8 L1 S3 pages 已在 v9 修正闭合；L2 为历史信息，v8 已修复。）

## 十、终态建议

v9 是纯元数据修正版本，科学正文与 v8 零差异。8/8 来源元数据全部与 NCBI/Crossref 权威记录一致，零 open findings。建议 run owner：

1. **接受 v9 为 final artifact**
2. **更新 run.md**：`final: v9.md`、`final_review: review-v9.md`
3. **Project 终态保持 `waiting_human`**（仍需 IRB/知情同意/腕动计/实验室资源）

本 reviewer 不裁决 Project terminal；仅向 run owner 提供建议。

RESULT: DELIVERABLE
