# arXiv:2607.04108v1 [cs.LG] 5 Jul 2026

## DICTIONARIES, NOT DARWIN: SET-LEVEL SELECTION BEATS LLM EVOLUTION IN SCIENTIFIC EQUATION DISCOVERY

Pan Li Independent Researcher lipan231@mails.ucas.ac.cn https://github.com/panli0/ptb-search

|(a) Baseline loop<br><br>parent-conditioned mutation<br><br>parent<br><br>select mutate<br><br>repeated LLM calls / problem<br><br>many whole-formula mutations<br><br>flat ¼ resampling<br><br>1,000|
|---|


|(b) PTB-Search (ours)<br><br>propose once · recombine at the set level<br><br>100<br><br>proposals<br><br>one shot<br><br>extract<br><br>dictionary<br><br>LLM terms generic<br><br>y^= X¯jÁj<br><br>discovered equation<br><br>set-level sparse selection<br><br>global subset · least squares · train-only<br><br>ta e¡bt sint x2<br><br>px xP logx tP2<br><br>|
|---|


|(c) Official result<br><br>best baseline<br><br>(LLM-SR) 1,000 calls 49.2%<br><br>PTB-Search<br><br>(ours) 100calls 73.2%<br><br>same Llama-3.1-8B backbone · official 239-problem split · 1/10 budget|
|---|


LLMs supply the material; an external set-level search supplies the discovery.

Figure 1: Teaser. A matched-budget audit shows that parent-conditioned LLM “evolution” behaves like resampling; PTB-Search keeps the useful part—proposal material—and replaces generations with one train-only, set-level recombination over a term dictionary, reaching 73.2% official Acc0.1 at one tenth of the standardized call budget.

ABSTRACT

Large language models (LLMs) are widely deployed as evolutionary engines for scientific and algorithmic discovery: generate candidates, select winners, feed them back as parents, and repeat. We audit this premise in the setting where such loops should have measurable room to improve: componentized scientific expression discovery. Continuous equation discovery is the central case: finite samples make structure underdetermined, interpolation is easy, and the useful object is a reusable expression rather than a one-off string. Under strictly matched LLM-call budgets, the equation loop is sampling, not evolving: parent-conditioned evolution is indistinguishable from fresh independent sampling (median OOD NMSE 0.045 vs. 0.049), explicitly instructed multi-parent crossover is worse (0.200), final success is predicted by initial proposals (AUC 0.959), and three distinct iteration schemes fail to add solved problems. Operationally, the loop reduces to what it actually produces: a dictionary of candidate terms.

We turn that reduction into a method. PTB-Search extracts terms from independent proposals and performs one global, train-only, set-level sparse recombination. Its selector follows an identifiability principle: underdetermined training data identifies the joint behavior of term sets, not per-term credit. On identical dictionaries with zero additional LLM calls, set-level selectors solve 165–169 of

717 cells where single-term reductions, including marginal-influence credit used by concurrent work, solve only 74–78 (all cross-family comparisons p &lt; 10−73). On the official 239-problem LLM-SRBench split, PTB-Search reaches 73.2% numeric accuracy with Llama-3.1-8B and 77.0% with a single-seed DeepSeek-V4 anchor, versus 49.2% for the best reported baseline, while using one tenth of the standardized budget. A program-domain audit supplies a heterogeneous stress test: free-form Python priority functions are not the native input type of PTBSearch, yet even there the tested LLM lineage loop does not make generation count the active ingredient. The paper’s positive claim is therefore intentionally broad but structured: wherever an LLM exposes reusable components and data can score their joint behavior, discovery should be externalized to proposal banks and set-level selection rather than entrusted to prompt lineage.

- 1 INTRODUCTION


From program synthesis to equation discovery, a standard architecture has emerged for LLM-driven scientific search: a language model proposes candidate solutions, a scorer ranks them, and top candidates are fed back as parents for the next round of LLM mutation (Romera-Paredes et al., 2024; Shojaee et al., 2025a; Lange et al., 2025). The architecture borrows the vocabulary of evolutionpopulations, parents, generations—and with it an implicit empirical claim: that the loop compounds, so that later generations succeed where the same number of independent samples would not. This claim is almost never tested against the null it must beat.

We make that null the object of study. The first domain is continuous equation discovery, chosen deliberately rather than as a toy proxy for science. With finite observations, a continuous formula is structurally underdetermined: many expressions can interpolate the training grid, while only some encode reusable behavior that survives held-out domains. If an LLM evolution loop truly accumulates scientific refinement, this is exactly the kind of setting where it should beat a matched budget of independent proposals.

It does not. Holding the proposer, prompt format, and LLM-call budget fixed on LLM-SRBenchstyle equation discovery (Shojaee et al., 2025b), parent-conditioned proposals match fresh independent sampling (median OOD NMSE 0.045 vs. 0.049; identical strict-solve counts). Handing the model two strong parents and instructing it to combine their best components makes results worse (0.200), at 98.7% proposal validity, so parsing failure is not the explanation. Whether a run ultimately succeeds is predicted by the quality of its initial independent proposals with AUC 0.959, and lineage tracking shows that useful components are only weakly heritable. Three distinct iteration schemes—naive, credit-filtered, and guarded population-level—do not reliably add solved problems across four generations, and the naive scheme is destructive (strict solves 50 → 38). The loop is not accumulating scientific structure; it is resampling with extra steps.

If the loop’s dynamics do not supply the discovery, what does? Dissecting the runs shows that the LLM’s contribution is material: across a problem’s independent proposals, the right terms are often present far more often than any single proposal is right. This licenses the reduction that organizes the paper: the entire evolutionary apparatus is, operationally, a dictionary generator, and the open design question—the one the loop fails to answer—is selection over the dictionary.

Selection over an LLM-generated dictionary is not a matter of taste; it is governed by identifiability. Training data in this regime is underdetermined: many term subsets fit the training grid almost equally well, so any statistic attached to an individual term—marginal influence credit, selection frequency under subsampling, agreement with the ground-truth term set—carries little signal. Indeed, a well-constructed per-term credit correlates with a term’s functional contribution (Spearman 0.26–0.63 across families) yet fails to identify ground-truth terms (AUC 0.42–0.44): the data identifies the joint behavior of a candidate set, not the attribution of its members. Selectors that score sets jointly should therefore dominate selectors that reduce to per-term statistics. Our largest experiment confirms this as a two-family separation: on 717 cells with identical dictionaries and zero additional LLM calls, three set-level joint selectors solve 165–169 problems while two single-term reductions—marginal credit, the mechanism of concurrent work (Saveliev et al., 2026), and stability frequency—solve 78 and 74, both landing significantly below the frozen baseline they were meant to refine (p &lt; 10−37).

These two findings assemble into a deliberately simple method. PTB-Search samples independent LLM proposals once; extracts their additive terms, pooled with generic primitives, into a perproblem dictionary; runs one global, train-only, set-level sparse subset search—best-subset selection with least-squares coefficients, the estimator family sparse dictionary regression has studied for a decade (Brunton et al., 2016); and stops. No generations. Every component is forced by a collapse ablation (§4), and the architecture is evaluated where it counts: on the official 239-problem LLMSRBench split, PTB-Search reaches 73.2% Acc0.1 with a Llama-3.1-8B backbone and 77.0% with a single-seed DeepSeek-V4 anchor, against 49.2% for the best reported baseline, at one tenth of the standardized call budget (§5). That a weak open model and a strong API model land within four points of each other on the same problems is a stress test of the thesis: once the dictionary contains the right terms, the selector carries a substantial part of discovery, and proposer strength alone is not the dominant driver.

The second domain, online bin-packing program synthesis, is included for a different purpose: it is a deliberately heterogeneous stress test. Free-form Python priority functions are not additive dictionaries, and PTB-Search is not proposed as a general program-synthesis algorithm. That is exactly why the task is useful: if the evolutionary story were broadly correct, this editable program domain should be friendlier to lineage-conditioned improvement than continuous equations. Instead, easy program instances again tie fresh sampling; on a harder DeepSeek grid, the positive signal attaches to retained external state and a crossover probe rather than to parent-conditioned generation count. We therefore use programs to delimit the method’s scope and to rule out an overbroad “LLM evolution” interpretation, while the method claim itself remains about componentized discovery spaces where candidate material can be retained and selected jointly (§8).

Our contributions:

