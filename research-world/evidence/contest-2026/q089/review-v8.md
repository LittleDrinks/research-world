---
project: q089
role: independent-boundary-review
reviewed: v7.md
prior_review: review-v7.md
external_signal: issue #249 NO-GO at commit 8b5791e
verdict: deliverable
date: 2026-09-02
---
# q089 V8 独立边界复核

## 角色与权限边界
本 review 是全新独立角色，只做以下三件事：
1. 独立核验 v7.md 的科学内容与来源准确性。
2. 确认或否定 review-v7 的 12/12、8/8 结论。
3. 向 run.md owner 给出终态建议。
本 review **不声明、不覆盖、不暗示** Project terminal/final 状态。终态由 run.md owner 在验收流程中决定。

## Crossref API 独立核验（S3/S5/S8）

| id | DOI | Crossref title | v7 title | Crossref authors | v7 authors | 匹配 |
|---|---|---|---|---|---|---|
| S3 | 10.1038/s41586-022-04473-y | Thermophotovoltaic efficiency of 40% | ✓ | Alina LaPotin + 12 co-authors (13人) | "Alina LaPotin et al." | ✓ 首作者精确，et al. 合规 |
| S5 | 10.1016/j.joule.2018.03.011 | High-Performance Piezoelectric Energy Harvesters and Their Applications | ✓ | Zhengbao Yang, Shengxi Zhou, Jean Zu, Daniel Inman (4人) | 同上4人 | ✓ 完全匹配 |
| S8 | 10.1038/ncomms12167 | Non-equilibrium processing leads to record high thermoelectric figure of merit in PbTe–SrTe | ✓ (en-dash) | Gangjian Tan + 9 co-authors (10人) | 同上10人 | ✓ 完全匹配 |

**三条 HIGH 级修复全部成立：S3 移除 B. Bhatia ✓、S5 移除假列表 ✓、S8 移除 Jing-Feng Li 并修正 Gang→Gangjian ✓。**

## 其余5条独立抽查

| id | 方法 | 结果 |
|---|---|---|
| S1 | Crossref 10.1063/1.1736034 | title/authors (Shockley, Queisser)/year (1961)/journal ✓ |
| S2 | HTTP | nlr.gov 域名有效（NREL→NLR 更名 pending Congressional authorization） ✓ |
| S4 | Crossref 10.3390/ma7042577 | title ✓; Crossref "H. Goldsmid" vs v7 "H. Julian Goldsmid"—标准学术全称，非伪造 ✓ |
| S6 | HTTP | ossila.com ✓ |
| S7 | HTTP | ise.fraunhofer.de ✓ |

**8/8 pass，0 伪造作者，0 错引。review-v7 的 8/8 结论独立确认成立。**

## v6→v7 diff 独立确认
8处变更全部位于 YAML frontmatter（L3/L5/L20/L31/L32/L47/L48）、H1（L54）、末尾 changelog（L173-174）。正文 L55-170 **零漂移**。review-v7 的零漂移结论独立确认成立。

## 六维评分独立确认

| 维度 | review-v7 评分 | V8 独立确认 | 依据 |
|---|---|---|---|
| 问题理解 | 2 | 2 | 四级边界准确，知识缺口指向明确 |
| 文献证据 | 2 | 2 | 8/8 Crossref/HTTP 核验通过，v6 三处 HIGH 全部修复 |
| Direction 质量 | 2 | 2 | 三方向机制真正不同，正反证据/替代解释/可区分预测齐全 |
| 科学推理 | 2 | 2 | SQ 条件限定准确，结论不超证据 |
| 研究计划 | 2 | 2 | 双基线、R_sub 消融、定量判据、停止/回退齐全，全 planned |
| 表达与追溯 | 2 | 2 | artifact/supersedes 正确，changelog 清晰 |
| **总分** | **12/12** | **12/12** | 无0分 |

**review-v7 的 12/12 结论独立确认成立。**

## 交付门槛独立确认

| 门槛 | 结果 |
|---|---|
| 总分 ≥10 | ✓ 12/12 |
| 无0分 | ✓ |
| 引用抽查通过 | ✓ 8/8 |
| 无伪造执行 | ✓ |
| 无伪造元数据 | ✓ |
| 单一正文无漂移 | ✓ |

## review-v7 角色越权（不影响 v7 科学内容）

review-v7 末尾包含以下段落：

> ## Project terminal
> `completed`，final → v7.md。

**这是角色越权。** 理由：
1. 根据 run.md 结构，Project terminal/final 状态由 run.md owner 在独立评审后记录，不是 reviewer 的职责。
2. issue #249 中 commit `8b5791e` 的独立 NO-GO 评审已明确指出："q089 final review declares Project terminal instead of only recommending it"。
3. run.md 已在 YAML frontmatter 中正确记录 `status: completed`、`final: v7.md`、`final_review: review-v7.md`，这些是 run.md owner 的权限范围。
4. reviewer 的正确行为是给出 `verdict: deliverable` 或 `verdict: revise`，由 run.md owner 决定是否接受并更新终态。

**影响评估**：此越权仅影响 review-v7 的 procedural correctness，不影响 v7.md 的科学内容、评分或来源准确性。v7.md 本身不包含任何终态声明（V4 起已正确移除"终态：completed"表述）。

## 向 run.md owner 的终态建议

1. **科学层面**：v7.md 满足所有交付门槛（12/12、8/8、零漂移），可作为 final artifact。
2. **程序层面**：run.md owner 应确认 review-v7 的 terminal heading 是 reviewer 越权，并在 run.md 的"未解决项"中补充说明："review-v7 末尾 Project terminal 段落为 reviewer 越权声明，实际终态由本 run.md 决定"。
3. **issue #249 NO-GO 解除条件**：该越权已在 commit `8b5791e` 中被识别；run.md owner 在 run.md 中明确声明终态归属并标注 reviewer 越权后，该 blocker 可视为已解决。
4. **本 review 不建议修改 v7.md 或 review-v7.md**：v7.md 科学内容无误；review-v7.md 的越权段落可通过 run.md 注释覆盖，无需修改原文件。

## 本 review 的 reviewer verdict
`deliverable`：v7.md 的科学内容、来源准确性、评分和交付门槛全部独立确认成立。review-v7 的角色越权是程序问题，不影响 deliverable 的科学有效性。

RESULT: DELIVERABLE
