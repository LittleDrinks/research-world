---
project: q049
protocol: contest-research-workflow-2026-09-01
status: completed
final: v3.md
final_review: review-v3.md
---
# q049 运行记录
## 问题
Why don't the orbits of planets decay and cause them to crash into each other?
Gravity keeps planets in stable orbits around the sun. Yet orbits do decay very gradually. Eventually, the planets will swirl into the sun.
## 版本与评审
| 产物 | Pi Session id | 模型 | 调用 | 非缓存输入 token | 缓存读取 token | 输出 token | 结果 |
|---|---|---|---:|---:|---:|---:|---|
| `baseline.md` | `01a0599a-eaa0-7819-90ca-403042218cd4` | `contest-qwen/qwen3-max` | 14 | 113047 | 238592 | 2417 | 直接回答；8/12；关键数值来源 3/3 |
| `v1.md` | `01a0599b-f95f-74e2-b861-aba3c5fd1fe6` | `contest-qwen/qwen3-max` | 25 | 98844 | 373120 | 4567 | 9/12；引用 2/5；`revise` |
| 无产物 | `01a059a1-9238-7a71-99d7-163443ee365b` | `contest-qwen/gpt-5.3-codex` | 4 | 0 | 0 | 0 | `failed`；一次 502、三次 429 |
| `review-v1.md` | `01a059a4-7583-7237-8303-6305b184b2ba` | `contest-qwen/gpt-5.6-sol` | 20 | 56741 | 408832 | 16023 | `revise`；发现错配 DOI、反向转述和 22 个数量级错误 |
| `v2.md` | `01a05a51-a3ca-79ae-8824-25e418141a88` | `contest-qwen/qwen3-max` | 18 | 96576 | 470272 | 5388 | 8/12；引用 5/5；`revise` |
| `review-v2.md` | `01a05a55-f781-7c5f-8dd7-a7e2c9e537d3` | `contest-qwen/gpt-5.6-sol` | 16 | 42946 | 274688 | 14931 | `revise`；发现机制捆绑、时间尺度和判据错误 |
| `v3.md` | `01a05afd-575a-7482-9e85-61bf295d506d` | `contest-qwen/qwen3-max` | 29 | 230444 | 803456 | 7907 | 最终候选；执行一次 Peters 公式校验 |
| `review-v3.md` | `01a05b03-f9a1-7b8c-bb04-c24f987326bc` | `contest-qwen/gpt-5.6-sol` | 18 | 37807 | 302592 | 11488 | `deliverable`；12/12；引用 5/5 |
成功的 `gpt-5.6-sol` reviewer Session 中出现过上游 `401/503` 重试；模型随后继续完成任务。失败的 `gpt-5.3-codex` Session 未生成内容，未被覆盖或计入成功评审。
## 同条件对照
| 指标 | 直接回答 | Workflow V1 |
|---|---:|---:|
| 模型 | `contest-qwen/qwen3-max` | `contest-qwen/qwen3-max` |
| 模型调用 | 14 | 25 |
| 非缓存输入 token | 113047 | 98844 |
| 缓存读取 token | 238592 | 373120 |
| 输出 token | 2417 | 4567 |
| 六维 rubric | 8/12 | 9/12 |
| 引用抽查 | 关键数值来源 3/3 | 全部来源 2/5 |
| 可区分 Direction | 0 | 3 |
| 可实施研究计划 | 无 | 有，但 V1 判据错误 |
Workflow V1 增加了 Direction 比较和研究计划，但没有自动提高科学可靠性；V1 的引用有效率低于直接回答，且关键定量错误需要两轮独立评审和两次修订才闭环。最终版相对 V1 从 9/12 提升到 12/12，引用从 2/5 提升到 5/5；代价是额外五个成功 Session、一个失败 Session 和一次限定计算。模型在生成侧保持 `qwen3-max`，评审侧换为 `gpt-5.6-sol`，因此最终改善不能只归因于 Workflow。
## 实际计算
V3 使用 Peters 圆轨道公式核验地球-太阳引力波耗散。输入、公式、命令、输出和退出码写入 `v3.md`；输出为 `P = 196.291 W`、`t = 3.374e+30 s = 1.069e+23 years`。输出文本 SHA-256 为 `7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361`。最终 reviewer 独立复算数值并重算该哈希，结果一致。
## 文件哈希
| 文件 | SHA-256 |
|---|---|
| `baseline.md` | `52d5d8175092d36cbfaf82b4663d22e087fd5e7a20f6c11cef199c5a0ef5dac4` |
| `v1.md` | `74e43718d54c346a857f763ce1b3a9fbbac53937dc944a36b1007427306bcce5` |
| `review-v1.md` | `96268a2457f613e15cec52a04fa2989568e24883db95906fe5d82568e949ae74` |
| `v2.md` | `f52147e11870e864caf6a420ad8abbf16edc8324a2844a47723af0a2b2ac8008` |
| `review-v2.md` | `de3c4080cf75477c45277a820fdf4a17cb1f3ba3b90712950dc6bc66a4d7a0f4` |
| `v3.md` | `c7109c684c5b64e509f8018e61650a4b8af05b29efc2a9175328428ab435ba0f` |
| `review-v3.md` | `f66d803febcdce3a483b09133b05d2ca19d26ab94862084927cea4e30f827472` |
## 未解决项
- V3 将约 1% 水星失稳概率错归于 Batygin & Laughlin 2008；该概率应由 Laskar & Gastineau 2009 支持。最终评审判为不影响实施与主结论的 Minor，交付时保留披露。
- V3 未把限定计算脚本作为 Artifact 保存，但公开了公式、输入、命令、输出和输出哈希；最终 reviewer 已独立复现。
