---
project: q021
artifact: receipt-v13
role: independent-audit
auditor_session: 01a05fe5-4531-7cb0-b013-4d6f2843955a
author_session: 01a05fd4-8beb-76f6-8686-a4d8cb510e49
reviewer_session: 01a05fd9-123c-7ed3-9600-cd8e65992dc8
reviewed:
  - research-world/evidence/contest-2026/q021/v10.md
  - research-world/evidence/contest-2026/q021/review-v12.md
verdict: DELIVERABLE
final_sha256: 172715a461245c8e8a47eb65d107193ef3c70f1373504472c0f4b296e4ebd347
review_sha256: 1eb41ae4cb22ffe8970abd2f8b77b4a222531763983e8d3a57a764a6fd89b14b
sources:
  - path: research-world/evidence/contest-2026/q021/v10.md
    use: candidate, scientific-drift comparison, and final digest
  - path: research-world/evidence/contest-2026/q021/review-v12.md
    use: reviewer verdict, rubric, source registry, and review digest
  - path: research-world/evidence/contest-2026/q021/v9.md
    use: preceding final and scientific-drift baseline
  - path: research-world/evidence/contest-2026/q021/run.md
    use: original question, prior final chain, and terminal ownership
  - path: research-world/projects/q021/project.json
    use: original-question record
  - path: docs/questions.json
    selector: id=21
    use: original-question cross-check
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11080102/
    use: S3 title and 2:49 versus 40:21 report-time evidence
  - url: https://pubmed.ncbi.nlm.nih.gov/38738189/
    use: S3 identifier access attempt
  - url: https://pubmed.ncbi.nlm.nih.gov/33879485/
    use: S5 identifiers and 9 percent median-margin evidence
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC8061825/
    use: S5 full-text access attempt
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC4560903/
    use: S8 prospective randomized-trial and stewardship evidence
  - url: https://academic.oup.com/cid/article/61/7/1071/289120
    use: S8 publisher-record access attempt
  - url: https://bmjopen.bmj.com/content/11/4/e044480
    use: S5 publisher-record access attempt
  - url: https://www.ijccm.org/abstractArticleContentBrowse/IJCCM/35828/JPJ/fullText
    use: S3 publisher-record access attempt
  - url: https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance
    use: S1 53 percent, 45 percent, 70 percent, and 2030-target evidence
  - url: https://doi.org/10.1128/MMBR.00016-10
    use: S2 DOI access attempt
  - url: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0301944
    use: S4 identity and ICU de-escalation context
  - url: https://stacks.cdc.gov/view/cdc/20705
    use: S6 report access attempt
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11297101/
    use: S7 title and combination-therapy context
  - url: https://pubmed.ncbi.nlm.nih.gov/20805405/
    use: S2 title, authors, year, PMID, and PMCID
  - url: https://pubmed.ncbi.nlm.nih.gov/39100751/
    use: S7 title, authors, year, PMID, and PMCID
  - url: https://pubmed.ncbi.nlm.nih.gov/26197846/
    use: S8 publication, PMID, and PMCID
---
# 独立审计
## 结论
`review-v12.md` 的 `DELIVERABLE` 与六维合计 12/12 成立；`v10.md` 可交付为候选，`waiting_human` 仍由 `run.md` 持有。
## 可复算记录
- `v10.md` SHA-256：`172715a461245c8e8a47eb65d107193ef3c70f1373504472c0f4b296e4ebd347`。
- `review-v12.md` SHA-256：`1eb41ae4cb22ffe8970abd2f8b77b4a222531763983e8d3a57a764a6fd89b14b`。
- 30% 对照事件率、10% 绝对界值、单侧 alpha=0.025、80% 效能的正态近似给出每组 329.653，向上取整为 330，总计 660；与 reviewer 的约 330/组一致。
## 核验
- DELIVERABLE/12/12：六个维度均为 2 分，问题界定、三条机制路线、pilot 设计、来源、数值与 planned/executed、终态所有权均有可追溯依据。
- 来源登记：reviewer 已登记候选、v9、前序评审、运行记录、原题及 S3/S5/S8 的原始或出版记录；审计实际使用的全部证据与外源访问均列于 frontmatter。WHO 页面复现 S1 的 53%、45%、近三分之一国家超过 70% 与 2030 年 70% 目标；PMC S3 复现 2:49 与 40:21；S5 记录复现 9% 中位绝对界值；PMC S8 复现前瞻性随机设计和 rmPCR/ASP 结果。
- 科学零漂移：`v9.md` 与 `v10.md` 的逐字差异仅含 artifact/supersedes、标题的 V9 尾注和移除旧的自指变更段及候选标记；S1-S8、三条路线、主方向、pilot、终点、统计和风险边界未变。
- planned/executed：候选明确为 planned，尚未提交 IRB；未把招募、随机、检测、医嘱调整或结局比较写成已执行。
- 终态所有权：`run.md` 保持 `status: waiting_human`、`final: v9.md`、`final_review: review-v11.md` 与 `final_receipt: receipt-v12.md`；`v10.md` 仍为 `revision_candidate`，reviewer 的交付判断未夺取终态。
- 机械约束：两项被核验产物均无空行，且没有禁用的自指标记。
## Residual Risk
- 当前环境未能提取 OUP、BMJ Open、IJCCM、CDC Stacks、S2 DOI 和 S5 PMC 页面；S3 PubMed 提取含不相干片段。开放全文、WHO 和 PubMed 交叉记录仍支持关键数值、书目和设计；访问限制不等同来源失效。
RESULT: DELIVERABLE