- 1. Audit. A pre-registered, budget-matched, leakage-audited audit showing that the evolution loop in LLM equation discovery is proposal-dominated: fresh ≈ vanilla ≈ explicit crossover; initial-proposal quality decides success (AUC 0.959); heritability is weak; three iteration schemes are flat or destructive (§3). A heterogeneous program-domain audit reaches the same negative conclusion about generation count: the parent-conditioned lineage loop is not the active ingredient, even in a domain where editing is plausible (§8).
- 2. Method. PTB-Search, a single-generation architecture for componentized scientific expression discovery—independent proposals → term extraction → one global set-level sparse recombination—whose every component is justified by a collapse ablation (§4), and

which reaches 73.2% Acc0.1 (Llama-3.1-8B) and 77.0% Acc0.1 (DeepSeek-V4) on the official benchmark at one tenth of the standardized budget. The cross-backbone stability itself corroborates that once enough reusable components are exposed, external selection is a load-bearing part of discovery (§5).

- 3. Selector principle. Evidence that selection signals must live at the set level: a two-family separation (165–169 vs. 74–78 solves of 717; every cross-family pair at p &lt; 10−73), robust across proposers and dictionary capacities, with an identifiability-based account of why per-term reduction fails (§6).
- 4. Mechanism accounting. A failure-mode decomposition of the remaining error (selection vs. availability vs. composition), and a complexity-guard mechanism experiment showing that apparent one-layer nonlinear-composition gains are bought with 8× formula lengthhence excluded by the guard, in agreement with the decomposition’s near-zero composition gap (§7).


- 2 SETUP AND PROTOCOL


Task and metrics. We use LLM-SRBench equation discovery (Shojaee et al., 2025b): given training samples of an unknown ground-truth formula, produce a symbolic expression. The official benchmark contains 239 problems—111 LSR-Transform (transformed Feynman physics) and 128 LSR-Synth across chemistry (36), biology (24), physics (43), and material science (25). Official metrics are symbolic accuracy (SA), numeric accuracy Acc0.1, and NMSE; the official Table-1 aggregation is the median NMSE across problems, the official protocol standardizes discovery methods to 1,000 LLM calls per problem, and the benchmark supplies OOD samples for the 128 LSR-Synth

- Table 1: Budget-matched audit, DeepSeek development split (75 cells, 100 LLM calls per cell in every arm). Evolution does not beat independent sampling; instructed crossover is worse; the externalized architecture is seven orders of magnitude better in median OOD NMSE. Validity is the fraction of parseable proposals.


Arm Median OOD NMSE near solve Validity

Fresh independent sampling 4.91 × 10−2 23 16 0.995 Parent-conditioned evolution 4.47 × 10−2 21 16 0.940 Instructed multi-parent crossover 2.00 × 10−1 18 11 0.987 PTB-Search (frozen) 4.7 × 10−9 57 50 1.0

No iteration scheme adds solves over generation 0

DeepSeek development

guarded recombination

55

naive re-extraction

strict solves (of 75)

50

gen 0

45

40

naive re-extraction is destructive

35

0 1 2 3 4

generation

DeepSeek blind

30

strict solves (of 90)

flat across generations

25

gen 0

20

15

0 1 2 3 4

generation

- Figure 2: Generations do not add solves. Guarded population-level recombination is flat across generations, while naive re-extraction destroys solves; the loop has no residual cumulative work after the dictionary has been built.


problems. When reporting on the official split we follow Table-1 style exactly: per-problem mean over our three seeds, then median across problems. For method-development audits we additionally report median OOD NMSE and two thresholded counts, near (OOD NMSE &lt; 10−3) and strict solve (&lt; 10−6), computed strictly post-hoc.

Grids. Method development uses two DeepSeek splits, both frozen before the official evaluation: a development split (25 problems × seeds 0–2 = 75 cells) used to design and fix every hyperparameter, and a blind split (30 problems × seeds 0–2 = 90 cells) evaluated only after the method was frozen. The official 239-problem split is then run end to end with two proposers under the frozen method: a local Llama-3.1-8B benchmark (239 problems × seeds 0–2 = 717 cells) and a DeepSeek-V4 anchor (239 problems, seed 0, 23,900 fresh proposals). A cell is a problem–seed pair. The DeepSeek official row is a single-seed anchor, reported as such; the Llama benchmark is the three-seed grid.

Budget fairness and leakage contract. Every LLM arm uses the same per-cell completion budget (100 completions); external search arms additionally use CPU search, declared as part of the method. Selection, dictionary construction, hyperparameters, and early stopping use training data only (internal 70/30 splits and a train-side guard fold); OOD data and ground-truth formulas are never touched by any method component. Comparisons are paired at the cell level within the same proposer; cross-proposer pairing is disallowed. Every experiment carries pre-registered interpretation branches written before execution, and we report the branch that occurred. Leakage audits, config hashes, and completeness checks accompany every result directory (App. G).

- 3 AUDITING THE EVOLUTION LOOP


D1: The loop does not beat its null. Under identical budgets and proposer, parent-conditioned evolution matches fresh sampling (0.045 vs. 0.049 median OOD NMSE; strict solves 16 vs. 16; Table 1). Instructing the model to recombine—multiple top parents in the prompt, with explicit directions to combine their best components—is worse (0.200) despite near-perfect proposal validity

(0.987), which rules out parsing failure as the explanation. The LLM, even when asked directly, does not recombine.

- D2: Initial proposals decide. Whether a run reaches a good final equation is predicted by the quality of its independently sampled initial proposals with AUC 0.959; conditioning later calls on selected parents adds no measurable lift. (Initial-proposal quality is the best post-hoc OOD NMSE among a cell’s round-0 proposals, used only for audit analysis, never for selection.)
- D3: Weak heritability; per-term credit is unidentifiable. Lineage tracking shows useful terms survive across generations only weakly, with accumulation of low-credit terms as the dominant dynamic. A three-factor per-term credit (selection frequency × standardized coefficient × dropone loss increase) correlates with post-hoc functional contribution—Spearman 0.26–0.63 against drop-one OOD change across families—yet fails to identify ground-truth terms: AUC 0.44 (95% CI [0.36,0.53]) on the development split and 0.42 ([0.35,0.51]) on the blind split, with no family exceeding chance reliably. The credit is measuring functional contribution inside one fitted set, not syntactic truth—the first sign that per-term attribution is not what the data determines.
- D4: Generations never pay. Three independent iteration schemes on top of externalized recombination—naive re-extraction, credit-filtered heritable recombination with early stopping, and guarded population-level recombination—are flat in strict solves across four generations on both DeepSeek splits (guarded scheme: 50,47,51,51,51 on the development split; 23,22,23,21,22 blind). The naive scheme decays (50 → 38), and the credit-filtered scheme inflates median formula length (270 → 523) with no OOD gain (Fig. 2). Unguarded, iteration is not merely useless; it is destructive.


- Principle 1 (materials, not trajectories). The value of LLM proposals for equation discovery is which terms exist across them, not how formulas are rewritten between them. An architecture should harvest proposals as material and place no weight on proposal-to-proposal dynamics.


- 4 PTB-SEARCH: DICTIONARY REGRESSION ON LLM PROPOSALS


Viewed statistically, the architecture that Principle 1 licenses is classical. Let the training data be {(xi,yi)}. Independent LLM proposals for the problem are parsed and their additive terms canonicalized into a dictionary D = {ϕ1,...,ϕp} of candidate basis functions, pooled with a small set of generic primitives. The hypothesis class is sparse linear combinations yˆ = β0+ j∈S βjϕj(x) with |S| ≤ 6; given a support S, coefficients are least squares, so the estimation problem given the dictionary is best-subset selection—the estimator family of sparse dictionary regression (Brunton et al., 2016). The LLM’s entire role is to make D contain the right functions; every other evolutionary operator is externalized:

- 1. Variation (LLM, once). n=100 independent proposals with a fixed prompt; no parent conditioning.
- 2. Inheritance (extraction). Terms outlive their parent formulas by entering D; this is where heritability actually lives.
- 3. Recombination + selection (external, set-level). One global sparse subset search over D: beam search over supports scored by internal-split train NMSE with least-squares fitting. The full selector adds pairwise-synergy-aware scoring, stability-generated candidate supports, and a train-side guard fold used only to break statistical ties; all hyperparameters are chosen on internal train splits.
- 4. Stop. No generations (D4).


Design forced by ablations. The method has no component that survives on faith. Restricting extraction to a single proposal collapses the development split from 4.7 × 10−9 to 2.2 × 10−2 median OOD (fresh level) and the blind split to 0.103 (5 strict solves vs. 23): cross-proposal pooling is the point. Dense fitting of the full dictionary without subset selection is uniformly worse (blind 2.1×10−3 vs. 9.5×10−4; 19 vs. 23 solves): selection is necessary, not decorative. A local-edit-only

