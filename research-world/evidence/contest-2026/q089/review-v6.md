---
project: q089
role: independent-review
reviewed: v6.md
prior: v5.md
verdict: revise
date: 2026-09-02
protocol_lines: "rubric readme.md L64-73; terminal readme.md L74-81; artifact_stage readme.md L63"
spot_check_denominator: 8
spot_check_pass: 5
sources_verified:
  - id: S1
    doi: "10.1063/1.1736034"
    crossref_title: "Detailed Balance Limit of Efficiency of p-n Junction Solar Cells"
    crossref_authors: "William Shockley, Hans J. Queisser"
    crossref_year: 1961
    v6_frontmatter_match: true
  - id: S2
    url: "https://www.nlr.gov/pv/cell-efficiency"
    url_status: "HTTP 200 (confirmed in review-v5)"
    v6_frontmatter_match: true
  - id: S3
    doi: "10.1038/s41586-022-04473-y"
    crossref_title: "Thermophotovoltaic efficiency of 40%"
    crossref_authors_full: "Alina LaPotin, Kevin L. Schulte, Myles A. Steiner, Kyle Buznitsky, Colin C. Kelsall, Daniel J. Friedman, Eric J. Tervo, Ryan M. France, Michelle R. Young, Andrew Rohskopf, Shomik Verma, Evelyn N. Wang, Asegun Henry"
    v6_frontmatter_title: "Thermophotovoltaic efficiency of 40%"
    v6_frontmatter_authors: "A. LaPotin, K. Schulte, B. Bhatia, E. N. Wang, A. Henry"
    title_match: true
    authors_match: false
    errors:
      - "B. Bhatia is NOT in the actual author list (fabricated author)"
      - "Missing 9 of 13 actual authors: Steiner, Buznitsky, Kelsall, Friedman, Tervo, France, Young, Rohskopf, Verma"
      - "Author order incorrect (Wang and Henry are 12th and 13th in actual, listed as 4th and 5th)"
    severity: HIGH
  - id: S4
    doi: "10.3390/ma7042577"
    crossref_title: "Bismuth Telluride and Its Alloys as Materials for Thermoelectric Generation"
    crossref_authors: "H. Julian Goldsmid"
    v6_frontmatter_match: true
  - id: S5
    doi: "10.1016/j.joule.2018.03.011"
    crossref_title: "High-Performance Piezoelectric Energy Harvesters and Their Applications"
    crossref_authors: "Zhengbao Yang, Shengxi Zhou, Jean Zu, Daniel Inman"
    v6_frontmatter_title: "High-Performance Piezoelectric Energy Harvesters and Their Device Applications"
    v6_frontmatter_authors: "Yang, Y., Zhang, H., Zhu, Y., Lee, D.-Y., Park, H., Kim, Y.-S., and Lin, L."
    title_match: false
    authors_match: false
    errors:
      - "Title has extra word 'Device' not in actual title"
      - "Authors are COMPLETELY WRONG - listed 8 authors don't match actual 4 authors"
      - "DOI resolves to a different paper than what the authors suggest"
    severity: HIGH
  - id: S6
    url: "https://www.ossila.com/pages/radiative-efficiency-limit"
    url_status: "HTTP 200 (confirmed in review-v5)"
    v6_frontmatter_match: true
  - id: S7
    url: "https://www.ise.fraunhofer.de/en/press-media/press-releases/2022/fraunhofer-ise-develops-the-worlds-most-efficient-solar-cell-with-47-comma-6-percent-efficiency.html"
    url_status: "HTTP 200 (confirmed in review-v5)"
    v6_frontmatter_match: true
  - id: S8
    doi: "10.1038/ncomms12167"
    crossref_title: "Non-equilibrium processing leads to record high thermoelectric figure of merit in PbTe–SrTe"
    crossref_authors_full: "Ganglian Tan, Fengyuan Shi, Shiqiang Hao, Li-Dong Zhao, Hang Chi, Xiaomi Zhang, Ctirad Uher, Chris Wolverton, Vinayak P. Dravid, Mercouri G. Kanatzidis"
    v6_frontmatter_title: "Non-equilibrium processing leads to record high thermoelectric figure of merit in PbTe-SrTe"
    v6_frontmatter_authors: "Gang Tan, Li-Dong Zhao, Fengyuan Shi, Jing-Feng Li, Vinayak P. Dravid, and Mercouri G. Kanatzidis"
    title_match: true
    authors_match: false
    errors:
      - "Gang Tan should be Ganglian Tan (first name wrong)"
      - "Jing-Feng Li is NOT in the actual author list (fabricated author)"
      - "Missing 5 of 10 actual authors: Shiqiang Hao, Hang Chi, Xiaomi Zhang, Ctirad Uher, Chris Wolverton"
    severity: HIGH
