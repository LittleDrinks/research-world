---
reviewer_session: "01a06168-79cc-74e2-915c-f621a2a5eef7"
runtime_model: "custom/gpt-5.6-terra"
snapshot:
  branch: "feat/249-deep-cases"
  head: "5ce53bd3ab507037c1ea58714293c83a47f362a6"
  state: "current dirty worktree"
reviewed_files:
  rules: "AGENTS.md"
  protocol: "readme.md"
  question_index: "docs/questions.json"
  aggregate: "research-world/evidence/contest-2026/deep-cases.md"
  q049: ["q049/run.md", "q049/v8.md", "q049/review-v8.md", "q049/receipt-v10.md", "q049/baseline-matched-v2.md", "q049/review-baseline-budget-v2.md", "q049/baseline-matched-v6.md", "q049/review-baseline-matched-v6.md"]
  q089: ["q089/run.md", "q089/v11.md", "q089/review-v14.md", "q089/receipt-v15.md"]
  q021: ["q021/run.md", "q021/v10.md", "q021/review-v12.md", "q021/receipt-v15.md"]
  q112: ["q112/run.md", "q112/v11.md", "q112/review-v13.md", "q112/receipt-v13.md"]
  q098: ["q098/run.md", "q098/v12.md", "q098/review-v13.md", "q098/receipt-v16.md"]
reviewed_sources:
  - "GitHub Issue #249 acceptance criteria via gh"
  - "docs/questions.json: 125 unique Q001-Q125 records; five case records"
  - "Pi and Codex raw session JSONL named by the five current receipt chains"
  - "five run ledgers: 183 unique UUIDv7 session records and 174 current-content SHA-256 entries"
verdict: "NO-GO"
---
## Five-case gate
| Case | V1/review/revision history | Project terminal owner | Score progression | Final-source denominator | Gate |
|---|---|---|---|---|---|
| q049 | Preserved | `run.md: completed`; final/review carry no Project status | 9/12 -> 12/12 | 6 declared, 6/6 reported | PASS |
| q089 | Preserved | `run.md: completed`; final/review carry no Project status | 10/12 -> 12/12 | 9 declared and used; 8/8 reported | FAIL |
| q021 | Preserved | `run.md: waiting_human`; final/review carry no Project status | 10/12 -> 12/12 | 8 declared, 8/8 reported | PASS |
| q112 | Preserved | `run.md: waiting_human`; final/review carry no Project status | 7/12 -> 12/12 | 9 declared, 9/9 reported | PASS |
| q098 | Preserved | `run.md: waiting_human`; final/review carry no Project status | 7/12 -> 12/12 | 8 declared, 8/8 reported | PASS |
- All five current pointer triples resolve. The 174 ledger SHA-256 values match current contents; their recomputed total is 2,903 calls, 17,958,561 non-cached input tokens, 96,843,452 cached-input tokens, and 2,039,537 output tokens. The 183 listed session identifiers are unique UUIDv7 values with the named raw records present.
- Candidate artifacts separate planned from executed work: q049 records only the Peters Earth-Sun calculation as executed; q089 TPV work and q021/q112/q098 research execution remain planned. `completed` denotes the document-chain terminal, not completed scientific execution.
- q089 `v11.md` and `receipt-v15.md` identify S1-S9, and `v11.md` uses S9 in its Direction evidence. `run.md` and `deep-cases.md` nevertheless report `8/8`; neither supplies a rule excluding S9. The reported denominator therefore cannot establish an exact citation pass.
## Benchmark gate — LIMITED
- q049 attempt 2 is a real compute-near direct response: the same canonical question and `qwen3-max`, five successful searches per side, one final write per side, 21/25 calls, and 113,326/98,844 non-cached input tokens. `review-baseline-budget-v2.md` correctly classifies it as eligible only for an approximate computation comparison.
- It is not a strict paired control: attempt 2 has 2,388/4,970 characters and 3,244/4,567 output tokens; attempt 6 has 4,708/4,970 characters and 27/25 calls but 1,182,967/98,844 non-cached input tokens. No direct response matches both compute and length.
- The direct answers lack explicit sources, Direction comparison, and research plan. V1-to-final improvement follows independent review, revision, and constrained calculation; it cannot be attributed solely to the workflow or generalized as a quality guarantee.
- `review-baseline-matched-v6.md` is preserved historical evidence, not a qualifying review: its `reviewer_session: current` and obsolete V1 projection are disclosed by the pointed `receipt-v10.md`. Its terminal-like language cannot support the benchmark gate.
## Scale protocol gate — PASS AS CONTROL SPECIFICATION
- The frozen Q001-Q125 protocol requires an independent Pi session per question, one transport retry, compact results, aggregate audit, and all four terminal states: `completed`, `partial`, `failed`, and `waiting_human`.
- Scientific insufficiency must remain `partial`; ethics, permission, facility, or domain thresholds must remain `waiting_human`; low-quality output must not be resampled into `completed`.
- This controls status selection and preserves failure evidence; it does not predict that all 125 outputs will be high quality.
## Residual risks
- Five heterogeneous cases cannot estimate Q001-Q125 quality, source availability, or domain-specific review failure rates.
- Publisher and primary-source access remain uneven: q089 lacks the original ISFH certificate and q098 retains a publisher-403 limitation.
- Historical terminal-like labels and the q049 legacy length review require their current receipt and aggregate qualifications to remain attached; neither is current Project-terminal authority or positive benchmark evidence.
- Receipt snapshots can predate post-promotion run-ledger updates; current-content hashes, not an earlier run snapshot hash, establish the present pointer chain.
## Current snapshot decision
The five-case evidence does not justify unblocking Q001-Q125. q089's unresolved nine-source versus `8/8` contradiction makes the aggregate citation gate non-auditable, independently of the limited q049 comparator and independently of any future output quality.
SCALE-UP: NO-GO
RESULT: REVISE
