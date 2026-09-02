---
project: q112
artifact: review-v9
role: independent-review
reviewer_session: "01a05f71-6072-7353-82ff-497b3534eeca"
reviewed: v7.md
supersedes: review-v8.md
prior_review: review-v8.md
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
# q112 v7 独立核验

## 六维评分

| 维度 | 分数 | 核验依据 |
|---|---:|---|
| 问题理解 | 2/2 | 功能单位固定为 1,000 次 750 mL、0–40°C、非加压冷食外带容器服务；碳酸饮料因压力和 CO₂ 阻隔要求被排除；三种系统的功能等价性均待性能门验证。 |
| 文献证据 | 2/2 | S1–S9 的书目信息、法规或报告标识及其限定用途均可回读；微塑料仅作为尚未并入汇总 LCIA 的证据缺口处理。 |
| Direction 质量 | 2/2 | rPET 机械回收、PLA/PHA 工业堆肥、PP 回收-洗涤-再用分别对应材料与基础设施不同的三条路线，均以性能门和当地条件比较。 |
| 科学推理 | 2/2 | `N_eff`、`R` 与 `n` 明确生产、洗涤、服务运输和回收运输负担；损失只经 `r` 进入模型，break-even 仅在分母为正时成立，并逐影响类别及不确定性抽样判定。 |
| 研究计划 | 2/2 | LCI 参数、实验室性能测试、基础设施映射、运营试点、数据质量要求、失败门和决策规则完整覆盖数据、方法、对照、判断、产物、资源与风险。 |
| 表达与追溯 | 2/2 | 问题、证据、三路线、条件取舍与 LCA 计划形成单一主线；来源编号和 v6→v7 版本关系可回读。 |
| **总分** | **12/12** | **无 0 分项。** |

## S1–S9 来源核验

| ID | 核验结果 | 关键对应关系 |
|---|---|---|
| S1 | pass | 2011 年欧盟塑料食品接触材料法规与迁移合规用途相符。 |
| S2 | pass | EN 13432:2000 的名称、年份及工业堆肥下 90% 生物降解/180 天条件与引用用途相符。 |
| S3 | pass | Eurostat 记录的 2023 年人均 35.3 kg 塑料包装废弃物及 42.1% 回收率相符。 |
| S4 | pass | RIVM Report 2016-0104 的题名、2016 年份、作者群及 ReCiPe 2016 影响评价用途相符。 |
| S5 | pass | DOI、2024 年份、期刊第 209 卷和文章号 107787 相符；PP、LDPE 与 PET 的水生微塑料表征因子用于 ReCiPe 2016 的限定性表述相符。 |
| S6 | pass | 2022/1616 的法规身份及再生塑料食品接触材料适用范围相符。 |
| S7 | pass | Lobel 与 Grzych 的 2023 年资料明确给出 80% 回收率对应平均 5 次、90% 对应平均 10 次使用的情景关系。 |
| S8 | pass | DOI 对应 PMID 28776036 与 PMCID PMC5517107；8,300 Mt 总产量、约 6,300 Mt 废弃物和其中约 9% 回收的分母一致。 |
| S9 | pass | DOI、四位作者、2022 年、期刊第 32 卷与 817–832 页的系统综述记录相符。 |

**来源抽查：9/9 通过。**

## 功能单位、路线与 LCA 计划

| 检查项 | 结论 |
|---|---|
| 功能单位 | 相同容积、温度范围、食品场景与性能要求使三种容器系统具有可检验的服务比较基础，而非预设材料等价。 |
| 三路线 | 路线 1 依赖 rPET 回收，路线 2 依赖工业堆肥，路线 3 依赖回收、洗涤和再配送；基础设施不足或性能失败时对应路线不可行。 |
| break-even | `N_eff=(1-r^D)/(1-r)`（`r=1` 时为 `D`），`R=P/N_eff+W+T+rL`，且仅在 `S-W-T-rL>0` 时计算最小循环数 `n`；环境优势须满足测得的 `N_eff≥n`。 |
| LCA 计划 | 摇篮到坟墓边界、LCI 数据层级、ReCiPe 2016 中点法、按影响类别的比较、独立微塑料证据缺口和不确定性处理均已界定。 |
| planned/executed | LCA 计算、性能测试、试点部署和比较分析均为 planned；未出现伪称已执行的结果、数据或推荐。 |

## 判定

`deliverable` 仅表示 `v7.md` 已达到候选稿交付门槛，不涉及 Project `status`。实验室测试、运营试点、当地基础设施数据、LCA 实算及利益相关方对设计参数的批准仍是后续执行条件。
RESULT: DELIVERABLE
