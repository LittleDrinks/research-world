---
project: q049
protocol: contest-research-workflow-2026-09-01
status: completed
final: v5.md
final_review: review-v5.md
final_receipt: receipt-v6.md
matched_baseline: baseline-matched-v9.md
matched_review: review-baseline-matched-v10.md
matched_receipt: receipt-baseline-matched-v9.md
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
| `baseline-matched.md` | `01a05e02-dc33-7618-9049-d458bb9f0ae8` | `contest-qwen/qwen3-max` | 32 | 162564 | 1657856 | 14483 | 未选 attempt 1；三次重写且 Peters 计算错 10 个数量级 |
| `baseline-matched-v2.md` | `01a05e0b-4ecc-7866-b6fa-51a5e78ebcbf` | `contest-qwen/qwen3-max` | 21 | 113326 | 555520 | 3244 | 未选 attempt 2；单次写入但长度不足且无来源 |
| `review-baseline-matched.md` | `01a05e0e-29a6-7ae4-b576-9f83ffa8a0be` | `contest-qwen/qwen3.7-max` | 33 | 168772 | 1296768 | 30502 | attempt 1/2 比较；发现定量错误 |
| `baseline-matched-v3.md` | `01a05e12-6fe4-7a37-9851-6e9928edd212` | `contest-qwen/qwen3-max` | 19 | 105927 | 388992 | 2523 | 未选 attempt 3；写入未核实的 `10^150` 年 |
| `baseline-matched-v4.md` | `01a05e15-bb6b-76c9-8dd9-fa631bb76608` | `contest-qwen/qwen3-max` | 23 | 159036 | 561664 | 8093 | 未选 attempt 4；违反最多六次检索、一次 write 的自定控制 |
| `review-baseline-matched-v4.md` | `01a05e1a-2fe5-73a2-898d-256e8dbdccd5` | `contest-qwen/qwen3.7-max` | 28 | 282890 | 1254528 | 16512 | attempt 4 评审；后续分支验收否决其协议合规性 |
| `baseline-matched-v5.md` | `01a05e40-1e01-7328-8454-b5ae761d51de` | `contest-qwen/qwen3-max` | 25 | 135692 | 555008 | 10937 | 未选 attempt 5；实际 5234 字符、三次仓库 write，并使用禁用来源 |
| `baseline-matched-v6.md` | `01a05e45-a299-7a05-b089-d721ecc89764` | `contest-qwen/qwen3-max` | 27 | 1182967 | 393984 | 12902 | 选定 attempt 6；raw 4708 字符、一次仓库 write；Peters 复算正确 |
| 无产物 | `01a05e4b-a17d-7e61-a1fa-df919f374c1c` | `contest-qwen/qwen3-max` | 28 | 134808 | 792704 | 4028 | 未选 attempt 7；超过检索控制后主动停止，未写仓库产物 |
| `review-baseline-matched-v6.md` | `01a05e4e-e52a-7aec-8570-14f7c2bc777f` | `contest-qwen/qwen3.7-max` | 37 | 239614 | 1706496 | 24193 | benchmark `deliverable`；baseline 6/12，V1 9/12 |
| 无产物 | `01a05e59-0f72-7d68-bf85-a4c61ed42c68` | `contest-qwen/qwen3-coder-plus` | 5 | 11883 | 0 | 53 | `failed`；上游拒绝 tool role，未生成收据 |
| `receipt-baseline-matched-v6.md` | `01a05e5a-0533-76d7-b904-a94f7ad80f5c` | `contest-qwen/qwen3.7-max` | 12 | 108308 | 468864 | 8716 | 独立回算 Session、模型、token、write、哈希与 RESULT；`deliverable` |
| `v4.md` | `01a05e78-2dc7-7f1a-8c8c-cc0d8f0d4fb4` | `contest-qwen/qwen3-max` | 14 | 81158 | 296192 | 6630 | 修正水星失稳概率来源归因并投影来源元数据；科学主线不变 |
| `review-v4.md` | `01a05e7d-bee7-7696-b996-6b0536574739` | `contest-qwen/qwen3.7-max` | 22 | 142884 | 1039104 | 13854 | `deliverable`；12/12；来源 6/6；概率来源已纠正 |
| `receipt-v4.md` | `01a05eb5-adc5-7ec2-a7a2-5952895be3eb` | `contest-qwen/qwen3.7-max` | 13 | 97686 | 359040 | 9177 | 独立确认最终来源分母 6/6、哈希、Peters 复算与概率归因 |
| `v5.md` | `01a05ed8-deed-7ad4-8e41-715198ec6381` | `contest-qwen/qwen3-max` | 13 | 59071 | 229888 | 5036 | 将 artifact 内“当前终态”改为“当前研究结论”；科学内容零漂移 |
| `review-v5.md` | `01a05edb-c929-7bc5-8e0b-87f556e74251` | `contest-qwen/qwen3.7-max` | 15 | 157174 | 540672 | 13907 | `deliverable`；12/12；来源 6/6；仅给 reviewer verdict |
| `receipt-v5.md` | `01a05ee1-6f4c-7a29-ac3a-f11bf0acad9e` | `contest-qwen/qwen3.7-max` | 11 | 62988 | 206976 | 6206 | 可归因审计回执；记录 auditor/reviewer UUID、哈希和 RESULT |
| `receipt-v6.md` | `01a05f3f-f617-7380-8f59-344f3b2029b9` | `custom/gpt-5.6-terra` | 6 | 29853 | 208384 | 10151 | `deliverable`；补齐来源 frontmatter，复核 v5/review-v5 与 6/6 来源 |
| `baseline-matched-v7.md` | `01a05ef6-9884-7843-86b2-20c6cab09c33` | `contest-qwen/qwen3-max` | 5 | 20707 | 44672 | 3702 | 证据角色修订；后续评审发现两项定量错误 |
| `review-baseline-matched-v7.md` | `01a05ef8-9585-7d65-a7a2-6669128fd27c` | `contest-qwen/qwen3-max` | 11 | 28598 | 183168 | 2705 | 错误自造 reviewer UUIDv4；保留并重跑 |
| `review-baseline-matched-v8.md` | `01a05efa-7470-7f50-8875-ad2f272de28b` | `custom/gpt-5.6-terra` | 12 | 99804 | 620544 | 22044 | `revise`；发现水星 Peters 时间、质量损失外移与来源投影缺陷 |
| `baseline-matched-v8.md` | `01a05f02-1368-7963-be17-d9147c57a04b` | `custom/gpt-5.6-terra` | 20 | 124865 | 1449984 | 23366 | 修正数值与四类来源；水星输入记录仍不完整 |
| `review-baseline-matched-v9.md` | `01a05f0a-8087-7740-a531-1ab7ce5ac613` | `custom/gpt-5.6-terra` | 13 | 96949 | 898816 | 23353 | `revise`；仅剩水星质量与半长轴输入未显式记录 |
| `baseline-matched-v9.md` | `01a05f12-6e5d-7931-a8cb-585b1cc893ce` | `custom/gpt-5.6-terra` | 12 | 69618 | 733184 | 17595 | 新候选；补齐两组 Peters 全部输入、单位、公式与输出 |
| `review-baseline-matched-v10.md` | `01a05f18-d17a-7910-ac13-60791233da3d` | `custom/gpt-5.6-terra` | 14 | 102891 | 1025536 | 18660 | `deliverable`；复算三项数值并核验四类主源 |
| `receipt-baseline-matched-v9.md` | `01a05f1f-d312-7c60-a8b8-ceaf0d54e2a6` | `custom/gpt-5.6-terra` | 15 | 83602 | 742656 | 15515 | `deliverable`；真实运行态 auditor/reviewer/author UUIDv7 |
成功的 `gpt-5.6-sol` reviewer Session 中出现过上游 `401/503` 重试；模型随后继续完成任务。失败的 `gpt-5.3-codex` Session 未生成内容，未被覆盖或计入成功评审。
## 同条件对照
最初的 `baseline.md` 与 V1 实际长度和 calls 不匹配，只保留为历史直接回答。七个全新 attempt 全部留痕；attempt 6 由独立 reviewer 判定为可交付 matched baseline。两侧相同原题、`qwen3-max`、检索权限和 3500–5000 中文字目标，均在一个独立 Session 内完成；实际检索路径分别为 Crossref 与 anysearch，不冒充同行为或因果。
| 指标 | Matched direct attempt 6 | Workflow V1 |
|---|---:|---:|
| 模型 | `contest-qwen/qwen3-max` | `contest-qwen/qwen3-max` |
| 文件字符 `wc -m` | 4708 | 4970（原始 write；当前投影 4968） |
| 模型调用 | 27 | 25 |
| 非缓存输入 token | 1182967 | 98844 |
| 缓存读取 token | 393984 | 373120 |
| 输出 token | 12902 | 4567 |
| 六维 rubric | 6/12 | 9/12 |
| 显式来源 | 0 条 | 全部来源 2/5 有效 |
| 可区分 Direction | 0 | 3 |
| 可实施研究计划 | 无 | 有，但 V1 判据错误 |
Matched direct attempt 6 的 Peters 时间经独立复算正确，但无显式 URL/DOI、Direction 或研究计划，不能作为学术答案直接采用。Workflow V1 增加了 Direction 比较和研究计划，但引用有效率只有 2/5，并含 22 个数量级的功率错误。最终版相对 V1 从 9/12 提升到 12/12，来源从 2/5 提升到 6/6；改善发生在独立评审、修订和一次限定计算之后，不能只归因于 Workflow。Attempt 6 token 显著高于 V1，作为实测成本差异报告，不事后重采样刷预算。
`baseline-matched-v9.md` 是后续独立 Session 形成的可追溯展示投影：修正水星 Peters 时间为 `4.343e22` 年、按条件质量损失率复算外移为 `0.005%`，并补齐四类主源和完整输入。该投影不回写 attempt 6 的冻结模型、长度、调用、token、检索路径或 6/12 评分。
## 实际计算
V3 使用 Peters 圆轨道公式核验地球-太阳引力波耗散。输入、公式、命令、输出和退出码写入 `v3.md`；输出为 `P = 196.291 W`、`t = 3.374e+30 s = 1.069e+23 years`。输出文本 SHA-256 为 `7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361`。最终 reviewer 独立复算数值并重算该哈希，结果一致。
## 文件哈希
| 文件 | SHA-256 |
|---|---|
| `baseline.md` | `52d5d8175092d36cbfaf82b4663d22e087fd5e7a20f6c11cef199c5a0ef5dac4` |
| `v1.md` | `7883753678e5efdbbd88618f89d79afbb6a0fda59eeb571c7b32b3bd0ee5f652` |
| `review-v1.md` | `96268a2457f613e15cec52a04fa2989568e24883db95906fe5d82568e949ae74` |
| `v2.md` | `f52147e11870e864caf6a420ad8abbf16edc8324a2844a47723af0a2b2ac8008` |
| `review-v2.md` | `de3c4080cf75477c45277a820fdf4a17cb1f3ba3b90712950dc6bc66a4d7a0f4` |
| `v3.md` | `c7109c684c5b64e509f8018e61650a4b8af05b29efc2a9175328428ab435ba0f` |
| `review-v3.md` | `f66d803febcdce3a483b09133b05d2ca19d26ab94862084927cea4e30f827472` |
| `baseline-matched.md` | `06b0ae4adfc29ae506290f8feb4eaaf961e2cad831d1dec1e4d8c084b3b708a6` |
| `baseline-matched-v2.md` | `add15e78cdeeb775a65b5df9cfe7afc5dd512c4acaa09a5025bad750cb249e1b` |
| `review-baseline-matched.md` | `1f6cd5cf3e9b2712481b539a372ee922ab101b66402825c6b79685650f46f125` |
| `baseline-matched-v3.md` | `21d42887f740922599d4f89f9b1d6428225fdf668b5784f106b0e0d8b08cfc5e` |
| `baseline-matched-v4.md` | `900c0e1351694896692bad2da26207f2c786f70af34b9c3de446a4c02310653f` |
| `review-baseline-matched-v4.md` | `41f52319488ac932cf94d9f94896ddfc35add7415235697a66a3a27c7979821b` |
| `baseline-matched-v5.md` | `ad68926ebc6a462ed95794c8723b4f62144bae983e9c4d0ae4d42ff7494d0eec` |
| `baseline-matched-v6.md` | `7f13d8dd0a682aa470fcffaa1098f8a140cc2d43006035aecb3ab4122cb42d1b` |
| `review-baseline-matched-v6.md` | `942c6d9551e69683b5c4820e41d605d3c014097fbb7ab94bbde6dd57775c936a` |
| `receipt-baseline-matched-v6.md` | `47e2785acbe9f313795338c0f9fc2c54aecbe92508a9a7349b65f53a0bda1e02` |
| `v4.md` | `fe013717797c44cc1dd401982ed1f0f8e22311a3b2661f3b489f9389981c54eb` |
| `review-v4.md` | `b61a0ffea0e40ca93bce9371eba4b71e5656e1bbfa5dfb9d8c871dcfdbe05068` |
| `receipt-v4.md` | `1ecd438af35d08ec332e155b98ea595cdaee4c26b5ab94a96d67619b04618591` |
| `v5.md` | `51dc9f52a52fb9379e9a2c148eeafe2fc5579dd5da498d6dd6cda9028ecd460f` |
| `review-v5.md` | `96b19f719b7a340fce43e2d3e192e67901d21c057c977bf08e5837d9d4c6f853` |
| `receipt-v5.md` | `dbdf4f3834e2e5793230af38b9338c7eda421a5e52b2dd81d2fd1fbdbc4d6636` |
| `receipt-v6.md` | `9f5cfbe0d5a3f9511fbe3ed7e1e4e3be3e3072433cd08f41cf199a902f653dbd` |
| `baseline-matched-v7.md` | `56b3cb6f0e4f576a5c64a8ac88b82f62f3551cca2493258f55f8492f8ed4b13b` |
| `review-baseline-matched-v7.md` | `8be38d58dc72d3c24493b84822d517310f9fb41dcc5706eccf62fd37fd388562` |
| `review-baseline-matched-v8.md` | `bcd6d55c8f93c692f7783eafa7f28c95359e1719a15fd81825d8449175262c78` |
| `baseline-matched-v8.md` | `ff985bb25cee86397170d5b306200bcb367e3f936d4bb19a00b44337bd424f60` |
| `review-baseline-matched-v9.md` | `e8804b03ca512bc085f6958f623287d996eaaae98fd269f7a2aaacd2ce78725c` |
| `baseline-matched-v9.md` | `6d017687fa1c716c9f56ae6162b3ad3c4299a54ac9cc40353a31e3604e7e6fa1` |
| `review-baseline-matched-v10.md` | `4e93a995cb39062e16d8b5a6ef3a605fd28785d7c2280c38aa6ae3c20e90bcf4` |
| `receipt-baseline-matched-v9.md` | `e27640f13b756bf149e2e5a62764b77c3634d0fd9fff664e4e65206870766caa` |
## 未解决项
- V3 的约 1% 水星失稳概率来源归因错误已在 V4 修正为 Laskar & Gastineau 2009；Batygin & Laughlin 2008 仅支撑构造的 1.261 Gyr 失稳轨迹。
- V3 未把限定计算脚本作为 Artifact 保存，但公开了公式、输入、命令、输出和输出哈希；最终 reviewer 已独立复现。
- Matched baseline attempt 6 只用于公平 benchmark，不可作为学术答案直接采用；其关键数值正确，但没有显式来源标识、Direction 或研究计划，独立 reviewer 已明确披露。
- receipt-v4 的 `auditor_session: current` 与 V4 artifact 的“当前终态”均保留为被拒历史；V5/review-v5/receipt-v5 已分别闭合角色边界与可归因性。
