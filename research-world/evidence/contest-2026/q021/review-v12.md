---
project: q021
artifact: review-v12
role: independent-review
reviewer_session: 01a05fd9-123c-7ed3-9600-cd8e65992dc8
author_session: 01a05fd4-8beb-76f6-8686-a4d8cb510e49
reviewed: v10.md
verdict: deliverable
sources:
  - path: research-world/evidence/contest-2026/q021/v10.md
    use: candidate
  - path: research-world/evidence/contest-2026/q021/v9.md
    use: baseline
  - path: research-world/evidence/contest-2026/q021/review-v11.md
    use: prior independent assessment
  - path: research-world/evidence/contest-2026/q021/run.md
    use: execution and terminal ownership record
  - path: docs/questions.json
    selector: id=21
    use: original question
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11080102/
    use: S3 original-study full text and report-time values
  - url: https://pubmed.ncbi.nlm.nih.gov/38738189/
    use: S3 DOI and bibliographic identifiers
  - url: https://pubmed.ncbi.nlm.nih.gov/33879485/
    use: S5 DOI, bibliographic identifiers, and 9 percent median margin
  - url: https://academic.oup.com/cid/article/61/7/1071/289120
    use: S8 publisher record, DOI, and randomized-trial findings
  - url: https://bmjopen.bmj.com/content/11/4/e044480
    use: publisher-page access attempt; 403 residual risk only
  - url: https://www.ijccm.org/abstractArticleContentBrowse/IJCCM/35828/JPJ/fullText
    use: publisher-page access attempt; timeout residual risk only
---
# 独立核验
## 结论
六维均通过，合计 12/12；候选内容可交付，研究本身仍处于 planned 门槛之前。
## 六维核验
| 维度 | 分数 | 依据 |
|---|---:|---|
| 问题界定 | 2 | 将宽泛提问收束为细菌性 AMR 的演化约束、特定情境和可测公共卫生结局，未把根除耐药性表述为可实现终点。 |
| 三个 Direction 与比较 | 2 | 减少选择压力和传播、快速诊断驱动窄谱治疗、进化约束联合或序贯治疗分别对应不同机制；均含反证、替代解释、可区分预测与不确定性，主方向的选择理由可追溯。 |
| 研究计划 | 2 | ICU 人群、随机化时点、干预与标准护理对照、流程主终点、ITT/PP、污染和 panel 外路径、资源及 IRB/BSL-2 gate 已闭合；30 例仅定位为可行性 pilot。 |
| 来源 | 2 | S3 的 DOI、题名、PMID 和 PMCID 相符，原始研究给出 2 小时 49 分与 40 小时 21 分；S5 的 DOI、题名和绝对非劣界值中位数 9% 相符；S8 的 DOI、题名、随机设计及 rmPCR/ASP 结论相符。 |
| 数值与 planned/executed | 2 | 2 小时 49 分为 2.82 小时，40 小时 21 分为 40.35 小时；在两组 30% 事件率、10% 绝对界值、单侧 0.025 和 80% 效能的近似下，每组 329.3 向上取整为 330。患者招募、随机、检测、医嘱调整和结局比较均未宣称执行。 |
| 终态所有权 | 2 | 候选产物仅标为 revision_candidate；终态指针和 waiting_human 仍由运行记录持有，未发生候选产物自行升格。 |
## 机械不变性
科学命题、S1-S8、三条路线、主方向、pilot 设计、终点、统计计划与风险边界逐字一致；非科学差异限于元数据、标题尾注及移除自指性修订段，故科学内容零漂移。
## 残余风险
BMJ Open 与 IJCCM 出版方页面分别返回 403 和超时；这不等同来源失效，已用可读的原始论文记录或出版方记录交叉核验可见 DOI、题名和关键数值。实际实施前仍须按既定 gate 取得 IRB、本地 BSL-2 资质、临床实施细则，并预先规定无医嘱变更、死亡或出院时的主终点处置。
RESULT: DELIVERABLE
