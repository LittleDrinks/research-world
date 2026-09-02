---
project: q021
role: independent-terminal-chain-audit
auditor_session: 01a06039-db62-7d21-b365-7a6b578832a2
auditor_model: custom/gpt-5.6-terra
audited:
  final: v10.md
  final_sha256: 172715a461245c8e8a47eb65d107193ef3c70f1373504472c0f4b296e4ebd347
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
    raw_final_sha256: 1eb41ae4cb22ffe8970abd2f8b77b4a222531763983e8d3a57a764a6fd89b14b
run_snapshot:
  path: research-world/evidence/contest-2026/q021/run.md
  sha256: 237c78f84ff35ee8a95ea1881f6e36279122b47753042d1c1a0f26fe26a5e9b2
  status: waiting_human
  final: v10.md
  final_review: review-v12.md
  final_receipt: receipt-v14.md
sources:
  - path: research-world/projects/q021/project.json
    sha256: 156a032c409d0d7233f1c58e576efec98d7306a378706675021a38cb05c86656
    use: canonical Project
  - path: docs/questions.json
    selector: id=21
    sha256: 577573a5e8a6f368cc229979123bac5504eae2a8bc2353d2753af84fe5e6d3e1
    use: canonical-question cross-check
  - path: research-world/evidence/contest-2026/q021/v9.md
    sha256: 542e39390419f067d9e6d2be117c861823ecc45d968fbaca9d29f0b3adf9a931
    use: review baseline
  - path: research-world/evidence/contest-2026/q021/review-v11.md
    sha256: 4c14e39c3a7e309809b06c62c179ad6bde58d37aae236c293bed4245061d5f4b
    use: prior independent assessment
  - path: research-world/evidence/contest-2026/q021/receipt-v13.md
    sha256: 17eb31d146eb2583c8786c3151bfa4f75b144f827196d67bb9b6641e0a7c527e
    use: preserved pre-promotion receipt
  - path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-09-02T01-56-00-107Z_01a05fd4-8beb-76f6-8686-a4d8cb510e49.jsonl
    sha256: c28c9f8b7ca96dc7e23e321d1132f484fa08689c0b500cbde31d52601ecf9e19
    use: exact author Pi session
  - path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-00-56-01a05fd9-123c-7ed3-9600-cd8e65992dc8.jsonl
    sha256: ba20cebfaf5c73cc6e2a008b5d55dc4929373229200f86c9dbd850bfe9bb961a
    use: exact reviewer Codex session
---
# Terminal-chain audit
- The current run snapshot has `waiting_human`, `v10.md`, `review-v12.md`, and `receipt-v14.md`; neither final artifact declares a terminal status, so `run.md` alone owns the Project terminal.
- Current final and review SHA-256 values match the digests recorded in `run.md`.
- The author Pi log has one `v10.md` write and three `contest-qwen/qwen3-max` completions with the recorded metrics. Its exact write payload contains a final `RESULT: CANDIDATE` line; current `v10.md` omits that line. Removing only that line reproduces the current bytes, but no later mutation of `v10.md` occurs in either declared author or reviewer raw log.
- The reviewer Codex log has 22 `custom/gpt-5.6-terra` token-ledger entries with the recorded totals. Its add-plus-update sequence reconstructs current `review-v12.md` exactly.
- Canonical Project and `docs/questions.json` id 21 match exactly. The candidate registry has eight distinct S1-S8 entries; review-local paths exist and its six source URLs match the reviewer raw queries after trailing-slash normalization.
- Six rubric rows total 12/12; review frontmatter `deliverable` agrees with `RESULT: DELIVERABLE`. Planned boundaries remain explicit; no research execution is claimed.
- This audit observes the CURRENT run pointer naming `receipt-v14.md`, unlike preserved `receipt-v13.md`, which observed the pre-promotion `v9.md`/`review-v11.md`/`receipt-v12.md` chain.
- The unlogged alteration between the only author write payload and current final prevents exact author-source integrity.
RESULT: REVISE
