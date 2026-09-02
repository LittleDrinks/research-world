---
project: q049
artifact: receipt-v4
role: independent-audit
auditor_session: current
audited: v4.md, review-v4.md, run.md, deep-cases.md
issue: 249
no_go_commit: 8b5791eaa20a6a98e9186533d870e0b82531f557
no_go_finding: "q049 citation denominator is inconsistent (6/6 vs 5/5)"
---
# q049 V4 独立审计回执
## 读取范围
根 `AGENTS.md`（项目编码/文档规范）、`research-world/README.md`（控制面说明）、`research-world/projects/q049/project.json`、`v4.md`、`review-v4.md`、`run.md`、`deep-cases.md`、issue #249 最近三条 comment（最新 NO-GO commit `8b5791e`）。未修改任何文件，未 commit/push。
## 一、来源条数逐条确认
v4.md frontmatter YAML `sources:` 块包含：
| ID | 作者 | 年份 | DOI |
|---|---|---|---|
| S1 | Batygin & Laughlin | 2008 | 10.1086/589232 |
| S2 | Laskar | 1989 | 10.1038/338237a0 |
| S3 | Rasio et al. | 1996 | 10.1086/177941 |
| S4 | Peters & Mathews | 1963 | 10.1103/PhysRev.131.435 |
| S5 | Peters | 1964 | 10.1103/PhysRev.136.B1224 |
| S6 | Laskar & Gastineau | 2009 | 10.1038/nature08096 |
`grep -c "id: S" v4.md` = **6**。v4 正文 §3 实际来源记录逐条列出 S1-S6，§4-§5 引用均使用 S1-S6 ID。**v4 实际有 6 条来源，确认无误。**
## 二、review-v4 的 6/6 是否为正确分母
review-v4.md 内部：
- §一 总分行："关键引用 **6/6** 通过"（line 70）
- §二 来源抽查表末尾："关键来源抽查通过率：**6/6** = 100%"（line 83）
- §二 S1/S6 分离核验段落明确说明"分母 = v4 全部 6 条来源"（line 58 frontmatter `sources_verified` 列出 6 条）
review-v4 的 6/6 以 v4 的 6 条来源为分母，**分母正确**。
## 三、run.md / deep-cases 旧 5/5 需 owner 修正
| 位置 | 当前文本 | 正确值 | 判定 |
|---|---|---|---|
| run.md line 39（review-v4 行） | "来源 5/5" | 6/6 | **错误** |
| run.md line 55（同条件对照末句） | "引用从 2/5 提升到 5/5" | 2/5 → 6/6 | **错误** |
| deep-cases.md line 4（q049 行 列） | "5/5" | 6/6 | **错误** |
| deep-cases.md line 10（同条件对照） | "最终版 5/5" | 6/6 | **错误** |
v3 有 5 条来源（无 S6），review-v3 的 5/5 正确。v4 新增 S6 后来源变为 6 条，但 run.md 两处和 deep-cases.md 两处仍写 5/5。**这 4 处需由 owner 修正为 6/6。** 此错误为转录/聚合层面，不影响 v4 或 review-v4 内部一致性。
## 四、文件哈希复算
| 文件 | 本 Session `sha256sum` | run.md 记录 | 匹配 |
|---|---|---|---|
| `v4.md` | `fe013717797c44cc1dd401982ed1f0f8e22311a3b2661f3b489f9389981c54eb` | `fe013717…` | ✓ |
| `review-v4.md` | `b61a0ffea0e40ca93bce9371eba4b71e5656e1bbfa5dfb9d8c871dcfdbe05068` | `b61a0ffe…` | ✓ |
**两个文件哈希与 run.md 文件哈希表完全一致。**
## 五、12/12 复算
review-v4 §一 六维评分表：
| 维度 | 分 |
|---|---|
| 问题理解 | 2 |
| 文献证据 | 2 |
| Direction 质量 | 2 |
| 科学推理 | 2 |
| 研究计划 | 2 |
| 表达与追溯 | 2 |
| **合计** | **12/12** |
6 × 2 = 12，无 0 分维度。**12/12 算术正确。**
## 六、Peters 数值确认
v4 §7 公布的计算结果：
- 功率 P = **196.291 W**
- Inspiral 时间 t = 3.374×10³⁰ s = **1.069×10²³ years**
- 输出 SHA-256 = `7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361`
review-v4 §三 独立复算：
- P = 196.291 W ✓（逐位吻合）
- t = 3.374×10³⁰ s = 1.069×10²³ years ✓（逐位吻合）
- 内部一致性 t = (1/4)·E_orb/P 比值 1.000000 ✓
- 输出哈希重算匹配 ✓
**Peters 数值经 review-v4 独立复算逐位确认，本审计确认两侧数值与哈希一致。**
## 七、Laskar/Gastineau 概率归因确认
| 断言 | v4 归因 | review-v4 核验 | 判定 |
|---|---|---|---|
| ~1% 水星不稳定概率（25/2501） | S6 (Laskar & Gastineau 2009) | Nature 459:817-819 abstract 确认 "set of 2,501 orbits"、"one per cent" | ✓ 正确 |
| 确定性水星坠日 ~1.261 Gyr | S1 (Batygin & Laughlin 2008) | arXiv:0804.1946 abstract 确认 "Mercury falls onto the Sun at ~1.261Gyr"；未报告概率 | ✓ 正确 |
v4 §4 D3 和 §5 明确分离：S1 用于混沌存在性（确定性实验），S6 用于概率统计（2501 轨道蒙特卡洛）。**归因正确，无错引。**
## 八、NO-GO 发现处置
issue #249 最新 NO-GO（commit `8b5791e`，2026-09-01T20:41:19Z）：
> "q049 citation denominator is inconsistent (6/6 vs 5/5)"
**确认**：不一致存在于 run.md（line 39、line 55）和 deep-cases.md（line 4、line 10），均为 5/5。v4 和 review-v4 内部一致使用 6/6，**无内部不一致**。修复范围为 run.md 和 deep-cases.md 共 4 处转录，不涉及 v4 或 review-v4 内容变更。
## 九、审计结论
| 检查项 | 结果 |
|---|---|
| v4 frontmatter S1-S6 六条来源 | ✓ 确认 |
| v4 正文引用 S1-S6 | ✓ 确认 |
| review-v4 分母 6/6 | ✓ 正确 |
| run.md/deep-cases 旧 5/5 | ✗ 4 处需 owner 修正 |
| v4 SHA-256 | ✓ 与 run.md 一致 |
| review-v4 SHA-256 | ✓ 与 run.md 一致 |
| 12/12 算术 | ✓ 正确 |
| Peters P=196.291 W / t=1.069e+23 yr | ✓ 双侧一致 |
| Laskar/Gastineau ~1% 归因 S6 | ✓ 正确 |
| S1/S6 分离 | ✓ 正确 |
| planned/executed 边界 | ✓ §6 planned、§7 唯一 executed |
v4 deliverable 本身通过审计。run.md 和 deep-cases.md 中 4 处 5/5→6/6 转录修正由 owner 执行，不影响 v4 或 review-v4 科学内容与评分。本回执不裁决 Project terminal。
RESULT: DELIVERABLE