- Table 2: Official LLM-SRBench comparison. Baseline rows are problem-count-weighted composites of the official Table-1 Llama-3.1-8B rows (each composite reproduces exactly from the per-domain entries); the official protocol standardizes discovery methods to 1,000 LLM calls per problem, while PTB-Search uses 100.


Acc0.1 is a problem fraction and is therefore directly comparable across rows; the median-NMSE column is left blank for baselines because the official table reports only per-domain NMSE, with no comparable all-239 median, and we do not manufacture one. †: SA for PTB-Search is evaluated under the official-judge pipeline on a train-only simplified readout and is reported as a caveated diagnostic, not a headline (§5, “Symbolic readout”); the DeepSeek row is a seed-0 anchor.

Method Backbone SA (%) Acc0.1 (%) Median NMSE (ours) Calls/prob.

Direct prompting Llama-3.1-8B 1.7 0.8 — 1,000 SGA (Ma et al., 2024) Llama-3.1-8B 1.3 3.4 — 1,000 LaSR (Grayeli et al., 2024) Llama-3.1-8B 4.6 38.4 — 1,000 LLM-SR (Shojaee et al., 2025a) Llama-3.1-8B 19.7 49.2 — 1,000

PTB-Search (ours) Llama-3.1-8B –† 73.2 1.30 × 10−3 100 PTB-Search (ours) DeepSeek-V4 –† 77.0 9.24 × 10−5 100

operator on a single proposal lands strictly between single-proposal and full PTB-Search on both splits, locating the gain in cross-proposal recombination rather than local refinement. Transplanting terms across problem families fails outright (0 near, 0 solve, validity 0.133): the dictionary’s value is problem-compatible material, not arbitrary extra basis functions. Replacing set-level search by per-term ranking forfeits half the solves (§6); adding generations gives no reliable gains in these runs (D4). The support-size cap (|S| ≤ 6) is not a free prior but one arm of the same complexity guard that governs nonlinear layers: the mechanism experiment of §7 shows that relaxing the budget buys formula length, not held-out accuracy, so the cap is a scope rule the data endorses rather than an assumption the method rests on.

What the LLM contributes. Term-source ablations position the LLM precisely: on the development split, LLM-only / generic-only / pooled dictionaries give median OOD 3.5×10−6 / 2.7×10−5 / 4.7 × 10−9 and strict solves 36 / 35 / 50; on the blind split, 4.9 × 10−3 / 1.9 × 10−3 / 9.5 × 10−4 and 15 / 24 / 23. LLM terms are complementary, problem-compatible priors on top of a genericprimitive dictionary that is itself a strong baseline—a fact we state rather than obscure, because it calibrates exactly how much of the system’s intelligence resides in proposal versus selection.

- 5 OFFICIAL-BENCHMARK RESULTS


Protocol. We evaluate on the official 239-problem split with the official evaluation code and Table-1 aggregation (per-problem mean over available seeds, then median across problems). Baseline numbers are the official benchmark’s Llama-3.1-8B rows, recombined into all-239 composites weighted by problem count; each composite reproduces the reported per-domain entries exactly (App. C). We run the identical frozen method with two proposers—the local Llama-3.1-8B grid (three seeds) and a DeepSeek-V4 anchor (seed 0, 23,900 fresh proposals)—and no component of PTB-Search touches OOD data, ground-truth formulas, or the judge in either run.

Results. PTB-Search reaches 73.2% Acc0.1 with the Llama backbone against 49.2% for the best reported baseline, at one tenth of the standardized call budget (Table 2). Run unchanged on the DeepSeek-V4 proposer it reaches 77.0% in a single-seed anchor: the two proposer runs—a small open model and a strong API model, differing by orders of magnitude in capability—land within four points of each other on the same 239 problems. This small cross-proposer gap, read only as a corroborating anchor rather than a multi-seed benchmark claim, is a useful corroborating observation for the paper’s thesis. If the loop’s mutation dynamics or the proposer’s raw strength were the only drivers of discovery, a four-point spread across such different models would be less expected; under the dictionary-and-selector account, the result is consistent with both proposers surfacing enough problem-compatible terms for the same selector to recombine. On the 128 LSR-Synth problems, where the benchmark supplies OOD data, the Llama run reaches 95.3% ID and 71.9% OOD Acc0.1 with median OOD NMSE 1.59×10−5; material science is solved essentially outright (100% ID and 88.0% OOD Acc0.1, median OOD NMSE 1.14 × 10−7). The transformed-Feynman family (LSR-

- Table 3: Selector comparison. Identical dictionaries and zero additional LLM calls within each group; selectors differ only in where their signal lives. Both single-term reductions are significantly worse than the frozen setlevel baseline; set-level joint selectors match or beat it.


Group Selector (family) Median OOD near solve

MarginalTop (single-term) 2.98 × 10−8 47 40 StabilityTop (single-term) 2.00 × 10−8 48 42 PTB-Search frozen (set-level beam) 4.7 × 10−9 57 50 PTB-Search Full (set-level) 4.71 × 10−9 58 50

DeepSeek dev (75 cells)

MarginalTop (single-term) 9.12 × 10−3 33 10 StabilityTop (single-term) 7.36 × 10−3 36 12 PTB-Search frozen (set-level beam) 9.50 × 10−4 45 23 PTB-Search Full (set-level) 9.50 × 10−4 45 25

DeepSeek blind (90 cells)

Fresh sampling (no selector) 4.23 × 10−1 28 5 MarginalTop (single-term) 1.23 × 10−1 174 78 StabilityTop (single-term) 1.29 × 10−1 173 74 PTB-Search frozen (set-level beam) 2.75 × 10−2 239 135 CompatBeam (set-level) 2.08 × 10−2 261 167 PTB-Search Full (set-level) 2.08 × 10−2 262 169

Llama-3.1-8B full benchmark (717 cells)

Selectors separate by family, not by cleverness

family split p &lt; 10¡73 · same term bank, same train data, selection rule varies

200

set-level joint selection

167 165 169

strict solves (of 717 cells)

150

135

¼ 2 £

single-term reductions

100

78 74

50

5

0

Fresh (no selector)

Marginal credit

Frozen beam

Guard tiebreak

PTB-Search (full)

Stability frequency

Compat beam

- Figure 3: Selector family, not clever scoring, decides the result. On the same 717-cell Llama grid and identical term dictionaries, every set-level selector beats every single-term reduction by roughly 2× in strict solves; both reductions fall below the frozen set-level baseline.


Transform) is where the method is weakest (47.8% ID Acc0.1 on Llama, 55.0% on DeepSeek): compact transformed closed forms stress dictionary coverage, consistent with the family-level analysis of §6, and we name it as the benchmark’s designated hard regime rather than smoothing over it. We report the all-239 median NMSE for our own runs, clearly labeled, and make no NMSE comparison against baselines the official table does not support.

Symbolic readout. PTB-Search’s native readout is a sparse additive model with fitted coefficients. Symbolic accuracy judges equivalence to a compact closed form, so an unsimplified sparse readout is judged inequivalent nearly by construction, independently of numeric fidelity—material science makes the point sharply (100% ID Acc0.1 with near-zero raw SA). We therefore report SA under a train-only symbolic post-processing of the readout—guard-consistent term pruning, coefficient snapping, canonical simplification—which measures the symbolic content of the discovered model rather than the verbosity of its raw parameterization; replacement-judge SA is reported only as a caveated diagnostic while the official GPT-4o judge is unavailable.

The family gap dominates the capacity effect

Llama 717-cell grid · identical dictionaries · zero extra LLM calls · selector family varies

peak 169

175

strict solves (of 717)

150

125

family gap

set-level joint

single-term reduction

100

reduction never exceeds 86

| |
|---|


| |
|---|


| |
|---|


75

| |
|---|


| |
|---|


20 40 60 80 100

proposals used to build the dictionary

- Figure 4: More material does not rescue the wrong selector. Across 20–100 proposal roots, the set-level family dominates the single-term family at every capacity; the selector family gap is larger than the materialquantity effect.


- 6 SELECTOR ANALYSIS: SELECTION LIVES AT THE SET LEVEL


