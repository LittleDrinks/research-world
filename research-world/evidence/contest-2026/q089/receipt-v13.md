---
project: q089
artifact: receipt-v13
role: independent-audit
auditor_session: "01a05ff0-9b18-78e3-9876-b5fa3cec1a11"
author_session: "01a05fe5-4488-7240-af78-40caadd1eadb"
reviewer_session: "01a05fe9-e149-7ec3-abde-b5d8ff3a8ca4"
reviewed:
  - research-world/evidence/contest-2026/q089/v10.md
  - research-world/evidence/contest-2026/q089/v9.md
  - research-world/evidence/contest-2026/q089/review-v13.md
  - research-world/evidence/contest-2026/q089/review-v12.md
  - research-world/evidence/contest-2026/q089/run.md
  - docs/questions.json#id=89
verdict: revise
sources:
  - role: original-question
    path: docs/questions.json
    selector: id=89
  - role: reviewed-candidate
    path: research-world/evidence/contest-2026/q089/v10.md
  - role: prior-candidate
    path: research-world/evidence/contest-2026/q089/v9.md
  - role: current-independent-review
    path: research-world/evidence/contest-2026/q089/review-v13.md
  - role: prior-independent-review
    path: research-world/evidence/contest-2026/q089/review-v12.md
  - role: run-record
    path: research-world/evidence/contest-2026/q089/run.md
  - role: primary-tpv
    url: https://www.nature.com/articles/s41586-022-04473-y
  - role: official-s9-publisher
    organization: LONGi
    url: https://www.longi.com/en/news/isfh-hibc-conversion-efficiency/
  - role: primary-s9-certification
    organization: ISFH
    availability: inaccessible
---
# q089 独立审计
## 裁决
`REVISE`。`review-v13.md` 的来源 2/2 与合计 12/12 不能维持：S9 的精确页面日期与可访问的 LONGi 官方页面不符。沿用其余五维分数时，来源为 1/2、合计为 11/12；更正日期并补清证书证据边界后方可重新计分。
## S9 与 ISFH
- LONGi 官方页面标题、HIBC、27.81% 和“经 ISFH 认证”的发布方主张可访问；页面显示日期为 `2025.4.14`，正文称 LONGi 于 2025 年 4 月 11 日宣布。
- `v10.md` 的 S9 元数据写作 `2025-04-13`，`review-v13.md` 同样将该日期作为精确来源依据；两者均未得到该页面支持。
- LONGi 发布页不是 ISFH 原始证书。ISFH 原件不可访问，无法独立核验证书编号、受测样品、测试条件、方法或认证范围；此项保留为 residual risk。
## TPV 基线
- `v10.md` 已将 planned 基线写明为 2400°C 黑体、平行平面单位面积、device-level view factor=1、1.4/1.2 eV tandem、`R_sub=95%` 与 `0/50/80/90/95/98%` sweep、`eta=P_elec/(Q_inc-Q_ref)`、Python 3.12、NumPy/SciPy、输入 JSON、CSV 和能量收支误差 `<0.1%`；system-level view factor 另扫 `0.3/0.5/0.7/1.0`，不与器件效率混用。
- Nature S3 支持 1.4/1.2 eV 串联器件、1,900–2,400°C 工作区间、2,400°C 下 41.1%+/-1% 和亚带隙反射率机制；`v10.md` 仅将该实验值作为外部对照。
## 执行与终态
- R_sub 消融、曲线和系统外推均为 planned；`run.md` 也明确无新的仿真、实验、数值输出或执行凭据，未把计划描述为 executed。
- `run.md` 的终态选择仍为 `v8.md`、`review-v11.md` 与 `receipt-v12.md`，并保留终态裁决所有权；`review-v13.md` 的 verdict 不能将 `v10.md` 升格为终态。
## 完整性
- `v10.md` SHA-256: `7e14d6c16cf0480c388503a989baf20dcf89443bb3fe92baa29672b5518bcf44`
- `review-v13.md` SHA-256: `1c21997d0ac54762dac399d7af4dba61c15d1fb757f538892dbc176703dd94eb`
RESULT: REVISE
