---
project: q112
role: independent-terminal-chain-audit
auditor_session: "01a06039-db8c-7080-8455-880f3334c38c"
auditor_model: custom/gpt-5.6-terra
audited:
  final:
    path: research-world/evidence/contest-2026/q112/v11.md
    sha256: d3d31ef832fecfe3a98b0165b3de00da710c57cb66b6508687e3b0c702cc2651
    author:
      session: "01a06002-67cb-7e94-87fd-bbb6fd661546"
      model: contest-qwen/qwen3-max
      metrics:
        calls: 9
        noncached_input_tokens: 65431
        cached_input_tokens: 54400
        total_input_tokens: 119831
        output_tokens: 4064
        total_tokens: 123895
  review:
    path: research-world/evidence/contest-2026/q112/review-v13.md
    sha256: 9e89852cbcf1ad0a1b3e47670384e4287cab5c068a42013b90dff278e13fc214
    reviewer:
      session: "01a06005-abc7-75f1-beeb-001ac619227e"
      model: custom/gpt-5.6-terra
      metrics:
        calls: 11
        noncached_input_tokens: 44030
        cached_input_tokens: 377088
        total_input_tokens: 421118
        output_tokens: 11290
        reasoning_output_tokens: 6834
        total_tokens: 432408
run_snapshot:
  path: research-world/evidence/contest-2026/q112/run.md
  sha256: 20487cf6e98cd437b519c92055119c215c94ad312f2f206f09dfbb1491339ac5
  status: waiting_human
  final: v11.md
  final_review: review-v13.md
  final_receipt: receipt-v13.md
sources:
  - id: C1
    type: canonical-project
    path: research-world/projects/q112/project.json
    sha256: 9b0e077ebe9a2be51f8fa3c7a2ffc128b0df776fbdf71070dd1de313192d28df
  - id: C2
    type: original-question-index
    path: docs/questions.json
    record: 112
    sha256: 577573a5e8a6f368cc229979123bac5504eae2a8bc2353d2753af84fe5e6d3e1
  - id: C3
    type: final-artifact
    path: research-world/evidence/contest-2026/q112/v11.md
    sha256: d3d31ef832fecfe3a98b0165b3de00da710c57cb66b6508687e3b0c702cc2651
  - id: C4
    type: final-review
    path: research-world/evidence/contest-2026/q112/review-v13.md
    sha256: 9e89852cbcf1ad0a1b3e47670384e4287cab5c068a42013b90dff278e13fc214
  - id: C5
    type: original-pi-session-jsonl
    path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-09-02T02-46-05-515Z_01a06002-67cb-7e94-87fd-bbb6fd661546.jsonl
    sha256: 8ea9fecc7fef5732e274623d628db71b45c60b9a985849c1fc7cc248c2574cf4
  - id: C6
    type: original-codex-session-jsonl
    path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-49-39-01a06005-abc7-75f1-beeb-001ac619227e.jsonl
    sha256: fe5f654c84d53c8976efaa28ab5d75995bc639466403915381b7e13b84e5eeca
  - id: C7
    type: preserved-prior-receipt
    path: research-world/evidence/contest-2026/q112/receipt-v12.md
    sha256: ced4c946845d90f4d3b778ffadd36c277effe1dfd7713efa3be8a0860ae7e2a5
  - id: C8
    type: preserved-prior-audit-jsonl
    path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-54-43-01a0600a-4da4-7033-b687-8139ab6ceada.jsonl
    sha256: ed0bc74de2721597da063a98e41af0ab78fedfd548677c1c9718f80978a8efc6
---
# q112 terminal chain
- The canonical Project question equals record 112 title plus full text.
- `v11.md` declares S1-S9 and every body source reference resolves to those IDs; `review-v13.md` pins the final hash, six 2/2 rubric scores, 12/12, and `RESULT: DELIVERABLE`.
- C5 recomputes the author identity and 9-call metrics; C6 recomputes the reviewer identity and 11-call metrics shown above. Their raw sessions write `v11.md` and `review-v13.md`, respectively.
- The CURRENT `run.md` snapshot names `receipt-v13.md`. Preserved `receipt-v12.md` and C8 observed the pre-promotion chain (`v8.md`, `review-v10.md`, `receipt-v10.md`).
- `run.md` alone holds the Project terminal `waiting_human`; final and review contain no Project `status`. `v11.md` declares no LCA, laboratory, pilot, or comparative execution.
RESULT: DELIVERABLE