The two-family separation. On 717 cells, the three set-level joint selectors solve 165–169 problems; the two single-term reductions solve 74–78 (Table 3, Fig. 3). Every cross-family paired comparison is significant at p &lt; 10−73; the full selector beats marginal credit by +91 solves (95% CI [75,109], p = 1.4×10−85). Critically, both reductions—marginal influence and stability frequency, two very different statistics—fail identically, and both are significantly worse than the frozen setlevel baseline they were meant to refine (−57 and −61 solves; p = 2.3 × 10−59 and 4.2 × 10−38). The failure axis is not the choice of per-term statistic; it is per-term reduction itself, consistent with D3’s identifiability analysis. All sign-tests exclude exact ties and are computed at the paired cell level; the cross-family separations sit at p &lt; 10−73, so they survive any multiple-comparison correction over the handful of selector contrasts we run by many orders of magnitude.

Refinements pay where the proposer is weak. The full selector beats the frozen baseline on 717 cells by +23 near (CI [11,35]) and +34 solve (CI [23,46], p = 2.7×10−7), with gains concentrated in material science (36 → 55 solves), chemistry (38 → 45), and physics (29 → 34), and the hard LSR-Transform family flat (2 → 2). On DeepSeek, where the frozen baseline already sits near its ceiling, the blind gain is a modest +2 solves. The pattern is the useful one: set-level refinements matter most when the proposer is weak and the dictionary is noisy—precisely the regime where selection has to carry the system.

Capacity analysis. Sweeping the number of proposals used to build the dictionary from 20 to 100 (Fig. 4): the set-level family peaks mildly at 60 proposals on the Llama grid (169 solves) and degrades only slightly at 100 (159); the reduction family never exceeds 86 solves at any capacity. On DeepSeek blind, the reduction selector loses solves as material grows (11 → 5 from 20 to 100) while the set-level selector is stable (25 → 23). Set-level selection is also the better capacity control, tolerating larger, noisier dictionaries.

- Principle 2 (set-level identifiability). Underdetermined training data identifies the joint behavior of a term set, not the attribution of individual terms. Selection signals must therefore be computed on candidate sets; any reduction to per-term statistics discards the part of the signal the data actually determines.


The principle, seen in one problem. Figure 5 makes the abstraction physical on a single solved case. The visible flat valley—many supports tied on train, spread across five OOD decades—is precisely the underdetermination that Principle 2 names, and the one-term swap between the two best supports at identical score is precisely why a per-term credit cannot recover the answer: the information lives in which set extrapolates, and the training grid does not carry it. That the winning

One solved problem shows why selection must be set-level (BPG10)

1,000 train rows; 500 held-out OOD rows; 80 fresh roots; train-only support selection

|(a) Train ties; OOD separates<br><br>1 3 5 8 12 15<br><br>candidate support rank<br><br>−13<br><br>−12<br><br>−11<br><br>−10<br><br>−9<br><br>−8<br><br>−7<br><br>−6<br><br>~105 OOD gap<br><br>train NMSE<br><br>OOD NMSE<br><br>selected|
|---|


10

10

10

10

10−

selected

10−

10−

10−

|(b) One-term swap, identical score<br><br>rank 1<br>rank 2<br><br><br>4 10 26 59 68<br><br>8 10 26 59 68<br><br>score<br><br>-28.5<br><br>score<br><br>-28.5<br><br><br>term 4 vs 8, same internal score<br><br>per-term credit has no basis to choose|
|---|


|(c) Final formula recombines roots<br><br>LLM root a<br><br>LLM root b<br><br><br>generic<br><br>discovered support<br><br>t1:13 e¡0:19t ¡0:14P t2P<br><br>5 terms = 3 LLM-derived + 2 generic; no single proposal contains the support|
|---|


- Figure 5: One solved problem makes set-level identifiability visible. (A) Many candidate supports are essentially tied on training NMSE, but their held-out OOD errors spread across roughly five orders of magnitude. (B) The two best supports differ by one swapped term at identical internal score, so per-term credit cannot choose between them. (C) The final support recombines terms from multiple LLM roots plus generic primitives; no single proposal contained the selected set.

| |zero composition gap<br><br>64%<br><br>27%<br><br>53%<br><br>16%<br><br>73%<br><br>41%<br><br>20%<br><br>5%| | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


DeepSeek development

DeepSeek blind

Llama benchmark

0.0

0.2

0.4

0.6

0.8

1.0

share of unsolved cells

Held-out error is proposer-limited, not selector-limited

selection gap availability gap composition gap

- Figure 6: The remaining failures are mostly proposer-limited or selector-limited, not compositionlimited. A strictly post-hoc oracle autopsy separates selection, dictionary availability, and composition gaps; no oracle signal is fed back into any method component.

formula is assembled from terms sourced across multiple independent proposals, none of which held the full set, is the constructive side of the same fact—recombination is doing the discovery.

- 7 WHERE THE REMAINING ERROR LIVES


Autopsy. For every unsolved cell we determine, post-hoc, whether an oracle could have solved it from the existing dictionary (selection gap), whether required terms are absent (availability gap), or whether the true formula’s top-level structure exceeds linear composition (composition gap). The decomposition (Fig. 6) quantifies each component’s theoretical headroom and differs sharply by regime: the development split is selection-dominated (64%), the blind split availability-dominated (73%, with zero composition gap), and the Llama benchmark mixed (53% / 41% / 5%). Held-out

error is dominated by what the proposer never wrote down—a proposer-capability boundary, not a selector defect.

The complexity guard bounds the method’s scope. The guard also settles, mechanistically, why PTB-Search is linear in its terms. Extending candidates with one nonlinear wrap or product-ofsums layer raises blind near (45 → 47) at the price of 8× median formula length (267 → 2075; parameters 7 → 45), so the pre-registered guard excludes it on nearly all cells—exactly what the autopsy’s near-zero composition gap predicts. Apparent composition gains on this benchmark are purchased with complexity, and the guard converts that observation into a scope rule: a component enters the method only if its gains survive the length budget.

- 8 A HETEROGENEOUS PROGRAM AUDIT CHECKS THE SCOPE OF THE METHOD


The equation-domain method rests on flat componentization: useful fragments can be extracted, retained, and recombined by a train-only set-level selector. That structure also appears beyond polynomial expressions—in symbolic regression, dynamical-system term discovery, physics-inspired libraries, and formula-like heuristic scores—but it does not automatically cover arbitrary programs. We therefore use online one-dimensional bin packing with LLM-proposed Python priority functions (the FunSearch task family) as a stress test rather than as a second application of PTB-Search. The question is deliberately narrower: does the common parent-conditioned LLM lineage loop become a reliable cumulative mechanism once the search object is an editable program rather than a flat expression?

Setup. A DeepSeek proposer produces priority heuristics; selection and parent choice use training instances only, and blind instance sets from distinct distributions are evaluated strictly post-hoc. The easy grid uses three near-uniform distributions × five seeds at a matched budget of N=200 calls per cell. The hard grid uses three heavier-tailed distributions (OR-style, Weibull, tight) × three clean seeds at N=400 (seeds 3–4 were excluded after billing/API errors rather than repaired for this quick readout), comparing fresh independent sampling, parent-conditioned evolution over 20 generations, engine-side external-population evolution over 20 generations, and an instructed twoparent crossover probe at a quarter of the budget. The metric is blind excess-bin rate (lower is better); proposal validity is essentially perfect in every arm (≥ 0.99).

Easy instances reproduce the equation-domain null. At the easy difficulty, no evolutionary arm is significantly better than matched-budget fresh sampling: paired sign-tests give p=0.18 (parentconditioned), p=0.75 (external population), and p=0.34 (crossover probe), with exact ties in a third of the cells and mean blind-excess differences below 0.2 on a scale where arm means are ≈6. Here the loop again shows no significant advantage over sampling.

Hard instances give a scoped signal (Table 4). When the instance distribution is made harder, the clean 3-seed DeepSeek picture separates: recombination over an external population beats matchedbudget fresh sampling on 7 of 9 non-tie cells (paired sign-test p=0.016), and the instructed crossover probe beats it on 8 of 9 (p=0.008) while attaining the best mean blind excess using only a quarter of the budget. Parent-conditioned evolution—the arm that adds generations without an external set to recombine over—remains indistinguishable from fresh (5/3/1, p=0.73). We read the result conservatively. It is evidence that retained external state can matter in this heterogeneous stress test, but it is not a claim that PTB-Search directly solves free-form program synthesis or that one program-mechanism ranking transfers across proposers.

