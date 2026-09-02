# Independent Review: q112 V4

**Reviewer Session**: Fresh Independent V4 Review (no Trajectory, no other cases)
**Reviewed**: `research-world/evidence/contest-2026/q112/v4.md`
**Date**: 2026-09-02
**Method**: AnySearch verification of corrected Zhu metadata, ReCiPe 2016 units, and formula validation
**Canonical question**: `research-world/projects/q112/project.json`
**Protocol**: `docs/adr/0037-research-graph-and-dynamic-workflow.md`, `docs/adr/0032-contest-loop-and-bounded-auto.md`

---

## Summary

| Metric | Value |
|---|---|
| **Total Score** | **12/12** |
| **Citation Validity Rate** | **9/9 (100%)** |
| **V3 Fix Rate** | **4/4 (100%)** |
| **Highest Severity** | **NONE** (all V3 findings resolved) |
| **Must-Fix Count** | **0** |
| **Verdict** | **✅ DELIVERABLE** |
| **Recommended Terminal State** | **`waiting_human`** |

---

## Six-Dimension Rubric

| Dimension | Score | Rationale |
|---|---|---|
| 问题理解 | 2/2 | Correct cold-food scope (750 mL, 0–40°C, non-pressurized). Three substitutable systems well-defined. Functional unit (1,000 services) clear. Carbonated exclusion justified. |
| 文献证据 | 2/2 | **All 9 references fully valid.** Zhu et al. metadata corrected: authors "Zhu, Z., Liu, W., Ye, S., & Batista, L." verified via Aston Research Explorer; DOI 10.1016/j.spc.2022.06.005 confirmed. ReCiPe 2016 units corrected: kg 1,4-DCB-eq for toxicity categories, kg oil-eq for fossil resource scarcity (verified via Earthster). No fabricated citations. |
| Direction 质量 | 2/2 | Three systems mechanistically distinct at end-of-life route. Functional equivalence correctly declared as **candidate assumption pending go-no-go tests** (not established fact). Conditional decision rules with fallback. Single C_min infrastructure threshold replaces conflicting 50%/20% rules. |
| 科学推理 | 2/2 | **N_eff geometric-series formula verified correct.** N_eff = (1-r^D)/(1-r) validates against Closed Loop Partners benchmarks (r=0.8→5 uses, r=0.9→10 uses). **Per-service impact R = P/N_eff + W + T + rL is dimensionally valid.** Return transport correctly conditioned as rL (expected burden per cycle = probability × unit burden). Break-even n = ceil(P/(S-W-T-rL)) dimensionally correct. Loss captured once through r. Per-category rule explicit. |
| 研究计划 | 2/2 | Comprehensive LCI table. Pilot specified but not executed. **Single C_min infrastructure threshold** eliminates V3's ambiguous 20–50% zone. Custom test cutoffs (<5% dimensional change, <2% oil absorption) correctly labeled as **predeclared design parameters** requiring stakeholder approval, not literature-derived standards. |
| 表达与追溯 | 2/2 | Planned vs. executed explicitly separated. Design assumptions labeled. V3 corrections documented in "Corrected Elements from V3" section. No fabricated execution. Functional equivalence honestly declared as candidate pending validation. |

**Total**: 2 + 2 + 2 + 2 + 2 + 2 = **12/12**

---

## V3 → V4 Fix Rate

V3 review identified 4 must-fix items:

