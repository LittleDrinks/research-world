---
project: q112
artifact: review-v11
role: independent-review
reviewer_session: "01a05fd9-12a1-7b82-ad8a-bc9edf75719a"
author_session: "01a05fd4-8bfe-73a6-ad0e-bc072b7f3871"
reviewed: v9.md
verdict: deliverable
sources:
  - id: A1
    type: local-artifact
    path: research-world/evidence/contest-2026/q112/v8.md
  - id: A2
    type: local-artifact
    path: research-world/evidence/contest-2026/q112/v9.md
  - id: A3
    type: local-review
    path: research-world/evidence/contest-2026/q112/review-v10.md
  - id: A4
    type: local-run-record
    path: research-world/evidence/contest-2026/q112/run.md
  - id: A5
    type: original-question
    path: research-world/projects/q112/project.json
  - id: E1
    type: doi-registration-metadata
    url: https://doi.org/10.1016/j.resconrec.2024.107787
    result: matched
  - id: E2
    type: doi-registration-metadata
    url: https://doi.org/10.1126/sciadv.1700782
    result: matched
  - id: E3
    type: doi-registration-metadata
    url: https://doi.org/10.1016/j.spc.2022.06.005
    result: matched
  - id: E4
    type: publisher-landing-page
    url: https://www.sciencedirect.com/science/article/doi/10.1016/j.resconrec.2024.107787
    result: inaccessible-403
  - id: E5
    type: publisher-landing-page
    url: https://www.science.org/doi/10.1126/sciadv.1700782
    result: inaccessible-403
  - id: E6
    type: publisher-landing-page
    url: https://www.sciencedirect.com/science/article/doi/10.1016/j.spc.2022.06.005
    result: inaccessible-403
  - id: E7
    type: standard-link-under-review
    url: https://www.cen.eu/work/products/CENStandards/Pages/default.aspx
    result: generic-cen-page
---
# q112 独立核验
## 六维评分
| 维度 | 分数 | 核验依据 |
|---|---:|---|
| 问题理解 | 2/2 | 原题的宽泛替代诉求被收束为 1,000 次 750 mL、0–40°C、非加压冷食外带容器服务；碳酸饮料因压力与 CO₂ 阻隔差异排除，避免把不可替代应用混入比较。 |
| 文献证据 | 2/2 | S5、S8、S9 的 DOI 登记元数据分别匹配题名、作者、期刊、年份、卷页或文章号；S1–S9 均保留可追溯标识，微塑料只作为未并入汇总 LCIA 的证据缺口。 |
| Direction 质量 | 2/2 | rPET 机械回收、PLA/PHA 工业堆肥与 PP 回收、洗涤、复用构成材料与基础设施不同的三条可比路线；三者均以性能门与当地 C_min 为前提，而非预设胜者。 |
| 科学推理 | 2/2 | `N_eff`、`R=P/N_eff+W+T+rL` 与仅在 `S-W-T-rL>0` 时成立的 `n` 保持一致；单位、影响类别、损失处理和不确定性判断没有数值或方向漂移。 |
| 研究计划 | 2/2 | LCI 参数、实验室门、基础设施映射、500 件/3 点/12 周试点、数据质量失败门与条件决策规则覆盖数据、方法、比较、资源与风险。 |
| 表达与追溯 | 2/2 | planned 与 executed 明确分离：LCA、实验、试点和比较均未执行；`waiting_human` 由运行记录保有，`deliverable` 仅裁定候选研究计划的交付，不覆盖后续实证终态。 |
| **总分** | **12/12** | **无 0 分项。** |
## 机械对照
`v8.md` 到 `v9.md` 的原始差异仅含 `artifact` 与 `supersedes` 元数据更新、将含 V3 指涉的标题改为中性标题，以及删除 V7→V8 变更日志和候选标记。将这两项元数据和标题归一化并排除被删变更日志后，剩余内容逐字节一致；问题定义、三条路线、方法、公式、阈值、失败门、条件决策、数值和 planned/executed 声明均无科学漂移。
## 来源与残余风险
DOI 登记元数据确认 S5 为 *Resources, Conservation and Recycling* 209:107787（2024）、S8 为 *Science Advances* 3(7):e1700782（2017）、S9 为 *Sustainable Production and Consumption* 32:817–832（2022）。三家出版方落地页在本运行环境返回 403；这是访问限制，不等同于来源失效。S2 的 EN 13432 链接是通用 CEN 页面，不是直接标准页；不得将其表述为对标准正文、55–60°C 条件或 180 天/90%阈值的直接核验。
## 结论
候选稿满足六维交付门槛，且机械对照确认自指清理未改变科学主张；后续仍须以实际测量、当地设施数据、LCA 执行和利益相关方批准取得实证结论。
RESULT: DELIVERABLE