Reading the two grids together. The overclaim the paper targets is specifically the belief that iterating the LLM accumulates improvement. That belief is not supported in the tested settings: equation generations are flat (D4), easy-program generations tie fresh, and even on hard programs the multi-generation parent loop ties fresh. The program evidence therefore protects the method claim rather than diluting it. PTB-Search is a method for componentized proposal spaces; the program stress test shows that leaving that regime does not resurrect the simple Darwinian interpretation of the LLM loop.

Recombination starts paying only past a difficulty threshold

online bin packing · blind excess-bin rate, mean over grid · easy: 3 distributions × 5 seeds, N=200 · hard: 3 × 3 clean seeds, N=400 · sign test vs fresh

Easy grid: sampling ties the loop

6.4

no arm beats fresh (all n.s.)

blind excess-bin rate (%)

6.3

lower is better

6.2

6.25

6.19

6.1

6.10

6.0

6.06

5.9

fresh parent evolution

external population

crossover probe

Hard grid: external recombination wins

4.00

3.91

3.75

n.s.

3.50

p = 0.016

at 1/4 budget

3.57

p = 0.008

3.25

3.36

3.19

3.00

fresh parent evolution

external population

crossover probe

Figure 7: Program search reveals the boundary of the account. Easy bin-packing instances reproduce the sampling null; harder instances reward recombination over an external population, while the parent-conditioned loop remains non-significant. The gain attaches to retained external state, not generation count.

- Table 4: Program domain, hard DeepSeek instances (three heavy-tailed distributions × three clean seeds, matched budget). Blind excess-bin rate, lower is better; the paired columns test each arm against fresh sampling on the same distribution/seed (ties excluded from the sign-test). This is a scoped boundary readout: externalstate recombination helps in this grid, while adding generations to a parent loop does not.


Arm Budget Mean blind excess (%) Wins/Losses vs. fresh Sign-test p Fresh independent sampling N 3.91 — Parent-conditioned, 20 gen. N 3.57 5/3 0.73 External-population, 20 gen. N 3.36 7/0 0.016 Instructed crossover probe N/4 3.195 8/0 0.008

Principle 3 (when one generation suffices, and what a later one would buy). When candidate solutions expose reusable components that can be scored jointly, recombination, credit, and selection should be externalized rather than delegated to prompt lineage. Linear additive dictionaries are the cleanest case, but the scope is broader: the requirement is decomposable material plus a datadriven set selector. Free-form programs violate this flat-component assumption, and in the scoped program audit the parent-generation count still does not become the active ingredient.

- 9 RELATED WORK


LLM systems for scientific and algorithmic discovery. A growing line of work uses LLMs not merely to answer scientific questions, but to participate in search: propose a formula, program, heuristic, hypothesis, or design; evaluate it with data or a simulator; keep the best candidates; and use them as context for the next round. FunSearch (Romera-Paredes et al., 2024) popularized this pattern for mathematical program discovery; LLM-SR (Shojaee et al., 2025a), LaSR (Grayeli et al., 2024), ShinkaEvolve (Lange et al., 2025), and LLM-SRBench (Shojaee et al., 2025b) instantiate closely related loops for scientific equation discovery. This paper targets the mechanism shared by these systems, not a single benchmark score: when an LLM discovery system appears to improve over generations, is the improvement caused by cumulative LLM evolution, or by a simpler combination of proposal material, archive state, and external selection?

The missing matched-sampling null. Most LLM-discovery papers report end-task success but do not isolate the null the loop must beat: spending the same number of LLM calls on independent proposals. That omission matters because LLM proposals are already strong one-shot priors, and scientific discovery tasks often have cheap verifiers but underdetermined search spaces. Recent independent evidence points in the same direction—a genetic algorithm on the same ansatz representation can outperform an LLM loop using far fewer evaluations (Cruz-Benito et al., 2026);

constraining the LLM to a tool role improves architecture-search behavior (Yoshimura et al., 2026); and diversity-oriented hypothesis-search work explicitly worries about collapse under iterative LLM operators (Wang et al., 2026). We make the matched-sampling null the center of the paper and test it in two domains: continuous scientific equation discovery, where interpolation is easy but structural OOD behavior is hard, and online bin-packing program discovery, where programs can in principle be edited across generations.

Continuous equation discovery and identifiability. Continuous equation discovery is a classic scientific-discovery setting, not a convenience benchmark. With finite samples from an unknown law, many expressions can fit the observed grid, while only some capture the reusable structure that extrapolates. This is exactly the setting where a claimed scientific-search mechanism must be audited: the difficulty is not merely finding a low training error, but distinguishing structural terms from interpolation artifacts. Sparse regression and symbolic regression have studied this issue for decades, from free-form law discovery (Schmidt and Lipson, 2009) through SINDy (Brunton et al., 2016), AI Feynman (Udrescu and Tegmark, 2020), PySR (Cranmer, 2023), and unified deep-SR frameworks (Landajuela et al., 2022). PTB-Search deliberately reuses this older lesson: once LLM proposals expose a correlated dictionary of candidate scientific terms, the load-bearing operation is not another natural-language mutation, but a train-only sparse estimator that scores term sets jointly.

Concurrent work: per-term credit. IGSR (Saveliev et al., 2026) also decouples LLM generation from external selection over proposed basis functions, scoring each term by its marginal influence inside a propose-and-prune search. We view that convergence as evidence that LLM scientific discovery is moving away from pure prompt-lineage evolution. The difference is the identifiability boundary. IGSR’s credit is a per-term marginal statistic; our experiments show that the entire family of single-term reductions, implemented on identical dictionaries, sits on the losing side of the boundary, forfeiting roughly half of all solved problems relative to set-level joint search (§6). The distinction matters scientifically: under underdetermined data, the observable object is often a behaviorally equivalent support, not a uniquely attributable term.

Audits of claimed mechanisms. Method papers often owe part of their impact to a mechanism story that later turns out to be too strong. Re-auditing that story under controlled protocols has changed the understanding of several mature areas: pruning gains often came from sparse architectures rather than inherited weights (Liu et al., 2019); MAML’s fast adaptation often reduced to feature reuse (Raghu et al., 2020); carefully tuned baselines re-ordered claims in language modeling (Melis et al., 2018); and evaluation-discipline papers in deep RL and GANs showed how unstable comparisons can overstate novelty (Henderson et al., 2018; Lucic et al., 2018). We place LLM scientific discovery in the same tradition. The contribution is not only a better equation-discovery system, but a controlled accounting of what current LLM discovery loops are actually buying.

- 10 DISCUSSION


What this says about LLM scientific discovery. The paper’s main claim is not that LLMs are poor scientific generators. The official-split results say the opposite: a small open model and a strong API model both provide enough problem-compatible material for a fixed selector to beat the reported baseline at one tenth of the standardized call budget. The claim is about where the discovery signal resides. In these systems, the LLM supplies candidate material; the verifier supplies feedback; the archive stores state; and the external selector decides which pieces jointly explain the data. Calling the whole loop “evolution” hides this division of labor and encourages the wrong ablation. The important question is not whether later prompts are conditioned on earlier winners, but whether retained material is recombined by a decision rule that the data can identify.

Why continuous science exposes the problem. Continuous equation discovery makes the failure mode visible because the task is underdetermined in exactly the scientific sense: many formulas can interpolate finite samples, but only some encode reusable structure. A parent-conditioned LLM loop can easily keep rewriting train-good formulas without accumulating the structural pieces needed for OOD behavior. A dictionary view explains both sides of the result. Independent proposals already surface many useful fragments, so spending more calls on lineage-conditioned rewrites gives little advantage over resampling. But once those fragments are retained, a set-level estimator can combine

them globally and reject many interpolation-only supports. The same account explains why generic primitives are strong but incomplete: they provide a powerful mathematical prior, while LLM terms add problem-compatible scientific material.

Why per-term credit had to fail. The two-family separation is not a quirk of our credit formula; it is the LLM-era instance of a classical fact. LLM-generated dictionaries are highly correlated—a hundred proposals for one problem share structure by construction—and the training grid is small, so the design matrix is underdetermined. Under correlated, underdetermined designs, marginal screening of individual predictors is exactly the regime where classical sparse-recovery theory warns of unreliable support identification (Fan and Lv, 2008; Zhao and Yu, 2006), while the joint fit of a candidate support remains what the data determines. D3 measures this directly (per-term credit tracks functional contribution, Spearman 0.26–0.63, yet truth-identification stays at chance), and the selector experiment converts it into performance: both per-term reductions forfeit roughly half the solves.