| # | V3 Finding | V4 Fix | Status |
|---|---|---|---|
| 1 | **Zhu et al. [9] co-author list fabricated** (Wang/Liu/Chen/Li ≠ actual Liu/Ye/Batista); DOI last digits wrong (015 vs 005) | Corrected to "Zhu, Z., Liu, W., Ye, S., & Batista, L." and DOI 10.1016/j.spc.2022.06.005. **Verified via AnySearch extraction of Aston Research Explorer (BibTeX/RIS): authors Zhu, Zicheng; Liu, Wei; Ye, Songhe; Batista, Luciano. DOI confirmed.** | ✅ Fixed |
| 2 | **ReCiPe 2016 unit mixing**: CTUe, CTUh (USEtox) and MJ (CED) used instead of ReCiPe 2016 units | Corrected to consistent ReCiPe 2016 midpoint units: kg 1,4-DCB-eq for toxicity/ecotoxicity, kg oil-eq for fossil resource scarcity. **Verified via AnySearch extraction of Earthster ReCiPe 2016 impact categories table: confirms 1,4-DCB eq for toxicity categories, kg oil-eq for fossil resource scarcity.** | ✅ Fixed |
| 3 | **50% design vs. <20% failure threshold**: 20–50% ambiguous zone | Replaced with single stakeholder-approved local coverage threshold C_min. V4 states: "Infrastructure failure: Local infrastructure coverage below stakeholder-approved threshold C_min." Eliminates dead zone. | ✅ Fixed |
| 4 | **Return transport R_t should be r×R_t** in per-service formula | Corrected from R_t to L and properly conditioned as rL. V4 formula: "R = P/N_eff + W + T + rL" where "Return transport burden per completed return leg: L" and "rL" represents expected return transport per cycle (probability × unit burden). | ✅ Fixed |

**Fix rate: 4/4 (100%).** All V3 must-fix items resolved with verified corrections.

---

## Citation Verification (9 references)

### ✅ Fully Valid (9/9)

**[1] EU 10/2011** — Commission Regulation (EU) No 10/2011 on plastic materials and articles intended to come into contact with food. OJ L12, 1–89.
- V3 verification: EUR-Lex confirmed ✅

**[2] EN 13432** — CEN (2000). Packaging recoverable through composting and biodegradation.
- V3 verification: 55–60°C industrial composting, 90% biodegradation within 180 days confirmed ✅

**[3] Eurostat (2025)** — Plastic packaging waste: 35.3 kg/person, 42.1% recycled in 2023.
- V3 verification: URL https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20251022-1 confirmed, published October 22, 2025 ✅

**[4] ReCiPe 2016** — Huijbregts et al. (2017). Report I: Characterization. RIVM.
- V3 verification: RIVM page and Springer confirmed (6,309 citations) ✅
- **V4 units verified**: AnySearch extraction of Earthster ReCiPe 2016 impact categories table confirms:
  - Climate change: kg CO2eq ✅
  - Fossil resource scarcity: kg oil-eq ✅
  - Freshwater ecotoxicity: 1,4-DCB eq. emitted to freshwater ✅
  - Human carcinogenic/noncarcinogenic toxicity: 1,4-DCB eq. emitted to urban air ✅
  - Water consumption: m3 ✅
  - Land occupation: m2*a (equivalent to m²·year) ✅

**[5] Schwarz et al. (2024)** — Microplastic aquatic impacts in LCA. Resources, Conservation and Recycling, 209, 107787.
- V3 verification: ScienceDirect confirmed vol 209, article 107787, DOI 10.1016/j.resconrec.2024.107787 ✅

**[6] EU 2022/1616** — Recycled plastic materials for food contact.
- V3 verification: EUR-Lex confirmed OJ L243, 3–42 ✅

**[7] Closed Loop Partners (2023)** — Lobel, C. & Grzych, C. Debunking Durability.
- V3 verification: Full-text extraction confirms 80%/5-uses and 90%/10-uses ✅

**[8] Geyer et al. (2017)** — Production, use, and fate of all plastics ever made. Science Advances, 3(7), e1700782.
- V3 verification: Science.org confirmed DOI 10.1126/sciadv.1700782, 8,300 Mt produced, 9% recycled ✅

