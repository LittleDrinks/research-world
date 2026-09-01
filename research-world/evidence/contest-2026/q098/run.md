---
project: q098
protocol: contest-research-workflow-2026-09-01
status: waiting_human
final: v6.md
final_review: review-v6.md
---
# q098 运行记录
## 问题
Why do we need sleep?
## 版本与评审
| 产物 | Pi Session id | 模型 | 调用 | 非缓存输入 token | 缓存读取 token | 输出 token | 结果 |
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
失败的 `gpt-5.6-sol` reviewer Session 未生成内容且未被覆盖；全新 `qwen3.7-max` Session 完成 V1 评审。模型切换单独披露，不把改进只归因于 Workflow。
## 结果
V1 已覆盖突触稳态、类淋巴和免疫代谢三方向，但混淆疫苗研究并让观察性设计承担因果结论。V2 的修订又用不相关论文支撑 HOMA-IR 效应和方差。最终版改为 120 名完成者的前瞻性 precision pilot，以基线 14 天腕动计睡眠预测 6 个月 HOMA-IR；Fisher-z 只作为粗相关精度基准，不冒充调整模型功效，三方向证据、局限和可区分预测均保留。
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
## 审计说明
- review-v2/review-v3 将工具重复展示误判为文件重复；编排器以标题和终态计数核验每版均只有一份正文，review-v5 通过 diff 再确认。
- Matthews 2012 的青少年横断面估计只作背景，不用于成人队列样本量。