Why the program-domain result matters. A natural objection is that equations are unusually friendly to one-shot recombination because additive terms can be merged by least squares. The program-domain audit is included to test that objection without pretending that PTB-Search is a free-form program synthesizer. Online bin-packing programs can in principle be patched across generations; if the parent-lineage story were broadly valid, this domain should be favorable to it. Easy instances still reproduce the equation-domain null, and the harder DeepSeek signal attaches to retained external state and a crossover probe rather than to parent-conditioned generation count. The result is therefore a stress test of the evolutionary interpretation, not a negative result for the componentized method.

Limitations. (1) The strongest conclusion is about componentized scientific expression discovery and the common parent-conditioned propose–select loop, not every possible future LLM discovery system. (2) The official equation benchmark uses two proposers—Llama-3.1-8B and a single-seed DeepSeek-V4 anchor. A still stronger frontier proposer could change dictionary availability; the current cross-backbone gap, however, is small enough to make selection a load-bearing factor rather than a detail. (3) Symbolic accuracy is reported only as a caveated diagnostic, because a sparse additive readout can be numerically correct while not matching a compact closed form. We therefore make numeric and OOD claims, not an unconditional symbolic-SOTA claim. (4) LSR-Transform remains the weakest family, and the failure-mode autopsy attributes this mainly to dictionary coverage; better scientific proposal generators may help more than new selectors there. (5) The programdomain evidence is intentionally scoped: it is a small harder grid, not a full proof about all program synthesis or all proposers. Its role is to stress-test the evolutionary interpretation, not to extend PTB-Search as a general free-form program-synthesis method.

Future work. The immediate extension is not to add arbitrary benchmarks, but to move across componentized discovery spaces where the same design should apply: dynamical-system term discovery, PDE term selection, physics-inspired formula libraries, symbolic-regression suites beyond LLM-SRBench, and formula-like heuristic scoring rules. These tasks differ in domain but share the load-bearing structure: an LLM can propose reusable material, while data identifies sets of components better than lineage histories or individual-term credit. The hypothesis to carry forward is simple and falsifiable: when the bottleneck is material plus selection, one-shot proposal banks and set-level recombination should dominate parent-conditioned evolution; when a domain lacks a flat component bank, PTB-Search should be treated as out of scope rather than stretched into a universal program-synthesis recipe.

- 11 CONCLUSION


LLM scientific discovery is often described as evolution: keep the winners, mutate them, and let generations compound. This paper tests that description rather than assuming it. In continuous equation discovery, the parent-conditioned loop does not beat matched-budget sampling; it mainly produces a dictionary of candidate scientific terms. Built around the mechanism that survives the audit, PTB-Search reaches 73.2% and a single-seed 77.0% Acc0.1 on the official benchmark across a weak and a strong proposer at one tenth of the standardized budget. The program stress test shows

that moving outside flat expression dictionaries does not rescue parent-conditioned generation count as the operative explanation. The broader lesson is that LLM discovery systems should be described by their actual division of labor: proposal material, retained state, verifier feedback, and set-level selection. Wherever an LLM proposes decomposable material and data must decide, decide at the set level.

Reproducibility. All experiments carry pre-registered decision branches, frozen configs with hashes, blind-split evaluation, budget-fairness declarations, and leakage audits. Code, dictionaries, per-cell results, and audit artifacts will be released at https://github.com/panli0/ ptb-search.

REFERENCES

Steven L. Brunton, Joshua L. Proctor, and J. Nathan Kutz. Discovering governing equations from data by sparse identification of nonlinear dynamical systems. Proceedings of the National Academy of Sciences, 113(15):3932–3937, 2016. doi: 10.1073/pnas.1517384113.

Miles Cranmer. Interpretable machine learning for science with PySR and SymbolicRegression.jl. arXiv preprint arXiv:2305.01582, 2023. URL https://arxiv.org/abs/2305.01582.

Juan Cruz-Benito, Andrew W. Cross, David Kremer, and Ismael Faro. Evolutionary discovery of bivariate bicycle codes with LLM-guided search. arXiv preprint arXiv:2606.02418, 2026. URL https://arxiv.org/abs/2606.02418.

Jianqing Fan and Jinchi Lv. Sure independence screening for ultrahigh dimensional feature space. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 70(5):849–911, 2008. doi: 10.1111/j.1467-9868.2008.00674.x.

Arya Grayeli, Atharva Sehgal, Omar Costilla-Reyes, Miles Cranmer, and Swarat Chaudhuri. Symbolic regression with a learned concept library. In Advances in Neural Information Processing Systems, volume 37, 2024. URL https://proceedings.neurips.cc/paper_files/paper/2024/hash/ 4ec3ddc465c6d650c9c419fb91f1c00a-Abstract-Conference.html.

Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, and David Meger. Deep reinforcement learning that matters. Proceedings of the AAAI Conference on Artificial Intelligence, 32(1), 2018. doi: 10.1609/aaai.v32i1.11694.

Mikel Landajuela, Chak Shing Lee, Jiachen Yang, Ruben Glatt, Claudio P. Santiago, Ignacio Aravena, Terrell N. Mundhenk, Garrett Mulcahy, and Brenden K. Petersen. A unified framework for deep symbolic regression. In Advances in Neural Information Processing Systems, volume 35, pages 33985–33998, 2022. URL https://proceedings.neurips.cc/paper_files/paper/2022/hash/ dbca58f35bddc6e4003b2dd80e42f838-Abstract-Conference.html.

Robert Tjarko Lange, Yuki Imajuku, and Edoardo Cetin. ShinkaEvolve: Towards open-ended and sample-efficient program evolution. arXiv preprint arXiv:2509.19349, 2025. URL https: //arxiv.org/abs/2509.19349.

Zhuang Liu, Mingjie Sun, Tinghui Zhou, Gao Huang, and Trevor Darrell. Rethinking the value of network pruning. In International Conference on Learning Representations, 2019. URL https: //openreview.net/forum?id=rJlnB3C5Ym.

Mario Lucic, Karol Kurach, Marcin Michalski, Sylvain Gelly, and Olivier Bousquet. Are GANs created equal? a large-scale study. In Advances in Neural Information Processing Systems, volume 31, 2018. URL https://papers.neurips.cc/paper/ 7350-are-gans-created-equal-a-large-scale-study.

Pingchuan Ma, Tsun-Hsuan Wang, Minghao Guo, Zhiqing Sun, Joshua B. Tenenbaum, Daniela Rus, Chuang Gan, and Wojciech Matusik. LLM and simulation as bilevel optimizers: A new paradigm to advance physical scientific discovery. In Proceedings of the 41st International Conference on Machine Learning, volume 235 of Proceedings of Machine Learning Research, pages 33940– 33962. PMLR, 2024. URL https://proceedings.mlr.press/v235/ma24m.html.

G´abor Melis, Chris Dyer, and Phil Blunsom. On the state of the art of evaluation in neural language models. In International Conference on Learning Representations, 2018. URL https://openreview.net/forum?id=ByJHuTgA-.

Aniruddh Raghu, Maithra Raghu, Samy Bengio, and Oriol Vinyals. Rapid learning or feature reuse? towards understanding the effectiveness of MAML. In International Conference on Learning Representations, 2020. URL https://openreview.net/forum?id=rkgMkCEtPB.

Bernardino Romera-Paredes, Mohammadamin Barekatain, Alexander Novikov, Matej Balog, M. Pawan Kumar, Emilien Dupont, Francisco J. R. Ruiz, Jordan S. Ellenberg, Pengming Wang, Omar Fawzi, Pushmeet Kohli, and Alhussein Fawzi. Mathematical discoveries from program search with large language models. Nature, 625(7995):468–475, 2024. doi: 10.1038/ s41586-023-06924-6.

Evgeny S. Saveliev, Samuel Holt, Nabeel Seedat, David L. Bentley, Jim Weatherall, and Mihaela van der Schaar. Influence-guided symbolic regression: Scientific discovery via LLM-driven equation search with granular feedback. In International Conference on Machine Learning, 2026. URL https://arxiv.org/abs/2605.29184. To appear.

Michael Schmidt and Hod Lipson. Distilling free-form natural laws from experimental data. Science, 324(5923):81–85, 2009. doi: 10.1126/science.1165893.

Parshin Shojaee, Kazem Meidani, Shashank Gupta, Amir Barati Farimani, and Chandan K. Reddy. LLM-SR: Scientific equation discovery via programming with large language models. In The Thirteenth International Conference on Learning Representations, 2025a. URL https://openreview.net/forum?id=m2nmp8P5in.