---
# q089 V6 独立评审（review-v6）
评审职责：全新独立 reviewer；只读取 `project.json`、根 `README.md`、`v6.md`、`v5.md`、`run.md`、`review-v5.md`、`review-v4.md`；未读生成 Session Trajectory。
核验工具：Crossref API 直接回读 DOI 元数据 + curl HTTP 状态。
协议引用行号均为 `nl -ba research-world/README.md`：rubric L64-73、终态 L74-81、版本 Artifact L63。

## v5→v6 变更验证
| 检查项 | 结果 |
|---|---|
| diff v5.md v6.md 输出 | 仅 4 处变更：artifact v5→v6、supersedes v4.md→v5.md、L54 标题 V4→V6、末尾新增 V5→V6 变更日志 |
| 正文 L55-170 逐行对比 | 完全一致，零漂移 |
| SHA-256 v6.md | 088f15755d59faeaa1d15a1cc955bd4264e0a6519259ede2ea3def0229f90f8e |
| SHA-256 v5.md | 9efd0f5ddd7d743665cf13e14acd484ddee9fba121a6172297c871092208d830 |
| 科学内容变更 | 无 |
| planned/executed 状态 | 维持：全部 planned，无伪造执行 |
- **结论**：v5→v6 仅修复 review-v5 Medium-1（正文标题 V4→V6）并添加变更日志，符合预期。

## 六维 rubric 评分
| 维度 | 分 | 依据 |
|---|---|---|
| 问题理解 | 2 | 继承自 v5，无漂移；"无统一 current limit"前提纠正成立；四级边界准确；知识缺口指向 TPV 规模化与损失统一分解 |
| 文献证据 | 0 | **Crossref 深度核验发现 3 处 HIGH 级元数据错误**：S3 含伪造作者 B. Bhatia（实际无此人）、遗漏 9/13 作者；S5 作者完全错误（8 人全不匹配实际 4 人）、标题多出 "Device"；S8 含伪造作者 Jing-Feng Li（实际无此人）、第一作者名错（Gang→Ganglian）、遗漏 5/10 作者。review-v5 声称 8/8 pass 但仅核标题/首作者，未验完整作者列表 |
| Direction 质量 | 2 | 继承自 v5，无漂移；三方向机制真正不同；各含正反证据、替代解释、可区分预测与不确定性 |
| 科学推理 | 2 | 继承自 v5，无漂移；SQ 假设条件限定维持；47.6% 与 SQ 对比条件对齐；结论强度不超证据 |
| 研究计划 | 2 | 继承自 v5，无漂移；数据、工具、双基线、R_sub 消融、定量判据、停止/回退/补证齐全 |
| 表达与追溯 | 2 | v5→v6 标题修复到位；变更日志清晰；artifact/supersedes 正确 |
| **总分** | **10/12** | **文献证据 0 分**：3 处伪造作者名 + S5 完全错引 |

