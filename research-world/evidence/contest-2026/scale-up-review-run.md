---
artifact: scale-up-review-provenance
case_ledger: deep-cases.md
selected_review: scale-up-review-v2.md
---
# 跨案例评审记录
| 产物 | Agent Session id | 模型 | 调用 | 非缓存输入 | 缓存读取 | 输出 | Artifact SHA-256 | Raw SHA-256 | 结论 |
|---|---|---|---:|---:|---:|---:|---|---|---|
| `scale-up-review.md` | `01a06168-79cc-74e2-915c-f621a2a5eef7` | `custom/gpt-5.6-terra` | 46 | 332495 | 4028274 | 48761 | `19528834f5665e09c0ca8e750f805072b741b895ffab28a41c12c880dc4cd35f` | `0a28abc19d439c9e2e910d111d762fbd3a4e2ede7bec760da2daa8ae1ff43d84` | `SCALE-UP: NO-GO`；q089 来源分母未闭合 |
| 无产物 | `01a062a6-7c2d-7f33-885a-85cbe262123b` | `custom/gpt-5.6-sol` | 7 | 61508 | 216887 | 4557 | — | `ff8b9e405aeb2f158a0cfb5096be846c83f03e7ac7aa78bd3230e9a105c7daeb` | 连续 3 次 502 后终止；不作科学裁决 |
| `scale-up-review-v2.md` | `session_1d146663-1e91-4917-9aa3-42f27d0c57de` | `kimi-code/k3-256k` | 48 | 122477 | 3885312 | 26596 | `065239009d96a59e428cd47977bd4fb0b10bfa3b79576f36bb184329c395d5c7` | `559e5ff8573f28ae47faeba21fc6ee3eff57b3248367282e50920936328fd88f` | `SCALE-UP: GO`；194 个 Session、183/183 文件哈希和五题终态通过 |
评审成本与五个 Project 的 3,144 次调用账本分列，不计入任何 Project；旧 NO-GO 与无产物重试均保留，最终放大判定由独立 Kimi 复审给出。
