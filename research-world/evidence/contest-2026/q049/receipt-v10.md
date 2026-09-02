project: q049
artifact: receipt-v10
role: independent-terminal-audit
auditor_session: 01a06149-17bc-7111-9df3-ff2c80079154
runtime_model: custom/gpt-5.6-terra
audited_files:
  - AGENTS.md
  - readme.md
  - research-world/projects/q049/project.json
  - research-world/evidence/contest-2026/deep-cases.md
  - research-world/evidence/contest-2026/q049/run.md
  - research-world/evidence/contest-2026/q049/v8.md
  - research-world/evidence/contest-2026/q049/review-v8.md
  - research-world/evidence/contest-2026/q049/receipt-v9.md
  - research-world/evidence/contest-2026/q049/v1.md
  - /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-08-31T20-56-29-279Z_01a0599b-f95f-74e2-b861-aba3c5fd1fe6.jsonl
  - research-world/evidence/contest-2026/q049/baseline-matched-v2.md
  - research-world/evidence/contest-2026/q049/review-baseline-budget-v2.md
  - research-world/evidence/contest-2026/q049/baseline-matched-v6.md
  - research-world/evidence/contest-2026/q049/review-baseline-matched-v6.md
  - research-world/evidence/contest-2026/q049/baseline-matched-v9.md
  - research-world/evidence/contest-2026/q049/review-baseline-matched-v10.md
  - research-world/evidence/contest-2026/q049/receipt-baseline-matched-v9.md
sources:
  - id: canonical-project
    path: research-world/projects/q049/project.json
    sha256: bdcfc4daa76d5472bf9f68c334269e64d455c9891ceaae69735963c86f09b1bf
  - id: current-run
    path: research-world/evidence/contest-2026/q049/run.md
    sha256: 7027d3725124679f289c4318258ad711ca9b277918a0e33b0565c7b861f64151
  - id: final
    path: research-world/evidence/contest-2026/q049/v8.md
    sha256: e0a6d83a65ae80f11c585f2b0c63053923b9e60b1fc8240cfb0f6627ebe65643
  - id: final-review
    path: research-world/evidence/contest-2026/q049/review-v8.md
    sha256: 987bc5c279da17f1bf157561bfbe6f62650bf97377206f4364810ee8351779e4
  - id: frozen-v1
    path: research-world/evidence/contest-2026/q049/v1.md
    sha256: 74e43718d54c346a857f763ce1b3a9fbbac53937dc944a36b1007427306bcce5
  - id: v1-original-pi-jsonl
    path: /home/q2635/.pi/agent/sessions/--home-q2635-wsl-workspace-ai4sci-worktrees-issue-249--/2026-08-31T20-56-29-279Z_01a0599b-f95f-74e2-b861-aba3c5fd1fe6.jsonl
    sha256: 91e124e8679eef4513563de60941688643447042ca37a1cccb96fd83aad4fc83
  - id: compute-control
    path: research-world/evidence/contest-2026/q049/baseline-matched-v2.md
    sha256: add15e78cdeeb775a65b5df9cfe7afc5dd512c4acaa09a5025bad750cb249e1b
  - id: length-control
    path: research-world/evidence/contest-2026/q049/baseline-matched-v6.md
    sha256: 7f13d8dd0a682aa470fcffaa1098f8a140cc2d43006035aecb3ab4122cb42d1b
verification:
  v1_original_write:
    pi_session: 01a0599b-f95f-74e2-b861-aba3c5fd1fe6
    writes_to_v1: 1
    original_bytes: 10515
    original_chars: 4970
    original_sha256: 74e43718d54c346a857f763ce1b3a9fbbac53937dc944a36b1007427306bcce5
    disk_sha256: 74e43718d54c346a857f763ce1b3a9fbbac53937dc944a36b1007427306bcce5
    bytes_equal: true
  final_review:
    reviewer_session: 01a05fd9-122e-7bc1-ab3c-513690287236
    verdict: deliverable
    rubric: "12/12"
    dimension_scores: [2, 2, 2, 2, 2, 2]
    final_sources: [S1, S2, S3, S4, S5, S6]
    final_source_count: "6/6"
  terminal_ownership:
    canonical_authority: run.md frontmatter.status
    status: completed
    final: v8.md
    final_review: review-v8.md
    canonical_authority_pass: true
  planned_executed_boundary:
    planned: [N-body integration, relativity, solar-mass-loss, tides, Monte-Carlo]
    executed: Peters Earth-Sun calculation only
    output_sha256: 7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361
    pass: true
  current_run:
    pointers_resolved: "8/8"
    hash_ledger_rows: 46
    hash_ledger_matches: "46/46"
  controls:
    workflow_v1:
      model: contest-qwen/qwen3-max
      calls: 25
      noncached_input_tokens: 98844
      cache_read_tokens: 373120
      output_tokens: 4567
      chars: 4970
      anysearch_searches: "5/5 successful"
      repository_writes: 1
    compute_near_control:
      artifact: baseline-matched-v2.md
      pi_session: 01a05e0b-4ecc-7866-b6fa-51a5e78ebcbf
      raw_write_equals_disk: true
      calls: 21
      noncached_input_tokens: 113326
      cache_read_tokens: 555520
      output_tokens: 3244
      chars: 2388
      call_delta_from_v1: "-16.00%"
      noncached_input_delta_from_v1: "+14.65137%"
      length_delta_from_v1: "-51.95171%"
      anysearch_searches: "5/5 successful"
      repository_writes: 1
    length_near_control:
      artifact: baseline-matched-v6.md
      pi_session: 01a05e45-a299-7a05-b089-d721ecc89764
      raw_write_equals_disk: true
      calls: 27
      noncached_input_tokens: 1182967
      cache_read_tokens: 393984
      output_tokens: 12902
      chars: 4708
      call_delta_from_v1: "+8.00%"
      noncached_input_multiple_of_v1: 11.96802
      length_delta_from_v1: "-5.27163%"
      repository_writes: 1
      temporary_writes: 5
      search_path: "7 Crossref curl calls; no anysearch"
    strict_double_match:
      same_model_direct_answer_records_checked: 11
      exists: false
      basis: "No raw direct-answer record has both calls=25 and noncached_input_tokens=98844 before length matching."
residual_risks:
  - "Frozen V1/V3/V4 and legacy direct-answer artifacts retain terminal-like prose or status: completed labels; readme.md defines them as Session self-descriptions, not Project-terminal authority."
  - "review-baseline-matched-v6.md retains reviewer_session: current and its obsolete V1 projection hash 788375.../4968 chars; raw V1 now proves 74e437.../4970 chars."
  - "receipt-v9.md records a historical run.md hash and pre-promotion v7 final pointer; this receipt audits the current v8 chain."
  - "No strictly compute-and-length-matched direct-answer control exists; compute and length conclusions remain separate near-control observations."
  - "This terminal audit counted and traced current source records; it did not refetch cited publications."
promotion:
  run_md_may_promote: true
  required_update: "Point final_receipt to receipt-v10.md and add its post-write SHA-256 to the run ledger."
verdict: deliverable
RESULT: DELIVERABLE