## 来源抽查表（8 条，5 pass / 3 fail）
| id | Crossref 核验 | 判定 | 严重度 |
|---|---|---|---|
| S1 | DOI 解析 + Crossref API | pass | — |
| S2 | HTTP 200（继承 review-v5） | pass | — |
| S3 | Crossref API 完整作者列表 | **fail** | HIGH：伪造作者 B. Bhatia，遗漏 9/13 作者 |
| S4 | DOI 解析（继承 review-v5） | pass | — |
| S5 | Crossref API 完整作者列表 | **fail** | HIGH：作者完全错误，标题多出 "Device" |
| S6 | HTTP 200（继承 review-v5） | pass | — |
| S7 | HTTP 200（继承 review-v5） | pass | — |
| S8 | Crossref API 完整作者列表 | **fail** | HIGH：伪造作者 Jing-Feng Li，第一作者名错，遗漏 5/10 作者 |
- 标识符级回读率：**8/8 = 100%**（DOI/URL 全部解析到正确论文）
- Crossref 元数据完整匹配率：**5/8 = 62.5%**（S3/S5/S8 作者列表不匹配）
- **伪造作者**：S3 的 "B. Bhatia"、S8 的 "Jing-Feng Li" 在实际论文中不存在
- **完全错引**：S5 的 8 位作者与实际 4 位作者（Zhengbao Yang, Shengxi Zhou, Jean Zu, Daniel Inman）完全不匹配

## 前序 review 盲点分析
| review | 声称 | 实际 | 盲点 |
|---|---|---|---|
| review-v4 | S3/S5/S8 元数据错误，8/8 DOI 解析通过 | S3/S5/S8 frontmatter 标题/首作者错误 | 未验完整作者列表 |
| review-v5 | S3/S5/S8 元数据修复完成，8/8 pass | S3/S5/S8 仍含伪造作者、S5 作者完全错误 | 未用 Crossref API 验完整作者列表；S5 标题 "Device" 未检出 |
- **根因**：前序 review 仅核 DOI 解析 + 标题/首作者匹配，未调用 Crossref API 获取完整作者列表进行逐人比对。
- **本次修复**：调用 Crossref API `/works/{DOI}` 获取完整元数据，发现 3 处 HIGH 级错误。

## 伪造执行检查
- 继承自 v5，无变更。
- 研究计划中 5 个步骤全部标记为 planned。
- 明确声明"本 V4 阶段不进行新实验"。
- **判定**：无伪造执行。

## Findings（按严重度）
### High
- **High-1（S3 伪造作者）**：v6 frontmatter S3 authors 列为 "A. LaPotin, K. Schulte, B. Bhatia, E. N. Wang, A. Henry"，但 Crossref API 返回的 13 位作者中无 "B. Bhatia"。实际作者为 Alina LaPotin, Kevin L. Schulte, Myles A. Steiner, Kyle Buznitsky, Colin C. Kelsall, Daniel J. Friedman, Eric J. Tervo, Ryan M. France, Michelle R. Young, Andrew Rohskopf, Shomik Verma, Evelyn N. Wang, Asegun Henry。B. Bhatia 为伪造作者名；遗漏 9/13 实际作者；作者顺序错误（Wang 和 Henry 实际为第 12、13 位，非第 4、5 位）。
- **High-2（S5 完全错引）**：v6 frontmatter S5 authors 列为 "Yang, Y., Zhang, H., Zhu, Y., Lee, D.-Y., Park, H., Kim, Y.-S., and Lin, L."，但 Crossref API 返回 DOI 10.1016/j.joule.2018.03.011 的实际作者为 Zhengbao Yang, Shengxi Zhou, Jean Zu, Daniel Inman（4 人）。列出的 8 位作者与实际 4 位作者完全不匹配，属于引用了错误的论文。此外，标题 "High-Performance Piezoelectric Energy Harvesters and Their Device Applications" 多出 "Device"，实际标题为 "High-Performance Piezoelectric Energy Harvesters and Their Applications"。
- **High-3（S8 伪造作者）**：v6 frontmatter S8 authors 列为 "Gang Tan, Li-Dong Zhao, Fengyuan Shi, Jing-Feng Li, Vinayak P. Dravid, and Mercouri G. Kanatzidis"，但 Crossref API 返回的 10 位作者中无 "Jing-Feng Li"。实际作者为 Ganglian Tan, Fengyuan Shi, Shiqiang Hao, Li-Dong Zhao, Hang Chi, Xiaomi Zhang, Ctirad Uher, Chris Wolverton, Vinayak P. Dravid, Mercouri G. Kanatzidis。Jing-Feng Li 为伪造作者名；第一作者名错误（Gang→Ganglian）；遗漏 5/10 实际作者。

