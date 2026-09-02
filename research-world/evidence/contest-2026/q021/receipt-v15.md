---
project: q021
role: independent-terminal-chain-audit
auditor_session: 01a0610a-1966-7c11-b9d4-811aa17ba6bc
audited:
  final: v10.md
  final_sha256: 9f8aac874355fc952258c25a9a609c993b1b634131bdb5b7e04661a6ee810422
  final_review: review-v12.md
  final_review_sha256: 1eb41ae4cb22ffe8970abd2f8b77b4a222531763983e8d3a57a764a6fd89b14b
author:
  session: 01a05fd4-8beb-76f6-8686-a4d8cb510e49
  model: contest-qwen/qwen3-max
  calls: 3
  non_cached_input_tokens: 16155
  cached_input_tokens: 30848
  output_tokens: 5112
  raw_write_payload_sha256: 9f8aac874355fc952258c25a9a609c993b1b634131bdb5b7e04661a6ee810422
reviewer:
  session: 01a05fd9-123c-7ed3-9600-cd8e65992dc8
  model: custom/gpt-5.6-terra
  calls: 22
  non_cached_input_tokens: 120973
  cached_input_tokens: 1337856
  output_tokens: 23962
run_snapshot:
  path: research-world/evidence/contest-2026/q021/run.md
  sha256: be21bcca021942b384baa6757eb082b6e8b2976dc4ae84332407c942d48f2333
  status: waiting_human
  final: v10.md
  final_review: review-v12.md
  final_receipt: receipt-v15.md
sources:
  - path: research-world/projects/q021/project.json
    sha256: 156a032c409d0d7233f1c58e576efec98d7306a378706675021a38cb05c86656
    use: canonical Project
  - path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-09-02T01-56-00-107Z_01a05fd4-8beb-76f6-8686-a4d8cb510e49.jsonl
    sha256: c28c9f8b7ca96dc7e23e321d1132f484fa08689c0b500cbde31d52601ecf9e19
    use: exact author Pi session
  - path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-00-56-01a05fd9-123c-7ed3-9600-cd8e65992dc8.jsonl
    sha256: ba20cebfaf5c73cc6e2a008b5d55dc4929373229200f86c9dbd850bfe9bb961a
    use: exact reviewer Codex session
---
# Terminal-chain audit
- The canonical Project, `v10.md`, and `run.md` identify q021 and the antibiotic-resistance question consistently.
- The single raw author write targets `v10.md`; its 8,879-character payload and current 18,764-byte file are byte-identical with SHA-256 `9f8aac874355fc952258c25a9a609c993b1b634131bdb5b7e04661a6ee810422`, including final `RESULT: CANDIDATE`.
- `artifact_stage: revision_candidate` and the author-session candidate result classify the candidate only. `run.md` frontmatter alone records the Project terminal: `waiting_human`.
- The reviewer raw ledger resolves to 22 calls, 120973 non-cached input tokens, 1337856 cached input tokens, and 23962 output tokens. Its add-and-update review chain yields the current `review-v12.md` hash.
- `review-v12.md` declares `deliverable`, six two-point rubric rows totaling 12/12, and `RESULT: DELIVERABLE`; it lists six web sources whose normalized URLs occur in reviewer raw queries. `v10.md` has distinct S1-S8 entries.
- The planned boundary remains explicit: v10 is a planned revision candidate, IRB has not been submitted, and the review records no patient recruitment, randomization, testing, prescribing change, or outcome comparison as executed.
- Preserved `receipt-v14.md` recorded the earlier missing final candidate line. The restored bytes remove that provenance failure without changing the Project terminal.
RESULT: DELIVERABLE
