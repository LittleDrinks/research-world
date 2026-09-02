---
project: q098
artifact: review-v13
role: independent-review
reviewer_session: 01a05fd9-1252-7f60-acf5-a779467d738c
author_session: 01a05fd4-8c03-7569-9af8-9f166cd18c40
reviewed: v12.md
verdict: deliverable
sources:
  - path: research-world/evidence/contest-2026/q098/v11.md
    role: baseline
  - path: research-world/evidence/contest-2026/q098/v12.md
    role: candidate
  - path: research-world/evidence/contest-2026/q098/review-v12.md
    role: prior-independent-review
  - path: research-world/evidence/contest-2026/q098/run.md
    role: terminal-record
  - path: docs/questions.json
    locator: id=98
  - id: S2
    doi_url: https://doi.org/10.1126/science.1241224
    publisher_url: https://www.science.org/doi/10.1126/science.1241224
    access: resolver-to-publisher; publisher-content-403
  - id: S3
    doi_url: https://doi.org/10.1126/science.aax5440
    publisher_url: https://www.science.org/doi/10.1126/science.aax5440
    access: resolver-to-publisher; publisher-content-403
  - id: S6
    doi_url: https://doi.org/10.5665/sleep.2112
    publisher_url: https://academic.oup.com/sleep/article-lookup/doi/10.5665/sleep.2112
    access: resolver-to-publisher; publisher-content-403
---
# q098 独立评审
## 结论
候选科学正文与基线一致；运行记录在独立评审通过前保留上一条已通过链，终态所有权合规。
## 机械核验
统一 diff 仅含 `artifact`、`supersedes`、标题中的版本标记和尾部变更说明；去除 frontmatter、标题版本标记及该说明后，正文比较退出码为 0。问题界定、三条机制、来源条目、数值、研究设计、局限和因果边界均逐字一致。
## 六维评分
| 维度 | 分数 | 依据 |
|---|:---:|---|
| 问题界定 | 2/2 | 原题覆盖可塑性、废物清除与整体健康；候选将其收束为健康成人睡眠时长与免疫-代谢关联，并明确观察性边界。 |
| Direction 与比较 | 2/2 | 突触稳态、类淋巴清除、免疫-代谢调节分别给出证据、限制、可区分预测和实施负担，选路理由基于可行性而非排除其他机制。 |
| 研究计划 | 2/2 | 人群、14天腕动计、基线与6个月时间点、主要终点、协变量、质控、缺失处理、多重性、预注册与伦理均明确；精度试点不冒充确证性功效研究。 |
| 来源与数值 | 2/2 | S1-S8 的标识完整；S2、S3、S6 的 DOI 解析至对应出版方，Fisher-z 的 0.092 与 0.18 以及招募数 142 可复算。原始页面在评审环境均返回 403，关键断言未逐条重读，作为 residual risk 记录，不等同来源失效。 |
| planned/executed | 2/2 | 候选使用计划性措辞且未报告受试者、样本、检测或健康结果；运行记录同样保留 `waiting_human` 与资源、伦理前置条件。 |
| 终态所有权与追溯 | 2/2 | 运行记录第5-7行在独立评审通过前保留上一条已通过链；候选只标为 `revision_candidate`，终态继续由运行记录独占，符合更新顺序。 |
**总分：12/12。**
RESULT: DELIVERABLE
