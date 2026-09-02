---
project: q049
artifact: baseline-matched-v9
artifact_stage: benchmark_candidate
author_session: 01a05f12-6e5d-7931-a8cb-585b1cc893ce
author_session_provenance: user-confirmed running Codex UUIDv7
supersedes: baseline-matched-v8.md
addresses_review: review-baseline-matched-v9.md
benchmark_provenance: new Codex Session; new benchmark candidate; not a replacement for the frozen matched-v6 comparison
primary_sources:
  - id: S1
    title: "Gravitational Radiation and the Motion of Two Point Masses"
    authors: "P. C. Peters"
    year: 1964
    doi: "10.1103/PhysRev.136.B1224"
    url: "https://doi.org/10.1103/PhysRev.136.B1224"
    supports: "Circular two-point-mass gravitational-radiation decay formula used for both inspiral recalculations."
  - id: S2
    title: "Existence of collisional trajectories of Mercury, Mars and Venus with the Earth"
    authors: "J. Laskar; M. Gastineau"
    year: 2009
    doi: "10.1038/nature08096"
    url: "https://doi.org/10.1038/nature08096"
    supports: "The authors' 5 Gyr, 2,501-orbit ensemble and its one-per-cent high-Mercury-eccentricity outcome."
  - id: S3
    title: "Distant future of the Sun and Earth revisited"
    authors: "K.-P. Schroder; Robert Connon Smith"
    year: 2008
    doi: "10.1111/j.1365-2966.2008.13022.x"
    url: "https://doi.org/10.1111/j.1365-2966.2008.13022.x"
    supports: "Peer-reviewed solar-evolution model with giant-stage mass loss and orbital expansion inverse to remaining solar mass."
  - id: S4
    title: "Stellar winds on the main-sequence"
    authors: "C. P. Johnstone; M. Gudel; T. Luftinger; G. Toth; I. Brott"
    year: 2015
    doi: "10.1051/0004-6361/201425300"
    url: "https://doi.org/10.1051/0004-6361/201425300"
    supports: "Peer-reviewed solar-wind reference rate of 1.4e-14 M_sun/yr; the stated 1e-14 M_sun/yr check is a rounded conditional calculation."
calculation_input_records:
  - id: I1
    source: "baseline-matched-v7.md, Executed Research / 1"
    supports: "Shared G, c, and M_sun values, plus the displayed Earth mass and semimajor axis."
    scope: "I1 does not display a Mercury mass or semimajor axis."
  - id: I2
    source: "review-baseline-matched-v9.md, Independent Calculations"
    supports: "The review's explicitly supplied Mercury mass and semimajor axis, adopted unchanged for the V9 Mercury-Sun calculation."
  - id: I3
    source: "adopted unit conversion"
    supports: "1 Julian year = 31,557,600 s, used only to display seconds as years."
---
# q049 Baseline Matched V9
## Artifact Boundary
V9 is a new benchmark candidate from the user-confirmed running author Session above. It supersedes `baseline-matched-v8.md`; it does not replace or re-freeze the frozen matched-v6 comparison and makes no Project terminal determination.
## Retained Scientific Corrections
| Item | Retained correction | Binding |
|---|---|---|
| Circular gravitational-wave decay | The Peters circular-orbit calculation gives Earth-Sun `1.069e23 yr` and Mercury-Sun `4.343e22 yr`. | [S1; I1; I2; I3] |
| Solar-wind arithmetic | For the explicit conditional inputs `1e-14 M_sun/yr` and `5e9 yr`, `Delta M/M = 5e-5`; adiabatic `Delta a/a` is therefore about `0.005%`. | [S3; S4] |
| Mercury instability | The retained instability statement is restricted to Laskar and Gastineau's ensemble: `2,501` integrations over `5 Gyr`, with `1%` producing large Mercury eccentricity. It is a multi-body chaotic outcome, not gravitational-wave inspiral. | [S2] |
| Solar-evolution boundary | The numerical solar-evolution statement is restricted to the cited model, which places the RGB tip `7.59 Gyr` from now and models giant-stage mass loss; a generic NASA overview is not used as a numerical authority. | [S3] |
| Unbound quantitative material | V7's unsupported tidal, stellar-encounter, and comparison-system numerical assertions are not retained. | n/a |
## Peters Inputs, Formula, and Outputs
For both circular two-point-mass cases, `m1 = M_sun` and `m2` is the named planet. [S1]
| Input | Earth-Sun value | Mercury-Sun value | Source or adopted value |
|---|---:|---:|---|
| `G` | `6.67430e-11 m^3 kg^-1 s^-2` | `6.67430e-11 m^3 kg^-1 s^-2` | I1 |
| `c` | `299792458 m s^-1` | `299792458 m s^-1` | I1 |
| `m1 = M_sun` | `1.9885e30 kg` | `1.9885e30 kg` | I1 |
| `m2` | `M_earth = 5.972e24 kg` | `M_mercury = 3.3011e23 kg` | Earth: I1; Mercury: I2, adopted from `review-baseline-matched-v9.md` |
| `a` | `a_earth = 1.496e11 m` | `a_mercury = 5.7909e10 m` | Earth: I1; Mercury: I2, adopted from `review-baseline-matched-v9.md` |
| display conversion | `1 Julian year = 31,557,600 s` | `1 Julian year = 31,557,600 s` | I3 |
`t = (5/256)(c^5/G^3)(a^4/(m1*m2*(m1+m2)))`. [S1]
| Case | Formula inputs substituted | Output |
|---|---|---:|
| Earth-Sun | `m1=1.9885e30 kg`, `m2=5.972e24 kg`, `a=1.496e11 m` with the shared `G` and `c` above | `t = 3.374197216379e30 s = 1.069218576945e23 yr` |
| Mercury-Sun | `m1=1.9885e30 kg`, `m2=3.3011e23 kg`, `a=5.7909e10 m` with the shared `G` and `c` above | `t = 1.370536799260e30 s = 4.342969044731e22 yr` |
`baseline-matched-v7.md` and I1 display the Earth-Sun inputs only. They do not display either Mercury input; V9 records the Mercury mass and semimajor axis as I2's adopted values rather than attributing them to V7/I1.
## Executed In This Author Session
- Read `baseline-matched-v8.md` and `review-baseline-matched-v9.md`, retaining the four primary-source bindings and the passed scientific corrections.
- Recalculated both Peters expressions from the complete input table: Earth-Sun `3.374197216379e30 s = 1.069218576945e23 yr`; Mercury-Sun `1.370536799260e30 s = 4.342969044731e22 yr`. [S1; I1; I2; I3]
- Recalculated the stipulated conditional mass-loss check: `(1e-14)(5e9) = 5e-5`, hence approximately `0.005000%` orbital expansion. [S3; S4]
## Planned
- Independent review of V9 and an attributable receipt or re-freeze decision remain unexecuted.
- No N-body integration, tide model, solar-evolution rerun, or matched-protocol replay was executed in this author Session.
RESULT: CANDIDATE
