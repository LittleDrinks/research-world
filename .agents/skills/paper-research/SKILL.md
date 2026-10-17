---
name: paper-research
description: Read a full scientific paper for a Project, extract page-grounded evidence, allocate review depth, delegate independent parallel reviews, and integrate verified evidence into the research graph.
---
## 全文与范围
1. 查询 Project 的 Question、Direction 和已有 Source，明确本次需要证据回答的问题。取得可合法读取的 PDF，记录标题、作者、版本、DOI/稳定 URL；无法取得全文时只报告元数据和访问缺口，停止全文审查。
2. 在 workspace 运行 `python /opt/paper-research/paper.py extract paper.pdf > paper.json`。中文用 `--language eng+chi_sim`；扫描内容与文本混合或文本层损坏时用 `--force-ocr`。输出保留输入 SHA-256、每页原文、提取方法和失败状态。页码是从 1 开始的 PDF 物理页码。
3. 核对总页数及所有空白/失败页；用 `pdftoppm` 导出疑似缺字、公式、图表页，使用 read 查看图像。OCR 文本仅是待核验转录；无法辨认的公式、数值、图表标为未验证。正文、附录、参考文献都列入覆盖清单。
## 分段与自适应深度
4. 按语义边界建立工作区分段清单，记录每段页码、逐页字符区间 `[start,end)`、主题、与 Question/Direction 的关系、thinking 及理由。允许重叠；逐页合并区间，检查每个非空原文字符均被覆盖；空白/失败页逐一记录缺口。不得只读相关段后声称全文已审查。
5. 简单背景/低相关段使用 low；直接相关方法和实验使用 medium；关键证明、相互冲突结果、复杂统计或跨段前提使用 high。根据审查发现重新分配深度，而非按章节标题机械决定。每段至少完成相关性筛查；未解决的关键问题追加独立复核。
## 独立并行审查
6. 用 delegate 的 `tasks` 数组每批提交最多 8 个任务，每项包含 `instructions`、`task`、`thinking`。每个 Child 的任务明确 Project 问题、目标段字符区间、完整 paper.json 路径和源哈希；全文在共享 workspace 中可按需读取。Child 指令只含自己的任务与证据约束，独立写入指定的不同输出文件；不附其他 Child 的意见或主 Agent 对话。
7. Child 检查本段与研究问题的关系、方法前提、适用范围、反例和跨章节依赖；追到实际引用段，不从标题或摘要猜内容。返回候选陈述、对应 Direction、支持/反驳/仅背景、原文 quote、page、source_sha256、前提、局限、未验证项及检查过的跨段位置。Child 只提出候选证据，写图由主 Agent 决定。
8. 按输入顺序读取 delegate.results，逐个检查 status 和 result_text；失败/取消/缺失输出列为缺口，不能视为完成。主 Agent 默认读取摘要与候选证据，按需打开全文或详细记录；对关键争议再委派独立复核。
## 综合与引用入图
9. 将候选引用组成 JSON 数组，每项至少含 source_sha256、page、quote。运行 `python /opt/paper-research/paper.py verify paper.json --citations citations.json > checked.json`；任何不匹配引用都先纠正或剔除。精确匹配仅证明转录中存在该片段，不能证明 OCR 正确或陈述成立。
10. 主 Agent 回查原页与上下文，确认引用足以支持陈述，区分作者报告、外部复现与自己的推断。核对跨段前提、去重、保留冲突；需要外部依据时使用 literature 检索一手来源，取得实际内容再核验，未取得则保留不确定性。复用已有 Source，避免把同一论文重复计算为独立支持。
11. 使用 artifact 的 `path` 参数原样捕获工作区中的转换全文 JSON 和综合证据 JSON（来源元数据、哈希、定位、预算理由、覆盖缺口、核验结果），取得不可变 Artifact id；小段新文本可用互斥的 `content` 参数。使用 record 将这些 artifact_ids 绑定到 Source，content.text 写清可支持的陈述及局限。需要新研究方向时记录 Direction，通过 Source→Direction 的 supports/refutes 关系关联；Direction→Question 用 depends_on。Quote 不匹配或语义尚未确认的内容不建立支持/反驳边。
12. 返回入图对象/Artifact id、支持与反驳的方向、尚存冲突、未读或不可核验部分。只有全部覆盖检查、子任务和引用核验完成时，才能报告本次审查完成；否则明确报告部分完成。
