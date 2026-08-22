# 确定性指标：三层报告，不合成总分
125 题是开放问题、无 gold answer，系统性能的确定性证明分三层：
(a) **过程指标**——从 Research event 与 Runtime Trace 派生的确定性读模型：双审一致率、人工介入率、退修率、复现哈希一致率、token 与耗时 per 题；
(b) **外部 ai4s bench 锚**——ResearchClawBench base 40 为主战场，InnovatorBench task 18/19/20 与 AstaBench 可行子集为侧证；
(c) **装配 bench**——领域簇手工 gold 工具需求，测装配者选择的精确率/召回率，同时是装配质量的验证手段。
三层分别报告，不合成总分（评测策略见 0019）；指标即读模型，每个值可回到产生它的节点或事件。BioMysteryBench 类终答案准确率 bench 不跑：单容器终答案任务不触发本系统的规划-审核-迭代机制，分数不改变任何决策。