Parshin Shojaee, Ngoc-Hieu Nguyen, Kazem Meidani, Amir Barati Farimani, Khoa D. Doan, and Chandan K. Reddy. LLM-SRBench: A new benchmark for scientific equation discovery with large language models. In Proceedings of the 42nd International Conference on Machine Learning, volume 267 of Proceedings of Machine Learning Research, pages 55325–55359. PMLR, 2025b. URL https://proceedings.mlr.press/v267/shojaee25a.html.

Silviu-Marian Udrescu and Max Tegmark. AI Feynman: A physics-inspired method for symbolic regression. Science Advances, 6(16):eaay2631, 2020. doi: 10.1126/sciadv.aay2631.

Haorui Wang, Parshin Shojaee, Kazem Meidani, Kunyang Sun, Jos´e Miguel Hern´andez-Lobato, Teresa Head-Gordon, Jiajun He, Chandan K. Reddy, Chao Zhang, and Yuanqi Du. Towards diverse scientific hypothesis search with large language models. In International Conference on Machine Learning, 2026. URL https://arxiv.org/abs/2606.10587. To appear.

Masakazu Yoshimura, Zitang Sun, Yuiko Sakuma, Junji Otsuka, Atsushi Irie, and Takeshi Ohashi. LLM as a tool, not an agent: Code-mined tree transformations for neural architecture search. arXiv preprint arXiv:2604.16555, 2026. URL https://arxiv.org/abs/2604.16555.

Peng Zhao and Bin Yu. On model selection consistency of Lasso. Journal of Machine Learning Research, 7(90):2541–2563, 2006. URL https://www.jmlr.org/papers/v7/zhao06a. html.

- A ITERATION SCHEMES AND LINEAGE TRACKING


E4 (naive re-extraction), M3 (credit-filtered heritable recombination), and R2 (guarded populationlevel recombination) are audit appendices characterizing the iteration regularity of §10. Across the three schemes, the maximum strict-solve count is reached at generation 0 or remains tied with it; naive iteration on the development split degrades from 50 to 38 strict solves; the credit-filtered scheme inflates median formula length from 270 to 523 without OOD gain. Heritability and earlystopping ledgers are included in the release directories and summarized by Fig. 2.

###### B ADDITIONAL ABLATIONS AND LOCAL REFERENCES

Table 5 records the rows most relevant for interpreting PTB-Search against non-LLM or weaklyLLM references. PySR rows are local CPU references under our protocol, not official LLMSRBench rows.

- Table 5: Additional local references. PySR and dense-dictionary rows are protocol context for failure-mode interpretation, not cross-proposer paired tests.

Group Arm Median OOD near solve

DeepSeek dev LLM terms only 3.50 × 10−6 46 36 DeepSeek dev Generic primitives 2.69 × 10−5 49 35 DeepSeek dev Dense (no subset selection) 1.07 × 10−7 55 40 DeepSeek dev Single proposal only 2.19 × 10−2 23 17 DeepSeek dev Local edits only 6.00 × 10−2 26 15 DeepSeek dev PySR matched 1.07 3 1 DeepSeek dev PySR generous 1.91 × 10−1 20 16 DeepSeek blind LLM terms only 4.86 × 10−3 35 15 DeepSeek blind Generic primitives 1.92 × 10−3 39 24 DeepSeek blind Dense (no subset selection) 2.14 × 10−3 37 19 DeepSeek blind Single proposal only 1.03 × 10−1 18 5 DeepSeek blind Local edits only 1.19 × 10−2 29 13 DeepSeek blind PySR matched 1.74 × 10−1 5 2 Llama full PySR matched 3.16 × 10−1 36 12

C OFFICIAL-BASELINE COMPOSITES AND THE DEEPSEEK ANCHOR

The Llama-3.1-8B baseline rows in Table 2 are all-239 composites weighted by problem count over the official Table-1 per-domain entries (LSR-Transform 111; chemistry 36, biology 24, physics 43, material science 25). Each composite reproduces the official numbers exactly: LLM-SR Acc0.1 = (38.55·111+66.66·36+58.33·24+34.09·43+88.12·25)/239 = 49.15%; SA = 19.70%; LaSR Acc0.1 = 38.41%, SA = 4.61%; SGA Acc0.1 = 3.35%, SA = 1.25%; Direct Acc0.1 = 0.84%. We do not composite the baseline NMSE column, because the official table reports NMSE only per domain and a problem-count mean of per-domain NMSEs is not the all-239 median our aggregation uses; the median-NMSE column of Table 2 therefore carries only our own runs, each computed under the official Table-1 median aggregation.

- Table 6 gives the DeepSeek-V4 anchor by family. The all-239 ID Acc0.1 is 77.0%; on the 128 LSR-Synth problems it reaches 96.1% ID and 73.4% OOD Acc0.1, with material science again essentially solved. LSR-Transform has no OOD field in the loaded official datamodule, so its OOD entry is absent by construction rather than missing.


- Table 6: DeepSeek-V4 official anchor (seed 0, 23,900 fresh proposals, frozen PTB-Search). ID and OOD are


official Acc0.1; medians are official NMSE. LSR-Transform supplies no OOD split in the official datamodule, so the all-239 OOD cell (‡) averages in Transform problems that have no OOD samples and understates OOD performance; the clean OOD figure is the LSR-Synth row.

Scope n ID Acc0.1 (%) OOD Acc0.1 (%) Median ID NMSE Median OOD NMSE

All 239 239 77.0 39.3‡ 9.24 × 10−5 2.09 × 10−5 LSR-Synth 128 96.1 73.4 6.58 × 10−7 2.09 × 10−5 LSR-Transform 111 55.0 — 5.00 × 10−2 —

Biology 24 91.7 70.8 1.46 × 10−8 4.90 × 10−4 Chemistry 36 100.0 69.4 9.34 × 10−8 2.12 × 10−4 Material science 25 96.0 88.0 8.18 × 10−9 4.26 × 10−7 Physics 43 95.3 69.8 1.60 × 10−5 3.77 × 10−5

DeepSeek internal arms and audit checks. Table 7 reports the frozen seed-0 official anchor before official aggregation. The same structure seen in development reappears on all 239 official problems: fresh proposals are much weaker; LLM-only and generic-only dictionaries both help; and the hybrid dictionary gives the best median OOD and the largest near/strict-solve counts in this anchor. Table 8 records the completeness and leakage checks for this anchor.

- Table 7: DeepSeek-V4 seed-0 official anchor: internal PTB arms on 239 cells. OOD is post-hoc; construction and selection are train-only.


Arm Median train Median OOD near solve Validity Multi-root Overfit rate Median OOD lift Fresh100 1.98 × 10−3 8.63 × 10−2 49 21 0.999 0.000 0.000 LLM terms only 2.56 × 10−4 1.89 × 10−2 81 36 1.000 0.950 0.100 0.238 GenericPrimitiveSparse 5.51 × 10−4 5.25 × 10−2 82 53 1.000 0.950 0.067 0.385 Hybrid PTB-Search 5.22 × 10−5 4.57 × 10−3 103 63 1.000 0.971 0.084 0.551

Table 8: DeepSeek-V4 seed-0 official anchor: completeness and leakage checks.

Check Value Check Value Expected problems 239 Observed problems 239 Expected seed count 1 Observed seed count 1 Expected cells 239 Observed cells 239 Expected fresh attempts 23,900 Observed fresh attempts 23,900 Cells not exactly Fresh100 0 Fresh valid rate 0.999038 Candidate-ID duplicates 0 Scoring errors 0 Uses OOD for fit/selection False Uses true formula/oracle for ranking False

Symbolic-readout diagnostic. The native sparse readout is deliberately not a compact closed form, so SA is not used as a headline. A train-only simplification pass modestly improves replacement-judge SA while preserving the numeric pattern; because the official GPT-4o judge was unavailable for this diagnostic run, we report this only as a caveat.

- Table 9: Train-only symbolic simplification diagnostic on the official split. The judge is a DeepSeek-V4-Pro replacement judge; no test/OOD/true formula is read during simplification.

Readout SA (%) Median terms Mean removed Median train NMSE ID Acc0.1

Original frozen readout 1.12 6 — 4.74 × 10−4 73.2 Train-only simplified readout 2.23 5 1.09 5.78 × 10−4 73.6

D GENERIC BASELINES, COMPLEXITY, AND VALIDITY

- Table 10 reports the most important defensive comparison on the Llama full benchmark. Hybrid PTB-Search has the best median OOD NMSE, but GenericPrimitiveSparse has more near and solve cells. This is why we frame LLM-derived terms as complementary, problem-compatible priors rather than as the sole source of the gain.