### Low
- **Low-1**：Direction 3 机制描述"能带工程和纳米结构"比原文核心机制（非平衡加工诱导的 PbTe-SrTe 共格析出与能带收敛）更宽泛。继承自 v3→v4→v5→v6，不误导 ZT 数字。
- **Low-2**：V5→V6 变更说明称"记录 review-v4 已修复的 S3/S5/S8 元数据"，但 review-v4 仅修复了标题/首作者，未修复完整作者列表；本次 Crossref 核验发现作者列表仍存在 3 处 HIGH 级错误。

## V1 到最终链不回退
| 版本 | 总分 | 关键变化 | 回退检查 |
|---|---|---|---|
| V1 | 10/12 | 初始候选 | — |
| V2 | 11/12 | 主方向收紧为 TPV；效率记录修正；SQ 精确化 | 无回退 |
| V3 | 12/12 | Yang DOI 修正；LONGi HIBC；NLR 更名状态；PbTe S8 补来源；executed 收缩 | 无回退 |
| V4 | 11/12 | 格式标准化（frontmatter 迁移）；artifact 标识；终态移除 | 文献证据从 2→1（frontmatter 元数据回归） |
| V5 | 11/12 | 修复 S3/S5/S8 标题/首作者 | 文献证据从 1→2（标题/首作者修复），表达与追溯从 2→1（正文标题未更新） |
| V6 | 10/12 | 修复正文标题 V4→V6 | **文献证据从 2→0**（Crossref 深度核验发现伪造作者、完全错引），表达与追溯从 1→2（标题修复） |
- V5→V6 分数下降（11→10）因 Crossref 深度核验暴露了前序 review 未检出的 HIGH 级元数据错误。科学内容保持 V3 水平，但 frontmatter 作者列表含伪造数据。

## Project terminal recommendation
按 readme.md L74-81 终态表逐项裁决：
1. `waiting_human`：不需要领域裁决、受限数据或伦理决定。**未命中。**
2. `failed`：模型/传输/Tool 产物可用，科学内容有效。**未命中。**
3. `completed`：最终版通过 rubric（10/12 ≥ 10/12）、无 0 分 **未通过**（文献证据 0 分）、关键引用抽查未通过（3/8 HIGH 级错误）、含伪造作者名（B. Bhatia、Jing-Feng Li）、S5 完全错引。**未命中。**

**推荐 run.md 终态保持 `completed` 但 final 不指向 v6.md**。v6.md 含 3 处 HIGH 级元数据错误（伪造作者、完全错引），需修复后方可作为 final。

## 交付门槛核对
| 门槛 | 结果 |
|---|---|
| 总分 ≥10/12 | 通过（10/12） |
| 无 0 分 | **未通过**（文献证据 0 分） |
| 关键引用抽查通过 | **未通过**（3/8 HIGH 级错误：S3/S5/S8 作者列表不匹配） |
| 无伪造执行结果 | 通过（无伪造执行） |
| 无伪造元数据 | **未通过**（S3 伪造作者 B. Bhatia、S8 伪造作者 Jing-Feng Li、S5 完全错引） |
| 独立 reviewer 判定可交付 | **未通过**（3 处 HIGH 级错误需修复） |

## 修复建议
1. **S3**：将 authors 从 "A. LaPotin, K. Schulte, B. Bhatia, E. N. Wang, A. Henry" 改为完整 13 人列表或至少删除伪造的 B. Bhatia 并补充遗漏作者。
2. **S5**：将 authors 从 "Yang, Y., Zhang, H., Zhu, Y., Lee, D.-Y., Park, H., Kim, Y.-S., and Lin, L." 改为 "Zhengbao Yang, Shengxi Zhou, Jean Zu, Daniel Inman"；将 title 从 "...and Their Device Applications" 改为 "...and Their Applications"。
3. **S8**：将 authors 从 "Gang Tan, Li-Dong Zhao, Fengyuan Shi, Jing-Feng Li, Vinayak P. Dravid, and Mercouri G. Kanatzidis" 改为完整 10 人列表或至少删除伪造的 Jing-Feng Li、修正 Gang→Ganglian、补充遗漏作者。

RESULT: REVISE
