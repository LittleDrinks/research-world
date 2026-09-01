---
project: q049
role: receipt
artifact: receipt-baseline-matched-v9
date: 2026-09-02
auditor_session: 01a05f1f-d312-7c60-a8b8-ceaf0d54e2a6
auditor_session_provenance: user-confirmed running Codex UUIDv7
author_session: 01a05f12-6e5d-7931-a8cb-585b1cc893ce
reviewer_session: 01a05f18-d17a-7910-ac13-60791233da3d
reviewed: [baseline-matched-v9.md, review-baseline-matched-v10.md]
sources:
  - baseline-matched-v9.md
  - review-baseline-matched-v10.md
  - https://doi.org/10.1103/PhysRev.136.B1224
  - https://doi.org/10.1038/nature08096
  - https://doi.org/10.1111/j.1365-2966.2008.13022.x
  - https://doi.org/10.1051/0004-6361/201425300
verdict: deliverable
---
# q049 Baseline Matched V9 Receipt
## 审计范围
仅核验 `baseline-matched-v9.md` 与 `review-baseline-matched-v10.md`。本 receipt 确认 Artifact/review，不裁决 Project terminal。
## 输入、公式与输出
- I1 的范围正确限于共享常量及 Earth-Sun 输入；I2 明确将 `M_mercury=3.3011e23 kg`、`a_mercury=5.7909e10 m` 归为从 `review-baseline-matched-v9.md` 采用的输入。
- 对两组输入独立代入 `t=(5/256)(c^5/G^3)(a^4/(m1*m2*(m1+m2)))`；量纲归约为秒。
- Earth-Sun 复算为 `3.374197216379e30 s = 1.069218576945e23 yr`；Mercury-Sun 复算为 `1.370536799260e30 s = 4.342969044731e22 yr`，均与 V9 一致。
- 条件质量损失复算 `(1e-14)(5e9)=5e-5`，绝热 `Delta a/a` 为 `+0.005000%`，与 V9 一致。
## 来源
| 来源 | 核验结论 |
|---|---|
| S1, Peters 1964 | DOI、题名与双点质量轨道衰减适用范围一致。 |
| S2, Laskar and Gastineau 2009 | 原始 Nature 记录支持 `2,501` 次、`5 Gyr`、`1%` 的多体水星偏心率结果。 |
| S3, Schroder and Connon Smith 2008 | 记录支持 `7.59 Gyr`、巨星阶段质量损失与轨道随剩余太阳质量反比扩张。 |
| S4, Johnstone et al. 2015 | 出版商记录支持 `1.4e-14 M_sun/yr`；V9 将 `1e-14` 限为条件性圆整输入。 |
## Review 与角色边界
- `review-baseline-matched-v10.md` 的 frontmatter `verdict: deliverable` 与末行 `RESULT: DELIVERABLE` 一致。
- V9 保持 `benchmark_candidate` 与 `RESULT: CANDIDATE`；V10 的 `DELIVERABLE` 仅确认该 Artifact 的审查通过。
- 两文件均不替换或重新冻结 matched-v6 对照；本 receipt 不作 Project terminal 判定。
## 绑定指纹
| 文件 | SHA-256 |
|---|---|
| `baseline-matched-v9.md` | `6d017687fa1c716c9f56ae6162b3ad3c4299a54ac9cc40353a31e3604e7e6fa1` |
| `review-baseline-matched-v10.md` | `4e93a995cb39062e16d8b5a6ef3a605fd28785d7c2280c38aa6ae3c20e90bcf4` |
## 结论
输入来源边界、Peters 公式及数值输出、四项来源绑定、review RESULT 与角色边界均通过核验。
RESULT: DELIVERABLE