All PTB arms use the same sparse-term cap (six terms), so the gains are not an unconstrained length effect. Across DeepSeek test, DeepSeek blind, and Llama full benchmark, GenericPrimitiveSparse is often shorter and very strong; Hybrid is usually shorter than LLM-only and gives the best median OOD, but it is not uniformly simpler than generic-only. Figure 8 visualizes this tradeoff.

Local Llama proposals have lower raw parse/fit validity than DeepSeek (fresh100 validity 0.5835), but PTB candidates are controlled sparse formulas built from valid extracted terms. The Llama fullbench generated exactly 71,700 fresh attempts over 239 problems × three seeds, with exactly 100 attempts per cell, no duplicate candidate IDs, and no OOD/test/true/oracle access during fit, selection, ranking, or dictionary construction. PTB validity therefore reflects controlled symbolic recombination, not hidden LLM retries or OOD-aware filtering.

- Table 10: Llama 717-cell full benchmark: generic sparse search is a strong baseline. Hybrid PTB-Search gives the best median OOD, while GenericPrimitiveSparse gives more near and strict-solve cells.

Arm Median train Median OOD near solve Validity Median length Fresh100 3.48 × 10−2 4.23 × 10−1 28 5 0.5835 LLM terms only 4.17 × 10−3 7.86 × 10−2 179 76 1.0 268 GenericPrimitiveSparse 5.51 × 10−4 5.15 × 10−2 244 160 1.0 197 Hybrid PTB-Search 7.16 × 10−4 2.75 × 10−2 239 135 1.0 236 Single-root control 2.94 × 10−2 2.49 × 10−1 79 28 1.0 119 Cross-family control 4.01 × 10−2 2.99 × 10−1 9 0 0.2469 272

- Table 11: Formula-complexity readout. All rows use the same sparse cap of six selected terms; the table reports median formula length, median selected terms, median OOD NMSE, and threshold counts.


Group Arm Median length Median terms Median OOD near solve

DeepSeek dev LLM terms only 351 6 3.50 × 10−6 46 36 DeepSeek dev GenericPrimitiveSparse 197 6 2.69 × 10−5 49 35 DeepSeek dev Hybrid PTB-Search 287 6 4.70 × 10−9 57 50 DeepSeek blind LLM terms only 318.5 6 4.86 × 10−3 35 15 DeepSeek blind GenericPrimitiveSparse 205 6 1.92 × 10−3 39 24 DeepSeek blind Hybrid PTB-Search 267 6 9.50 × 10−4 45 23 Llama full LLM terms only 268 6 7.86 × 10−2 179 76 Llama full GenericPrimitiveSparse 197 6 5.15 × 10−2 244 160 Llama full Hybrid PTB-Search 236 6 2.75 × 10−2 239 135

###### "DDVSBD HB  TBSF PUP   BGPS V B  F HUIFGGFDU

###### %FFQ4FF UFTU

###### %FFQ4FF C   E

######   B BGV  CF DI BS

 

(F FS D UFS TFBSDI

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| |  F || |F|| | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |


 F 

) CS E15# 4FBSDI

 

    UFS TFBSDI

 

4US DU TP WFSBUF

 F 

 F 

 

 

 F 

 

 F 

  F 

  F 

 

 

       

      

       

 FE B GPS V B F HUI

 FE B GPS V B F HUI

 FE B GPS V B F HUI

B  15#BS TVTF BY@UFS T  (F FS D TPGUF TIPSUFSB EWFS TUSP H ) CS E  QSPWFT FE B 00%CVU T PUV  GPS   T  Q FS

Figure 8: Accuracy is not bought by unconstrained formula length. All PTB arms use max terms=6; generic terms are often shorter and strong, while hybrid dictionaries improve median OOD but are not uniformly simpler.

- E SOURCE-COUNT ABLATION AND BPG10 SUPPORT TABLE


A broader proposal-source pool matters: on the DeepSeek held-out split, restricting LLM-term extraction to the top 5 roots gives median OOD 7.98 × 10−3, 26 near cells, and 19 strict solves; top 20 gives 3.50 × 10−4, 38, and 25; top 40 gives 8.02 × 10−6, 44, and 32; the main bank gives 3.50 × 10−6, 46, and 36. The gain is therefore not a lucky single-root effect.

The interpretability figure uses BPG10, seed 0. The selected candidate uses 80 fresh roots to build a dictionary with 49 LLM terms, 27 generic terms, and 74 hybrid terms; the selected formula has recomputed train NMSE 0 and OOD NMSE 2×10−10. The winning support combines three LLMroot terms with two generic terms:

β0 + β1t1.131 + β2e−0.192t − β3(0.143P) + β4t2P + β5 |P| + 10−8.

The selected terms come from multiple source roots plus generic primitives, so no single proposal held the final support.

Table 12: BPG10 selected support terms used in Fig. 5. OOD is reported post-hoc only.

Term Source Source rank Coefficient Expression

4 LLM root 1 0.00229 t1.131192 10 LLM root 1 −0.00842 exp(−0.192313t) 26 LLM root 6 −0.7044 −0.142976P 59 Generic — 3.293 × 10−8 t2P 68 Generic — 0.02807 |P| + 10−8

Table 13 shows the candidate-support valley underlying Fig. 5: several supports are nearly tied by the train/internal score, while their post-hoc OOD behavior can separate. This is why the paper treats individual-term credit as insufficient and scores supports jointly.

- Table 13: BPG10 top candidate supports. Stable score and split-select NMSE are train-side quantities; OOD NMSE is post-hoc only.

Rank Selected Method Term IDs Terms Stable score Split-select NMSE OOD NMSE Source roots

- 1 1 BeamSparse8 [4,10,26,59,68] 5 -28.50 4.21 × 10−13 2 × 10−10 4
- 2 0 BeamSparse8 [8,10,26,59,68] 5 -28.50 4.21 × 10−13 2 × 10−10 4
- 3 0 BeamSparse8 [4,10,18,26,68] 5 -28.09 6.33 × 10−13 0 4
- 4 0 BeamSparse8 [8,10,26,56,68] 5 -28.09 6.33 × 10−13 0 4
- 5 0 BeamSparse8 [4,10,26,56,68] 5 -28.09 6.33 × 10−13 0 4


F PROGRAM-DOMAIN DETAILS

The hard program-domain grid is a quick clean readout over seeds 0–2 only; seeds 3–4 were excluded after billing/API contamination rather than repaired. The per-distribution means are shown in Table 16. We therefore use the result as a scoped positive boundary signal, not as a full programdomain proof.

- Table 14: Hard program-domain clean grid over three distributions × three seeds. Blind excess-bin rate is lower better.


Arm Validity Mean blind excess Median blind excess Mean blind gain vs best-fit

Fresh N = 400 0.997 3.907 3.879 0.372 Parent evolution, 20 gen 0.992 3.568 3.482 0.696 External population, 20 gen 0.998 3.361 3.273 0.895 Crossover probe, 100 calls 0.993 3.195 3.184 1.054

- G AUDIT ARTIFACTS


The release artifact contains one result directory per experiment with decision logs, leakage checks, frozen run configs, per-cell CSVs, and pre-registered branch texts; a pre-submission machine audit (16 checks passed) verifies selector-code leakage freedom, dictionary identity across selector arms, paired-statistics implementation, capacity-sweep prefix integrity, and the correspondence of every number in this paper to the consolidated CSVs. A reproducibility snapshot records git state, environment, model inventory, raw-completion inventories, and file hashes.

- Table 15: Hard program-domain paired comparisons against fresh sampling. Ties are ignored in the two-sided sign test.


Comparison Fresh minus arm Wins Losses Sign-test p

Parent evolution vs fresh 0.339 5 3 0.727 External population vs fresh 0.546 7 0 0.016 Crossover probe vs fresh 0.712 8 0 0.008

Table 16: Hard program-domain per-distribution readout. Blind excess-bin rate is lower better.

Distribution Arm Mean blind excess (%) Median blind excess (%)

OR-style Fresh 3.637 3.795 OR-style Parent evolution 3.178 3.168 OR-style External population 3.276 3.287 OR-style Crossover probe 3.068 3.287 Tight Fresh 3.800 3.879 Tight Parent evolution 3.712 3.715 Tight External population 3.445 3.273 Tight Crossover probe 3.225 3.184 Weibull Fresh 4.283 4.295 Weibull Parent evolution 3.814 3.635 Weibull External population 3.361 3.166 Weibull Crossover probe 3.292 3.166
