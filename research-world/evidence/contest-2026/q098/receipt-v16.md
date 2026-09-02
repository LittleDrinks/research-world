---
project: q098
role: independent-terminal-chain-audit
auditor_session: 01a06039-db99-7d41-913d-78044baea021
auditor_model: custom/gpt-5.6-terra
audited:
  final: research-world/evidence/contest-2026/q098/v12.md
  final_review: research-world/evidence/contest-2026/q098/review-v13.md
run_snapshot:
  status: waiting_human
  final: v12.md
  final_review: review-v13.md
  final_receipt: receipt-v16.md
sources:
  - path: AGENTS.md
    role: worktree-rules
  - path: readme.md
    role: terminal-protocol
  - path: research-world/projects/q098/project.json
    role: canonical-project
  - path: docs/questions.json
    locator: id=98
  - path: research-world/evidence/contest-2026/q098/run.md
    role: terminal-record
  - path: research-world/evidence/contest-2026/q098/v11.md
    role: prior-candidate-source
  - path: research-world/evidence/contest-2026/q098/v12.md
    role: current-final
  - path: research-world/evidence/contest-2026/q098/review-v12.md
    role: prior-independent-review-source
  - path: research-world/evidence/contest-2026/q098/review-v13.md
    role: current-final-review
  - path: research-world/evidence/contest-2026/q098/receipt-v15.md
    role: preserved-pre-promotion-receipt
  - path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-09-02T01-56-00-131Z_01a05fd4-8c03-7569-9af8-9f166cd18c40.jsonl
    role: author-raw-session
  - path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-00-56-01a05fd9-1252-7f60-acf5-a779467d738c.jsonl
    role: reviewer-raw-session
---
# q098 终态链独立审计
当前 `run.md` 为唯一 Project 终态记录：`status: waiting_human`、`final: v12.md`、`final_review: review-v13.md`、`final_receipt: receipt-v16.md`；当前候选仅为 `revision_candidate`，当前评审仅有 reviewer verdict，均未声明 Project status。
本审计观察 CURRENT run 指针将 final_receipt 命名为 `receipt-v16.md`；保留的 `receipt-v15.md` 观察的是提升前 `v11.md`、`review-v12.md`、`receipt-v14.md` 链，未用于当前终态。
当前 SHA-256 与 `run.md` 记录一致：`v12.md` `865aa07f50479ea59237887aaf4c5d594371f9638b82ae51766f7585aecc47ab`；`review-v13.md` `4af25f861fd1016a6c4d11eb39ca9485f9ae30e072c75f021a9ae1eb0cd55364`。
作者 Pi JSONL 确认 `01a05fd4-8c03-7569-9af8-9f166cd18c40` 使用 `contest-qwen/qwen3-max`：5 calls、30,827 非缓存输入、51,328 缓存读取、4,384 输出 token；reviewer Codex JSONL 确认 `01a05fd9-1252-7f60-acf5-a779467d738c` 使用 `custom/gpt-5.6-terra`：20 calls、1,024,597 总输入减 957,440 缓存读取为 67,157 非缓存输入、26,218 输出 token；均与运行记录相符。
`review-v13.md` 的 `reviewed: v12.md`、`verdict: deliverable`、六项 2/2 合计 12/12 和末行 `RESULT: DELIVERABLE` 一致。候选登记 S1-S8，评审登记的 S2/S3/S6 DOI 均对应候选来源；原始 reviewer trace 记录 resolver 与 publisher 访问及 publisher 403，这一来源内容复核限制已保留为风险而非伪造通过。
候选只陈述招募、测量、分析、预注册和伦理的 planned 条件，未报告受试者、样本、检测或健康结果；文档生成会话不构成研究执行。`waiting_human` 仍由 `run.md` 独占，IRB、知情同意、腕动计和实验室资源仍为前置条件。
RESULT: DELIVERABLE
