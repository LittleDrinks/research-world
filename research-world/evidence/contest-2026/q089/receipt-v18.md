---
artifact: receipt-v18
role: independent-final-chain-auditor
case_id: q089
auditor_session: "01a0628a-8aca-74c0-9ad6-37c3c1584dfa"
auditor_model: "custom/gpt-5.6-sol"
audited:
  candidate: {artifact: "v14.md", sha256: "2171f8b03c2a3cc939d516b7a0ad7ec3b3d88c3566dd57aa59907b7a7aae5e22"}
  review: {artifact: "review-v18.md", sha256: "e12b136715a4dd68649b6a26aafaa053f673d7d3e757c0e49b911d565a823e04"}
verdict: deliverable
---
# q089 v14/review-v18 最终链回执
## 固定产物与机械门
- `v14.md` 第一次 `sha256sum` 与第二次 `openssl dgst -sha256` 均得 `2171f8b03c2a3cc939d516b7a0ad7ec3b3d88c3566dd57aa59907b7a7aae5e22`；末行精确为 `RESULT: CANDIDATE`；空行数为 0。
- `review-v18.md` 第一次 `sha256sum` 与第二次 `openssl dgst -sha256` 均得 `e12b136715a4dd68649b6a26aafaa053f673d7d3e757c0e49b911d565a823e04`；末行精确为 `RESULT: DELIVERABLE`；空行数为 0。
- `review-v18.md` 含 9 个 S1-S9 `PASS` 行，来源结论 9/9；六个 rubric 行均为 2/2，合计 12/12；High=0、Medium=0。
- `review-v18.md` 只记录 reviewer verdict；frontmatter 不含 `status`、`final`、`final_review` 或 `final_receipt`，不裁决 Project 终态。
## Author raw provenance
- Session `01a06244-6e81-77f3-a53f-4281ec7776f4` 的 raw 为 `/home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T21-17-27-01a06244-6e81-77f3-a53f-4281ec7776f4.jsonl`，SHA-256 为 `2aefecc95e514f59dbfdd4fc57d181ebd3c6312cc436f1afe1b50047bff7a608`。
- Raw `session_meta.id` 与 `v14.md` 的 `revision_session` 完全一致；raw `turn_context.model=gpt-5.6-sol` 与产物 `runtime_model` 完全一致，`session_meta.model_provider=custom` 记录运行提供方。
- 调用只计 `event_msg` 中的 `token_count`，共 17 个；最后一个 cumulative `total_token_usage` 为输入 932306、缓存 850495、输出 16928，故非缓存输入为 `932306-850495=81811`。
## Reviewer raw provenance
- Session `01a0625c-da1f-7dd3-9a0f-87f83c60e66b` 的 raw 为 `/home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T21-44-07-01a0625c-da1f-7dd3-9a0f-87f83c60e66b.jsonl`，SHA-256 为 `8ae7fd53bd875258883c8537ad5eaf275999b7af00e54b3cd467d7db90f0c828`。
- Raw `session_meta.id` 与 `review-v18.md` 的 `reviewer_session` 完全一致；`session_meta.model_provider=custom` 与 `turn_context.model=gpt-5.6-sol` 组合为 `custom/gpt-5.6-sol`，与产物 `runtime_model` 一致。
- 调用只计 `event_msg` 中的 `token_count`，共 36 个；最后一个 cumulative `total_token_usage` 为输入 3794415、缓存 3623013、输出 29005，故非缓存输入为 `3794415-3623013=171402`。
## Planned/executed 与 benchmark 边界
- `v14.md` 将 S1 PV 代理、TPV 基线、`R_sub` 消融、`F` 扫描、数值门、表格与图形全部标为 `planned`；`executed` 仅含 S1-S9 主张边界和适用范围回读，仿真、实验与系统外推均为 0。
- Reviewer 的 Python 3.12 标准库探针只验证公式与门的可执行性，不构成 v14 执行结果，不改写 planned/executed 边界。
- S3 的 tandem TPV、`41.1±1%`、钨发射体与实测 IV 只作外部 benchmark；不复现、不拟合、不进入单结主计算或正确性门，也不作为本案测得结果。
## 角色与 run 限制
- `run.md` 是唯一 Project 终态所有者。审计时其旧指针仍为 `final=v11.md`、`final_review=review-v14.md`、`final_receipt=receipt-v15.md`；编排器将在回执落盘后原子更新。
- 更新前的 `run.md` 不属于 v14/review-v18 最终链；未将其旧哈希列作或冒充最终 run 哈希。
RESULT: DELIVERABLE
