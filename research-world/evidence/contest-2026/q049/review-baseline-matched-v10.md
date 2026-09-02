---
project: q049
artifact: review-baseline-matched-v10
reviewer_session: 01a05f18-d17a-7910-ac13-60791233da3d
reviewer_session_provenance: runtime CODEX_SESSION_ID; user-confirmed Codex UUIDv7
author_session: 01a05f12-6e5d-7931-a8cb-585b1cc893ce
reviewed: [baseline-matched-v9.md]
prior_review: review-baseline-matched-v9.md
sources:
  - baseline-matched-v9.md
  - review-baseline-matched-v9.md
  - baseline-matched-v7.md
  - baseline-matched-v6.md
  - review-baseline-matched-v6.md
  - run.md
  - ../../../../readme.md
  - https://doi.org/10.1103/PhysRev.136.B1224
  - https://doi.org/10.1038/nature08096
  - https://doi.org/10.1111/j.1365-2966.2008.13022.x
  - https://doi.org/10.1051/0004-6361/201425300
verdict: deliverable
---
# q049 Baseline Matched V10 Independent Review
## Scope And Prior Blocker
- Reviewed `baseline-matched-v9.md` against the sole blocker in `review-baseline-matched-v9.md`: the Mercury-Sun result needed both omitted inputs and their provenance.
- V9 closes it: I1 is limited to the displayed Earth inputs; I2 explicitly records `M_mercury = 3.3011e23 kg` and `a_mercury = 5.7909e10 m` as adopted unchanged from the prior review. It no longer attributes either value to V7/I1.
## Independent Calculations
| Check | Inputs, units, formula, and independent result | V9 |
|---|---|---|
| Earth-Sun Peters | `G=6.67430e-11 m^3 kg^-1 s^-2`, `c=299792458 m s^-1`, `m1=1.9885e30 kg`, `m2=5.972e24 kg`, `a=1.496e11 m`, `1 Julian yr=31557600 s`; `t=(5/256)(c^5/G^3)(a^4/(m1*m2*(m1+m2)))`; `3.374197216379e30 s = 1.069218576945e23 yr`. | match |
| Mercury-Sun Peters | Shared `G`, `c`, `m1`, and year conversion above; `m2=3.3011e23 kg`, `a=5.7909e10 m`; same formula; `1.370536799260e30 s = 4.342969044731e22 yr`. | match |
| Conditional solar-wind check | `(1e-14 M_sun/yr)(5e9 yr)=5e-5 M_sun`; for adiabatic mass loss, `Delta a/a` is approximately `+5e-5 = +0.005000%`. | match |
The SI dimensions reduce to seconds: `(c^5/G^3)a^4/(m1*m2*(m1+m2))` has unit `s`. The Julian-year conversion is stated as an adopted display conversion, not a source attribution.
## Primary Source Audit
| Category | Primary source | Result |
|---|---|---|
| Gravitational radiation | S1, Peters 1964 | APS identifies the paper and its integration of semimajor-axis and eccentricity decay for bound two-point-mass orbits; the circular Peters calculation is in scope. |
| Solar-system dynamics | S2, Laskar and Gastineau 2009 | Nature reports `2,501` Solar-System integrations over `5 Gyr`; one per cent give a large Mercury-eccentricity increase. V9 confines the claim to that multi-body result, not gravitational-wave decay. |
| Solar evolution | S3, Schroder and Connon Smith 2008 | The MNRAS model gives the RGB tip at `7.59 Gyr` from now, mass loss, and potential orbital expansion inversely proportional to remaining solar mass. |
| Stellar wind | S4, Johnstone et al. 2015 | The A&A record gives a solar-wind mass-loss rate of `1.4e-14 M_sun/yr`; V9 correctly labels `1e-14 M_sun/yr` as a rounded conditional input rather than a five-gigayear forecast. |
## Evidence Boundaries
- `Executed` is limited to the two formula recalculations and the stipulated conditional arithmetic. `Planned` correctly excludes N-body, tide, solar-evolution, and matched-protocol reruns; no simulated result is represented as executed.
- V9 remains a new `benchmark_candidate`. It does not replace or re-freeze `baseline-matched-v6.md` and `review-baseline-matched-v6.md`.
- No Project terminal is decided here. `run.md` remains the only Project-terminal authority. V9's absence from `run.md` and the absence of a receipt before submission are not Artifact blockers.
## Verdict
`DELIVERABLE`: the prior review's only blocker is closed, all Earth and Mercury inputs, units, formula, seconds-to-years outputs, and the conditional `0.005000%` result reproduce exactly; the four primary-source bindings and all stated authority boundaries pass.
RESULT: DELIVERABLE
