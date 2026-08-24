---
sources:
  - https://export.arxiv.org/api/query
  - https://www.ebi.ac.uk/europepmc/webservices/rest/search
---
# Research Kernel Paper Corpus
六十篇论文覆盖形式证明、科学 benchmark、数值模拟、科学观测、湿实验和临床或人类数据，每类十篇。`sources.seed.json` 冻结选择，`raw/` 保存原文快照，`metadata.json` 保存摘要，`graphs/` 保存反向分解，`manifest.json` 保存版本、哈希和许可信息。
## 标注约束
- `explicit`：论文正文直接陈述该节点或关系。
- `inferred`：为了图谱呈现而重建的关系，不冒充作者留下的研究轨迹。
- 不从成稿反推出未公开的失败实验、调用记录或时间顺序。
- `locator` 指向论文中的章节、图表或页码；面板节点可回到本地原文与官方来源。
- 七篇种子论文为章节级人工分解，新增五十三篇为摘要级确定性分解并保留完整原文；`scripts/audit_corpus.py` 校验来源哈希、类别配额、节点类型、边引用、溯源字段和重复正文。
## 语料边界
语料用于验证同一 Research Kernel 能否表达不同研究模态，不构成系统综述。PDF 与 XML 仅用于本地研究原型；再分发受各来源许可约束。
