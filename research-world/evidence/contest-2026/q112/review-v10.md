---
project: q112
artifact: review-v10
role: independent-review
reviewer_session: "01a05fa3-b7b7-7c82-a49c-50fb43406ffe"
reviewed: v8.md
supersedes: review-v9.md
prior_review: review-v9.md
verdict: deliverable
sources:
  - id: S1
    title: "Commission Regulation (EU) No 10/2011 on plastic materials and articles intended to come into contact with food"
    authors: ["European Commission"]
    year: 2011
    url: "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32011R0010"
  - id: S2
    title: "EN 13432:2000 Packaging – Requirements for packaging recoverable through composting and biodegradation"
    authors: ["CEN"]
    year: 2000
    url: "https://www.cen.eu/work/products/CENStandards/Pages/default.aspx"
  - id: S3
    title: "Plastic packaging waste in the EU: 35.3 kg per person"
    authors: ["Eurostat"]
    year: 2025
    url: "https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20251022-1"
  - id: S4
    title: "ReCiPe 2016: A harmonized life cycle impact assessment method at midpoint and endpoint level. Report I: Characterization"
    authors: ["Huijbregts, M. A. J.", "et al."]
    year: 2016
    url: "https://www.rivm.nl/bibliotheek/rapporten/2016-0104.html"
  - id: S5
    title: "Microplastic aquatic impacts included in Life Cycle Assessment"
    authors: ["Schwarz, A. E.", "et al."]
    year: 2024
    doi: "10.1016/j.resconrec.2024.107787"
    journal: "Resources, Conservation and Recycling"
    volume: 209
    pages: "107787"
  - id: S6
    title: "Commission Regulation (EU) 2022/1616 on recycled plastic materials and articles intended to come into contact with foods"
    authors: ["European Commission"]
    year: 2022
    url: "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R1616"
  - id: S7
    title: "Debunking Durability: How Durable Does Reusable Packaging Need to Be?"
    authors: ["Lobel, C.", "Grzych, C."]
    year: 2023
    url: "https://www.closedlooppartners.com/debunking-durability-how-durable-does-reusable-packaging-need-to-be"
  - id: S8
    title: "Production, use, and fate of all plastics ever made"
    authors: ["Geyer, R.", "Jambeck, J. R.", "Law, K. L."]
    year: 2017
    doi: "10.1126/sciadv.1700782"
    journal: "Science Advances"
    volume: 3
    issue: 7
    pages: "e1700782"
  - id: S9
    title: "Packaging design for the circular economy: a systematic review"
    authors: ["Zhu, Z.", "Liu, W.", "Ye, S.", "Batista, L."]
    year: 2022
    doi: "10.1016/j.spc.2022.06.005"
    journal: "Sustainable Production and Consumption"
    volume: 32
    pages: "817–832"
verified: 2026-09-02
---
# q112 v8 核验
## 六维评分
| 维度 | 分数 | 核验依据 |
|---|---:|---|
| 问题理解 | 2/2 | 功能单位固定为 1,000 次 750 mL、0–40°C、非加压冷食外带容器服务；碳酸饮料因压力和 CO₂ 阻隔要求被排除；三种系统的功能等价性均待性能门验证。 |
| 文献证据 | 2/2 | S1–S9 的法规、标准、统计、报告、论文与行业资料标识可回读；微塑料仅作为未并入汇总 LCIA 的证据缺口。 |
| Direction 质量 | 2/2 | rPET 机械回收、PLA/PHA 工业堆肥、PP 回收-洗涤-再用构成材料与基础设施不同的三条路线，均受性能门和当地条件约束。 |
| 科学推理 | 2/2 | `N_eff`、`R` 与 `n` 分别处理生产、洗涤、服务运输和回收运输；损失仅经 `r` 计入，break-even 仅在分母为正时成立，并逐影响类别及不确定性抽样判断。 |
| 研究计划 | 2/2 | LCI 参数、实验室性能测试、基础设施映射、运营试点、数据质量要求、失败门和条件决策规则覆盖数据、方法、对照、判断、产物、资源与风险。 |
| 表达与追溯 | 2/2 | 功能单位、来源、三路线、条件取舍与 LCA 计划保持单一主线；来源编号、版本链和候选标记可回读。 |
| **总分** | **12/12** | **无 0 分项。** |
## 来源
| ID | 核验结果 | 关键对应关系 |
|---|---|---|
| S1 | pass | EUR-Lex 的 10/2011 记录对应塑料食品接触材料与迁移合规用途。 |
| S2 | pass | EN 13432:2000 的题名、年份及堆肥与生物降解评价用途相符。 |
| S3 | pass | Eurostat 条目对应 2023 年欧盟人均 35.3 kg 塑料包装废弃物和 42.1% 回收率。 |
| S4 | pass | RIVM 2016-0104 对应 Huijbregts 等人的 ReCiPe 2016 Characterization 报告。 |
| S5 | pass | DOI、2024 年份、Resources, Conservation and Recycling 第 209 卷与文章号 107787 相符；用途限于水生微塑料 LCIA 证据缺口。 |
| S6 | pass | EUR-Lex 的 2022/1616 记录对应再生塑料食品接触材料。 |
| S7 | pass | Lobel 与 Grzych 的情景关系为 80% 回收率对应平均 5 次使用、90% 对应平均 10 次使用。 |
| S8 | pass | DOI 对应 PMID 28776036 与 PMCID PMC5517107；8,300 Mt 总产量、约 6,300 Mt 废弃物与约 9% 回收的分母一致。 |
| S9 | pass | DOI、四位作者、2022 年、Sustainable Production and Consumption 第 32 卷与 817–832 页相符。 |
**S1–S9：9/9 通过。**
## 版本差异
| 项目 | v7.md → v8.md |
|---|---|
| 元数据 | `artifact` 更新为 v8，`supersedes` 更新为 v7.md。 |
| 排版与指涉 | 空白行全部删除；未出现指向文本载体的自我指涉。 |
| 科学内容 | 非空科学行逐一对应，问题定义、三路线、方法、公式、阈值、失败门、条件决策与定量条件均无漂移。 |
| 执行声明 | planned/executed 边界、证据缺口和后续物理执行条件不变。 |
## 路线、LCA 与执行边界
| 检查项 | 结论 |
|---|---|
| 三路线 | 路线 1 为 rPET 回收，路线 2 为 PLA/PHA 工业堆肥，路线 3 为 PP 回收、洗涤和再配送；性能失败或基础设施低于 C_min 时对应路线不可行。 |
| LCA | 摇篮到坟墓边界、LCI 数据层级、ReCiPe 2016 中点法、逐影响类别比较、独立微塑料证据缺口和不确定性处理均已界定。 |
| break-even | `N_eff=(1-r^D)/(1-r)`，`r=1` 时为 `D`；`R=P/N_eff+W+T+rL`；仅在 `S-W-T-rL>0` 时计算 `n`，环境优势要求测得 `N_eff≥n`。 |
| planned/executed | LCA 计算、实验室测试、试点部署和比较分析均为 planned；没有作为 executed 证据的结果、数据或推荐。 |
| 交付边界 | `deliverable` 仅表示 v8.md 符合候选稿交付门槛；不对 Project terminal 作出判定。 |
RESULT: DELIVERABLE