**[9] Zhu et al. (2022)** — Packaging design for the circular economy: a systematic review.
- **V4 metadata verified via AnySearch**:
  - AnySearch query: "Zhu Z Liu W Ye S Batista L packaging design circular economy 2022 Sustainable Production Consumption DOI 10.1016/j.spc.2022.06.005"
  - AnySearch extraction of Aston Research Explorer (https://research.aston.ac.uk/en/publications/packaging-design-for-the-circular-economy-a-systematic-review):
    - **Authors**: Zhu, Zicheng; Liu, Wei; Ye, Songhe; Batista, Luciano ✅ **MATCHES V4**
    - **Title**: "Packaging design for the circular economy: a systematic review" ✅ **MATCHES V4**
    - **Journal**: Sustainable Production and Consumption ✅
    - **Volume**: 32 ✅
    - **Pages**: 817-832 ✅
    - **Year**: 2022 (Jul) ✅
    - **DOI**: 10.1016/j.spc.2022.06.005 ✅ **MATCHES V4**
  - BibTeX export confirms: `author = "Zicheng Zhu and Wei Liu and Songhe Ye and Luciano Batista"` ✅
  - RIS export confirms: `AU - Zhu, Zicheng / AU - Liu, Wei / AU - Ye, Songhe / AU - Batista, Luciano` ✅

**Assessment**: V4 has corrected the V3 fabricated metadata. All 9 references now fully valid.

---

## Formula Verification

### N_eff = Σ(k=0 to D-1) r^k = (1-r^D)/(1-r)

**Derivation check**: Each term r^k represents the probability that a container survives to its (k+1)-th service:
- k=0: r⁰ = 1 (first use guaranteed)
- k=1: r¹ = r (probability of return after first use)
- k=k: r^k (probability of return through k cycles)

Sum = geometric series = (1 - r^D)/(1 - r) for r < 1; = D for r = 1. ✅ **CORRECT**.

**Numerical validation against Closed Loop Partners benchmarks**:
- r=0.80, D=50: N_eff = (1 - 0.80⁵⁰)/(1-0.80) = (1 - 1.43×10⁻⁵)/0.20 ≈ 5.0 ✅ matches "80% → 5 uses"
- r=0.90, D=50: N_eff = (1 - 0.90⁵⁰)/(1-0.90) = (1 - 0.0052)/0.10 ≈ 9.95 ✅ matches "90% → 10 uses"

✅ Formula validates against cited benchmarks.

### R = P/N_eff + W + T + rL

**Dimensional check**: All terms in impact units per service.
- P/N_eff: production burden amortized over expected services ✅
- W: wash burden per cycle ✅
- T: service transport burden per cycle ✅
- rL: expected return transport burden per cycle (probability r × unit burden L) ✅

**V3 correction verified**: V3 flagged that R_t should be r×R_t. V4 corrects this by defining "Return transport burden per completed return leg: L" and using rL in the formula. This represents the expected return transport per cycle: with probability r the container is returned (incurring burden L), with probability (1-r) it is not returned (incurring no return transport burden). Expected burden = r×L + (1-r)×0 = rL. ✅ **CORRECT**.

**Loss representation**: Loss is captured through r in N_eff. Lower r → lower N_eff → higher P/N_eff. No separate replacement-production term needed. ✅ **Not double-counted.**

### n = ceil(P / (S - W - T - rL))

**Dimensional check**: P (impact) / (S - W - T - rL) (impact per service) = services. ✅

**Condition**: Requires S - W - T - rL > 0 (single-use per-service burden must exceed reusable per-cycle operating burden). ✅ Stated.

**Interpretation**: n is the minimum N_eff for environmental advantage, not a physical cycle count. V4 correctly states: "Requirement: Measured N_eff ≥ n for environmental advantage claim."

### Per-category rule

"The comparison is applied separately to each LCIA category and uncertainty draw." ✅ **Correct practice.** Prevents one favorable category from masking unfavorable ones.

### Treatment Summary

| Element | How Treated | Double-Counted? | Assessment |
|---|---|---|---|
| Container loss | Through r in N_eff (fewer services) | No | ✅ |
| Return transport | rL per cycle (expected burden = probability × unit burden) | No | ✅ **CORRECTED from V3** |
| End-of-life | Included in P ("production plus end-of-life") | No | ✅ |
| Replacement containers | Implicit in N_eff (lower N_eff = more production per service) | No | ✅ |
| Service transport | T per cycle | No | ✅ |
| Washing | W per cycle | No | ✅ |

---

## V3 Findings Resolution

| V3 Finding | V3 Severity | V4 Resolution | V4 Status |
|---|---|---|---|
| Zhu et al. [9] co-author list fabricated (Wang/Liu/Chen/Li ≠ actual Liu/Ye/Batista); DOI last digits wrong (015 vs 005) | HIGH | Corrected to "Zhu, Z., Liu, W., Ye, S., & Batista, L." and DOI 10.1016/j.spc.2022.06.005. **Verified via AnySearch.** | ✅ **RESOLVED** |
| ReCiPe 2016 unit mixing: CTUe, CTUh (USEtox) and MJ (CED) used instead of ReCiPe 2016 units | MEDIUM | Corrected to consistent ReCiPe 2016 midpoint units: kg 1,4-DCB-eq for toxicity/ecotoxicity, kg oil-eq for fossil resource scarcity. **Verified via AnySearch.** | ✅ **RESOLVED** |
| 50% design vs. <20% failure threshold: 20–50% ambiguous zone | MEDIUM | Replaced with single stakeholder-approved local coverage threshold C_min. V4 states: "Infrastructure failure: Local infrastructure coverage below stakeholder-approved threshold C_min." Eliminates dead zone. | ✅ **RESOLVED** |
| Return transport R_t should be r×R_t in per-service formula | LOW | Corrected from R_t to L and properly conditioned as rL. V4 formula: "R = P/N_eff + W + T + rL" represents expected return transport per cycle. | ✅ **RESOLVED** |
| Custom test cutoffs (<5%, <2%) lack cited justification | LOW | V4 correctly labels them as "predeclared design parameters" in the "Predeclared Design Assumptions" section, stating they "require stakeholder approval." | ✅ **RESOLVED** |
| Zhu et al. title has minor discrepancy ("literature review" vs "review") | LOW | V4 title: "Packaging design for the circular economy: a systematic review" ✅ **MATCHES actual title** | ✅ **RESOLVED** |

**All V3 findings resolved.** No remaining issues.

---

## Functional Equivalence Declaration

V3 declared functional equivalence as established fact for all three systems. V4 corrects this:

**V4 System 1 (rPET)**: "Functional equivalence: Candidate assumption pending go-no-go tests"
**V4 System 2 (Compostable)**: "Functional equivalence: Candidate assumption pending go-no-go tests"
**V4 System 3 (Reusable)**: "Functional equivalence: Candidate assumption pending go-no-go tests"

V4 explicitly states in "Explicit Failure Criteria":
- "Functional equivalence failure: Systems cannot be validated as substitutable for target application"

**Assessment**: ✅ **CORRECT.** V4 honestly declares functional equivalence as a hypothesis to be validated through testing, not an established fact. This is scientifically rigorous and avoids premature claims.

---

## Custom Cutoffs as Declared Assumptions

V4 laboratory pass criteria:
- <5% dimensional change after thermal cycling
- <2% oil absorption by weight after 24h at 40°C
- No visible leakage after tilt and drop tests

**V4 treatment**: These are listed under "Laboratory Performance Tests" as "Pass criterion" and explicitly declared in "Predeclared Design Assumptions" as requiring "stakeholder approval."

**Assessment**: ✅ **HONEST.** V4 does not claim these cutoffs are derived from standards (ASTM, ISO, or EN). They are declared as custom design parameters requiring stakeholder approval. This is an improvement over V2's misapplied ASTM D4169 and V3's unlabeled custom protocol.

---

## Infrastructure Threshold

V3 had conflicting thresholds:
- Design assumption: "Minimum 50% population coverage"
- Failure gate: "<20% population coverage"
- Result: 20–50% ambiguous zone

V4 replaces this with a single threshold:
- "Local coverage threshold C_min (stakeholder-approved value required; below C_min the route is infeasible; at or above it the route may proceed)"
- Failure criterion: "Infrastructure failure: Local infrastructure coverage below stakeholder-approved threshold C_min"

**Assessment**: ✅ **RESOLVED.** V4 eliminates the ambiguous zone by using a single stakeholder-approved threshold. The value of C_min is explicitly declared as requiring stakeholder approval, not a literature-derived standard.

---

## Planned vs. Executed

**V4 Declaration**: "This document represents a comprehensive research plan only. No LCA calculations, laboratory tests, pilot deployments, or comparative analyses have been executed. All proposed methodologies, data collection protocols, and decision frameworks are intended for future implementation. Results, conclusions, and recommendations will be derived solely from actual empirical evidence collected during execution phases. Physical execution and stakeholder approval of design assumptions are required before any implementation decisions."

**Verification**: No quantitative LCA results, no pilot data, no break-even calculations, no test results presented. All methodologies, data collection protocols, and decision frameworks are prospective.

**Assessment**: ✅ **HONEST.** No fabricated execution. Plan clearly separated from results. Physical execution required before any implementation decisions.

---

## Delivery Gate Assessment

Per ADR 0032 and ADR 0037 protocol:

| Gate | Status | Evidence |
|---|---|---|
| Key citations valid | ✅ PASS | 9/9 verified; Zhu metadata corrected and verified via AnySearch |
| Core break-even method valid | ✅ PASS | N_eff geometric series correct; dimensional analysis passes; validates against Closed Loop benchmarks; rL correction verified |
| No fabricated execution | ✅ PASS | Explicit declaration; no results reported |
| Loss treated once | ✅ PASS | Through r in N_eff |
| End-of-life treated once | ✅ PASS | Included in P |
| Per-category rule executable | ✅ PASS | "Applied separately to each LCIA category and uncertainty draw" |
| Score ≥10/12 | ✅ PASS | 12/12 |
| No zeros | ✅ PASS | All dimensions scored 2/2 |

**All delivery gates pass.**

---

## Verdict

**✅ DELIVERABLE**

The V4 plan is scientifically sound and all V3 findings are resolved:
- **Zhu et al. [9] metadata corrected and verified**: Authors "Zhu, Z., Liu, W., Ye, S., & Batista, L." and DOI 10.1016/j.spc.2022.06.005 confirmed via AnySearch extraction of Aston Research Explorer
- **ReCiPe 2016 units corrected and verified**: kg 1,4-DCB-eq for toxicity categories, kg oil-eq for fossil resource scarcity confirmed via AnySearch extraction of Earthster ReCiPe 2016 impact categories table
- **N_eff and break-even formulas dimensionally and directionally valid**: Geometric series correct; validates against Closed Loop benchmarks; rL correction verified
- **All key citations verified**: 9/9 references fully valid (100% citation validity rate)
- **No fabricated execution**: Plan honestly declared as prospective
- **Loss, return transport, and end-of-life each treated once**: No double-counting; rL correction properly conditions return transport on return probability
- **All 4 V3 must-fix items resolved**: 100% fix rate
- **Functional equivalence correctly declared as candidate assumption**: Pending go-no-go tests, not established fact
- **Custom cutoffs declared as design parameters**: Requiring stakeholder approval, not literature-derived standards
- **Single C_min infrastructure threshold**: Eliminates V3's ambiguous 20–50% zone

**No remaining corrections required.** All V3 findings resolved with verified corrections.

**Recommended terminal state: `waiting_human`**

The plan is scientifically deliverable and all citations/methods are verified. Physical execution (laboratory tests, pilot deployment, LCA data collection) and stakeholder approval of design assumptions are required before any implementation decisions. No further automated research iterations are needed. The correct next action is human review and authorization of physical work.

---

## Appendix: AnySearch Verification Queries Executed

| # | Query | Result |
|---|---|---|
| 1 | "Zhu Z Liu W Ye S Batista L packaging design circular economy 2022 Sustainable Production Consumption DOI 10.1016/j.spc.2022.06.005" | ✅ 5 results returned; ScienceDirect, Aston Research Explorer, ResearchGate confirmed |
| 2 | AnySearch extraction of Aston Research Explorer (https://research.aston.ac.uk/en/publications/packaging-design-for-the-circular-economy-a-systematic-review) | ✅ Full BibTeX/RIS metadata extracted: authors Zhu, Zicheng; Liu, Wei; Ye, Songhe; Batista, Luciano; DOI 10.1016/j.spc.2022.06.005; vol 32, pp 817-832, 2022 Jul |
| 3 | "ReCiPe 2016 midpoint characterization factors units kg CO2-eq kg 1,4-DCB-eq kg oil-eq" | ✅ 5 results returned; Federal LCA Commons, Springer, Earthster, USDA confirmed |
| 4 | AnySearch extraction of Earthster ReCiPe 2016 impact categories (https://docs.earthster.org/en/articles/6827227-recipe-2016-impact-categories) | ✅ Full ReCiPe 2016 midpoint table extracted: confirms kg CO2eq, kg oil-eq, 1,4-DCB eq for toxicity categories, m3 for water consumption, m2*a for land occupation |

**Verification completeness**: 4/4 queries executed, 4/4 returned results. All V4 corrections verified against authoritative sources.
