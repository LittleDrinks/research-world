---
project: q098
protocol: contest-research-workflow-2026-09-01
status: waiting_human
final: v12.md
final_review: review-v13.md
final_receipt: receipt-v16.md
---
# q098 运行记录
## 问题
Why do we need sleep?
## 版本与评审
| 产物 | Agent Session id | 模型 | 调用 | 非缓存输入 token | 缓存读取 token | 输出 token | 结果 |
|---|---|---|---:|---:|---:|---:|---|
| `v1.md` | `01a05d99-7ab0-7442-9075-78446a6555e4` | `contest-qwen/qwen3-max` | 21 | 482525 | 503808 | 5569 | 7/12；因果过度、疫苗事实和样本量错误 |
| 无产物 | `01a05da0-e5f9-7f08-b6a5-b254bd0cd50c` | `contest-qwen/gpt-5.6-sol` | 1 | 0 | 0 | 0 | `failed`；无 assistant 内容或评审文件 |
| `review-v1.md` | `01a05da5-4bf9-747b-b6d9-215bdbcbb9ce` | `contest-qwen/qwen3.7-max` | 20 | 126634 | 464640 | 16192 | fallback reviewer；7/12；断言级引用 73% |
| `v2.md` | `01a05dad-2cec-7b69-92cc-4347173fddef` | `contest-qwen/qwen3-max` | 19 | 69945 | 291200 | 5875 | 修复因果和疫苗；引入两条定量错引 |
| `review-v2.md` | `01a05db2-1d60-71e9-a62c-e09af5e5a377` | `contest-qwen/qwen3.7-max` | 32 | 220443 | 1153152 | 24989 | 8/12；样本量依据失效 |
| `v3.md` | `01a05dbe-9a33-7f76-9475-8716b9e4ddbf` | `contest-qwen/qwen3-max` | 29 | 155355 | 828544 | 6029 | 改为无虚构效应量的 precision pilot |
| `review-v3.md` | `01a05dc3-79a0-7f29-a1b2-54d2c48ac6e4` | `contest-qwen/qwen3.7-max` | 13 | 133121 | 451968 | 16146 | 9/12；发现 Xie 错述及纳排缺口 |
| `v4.md` | `01a05dcd-e210-746d-a131-eb69a059a937` | `contest-qwen/qwen3-max` | 19 | 165842 | 301440 | 5807 | 修复六项缺陷；8/8 引用 |
| `review-v4.md` | `01a05dd1-c18c-7e6e-a583-f2bc4b1af877` | `contest-qwen/qwen3.7-max` | 21 | 126608 | 489984 | 12117 | 11/12；两项 Low 内部一致性问题 |
| `v5.md` | `01a05dd6-fce5-7b29-81ec-41c7ecc9e82b` | `contest-qwen/qwen3-max` | 7 | 52105 | 46080 | 4663 | 最终候选；最小修订 |
| `review-v5.md` | `01a05dd9-b644-7462-88e2-04971a2295e2` | `contest-qwen/qwen3.7-max` | 21 | 93233 | 346368 | 10699 | `deliverable`；12/12；引用 8/8；无残留 finding |
| `v6.md` | `01a05e01-c0a6-78f9-bac2-8ac56832cd4f` | `contest-qwen/qwen3-max` | 12 | 64850 | 225408 | 4734 | 收口为协议终态 `waiting_human` |
| `review-v6.md` | `01a05e04-9b92-7d94-bc88-0e6b15604e0e` | `contest-qwen/qwen3.7-max` | 22 | 168038 | 599808 | 13300 | `deliverable`；12/12；引用 8/8 沿用且无科学回退 |
| `receipt-v6.md` | `01a05e40-d8b3-7b36-9df9-d393c3d7cae5` | `contest-qwen/qwen3.7-max` | 9 | 62793 | 257664 | 5172 | 终态审计回执；复算 reviewer 模型、Session、token 与 RESULT |
| `v7.md` | `01a05e7a-73cf-7d60-855d-9c4c92b40ccd` | `contest-qwen/qwen3-max` | 7 | 30335 | 107264 | 5061 | 来源元数据投影；科学内容不变 |
| `review-v7.md` | `01a05e7d-fc50-7f02-a114-051098f7d274` | `contest-qwen/qwen3.7-max` | 21 | 168795 | 1039104 | 15833 | `deliverable`；12/12；来源 8/8；无科学漂移 |
| `v8.md` | `01a05eb5-adce-7ecb-b63d-0f0daae487df` | `contest-qwen/qwen3-max` | 18 | 49173 | 444032 | 6094 | 修正 S5 作者与 S7/S8 错配 DOI |
| `review-v8.md` | `01a05eb9-2de5-73c8-b99d-977f4b97dede` | `contest-qwen/qwen3.7-max` | 31 | 280519 | 1706496 | 22147 | `deliverable`；12/12；发现 S3 继承页码错误 |
| `v9.md` | `01a05ec1-53ee-77ff-805e-3947e3934067` | `contest-qwen/qwen3-max` | 4 | 25509 | 45952 | 4675 | 单点修正 S3 页码为 628-631 |
| `review-v9.md` | `01a05ec2-ed31-7d94-b162-eff2abc39cf8` | `contest-qwen/qwen3.7-max` | 10 | 76539 | 274560 | 7482 | `deliverable`；12/12；来源 8/8；零 open findings |
| `v10.md` | `01a05ed8-dedd-7933-b0cc-3b23e3065aee` | `contest-qwen/qwen3-max` | 11 | 31867 | 171264 | 5431 | 补全 S5 权威题名的 Brief communication 前缀 |
| `review-v10.md` | `01a05edc-80ec-717a-a4d2-81b799ea5e7a` | `contest-qwen/qwen3.7-max` | 17 | 87011 | 523776 | 10890 | `deliverable`；12/12；来源 8/8；真实 reviewer UUID |
| `receipt-v10.md` | `01a05ef6-9878-7507-ae77-c5e8dc01cac6` | `contest-qwen/qwen3-max` | 10 | 42537 | 188288 | 2269 | 回执漏列 review-v10 审计对象；保留并重跑 |
| `receipt-v11.md` | `01a05ef8-958d-7e07-8a94-c5d2d687be22` | `contest-qwen/qwen3-max` | 7 | 26870 | 90624 | 1349 | 回执错误自造 UUIDv4；保留并由 v12 取代 |
| `receipt-v12.md` | `01a05efa-7498-7d30-bc41-cffd0ba81d92` | `custom/gpt-5.6-terra` | 13 | 59204 | 526080 | 11963 | `deliverable`；真实运行态 auditor UUIDv7；审计 v10/review-v10 |
| `review-v11.md` | `01a05f3f-f612-72e0-a196-8bb2854bf37d` | `custom/gpt-5.6-terra` | 7 | 46621 | 293120 | 11631 | `deliverable`；12/12；来源 8/8；补齐来源 frontmatter |
| `receipt-v13.md` | `01a05f4a-b3f2-71f2-8682-856dc4c8fa28` | `custom/gpt-5.6-terra` | 8 | 23388 | 243712 | 7529 | `deliverable`；独立复核 v10/review-v11、8/8 来源与文件哈希 |
| `v11.md` | `01a05f99-1ced-70dc-a4cb-dbb743d95ca7` | `contest-qwen/qwen3-max` | 7 | 24317 | 71040 | 4532 | 紧凑排版与客观主语投影；科学内容与 v10 一致 |
| `review-v12.md` | `01a05fa3-b7cd-7951-9f16-30e482036cb3` | `custom/gpt-5.6-terra` | 21 | 94643 | 980795 | 19188 | `deliverable`；12/12；来源 8/8；补齐独立 reviewer 身份 |
| `receipt-v14.md` | `01a05fb1-0836-70c2-bdc3-226775469d44` | `custom/gpt-5.6-terra` | 11 | 36693 | 285224 | 7213 | `deliverable`；独立复核 v11/review-v12、哈希、格式与执行边界 |
| `v12.md` | `01a05fd4-8c03-7569-9af8-9f166cd18c40` | `contest-qwen/qwen3-max` | 5 | 30827 | 51328 | 4384 | 移除版本变更自我指涉；科学内容不变 |
| `review-v13.md` | `01a05fd9-1252-7f60-acf5-a779467d738c` | `custom/gpt-5.6-terra` | 20 | 67157 | 957440 | 26218 | `deliverable`；12/12；来源 8/8 |
| `receipt-v15.md` | `01a05fe5-4576-7ac3-8ab7-57401ad9249b` | `custom/gpt-5.6-terra` | 9 | 55322 | 269056 | 12689 | `deliverable`；独立复核 v12/review-v13、来源、哈希与执行边界 |
| `receipt-v16.md` | `01a06039-db99-7d41-913d-78044baea021` | `custom/gpt-5.6-terra` | 29 | 174310 | 2076715 | 37212 | `deliverable`；核验当前 run 指针、原始会话、来源与 planned 边界 |
失败的 `gpt-5.6-sol` reviewer Session 未生成内容且未被覆盖；全新 `qwen3.7-max` Session 完成 V1 评审。模型切换单独披露，不把改进只归因于 Workflow。
## 结果
V1 已覆盖突触稳态、类淋巴和免疫代谢三方向，但混淆疫苗研究并让观察性设计承担因果结论。V2 的修订又用不相关论文支撑 HOMA-IR 效应和方差。最终版改为 120 名完成者的前瞻性 precision pilot；V8 以 NCBI 修正 S5 作者和两条疫苗论文 DOI，V9 修正 S3 页码。Fisher-z 只作为粗相关精度基准，不冒充调整模型功效，三方向证据、局限和可区分预测均保留。
## 终态
`waiting_human`。研究计划已通过独立评审；继续需要 IRB、参与者知情同意、腕动计和实验室资源，观察性结果仍不能建立因果关系。
## 文件哈希
| 文件 | SHA-256 |
|---|---|
| `v1.md` | `ccf1f9ad34fff202cf0c95e4b25c3c3ca8d42f40bc4534e419bda6870ffd223e` |
| `review-v1.md` | `bba674fabf19d28c9aa388c4585b35c7fb37273d47d3fef92b202a09cfc140c7` |
| `v2.md` | `50341e2bd07eece152070aff4ab658b5c615c134fad6cc0e60fd457af4e56806` |
| `review-v2.md` | `aac26ca524b6a05339e0b5c590bce06124ba960b7b3fb0e74aeab0194e4461b3` |
| `v3.md` | `1757fcb6ed5f85b7ec9f82770ac9c347911e226fc8933c506fd307be4f983536` |
| `review-v3.md` | `7331f7ba4e718b1f6157ca8432d0e8e9e6eb6a85bffc950c7ab598ee2d8be83d` |
| `v4.md` | `4e9b524cf6d26fb1834ea93eebeec8f0cfc8a15aeba8b7035bc0f1fc6e9eeed5` |
| `review-v4.md` | `818ef6f21884d810b0966a5df3ff11b775fe95051cc04fc1d9b5513f9a144cd8` |
| `v5.md` | `30d9d533299bb636a603dfc108c6783784448919bdc0f09a9228f5030b96cb6d` |
| `review-v5.md` | `d67f31b996bf14abb1b2a41a76d0f0e74dd7cdd8899665d45d5ee14bb92ea51c` |
| `v6.md` | `d28d61310c90fe9a9ec8506fae7229827a9d35081210ce9b7f55807003ebcb00` |
| `review-v6.md` | `d6b3dfa704089e9aef44d6f9aad2a8ddc9a29cb99fb9cde12eb15fb2a5fbabc3` |
| `receipt-v6.md` | `5031a70987184d4db06d0ea3e418b5e27275b19e3db0f72ce42f06408ad630fc` |
| `v7.md` | `dcd7ae30be8d1bebf3b69025141edfbb75d2585c2ea918be28b7453839ca2faf` |
| `review-v7.md` | `4bde0114d587eb675c9efaff15bcc327a18fa5f7fad708be3120a01b88846fe4` |
| `v8.md` | `e56b7e30297e4fb9642e4f97d0803665062980220c275cd5be45b0651dbb1916` |
| `review-v8.md` | `407319e10562c77cb93525efa9caddca9a97bcaf90779e8a5348f44e5486766a` |
| `v9.md` | `3c2c0c582abc502626be4e6fcbdabb309f82baa44338e88462c670e95b1498d4` |
| `review-v9.md` | `ab76206f2868783aa4ecf8987a737103cfce00d1c9729ebff017bb692090069a` |
| `v10.md` | `324a1a9c5eaffdd78c2f95a9294282df5d93d9630a5dfc14d9fa80e11fb92c1b` |
| `review-v10.md` | `d7089814bf81e341d9cb16271c907b52ac4512842864a251b7940b06cfa96dad` |
| `receipt-v10.md` | `5b36111570f2d19f4da6732697e7d85ee26759ce9f8994a6ba581aced4a28f06` |
| `receipt-v11.md` | `4d4d9985aeb715b973f9575d56e7b7d796f359de2157efd7c097471e89db90cd` |
| `receipt-v12.md` | `3f33cd8dba59317084fc5250b759a4b8508455573eff9d07e823240e28b2631d` |
| `review-v11.md` | `336b9f323781da08dbcfbdd1ee2b54e3347ea43ab10e3aa8d0a21cab985b65e5` |
| `receipt-v13.md` | `ff981a0f1690e1250bfaf1dc5e582ae20f2d83f5086d7b3301bdf96328ef71ab` |
| `v11.md` | `34f221f1dbea4a308b2c66e794c15a6fbaed20e20716ddc3588925b54e4b552a` |
| `review-v12.md` | `addc24514fa720383a80dc60d442fe56b32f4d33f2959583bfabccc80988c89d` |
| `receipt-v14.md` | `ea1baf9ead0cc64fb454f60e087694d7d557232a1604cb3e09f787eb8bc0bc22` |
| `v12.md` | `865aa07f50479ea59237887aaf4c5d594371f9638b82ae51766f7585aecc47ab` |
| `review-v13.md` | `4af25f861fd1016a6c4d11eb39ca9485f9ae30e072c75f021a9ae1eb0cd55364` |
| `receipt-v15.md` | `60a85b8d09f808cf9a55e10209fc9b02d51c17d6564ae8560a3fdaab231af14c` |
| `receipt-v16.md` | `12ffe0d70a860a4f35f40011e6141a17654ea3c78d063c61fea5b036f0f8cb9d` |
## 审计说明
- review-v2/review-v3 将工具重复展示误判为文件重复；编排器以标题和终态计数核验每版均只有一份正文，review-v5 通过 diff 再确认。
- Matthews 2012 的青少年横断面估计只作背景，不用于成人队列样本量。
- 旧 `receipt-v6.md` 只审计 V6，不作为 V7 最终回执。
- review-v7 漏检 S5 作者与 S7/S8 DOI 错配；V8/V9 与独立 review 保留完整修复链。
- receipt-v10 漏列 review-v10 审计对象，receipt-v11 自造 UUIDv4；两次尝试均保留，当前 receipt-v12 使用真实运行态 auditor UUIDv7。
