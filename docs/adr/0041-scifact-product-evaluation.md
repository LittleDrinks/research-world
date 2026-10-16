---
status: accepted
issue: 322
sources:
  - https://github.com/allenai/scifact/tree/68b98a56d93e0f9da0d2aab4e6c3294699a0f72e
  - https://github.com/allenai/scifact-evaluator/tree/66feffc5b2cc9e28e3ce3b8c9e824c3c642981eb
---
# SciFact 产品评测
官方 TF-IDF 从固定摘要语料检索 top-3；模型输入只含 claim 文本、候选文档编号与句子，不含 cited_doc_ids 或 gold evidence。检索在实验组之外运行，两组获得完全相同的候选。
baseline 与 research 使用同一个 Pi 模型、thinking 和每题超时。baseline 不选工具；research 选 graph、record、connect、delegate，独立审查只读给定摘要。每题每组使用全新 Project/Session，不跨题复用图谱，不启用在线文献检索。成本可能不同；未强制同等总 token 预算时不声称系统增益。
官方 evaluator 原样评分；结构非法或运行失败保留记录并以空 evidence 进入总分，另外报告可用输出率。逐题诊断区分检索覆盖、输出格式、运行状态和官方评分，不将代理分类直接当作根因。
固定前 N 条 train 仅联调；完整 dev 必须在配置冻结后单独运行。保存输入、候选、模型配置、源码/数据哈希、原始答案、预测、官方分数、父子轨迹和耗时。用量或价格缺失时记未知，不用事件条数估算 token 或费用。
产品执行适配器只接收研究问题、消息和 Agent 配置标识，返回答案、运行状态和轨迹引用；不读取 SciFact gold、不解析预测标签、不调用评分器。SciFact 模块负责协议和评分，CLI 只组织二者。
提交 Session 前持久保存 Project、message_id 与完整请求。响应超时后按已存 message_id 查询同一 Project 的 Session，找到原执行后取消并导出；不重新创建模型工作。网络持续不可达时显式标记 cleanup_pending，保存恢复材料，不能宣称已取消。
