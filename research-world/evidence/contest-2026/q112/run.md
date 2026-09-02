---
project: q112
protocol: contest-research-workflow-2026-09-01
status: waiting_human
final: v7.md
final_review: review-v9.md
final_receipt: receipt-v9.md
---
# q112 运行记录
## 问题
Can we create an environmentally friendly replacement for plastics?
## 版本与评审
| 产物 | Pi Session id | 模型 | 调用 | 非缓存输入 token | 缓存读取 token | 输出 token | 结果 |
|---|---|---|---:|---:|---:|---:|---|
| `v1.md` | `01a05d99-7ac5-79c5-9cf3-db6598a2b9e8` | `contest-qwen/qwen3-max` | 30 | 190156 | 712960 | 5845 | 7/12；材料与应用不等价；存在虚构 DOI |
| 无产物 | `01a05da0-e5f7-79d3-bc1f-e7a106820c02` | `contest-qwen/gpt-5.6-sol` | 1 | 0 | 0 | 0 | `failed`；无 assistant 内容或评审文件 |
| `review-v1.md` | `01a05da5-4c00-781e-8279-053cd371dd1e` | `contest-qwen/qwen3.7-max` | 13 | 74002 | 211200 | 9922 | fallback reviewer；7/12；关键引用 4/6 |
| `v2.md` | `01a05dac-0834-7587-90f6-76539baceb85` | `contest-qwen/qwen3-max` | 21 | 105419 | 422016 | 4283 | 改为冷食容器功能单位；计划未执行 |
| `review-v2.md` | `01a05db2-2d63-7301-a70c-9462804dc7c1` | `contest-qwen/qwen3.7-max` | 21 | 175727 | 612480 | 11675 | 10/12；引用 6/8；标准和方程需修订 |
| `v3.md` | `01a05db8-b327-7c0f-8eb4-a84f69c4a677` | `contest-qwen/qwen3-max` | 18 | 66659 | 329728 | 5108 | 修复 break-even 主体与来源 |
| `review-v3.md` | `01a05dbc-f9a3-7ec0-86e3-ab6f2547786f` | `contest-qwen/qwen3.7-max` | 18 | 124439 | 574464 | 20427 | 10/12；发现 Zhu 元数据、LCIA 单位和阈值死区 |
| `v4.md` | `01a05dc9-272c-7f4f-ad57-9d9c25e41001` | `contest-qwen/qwen3-max` | 21 | 93900 | 325248 | 5326 | 最终候选；修复全部残留项 |
| `review-v4.md` | `01a05dcd-f046-7178-bcae-0c5ff5cbca4f` | `contest-qwen/qwen3.7-max` | 21 | 98845 | 371712 | 11939 | `deliverable`；12/12；引用 9/9；无残留 finding |
| `v5.md` | `01a05e7a-63ca-7614-a67d-c5d8b17e8d19` | `contest-qwen/qwen3-max` | 7 | 42199 | 91264 | 4279 | 来源元数据投影；科学内容不变 |
| `review-v5.md` | `01a05e7d-ecea-7ccf-b741-6424ed98200b` | `contest-qwen/qwen3.7-max` | 16 | 263944 | 709632 | 18280 | `deliverable`；12/12；来源 9/9；无科学漂移 |
| `v6.md` | `01a05eb5-adbe-7342-a986-848354ebad32` | `contest-qwen/qwen3-max` | 15 | 63773 | 261760 | 5377 | 修正 ReCiPe 2016 报告定位与 Geyer 9% 分母 |
| `review-v6.md` | `01a05eb9-2dea-777b-9ed5-3b663f2538f8` | `contest-qwen/qwen3.7-max` | 11 | 107393 | 291456 | 10305 | `deliverable`；12/12；来源 9/9；报告与论文不再混用 |
| `review-v7.md` | `01a05ed8-ded8-7e65-b17a-064d1458c1e7` | `contest-qwen/qwen3.7-max` | 21 | 161868 | 726528 | 15414 | `deliverable`；12/12；PMID28776036/PMC5517107；角色边界闭合 |
| `receipt-v7.md` | `01a05ef6-9865-7360-9bff-b27cd32511a0` | `contest-qwen/qwen3-max` | 11 | 65524 | 188928 | 1707 | `deliverable`；真实 auditor UUIDv7；复核 PMC5517107 与 review-v7 |
| `review-v8.md` | `01a05f3f-f603-77e3-9e19-f6380fad6206` | `custom/gpt-5.6-terra` | 12 | 88330 | 777216 | 19169 | `deliverable`；12/12；来源 9/9；补齐来源元数据并移除自我指涉 |
| `receipt-v8.md` | `01a05f4a-b3ea-7e61-ad54-860b691135bb` | `custom/gpt-5.6-terra` | 9 | 27159 | 294656 | 8663 | `deliverable`；独立复核 v6/review-v8、9/9 来源与文件哈希 |
| `v7.md` | `01a05f67-6543-73c9-86bd-35777541fcc7` | `contest-qwen/qwen3-max` | 7 | 35542 | 61440 | 4241 | 移除自我指涉与正文 raw URL 重复；科学内容与 v6 一致 |
| `review-v9.md` | `01a05f71-6072-7353-82ff-497b3534eeca` | `custom/gpt-5.6-terra` | 33 | 107601 | 2068560 | 18710 | `deliverable`；12/12；来源 9/9；独立核验三路线与 LCA 边界 |
| `receipt-v9.md` | `01a05f7d-eb51-7c12-aa95-d10fe3f54fc0` | `custom/gpt-5.6-terra` | 7 | 37292 | 164535 | 8586 | `deliverable`；独立复核 v7/review-v9、来源、哈希与执行边界 |
失败的 `gpt-5.6-sol` reviewer Session 未生成内容且未被覆盖；全新 `qwen3.7-max` Session 完成 V1 评审。模型切换单独披露，不把改进只归因于 Workflow。
## 结果
V1 把不可替代的碳酸饮料材料体系放在同一比较中。V2 改为 1,000 次 750 mL 冷食外带容器服务，比较 rPET、工业堆肥 PLA/PHA 和可复用 PP；后续评审修复错用标准、来源元数据、ReCiPe 单位和复用 break-even 方程。最终模型 `N_eff=(1-r^D)/(1-r)`，逐影响类别比较 `P/N_eff+W+T+rL` 与单次方案，所有阈值均为待批准设计参数。
## 终态
`waiting_human`。研究计划已通过独立评审；继续需要实验室性能测试、实际回收率和洗涤数据、当地基础设施信息、LCA 执行及利益相关方阈值批准。
## 文件哈希
| 文件 | SHA-256 |
|---|---|
| `v1.md` | `c440b6b0ccea8c8ef2c1a3247fc5a1eae4e6ce80300f9ce941fa591b784ea1e2` |
| `review-v1.md` | `257b1a3f70acac4ad2b90b40634d12a605cef78d4b240dad554a37d9424f7e8a` |
| `v2.md` | `02ee4f585c6b7f8281e3c9608a5697f3e4956db11c7100ac81ffe7cd920b9507` |
| `review-v2.md` | `fbb3d6c7e91e8a7cf06105816fd3c3fe649f839b325041003ebb99560c3d3ba7` |
| `v3.md` | `f47920cacf87f45578c4d02bc19a0d3362e85cbea322a285d1bb0f817fa82ab8` |
| `review-v3.md` | `e25d6c2900d16ed19621d5eef1e88a9c66cb75596044b0ada6740e1c164b8a19` |
| `v4.md` | `2bf58071c11bd0b418ac1b8f02460815ef1aba5278eff3c35c7830799a539a78` |
| `review-v4.md` | `b5e1f5333e178bb2340eaacedfea90ae0cb72f4fc2866b88e4042d6fcb830aef` |
| `v5.md` | `c5de3df5b67652f81a73e0130a96c211f1bf9d391585a1677d966f37c5f0776a` |
| `review-v5.md` | `9ef61264edcd5fac6d5a5b505090613d4504fe05003f9227c50a6c732ab56ae9` |
| `v6.md` | `c26821f134516a9aab1932ed97805ad3f6c3b4a43301d8c2f2d91a3c3f80b84d` |
| `review-v6.md` | `a52e3bfc0e9f56ace3c22913f65dbacf978a5fda74faebe5b194b08c2c2db934` |
| `review-v7.md` | `b8f1655bc67d432c8834e55b8faa18ebfb315b17f798e0f6d95ca5fc9d887cb9` |
| `receipt-v7.md` | `556e4e677294107b928a39c3807698247d39748c6d7c2a637a0a90f8e31e5cbc` |
| `review-v8.md` | `8a1428715fa0f37ad27345082438e4a143d9347a7c3f5732c1c88755e7397a83` |
| `receipt-v8.md` | `8a155ba011ae89ca072f667024abb49b7a62b9747a3821d1b0e4f1c58f709723` |
| `v7.md` | `d5fa738aaf7d543da86adbfbc7912b5412032d33c460a9b3db32311e28772c4e` |
| `review-v9.md` | `ee75da959fd5307421f1c603672926450653871aaff708be57313dacf1c22a8e` |
| `receipt-v9.md` | `6aaa7fde51542638ed8a565148e2cda75b0fc3f777b24822dba10c6efc097bd3` |
## 未解决项
- 计划质量不等价于材料性能、LCA 或运营系统已被实证验证。
- 自定义性能阈值与基础设施阈值仍需研究团队和利益相关方批准。
- review-v6 的错误 PMC 与“planned 终态”措辞保留为被拒历史；review-v7 使用正确主记录并只给 reviewer verdict/建议。
- receipt-v7 使用真实 auditor/reviewer UUIDv7，复核 PMC5517107 与 12/12 verdict，不裁决 Project 终态。
