---
project: q112
role: independent-review
reviewed: v5.md
prior: v4.md
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
    year: 2017
    url: "https://www.rivm.nl/en/life-cycle-assessment-lca"
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
# 文件结构核验
`wc -l v5.md` = 256；`rg -n '^---$|^# |^REVISION_RESULT'` 返回 line 1/63（frontmatter）、line 65（唯一 H1）、line 257（EOF，末行无换行）。单一 YAML frontmatter、单一正文、单一 REVISION_RESULT 标记。无重复正文。
# Findings
## Low
### F1 — Geyer 产量数据表述精度
候选写"8,300 Mt produced through 2015, with only 9% recycled"。Geyer 原文为 8300 Mt 总产量、6300 Mt 废弃物产生量中 9% 被回收。候选表述是政策文献常用简写，不构成科学错误，但精确引用时应注明 9% 对应的是废弃物子集。
# Rubric
| 维度 | 分 | 依据 |
|---|---|---|
| 问题理解 | 2 | 功能单位（1,000 次 750 mL 冷食容器服务）精确，排除碳酸饮料有技术理由，三系统等价性标为待验证 |
| 文献证据 | 2 | 9 个来源全部通过独立核验（见抽查表），微塑料作为证据缺口显式保留 |
| Direction 质量 | 2 | rPET/PLA-PHA/PP-reuse 三条路线在终端机制层面不同，决策条件化于基础设施阈值 |
| 科学推理 | 2 | 所有结论条件化，break-even 模型量纲正确，无超证据强度断言 |
| 研究计划 | 2 | LCI 参数表、性能测试 pass/fail 标准、pilot 设计、go/no-go 门均具体可执行 |
| 表达与追溯 | 2 | 单一 frontmatter + 单一正文 + 单一 REVISION_RESULT，V4→V5 Changes 段明确列出零科学变更，来源 ID 与版本可回读 |
**总分 12/12**，无 0 分项。
# 来源抽查
分母 9，通过 9，通过率 100%。
| ID | 核验动作 | 工具 | 结果 | 作用/局限 |
|---|---|---|---|---|
| S1 | EUR-Lex CELEX 确认 | tavily | pass | 食品接触合规基准；不覆盖再生塑料专项 |
| S2 | CEN 标准文本与认证机构交叉验证 | tavily | pass | 55–60°C、90%/180 d 生物降解已确认；仅限工业堆肥 |
| S3 | Eurostat ddn-20251022-1 原文直读 | tavily | pass | 42.1% (2023) 已确认；数据年份 2023 非发布年份 2025 |
| S4 | Springer IJLCA 22(2) 与 Earthster 单位表交叉 | tavily | pass | kg CO₂-eq / kg oil-eq / kg 1,4-DCB-eq / m³ / m²·year 全部匹配 |
| S5 | ScienceDirect 文章页与 ResearchGate 确认 | tavily | pass | DOI、期刊、卷号、文章号一致；微塑料 CF 为初步性质 |
| S6 | EUR-Lex ELI 与 TUV SUD 摘要交叉 | tavily | pass | 正确替代 EC 282/2008；OJ L 243 页码 3–46 |
| S7 | Closed Loop Partners 出版商页面直读 | anysearch + tavily | pass | 80%→5 次、90%→10 次已逐字确认；行业报告非同行评审 |
| S8 | Science Advances 出版商页面 + PubMed 三方交叉 | anysearch + tavily | pass | 8300 Mt、9% 回收已确认；DOI 10.1126/sciadv.1700782 有效 |
| S9 | Aston Research Explorer / ScienceDirect 确认 | tavily | pass | 作者 Zhu/Liu/Ye/Batista、DOI .005、Vol 32 pp 817–832 全部匹配 |
# LCA 单位核验
ReCiPe 2016 midpoint 六项影响类别单位逐一对照 Earthster 与 Springer 原文：
| 候选声明 | 核验结果 |
|---|---|
| kg CO₂-eq (climate change) | pass |
| kg oil-eq (fossil resource scarcity) | pass |
| kg 1,4-DCB-eq (freshwater ecotoxicity) | pass |
| kg 1,4-DCB-eq (human toxicity) | pass |
| m³ (water consumption) | pass |
| m²·year (land use) | pass |
# Return-rate 阈值与 Decision Rule 核验
- 80% return → 5 average uses：Closed Loop Partners 原文逐字确认 "For containers to have five uses on average in their lifetime, return rates need to be 80%"。pass。
- 90% return → 10 average uses：原文 "For a 90% return rate…containers are used only 10 times on average"。pass。
- 候选将上述阈值标为 "predeclared design assumptions requiring explicit approval"，未冒充文献事实。pass。
- Decision rule 三步（performance gates → infrastructure C_min → uncertainty-aware LCA）逻辑自洽，无 route 被无条件推荐。pass。
# N_eff 模型量纲与方向性
- N_eff = (1−r^D)/(1−r) 为标准几何级数求和，量纲为"次数"。正确。
- R = P/N_eff + W + T + rL：P 为生产负担（一次性），除以 N_eff 摊销；W/T 为每周期负担；rL 为返回运输按概率加权。量纲一致。
- break-even n = ⌈P/(S−W−T−rL)⌉ 仅在 S−W−T−rL > 0 时有意义。正确。
- Loss 通过 r 表达，不双重计数。正确。
# 伪造执行检查
候选显式声明 "This document represents a comprehensive research plan only. No LCA calculations, laboratory tests, pilot deployments, or comparative analyses have been executed." 全文无伪造实验结果、无模拟数据填充 planned 项。pass。
# V1→最终链完整性
| 版本 | 关键变化 | 回退 |
|---|---|---|
| v1 | 初始候选；材料不等价、虚构 DOI | — |
| v2 | 改为冷食容器功能单位 | 无 |
| v3 | 修复 break-even 主体与来源 | 无 |
| v4 | 修复 Zhu 元数据、ReCiPe 单位、C_min 阈值死区、功能等价、rL 条件化 | 无 |
| v5 | 来源投影（编号引用→YAML source ID）、版本阶段标注；科学内容零变更 | 无 |
V1→v5 链不回退。v5 相对 v4 无科学漂移，仅来源投影与版本阶段修正。
# planned/executed 一致性
候选所有方法学、数据收集、pilot 部署和比较分析均标为 planned。Planned vs. Executed Declaration 段显式声明无执行。与 run.md 记录一致。
# artifact_stage 与终态
`artifact_stage: revision_candidate` 是版本阶段标签，不是 Project 终态。历史 Artifact 中出现的其他状态词不参与终态统计。
# Project terminal recommendation
推荐唯一终态 `waiting_human`。研究计划已通过独立评审（v4 rubric 12/12；v5 为纯来源投影修正，科学内容不变，本评审 12/12）。继续执行需要实验室性能测试、实际回收率与洗涤数据、当地基础设施覆盖信息、LCA 实际执行及利益相关方对设计假设的批准。与 run.md 当前 `status: waiting_human` 一致。
# 可选改进
- 精确化 Geyer 9% 的分母（6300 Mt 废弃物子集）可在 frontmatter 注释或 V4→V5 Changes 中注明（F1）。
RESULT: DELIVERABLE
