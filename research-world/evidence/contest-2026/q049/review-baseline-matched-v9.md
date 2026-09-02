---
project: q049
artifact: review-baseline-matched-v9
reviewer_session: 01a05f0a-8087-7740-a531-1ab7ce5ac613
reviewer_session_provenance: user-confirmed running Codex UUIDv7
author_session: 01a05f02-1368-7963-be17-d9147c57a04b
reviewed: [baseline-matched-v8.md]
prior_review: review-baseline-matched-v8.md
sources:
  - baseline-matched-v8.md
  - baseline-matched-v7.md
  - review-baseline-matched-v8.md
  - ../../../../readme.md
  - https://doi.org/10.1103/PhysRev.136.B1224
  - https://doi.org/10.1038/nature08096
  - https://doi.org/10.1111/j.1365-2966.2008.13022.x
  - https://doi.org/10.1051/0004-6361/201425300
verdict: revise
---
# q049 Baseline Matched V9 Independent Review
## Prior REVISE Recheck
- Resolved: Earth-Sun is `1.069e23 yr`; Mercury-Sun is no longer stated as `1e20 yr`; the conditional solar-wind result is no longer `0.1%`.
- Resolved: S1-S4 replace the unsupported NASA, tidal, encounter, and comparison-system quantitative material.
- Retained boundary: V8 is a new candidate, not a replacement or re-freeze of matched V6, and makes no Project terminal determination.
## Independent Calculations
| Check | Independent result | V8 result |
|---|---:|---:|
| Earth-Sun Peters, V7 displayed inputs | `3.374197216379e30 s = 1.069218576945e23 yr` | match |
| Mercury-Sun Peters, `m=3.3011e23 kg`, `a=5.7909e10 m` | `1.370536799260e30 s = 4.342969044731e22 yr` | match |
| Conditional mass loss | `(1e-14)(5e9)=5e-5`; adiabatic outward `Delta a/a=+0.005000%` | match |
The Mercury number is arithmetically correct only after supplying the two parameters above. I1 names `baseline-matched-v7.md` as their displayed record, but V7 displays Earth-Sun inputs only; it does not record either Mercury value.
## Primary Source Audit
| Category | Source | Result |
|---|---|---|
| Gravitational radiation | S1, Peters 1964 | Primary APS record supports integrated two-point-mass orbital decay; the circular calculation is within that scope. |
| Solar-system dynamics | S2, Laskar and Gastineau 2009 | Primary Nature abstract supports `2,501` integrations over `5 Gyr` and `1%` with large Mercury eccentricity. V8 does not overstate that result as gravitational-wave decay. |
| Solar evolution | S3, Schroder and Connon Smith 2008 | Primary MNRAS record supports the `7.59 Gyr` RGB-tip model, giant-stage mass loss, and orbital expansion inverse to remaining solar mass. |
| Stellar wind | S4, Johnstone et al. 2015 | Primary A&A record supports the `1.4e-14 M_sun/yr` reference rate. V8 labels `1e-14` as a rounded conditional input, not a five-gigayear forecast. |
## Evidence and Authority Boundaries
- `planned` correctly excludes N-body, tide, solar-evolution, and matched-protocol reruns. No simulated result is represented as executed.
- V8's candidate status does not require inclusion in `run.md`, a receipt, or a re-freeze. Its Earth and conditional mass-loss calculations provide sufficient method and output for their stated checks; only the Mercury input record is incomplete.
- `RESULT: CANDIDATE` is an Artifact stage. The reviewer verdict below does not decide a Project terminal; `run.md` remains the only Project-terminal authority.
## Blocking Findings
1. **Major - false calculation-input provenance.** V8 says I1 contains displayed SI inputs for both Peters recalculations, but its only cited input record omits the Mercury mass and semimajor axis. Record both values and their source before calling the Mercury result reproducible.
## Verdict
`REVISE`: the scientific corrections, four primary-source bindings, candidate boundary, and Project-role boundary pass, but the Mercury calculation is not reproducible from the input record V8 claims to use.
RESULT: REVISE
