---
project: q049
artifact: baseline-matched-v8
artifact_stage: benchmark_candidate
author_session: 01a05f02-1368-7963-be17-d9147c57a04b
author_session_provenance: runtime CODEX_SESSION_ID
supersedes: baseline-matched-v7.md
addresses_review: review-baseline-matched-v8.md
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
calculation_input_record:
  id: I1
  source: baseline-matched-v7.md
  supports: "The displayed SI masses and semimajor axes reused unchanged for the two Peters formula recalculations."
---
# q049 Baseline Matched V8
## Artifact Boundary
`baseline-matched-v8.md` is a new benchmark candidate produced by the runtime-confirmed author Session above. It supersedes `baseline-matched-v7.md`; it does not replace or re-freeze the matched-v6 comparison, and it makes no Project terminal determination.
## Recalculation Basis
Both inspiral values use the Peters circular-orbit expression `t = (5/256)(c^5/G^3)(a^4/(m1*m2*(m1+m2)))` with I1's unchanged inputs. [S1; I1]
## Scientific Changes From V7
| Item | V8 correction | Binding |
|---|---|---|
| Circular gravitational-wave decay | Reusing V7's displayed SI inputs in the Peters circular-orbit formula gives Earth-Sun `1.069e23 yr` and Mercury-Sun `4.343e22 yr`. | [S1; I1] |
| Solar-wind arithmetic | For the explicit conditional inputs `1e-14 M_sun/yr` and `5e9 yr`, `Delta M/M = 5e-5`; adiabatic `Delta a/a` is therefore about `0.005%`. | [S3; S4] |
| Mercury instability | The retained instability statement is restricted to Laskar and Gastineau's ensemble: `2,501` integrations over `5 Gyr`, with `1%` producing large Mercury eccentricity. It is a multi-body chaotic outcome, not gravitational-wave inspiral. | [S2] |
| Solar-evolution boundary | The numerical solar-evolution statement is restricted to the cited model, which places the RGB tip `7.59 Gyr` from now and models giant-stage mass loss; a generic NASA overview is not used as a numerical authority. | [S3] |
| Unbound quantitative material | V7's unsupported tidal, stellar-encounter, and comparison-system numerical assertions are not retained. | n/a |
## Executed In This Author Session
- Retrieved and checked the publisher or DOI metadata for [S1]-[S4], including the APS Peters record, the Nature Laskar-Gastineau abstract, and the two peer-reviewed solar-evolution and wind records.
- Recalculated the Peters circular-orbit expression using I1's unchanged V7 inputs: Earth-Sun `1.069218576945e23 yr`; Mercury-Sun `4.342969044731e22 yr`, rounded above as `4.343e22 yr`. [S1; I1]
- Recalculated the stipulated adiabatic check: `(1e-14)(5e9) = 5e-5`, hence approximately `0.005000%` orbital expansion. [S3; S4]
## Planned
- Independent review of V8 and an attributable receipt or re-freeze decision remain unexecuted.
- No N-body integration, tide model, solar-evolution rerun, or matched-protocol replay was executed in this author Session.
RESULT: CANDIDATE
