# 首批五案例结果
| Project | 验证形态 | V1 | 最终版 | 引用 | 终态 | 最终证据 |
|---|---|---:|---:|---:|---|---|
| `q049` | 引文约束、限定计算、同模型直接回答 | 9/12 | 12/12 | 6/6 | `completed` | `q049/v6.md`、`q049/review-v6.md`、`q049/receipt-v7.md`、`q049/run.md`；matched 展示链为 `baseline-matched-v9.md`、`review-baseline-matched-v10.md`、`receipt-baseline-matched-v9.md` |
| `q089` | 效率边界、材料路线、TPV 计划 | 10/12 | 12/12 | 8/8 | `completed` | `q089/v7.md`、`q089/review-v10.md`、`q089/receipt-v11.md`、`q089/run.md` |
| `q021` | 冲突证据、临床 pilot、ITT | 10/12 | 12/12 | 8/8 | `waiting_human` | `q021/v8.md`、`q021/review-v10.md`、`q021/receipt-v11.md`、`q021/run.md` |
| `q112` | 功能单位、LCA、复用 break-even | 7/12 | 12/12 | 9/9 | `waiting_human` | `q112/v7.md`、`q112/review-v9.md`、`q112/receipt-v9.md`、`q112/run.md` |
| `q098` | 三机制比较、人体时序 pilot | 7/12 | 12/12 | 8/8 | `waiting_human` | `q098/v10.md`、`q098/review-v11.md`、`q098/receipt-v13.md`、`q098/run.md` |
## 同条件对照
q049 冻结的 matched `qwen3-max` attempt 6 为 6/12，Workflow V1 为 9/12，最终版为 12/12。两侧 raw artifact 长度为 4708/4970 字符、calls 为 27/25；attempt 6 没有显式来源记录，Workflow V1 全部来源 2/5 有效，最终版 6/6。`baseline-matched-v9.md` 是独立 Session 产生的可追溯展示投影，修正水星 Peters 时间、条件质量损失外移并补齐来源，不回写 attempt 6 的冻结长度、调用、token 或评分。V1 增加三个 Direction 与研究计划，但可靠性没有自动提升：attempt 6 的地球 Peters 数值正确却不可追溯，V1 的功率错 22 个数量级并含错配 DOI。最终改善发生在独立评审、修订和限定计算之后；模型变化单独披露，不能把全部提升只归因于 Workflow。六个未选 attempt 与后续修订均保留在 `q049/run.md`。
## 代价
| Project | 模型调用 | 非缓存输入 token | 缓存读取 token | 输出 token |
|---|---:|---:|---:|---:|
| `q049` | 658 | 4914275 | 22179886 | 425285 |
| `q089` | 309 | 1718005 | 7985123 | 192331 |
| `q021` | 414 | 2501811 | 11393019 | 222885 |
| `q112` | 313 | 1929772 | 9195783 | 189256 |
| `q098` | 410 | 2869860 | 11614336 | 243646 |
| **合计** | **2104** | **13933723** | **62368147** | **1273403** |
统计包含基线、生成、评审、修订和失败 Session；128 个 Session UUIDv7 唯一，122 个文件 SHA-256 均与当前内容一致，明细见对应 `run.md`。
## 放大前结论
- 三方向、来源和研究计划在 V1 中出现，不代表科学可靠；五题首轮均需评审或修订。
- 错误模式集中在精确数字错引、来源元数据拼接、比较对象不等价、观察性设计因果过度、样本量与终点不匹配、planned 被写成 executed。
- reviewer 的 `deliverable` 不是免检信号；q112 在 10/12 和 75% 引用有效率时仍保留错用标准与错误方程，继续修订后才达到 12/12、9/9。
- 终审的 `12/12` 也不是永久事实；分支级独立验收发现 q021 V5 将正确 PMID 与错误 DOI 拼接，V6 重新交叉核验后才恢复 12/12。
- 标识符可解析也不等于元数据正确；q089 V4-V6 的 DOI 均有效，但题名和作者错配，V6 甚至含不属于论文的作者，V7 以 Crossref 逐项修复后才恢复 12/12。
- 上游无内容或无文件按 `failed` 留痕并以全新 Session 重试；q049、q021、q112、q098 保留全部无可用产物的失败 Session。
- 工具输出重复不等于文件重复；q021、q098 的重复 finding 经标题、终态计数和后续 diff 否证。
- 全量运行采用每题独立 Pi Session、一次传输重试、紧凑 Markdown 结果和聚合审计；科学不足记 `partial`，需要伦理、权限、设施或领域阈值时记 `waiting_human`，不得重复抽样刷成成功。
