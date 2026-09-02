---
reviewer_session: 01a05efa-7470-7f50-8875-ad2f272de28b
author_session: 01a05ef6-9884-7843-86b2-20c6cab09c33
reviewed: [baseline-matched-v7.md]
prior_review: review-baseline-matched-v7.md
supersedes: review-baseline-matched-v7.md
sources:
  - baseline-matched-v7.md
  - baseline-matched-v6.md
  - review-baseline-matched-v7.md
  - run.md
  - receipt-baseline-matched-v6.md
  - ../../../../readme.md
  - https://doi.org/10.1103/PhysRev.136.B1224
  - https://doi.org/10.1038/nature08096
  - https://solarsystem.nasa.gov/solar-system/sun/overview/
verdict: revise
---
# q049 Baseline Matched V8 Independent Review
## Scope
- Runtime-confirmed reviewer Session: `CODEX_SESSION_ID=01a05efa-7470-7f50-8875-ad2f272de28b`; the UUIDv7 value above is copied from that runtime value.
- Audited only `baseline-matched-v7.md` as a benchmark artifact. `run.md` and the v6 receipt establish the preceding frozen comparison; they are not used to decide any Project terminal.
## Scientific Drift and Fresh Checks
- `diff` from v6 to v7 preserves the physical-proposition paragraphs. The changes are provenance and presentation: new frontmatter including three sources, `planned` wording, a renamed conclusion, and `RESULT: CANDIDATE`. Thus no new physical proposition was introduced, but v7 is not an identical artifact and its new source assertions need independent proof.
- Recomputing the displayed Peters circular-orbit expression with its listed Earth-Sun inputs gives `3.374197216e30 s = 1.069218577e23 yr`, supporting lines 27-49.
- The same expression with Mercury mass and semimajor axis gives `4.342969045e22 yr`; lines 59 and 121 should not describe this as `1e20 yr` order of magnitude. The broad conclusion that gravitational-wave decay is negligible remains supported.
- With the artifact's own solar-wind rate of `1e-14 M_sun/yr`, five billion years gives an adiabatic fractional orbital expansion of about `0.005%`, not the `0.1%` at line 90. No bound or changed rate is supplied to justify the larger figure.
## Source Audit
- `10.1103/PhysRev.136.B1224` resolves to P. C. Peters, *Gravitational Radiation and the Motion of Two Point Masses* (Physical Review, 1964); it is an appropriate source for the circular point-mass inspiral calculation.
- `10.1038/nature08096` resolves to J. Laskar and M. Gastineau, *Existence of collisional trajectories of Mercury, Mars and Venus with the Earth* (Nature, 2009); the bibliographic attribution is correct. The review does not treat DOI resolution alone as evidence for every detailed simulation statement in lines 55-63.
- The cited NASA URL is live as a general Sun overview, but the extracted content supplies no traceable support for the five-billion-year red-giant timeline, radius, engulfment, or mass-loss assertions in lines 67-82. The claimed ESA and peer-reviewed support is not listed.
- Lines 89-113 add quantitative tidal, solar-wind, stellar-encounter, and comparison-system claims without a source binding. Three valid links therefore do not establish the prior review's claim that all major claims are sourced.
## Benchmark Fairness
- The frozen matched comparison names `baseline-matched-v6.md`, its review, and its receipt in `run.md`. It records v6 as a 4708-character, one-write artifact from Session `01a05e45-a299-7a05-b089-d721ecc89764`; the receipt verifies that v6 hash and write only.
- V7 has a different hash and 5014 characters. It adds three explicit sources where the frozen comparison reports zero, changes the result designation, and is absent from the recorded matched baseline, review, receipt, hash table, and Git index.
- No execution record or receipt ties the v7 content to the declared author Session or re-freezes model, search permissions, calls, tokens, single-write behavior, and output budget. It is therefore an unproven derivative, not a fair replacement for the matched direct attempt.
## Artifact Verdict
`REVISE`: retain v6 as the frozen benchmark. A new sourced baseline requires its own attributable execution and receipt; its source-to-claim coverage and the two quantitative statements above must be corrected before a new matched comparison can be reviewed.
RESULT: REVISE
