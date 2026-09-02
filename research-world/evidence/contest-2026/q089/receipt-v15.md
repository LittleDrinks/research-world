---
project: q089
role: independent-terminal-chain-audit
auditor_session: "01a06039-db7e-7833-a8a1-4610dbd5c7f4"
auditor_model: "custom/gpt-5.6-terra"
audited:
  final:
    path: research-world/evidence/contest-2026/q089/v11.md
    sha256: 1a535a2056ed9ac14589e00d60245b38561590f3d83238f9846dc200fea8b33f
    author_session: "01a05ff8-25bc-7a38-a81e-397f265f99b4"
    author_model: "contest-qwen/qwen3-max"
    initial_model_selection: "contest-qwen/qwen3-coder-plus"
    calls: 10
    uncached_input_tokens: 58452
    cached_input_tokens: 82304
    output_tokens: 4626
    raw_write_sha256: 1a535a2056ed9ac14589e00d60245b38561590f3d83238f9846dc200fea8b33f
  review:
    path: research-world/evidence/contest-2026/q089/review-v14.md
    sha256: 046ca460660309a60cd005a1e4fc3ad5307a3ba567902f83a49ba00feb23037d
    reviewer_session: "01a05ffb-52c2-7492-a5ab-67d83184c40e"
    reviewer_model: "custom/gpt-5.6-terra"
    calls: 15
    raw_input_tokens: 682890
    uncached_input_tokens: 53898
    cached_input_tokens: 628992
    output_tokens: 12216
    reasoning_output_tokens: 7120
    raw_reconstructed_sha256: 046ca460660309a60cd005a1e4fc3ad5307a3ba567902f83a49ba00feb23037d
run_snapshot:
  path: research-world/evidence/contest-2026/q089/run.md
  sha256: a2b7fd53b86fabcda91d0cbfadcf682a7f5d3769d0986f9cafc6894ade3a7c6c
  status: completed
  final: v11.md
  final_review: review-v14.md
  final_receipt: receipt-v15.md
sources:
  - role: canonical-question
    path: docs/questions.json
    selector: id=89
  - role: canonical-project
    path: research-world/projects/q089/project.json
  - role: candidate-frontmatter
    path: research-world/evidence/contest-2026/q089/v11.md
    source_ids: "S1,S2,S3,S4,S5,S6,S7,S8,S9"
  - role: review-frontmatter
    path: research-world/evidence/contest-2026/q089/review-v14.md
  - role: author-session-jsonl
    path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-09-02T02-34-53-244Z_01a05ff8-25bc-7a38-a81e-397f265f99b4.jsonl
    sha256: c230262efcd6f6d1581e51e1015ffe3df35f9871e838ed2875ffb6e34a07aa9f
  - role: reviewer-session-jsonl
    path: /home/q2635/.codex/sessions/2026/09/02/rollout-2026-09-02T10-38-21-01a05ffb-52c2-7492-a5ab-67d83184c40e.jsonl
    sha256: 44b2d04886e8932d90f25b24130763a8f7e9d39fa33a87a6a0bc56d0a2db255d
  - role: official-s9-publisher
    url: https://www.longi.com/en/news/isfh-hibc-conversion-efficiency/
    page_date: "2025-04-14"
    announcement_date: "2025-04-11"
---
# q089 terminal-chain audit
- Current run pointer names `receipt-v15.md`; preserved `receipt-v14.md` observed the pre-promotion chain.
- `run.md` alone records Project `status: completed` and the `v11.md`/`review-v14.md` terminal pair; neither Artifact carries a Project status.
- Pi raw write bytes equal the current final hash; all ten usage-bearing author calls are qwen3-max after an initial qwen3-coder-plus selection. Codex raw file-change reconstruction equals the current review hash; its declared session, model, calls, and token metrics match raw records.
- Canonical question `id=89` matches the q089 Project projection. Candidate frontmatter contains complete S1-S9 identifiers; all seven local review-source paths resolve. The live S9 publisher page gives `2025.4.14`, an April 11 announcement, 27.81% HIBC, and ISFH attribution; an original ISFH certificate remains a stated residual risk.
- Review frontmatter verdict and terminal result both say deliverable; six rubric dimensions are 2/2 for 12/12. TPV simulation, R_sub sweep, and system extrapolation remain planned, with no research execution claimed.
RESULT: DELIVERABLE
