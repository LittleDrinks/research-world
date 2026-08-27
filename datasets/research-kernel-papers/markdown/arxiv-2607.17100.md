## Auto Research for Materials: Auditable AI-Scientist Workflows with Held-Out Transfer

#### Jingjie Ning1, Xiaochuan Li1, Shanshan Zhong1, Ji Zeng1, Guolin Ke2

1School of Computer Science, Carnegie Mellon University 2DP Technology {jening, xiaochu4, szhong2, jizeng}@cs.cmu.edu, kegl@dp.tech

# arXiv:2607.17100v2 [cs.MA] 29 Jul 2026

###### Abstract

Auto Research uses language-model agents to propose, implement, and evaluate machine-learning changes in a closed loop, but is usually judged by its terminal pipeline. A terminal score cannot reveal which technical decision produced a gain or distinguish a reusable discovery from a change adapted to development feedback. We introduce intervention-centered Auto Research, which validates research decisions rather than only final artifacts and makes their reliability measurable. Feature, Model, Representation, and Data axes are searched independently with inner five-fold feedback. Each axis winner is frozen before an outer-holdout matrix compares all alternatives on evidence the loop never sees. Across 701 agentexecuted attempts spanning ten Matbench endpoints, outer evidenceconfirmstheselectedinterventiononnineoftenendpointsandpreserves89.3%ofnon-tiedinterventionorderings. ItalsorejectsanaggregateRepresentationgainthatinnerfeedback endorsed. The resulting matrix reveals an informationdependent hierarchy. Composition-only tasks support several routes to improvement, whereas structure-informed tasks favor local geometry features and complementary tree ensembles. A subsequent compatibility test combines already frozen Feature and Model code without further search or tuning and raisesmeanouter-holdoutimprovementfrom19.0%to26.3%. By validating decisions rather than only artifacts, this design turns adaptive search into reusable evidence wherever agents propose executable alternatives against a fixed evaluator.

#### 1 Introduction

Auto Research uses language-model agents to propose, implement, evaluate, and revise machine-learning changes in a closed loop. Existing benchmarks and AI-scientist studies establish that these agents can improve programs, task scores, and research artifacts (Huang et al. 2024; Chan et al. 2025; Jiang et al. 2025; Lu et al. 2026; Novikov et al. 2025; Martinek et al. 2026; Gao, Fang, and Zitnik 2026). The next question is whether decisions from adaptive search remain supported after its feedback loop ends. A final pipeline may entangle data, representation, feature, and model changes, so its score cannot identify what carried the gain. Repeated selection against the same feedback can also favor a change that does not survive new data (Cawley and Talbot 2010; Dwork et al. 2015; Recht et al. 2019). Decision-level validation matters for cumulative science because later work builds on the change that remains justified and reusable, and

a high-scoring artifact alone does not identify that change. Auto Research therefore needs a methodology that preserves attribution during discovery and separates search feedback from final validation.

We develop intervention-centered Auto Research. A research intervention is an executable modification confined to one declared axis of a research workflow. We use axis for the editable category, attempt for one evaluated proposal, and intervention for the selected frozen code. In this study, the axes are Feature, Model, Representation, and Data. The agent proposes and implements candidates on each axis under equal inner feedback. An outer-holdout matrix then compares every intervention on selection regret, ordering, breadth, and compatibility. This makes research decisions attributable and directly comparable where a terminal-pipeline score cannot.

The materials results show both sides of decision validation. Inner feedback retains a structure Representation intervention with a 1.4% gain, but the outer holdout rejects it with a 3.0% loss. Independently searched structure Feature and Model interventions instead lead on different property families. A later deterministic compatibility test combines their frozen code without further search or tuning and improves all six structure endpoints. A terminal score alone cannot expose either the sign reversal or the reusable division of labor.

Materials prediction makes information availability an explicit design factor. Composition-only endpoints expose formula evidence, whereas structure-informed endpoints also expose atomic coordinates. We compare axes within each regime under matched search and evaluation contracts, then use a controlled input comparison on fixed endpoints to separate information type from input dimension. This tests whether an autonomous scientist directs effort toward missinginformationorsimplyrepeatsapreferredmodelingmove.

Across seven campaigns and ten Matbench endpoints, inner five-fold feedback selects the best intervention on nine outer holdouts, while 89.3% of non-tied pairs retain their ordering.Compositionsupportsseveralaxes.Withstructureinputs, Feature leads on phonons and perovskites, while Model leads on elastic and optical tasks. Combining independently found Feature and Model interventions raises mean outerholdout improvement from 19.0% to 26.3%.

This paper makes three contributions.

• Intervention-centered Auto Research. We combine

Search with Feedback

Hypothesis

### Feedback Loop

Lineage Edit code

Evaluation

Feature Model Represen-tation

Data

Freeze

Label Boundary

Code+config+hash

SHA-256 Manifest

Untouched Holdout

9 of 10 selections transfer

Feature Asset

Model Asset

Feedback Loop Frozen Code Held-out Transfer

- Figure 1: Overview of intervention-centered Auto Research. Independent Feature, Model, Representation, and Data searches use inner five-fold feedback. At the label boundary, the selected code, configuration, and SHA-256 manifest are frozen before the untouched outer holdout is evaluated; 9 of 10 inner-selected choices remain best outside the loop.


axis-isolated discovery, inner five-fold feedback, code freezing, and once-only outer-holdout evaluation. The resulting design converts open-ended search into attributable interventions with measurable selection, ordering, breadth, and compatibility.

- Evidence for held-out transfer. Across 701 attempts and ten endpoints, inner five-fold feedback selects the best tested choice on nine outer holdouts, with 0.228 percentage-point mean regret and 89.3% pairwise agreement. The same audit rejects an apparent Representation gain that inner feedback alone would have endorsed.
- Information-dependent findings. Composition-only tasks support several useful axes. With crystal structure, geometry features and complementary tree models lead among those tested, while added composition embeddings do not replace structural information. Separately found feature and model code remains compatible and improves all six structure outer holdouts.


#### 2 Related Work

Automated pipeline and program search. Auto-sklearn and TPOT search machine-learning pipelines, AutoGluon builds stacked ensembles, and AutoML-Zero evolves learning programs from basic operations (Feurer et al. 2015; Olson and Moore 2016; Erickson et al. 2020; Real et al. 2020). FunSearch, AIDE, and AlphaEvolve use language models to search executable programs (Romera-Paredes et al. 2024; Jiang et al. 2025; Novikov et al. 2025). Controlled decompositions of multi-model pipelines further show that an aggregate gain can combine distinct mechanisms (Ning, Li, and Yu 2026). We ask how adaptive research can preserve attribution and test each technical change after search.

Evaluation of AI scientists. The AI Scientist automates a research cycle from ideation through manuscript review (Lu et al. 2026). MLAgentBench and MLE-bench evaluate terminal solutions, while SkillLearnBench separates skill,

trajectory, and outcome quality and finds that feedback gains depend on task structure (Huang et al. 2024; Chan et al. 2025; Zhong et al. 2026). Agentomics and AutoScientists emphasize validated artifacts or long-running team search (Martinek et al. 2026; Gao, Fang, and Zitnik 2026). These evaluations ask what an agent can produce. We ask whether frozen interventions remain supported outside the loop.

The closest Auto Research studies. An anonymized prior study used lineage to search fixed-evaluator training recipes (Anonymous 2026b). A second study certified one axisisolated molecular-prediction intervention against its baseline (Anonymous 2026a). The former evaluates a terminal recipe, and the latter evaluates one selected change against its baseline. We instead freeze every independently searched axis winner and compare them under shared outer evidence. This produces a different evidence object that measures decision regret, alternative ordering, reusable breadth, and cross-axis compatibility rather than another winner-versusbaseline certificate.

Autonomous materials research. LLMatDesign and SparksMatter use language-model feedback to propose and refine candidate materials, while MASTER and MADE optimize sequential simulation or candidate-selection campaigns (Jia, Zhang, and Fung 2024; Ghafarollahi and Buehler 2026; Rothfarbetal.2026;Maliketal.2026).AutoMatinsteadtests whether coding agents can reproduce findings from materials papers (Huang et al. 2026). Autonomous laboratories couple AI with physical experiments (Szymanski et al. 2023; Boiko et al. 2023). Their principal outputs are candidates, discovery efficiency, experimental execution, or reproduction success. We hold the materials tasks and evaluator fixed and study controlled changes to a predictive pipeline. This design exposes which intervention type remains useful under composition-only and structure-informed inputs.

Table 1 positions this work by the evidence each study family produces after search. A strong final artifact does

not reveal whether its constituent changes survive separately. Our design preserves the full set of frozen alternatives and evaluates which technical results transfer beyond adaptive feedback.

Materials prediction and evaluation. Matbench standardizes tasks and folds for inorganic property prediction (Dunn et al. 2020); Matbench Discovery extends evaluation to crystal-stability prediction under realistic discovery objectives (Riebesell et al. 2025). Composition descriptors and models include Magpie, MODNet, Roost, and CrabNet (Ward et al. 2016; De Breuck, Hautier, and Rignanese 2021; Goodall and Lee 2020; Wang et al. 2021), while CGCNN, MEGNet, coNGN, and ALIGNN use crystal geometry (Xie and Grossman 2018; Chen et al. 2019; Ruff et al. 2024; Choudhary and DeCost 2021). We use these families to define candidate interventions rather than proposing another fixed architecture.

#### 3 Intervention-Centered Auto Research

##### Evidence-Separated Search

The method separates discovery, selection, and validation. A campaign is a sequence of propose, edit, and evaluate attempts on one editable axis using only inner five-fold feedback. It freezes the exact selected code as an intervention. The same feedback chooses among these interventions and the baseline. A once-only outer-holdout matrix then scores every alternative on evidence the loop never saw.

Let T be the prediction endpoints and let A contain the editable axes. Our primary outcome is the outer-holdout regret of the intervention selected by inner five-fold feedback, not the gain of the terminal program. For inner fold k, candidate c has direction-corrected normalized improvement

(bt,k − st,k(c))/bt,k, for MAE, (st,k(c) − bt,k)/bt,k, for ROC-AUC,

(1)

ut,k(c) =

where bt,k and st,k(c) are the baseline and candidate scores on the same fold. During search, every score is computed only inside the outer training set. We use K = 5 fixed folds and return

K

1 K

ut,k(c) (2)

dt(c) =

k=1

to the agent. Thus MAE and ROC-AUC enter cross-endpoint aggregation on the same “larger is better” scale. Aggregation therefore reflects relative improvement rather than the raw magnitude of each endpoint’s metric. The per-endpoint choice still uses only that endpoint’s dt. The five-fold average reduces dependence on any single partition and gives every candidate the same multi-partition comparison.

Why inner five-fold feedback matters. In a closed-loop search, feedback both scores the current candidate and determines which hypothesis the agent extends next, so a splitspecific fluctuation can redirect many later experiments. Every candidate receives the same five inner partitions and the same evidence budget before the record is updated. No single partition controls the next branch. The outer holdout has a different role and is evaluated only after code and choices

have been frozen. Combining multi-partition feedback with a code freeze and once-only outer evaluation gives continuous Auto Research a stable ranking signal and a separate audit of the resulting decision.

Each axis a has a separate campaign and set of editable files Ca. The campaign freezes the intervention

1 |Ta| t∈T

dt(c). (3)

c∗a = arg max c∈Ca

a

This produces one frozen intervention per searched axis. For each endpoint, inner five-fold feedback then chooses among the baseline and these interventions,

dt(c∗a), (4)

aˆt = arg max

a∈A∪{0}

with c0 denoting the baseline. The outer-holdout labels play no role in either selection.

##### Materials Instantiation

The Feature axis changes hand-crafted descriptors derived from composition or structure. The Model axis changes the estimator, ensemble, regularization, or output calibration. The Representation axis changes embedding-based inputs, including fraction-weighted mat2vec, MEGNet-derived, and one-hot elemental representations (Tshitoyan et al. 2019; Chen et al. 2019). The Data axis changes agent-curated candidate training rows after formula and source checks. Every campaign starts from the same baseline. Attempts may build on earlier retained code within that campaign, while hashes verify that files outside its assigned axis remain unchanged. Axisisolationisimportantbecauseanend-to-endwinnerthat changes all four axes cannot show which research decision carried the gain.

Each axis also represents a different diagnosis of prediction error. Feature search asks whether the current variables omit useful physics. Representation search asks whether known inputs are encoded poorly. Model search changes the inductive bias that maps inputs to targets. Data search asks whether the observed examples are sufficient. Keeping these diagnoses separate means that a winning axis identifies where the next unit of research effort should go instead of only recording a better configuration.

Within a campaign, the agent proposes a hypothesis, edits the permitted files, invokes the evaluator, and receives the five-fold mean plus execution status. Earlier hypotheses, diffs, scores, and failed experiments are available when proposing the next attempt. This experiment record guides search but is not an evaluation target.

##### Frozen-Code Held-Out Transfer

After freezing all c∗a, the trusted evaluator fits each intervention on outer-training data and scores the holdout. Agentwritten code receives training labels and unlabeled evaluation inputs; only the evaluator process can read outer-holdout labels.

Let ht(c) be the direction-corrected normalized outerholdout improvement, defined in the same way as Eq. (1). We

###### Study family Primary question Unit evaluated after search

Program and pipeline search

Did search find a strong program? Terminal program or pipeline; final task score

End-to-end AI scientists Did the agent produce a valid artifact? Paper or artifact; execution or review Materials agents Did the loop find a useful candidate? Candidate or campaign; simulation or synthesis Prior axis certification Did one selected change generalize? Frozen intervention against its baseline This work Which independently searched

All frozen alternatives; outer-holdout selection, ordering, breadth, and compatibility

intervention remains useful under each information regime?

- Table 1: Positioning by the evidence produced after search. This work compares all independently searched axes on selection, ordering, breadth, and compatibility.


measure the cost of choosing from inner five-fold feedback with selection regret

). (5)

ht(c∗a) − ht(ca∗ˆ

rt = max

t

a∈A∪{0}

An endpoint exhibits held-out transfer when rt = 0. This comparison includes the baseline and independently searched single-axis interventions, but not later combinations. We also compare every within-task pair of interventions. Pairwise ordering agreement asks whether the sign of dt(c∗a) − dt(c∗b) matches the sign of ht(c∗a) − ht(c∗b). This uses the full outer-holdout matrix rather than only its winner.

Unlikeaterminalscore,theouter-holdoutmatrixpreserves selection regret and the ordering of every alternative.

We define endpoint breadth as the number of endpoints for which one frozen intervention has positive outer-holdout effect, ht(c) &gt; 0. Property-family breadth counts a family when atleastoneofitsendpoints has positiveeffect. Compatibility is a separate post-search analysis. After the single-axis outer matrix was complete, we formed one deterministic Feature and Model assembly from the already frozen files without additional search or tuning. This assembly is excluded from the primary 9-of-10 selection result.

#### 4 Experimental Design

Composition tasks. We use the four Matbench endpoints with composition input and experimental targets (Dunn et al. 2020). Experimental band gap and steel yield strength use MAE; metallicity and glass-forming ability use ROC-AUC. The baseline combines 132 Magpie descriptors (Ward et al. 2016, 2018) with CatBoost (Prokhorenkova et al. 2018). Four campaigns search Feature, Model, Representation, and Data. Agent-curated candidate rows are filtered by reduced formula and source before sampling.

Structure tasks. Six MAE endpoints cover phonons (vibrational), bulk and shear moduli (elastic), refractive index (optical), and two-dimensional exfoliation plus perovskite formation energy (thermodynamic), spanning four property families. These are the remaining structure-input Matbench tasks with fewer than 20,000 examples. We omit the three Materials Project tasks with more than 100,000 examples so that every candidate can receive the same CPU-only five-fold evaluation budget. The campaign baseline adds an eightdescriptor density-and-symmetry block to Magpie, giving

140 inputs. Three campaigns search richer structure features, model and calibration changes, and composition embeddings. We evaluate the Data axis on composition tasks, where reduced formula supports exact overlap checks for external rows. Structure tasks instead hold the dataset fixed and compare Feature, Model, and Representation under matched crystal inputs and target definitions. All seven campaigns use the same 100-attempt stopping rule. One campaign recorded a 101st evaluation that completed at the stopping boundary, yielding 701 attempts without changing the frozen intervention. Two Structure-Model attempts terminated during execution before returning a score, leaving 699 scored attempts.

Outer-holdout protocol. We use the official Matbench fold-0 test as the outer holdout and build inner five-fold feedback only from its training partition. Outer-holdout labels are not loaded into an agent process. Once selection is complete, each frozen intervention is retrained on the complete outer training partition and scored on the outer holdout. We also replay frozen configurations over the five official Matbench folds for comparison with published references. Becausefourofthosefoldsreuseexamplesfromthesearchpool, this official-fold replay is post-selection benchmark context rather than a second independent test.

Agent and compute. DeepSeek-V4-Pro (DeepSeek-AI 2026) generated hypotheses and code changes under identical search contracts, budgets, and evaluator access for all axes. Experiments ran with Python 3.12 on a 32-vCPU AWS c7a.8xlarge instance; structure featurization and all model fitting were CPU-only. The analysis uses the complete set of successful and failed attempts, while headline comparisons use only the pre-defined baseline and frozen interventions.

#### 5 Results

Table 2 lists the intervention returned by each campaign. Each entry describes frozen executable code rather than a label assigned after evaluation.

##### Outer Evidence Confirms Nine, Rejects One

Figure 2 gives the primary selection result. Inner five-fold feedback chooses four different intervention types across the ten endpoints. On composition tasks, it chooses a Model change for band gap and glass formation, a Representation

- Figure 2: Intervention selection on ten outer holdouts. Each row reports the effect of the frozen intervention chosen by inner five-fold feedback. The right column checks that choice against the best tested single intervention on the outer holdout; they agree


on nine endpoints. Bars show ht, the direction-corrected normalized outer-holdout improvement. Annotations show relative MAE reductions and absolute ROC-AUC changes.

change for steel strength, and a Feature change for metallicity. All four remain the best tested single intervention on their outer holdouts. Their effects include a 17.4% MAE reduction for band gap, an 18.6% reduction for steel strength, and absolute ROC-AUC gains of 0.0069 and 0.0198 for metallicity and glass formation.

Onstructuretasks,innerfive-foldfeedbackselectstheFeature intervention for phonons, two-dimensional exfoliation, and perovskite formation energy. It selects the Model intervention for both elastic moduli and refractive index. Five of these six choices remain best on the outer holdout. The exception is two-dimensional exfoliation. Its Feature intervention improves inner five-fold MAE from 42.85 to 38.79, but the 128-case outer holdout favors the baseline at 25.53 over 26.11. This endpoint has the smallest evaluation sample in the structure suite, with 128 outer cases and 101–102 cases per inner fold, and is the only task on which the two evidence sources disagree.

Selection regret gives a more graded view than the winner count. It is zero on nine endpoints and 2.279 percentage points on two-dimensional exfoliation, for a ten-task mean of 0.228 points. The full intervention ordering is also largely retained. The composition matrix contains 40 pairwise comparisons among the baseline and four axes, and the structure matrix contains 36 among the baseline and three axes. Inner five-fold and outer-holdout order agree on 67 pairs, reverse

on eight, and tie on one, giving 89.3% agreement among non-ties. Two-dimensional exfoliation is the only negativecorrelation task and accounts for four of the eight reversals. The official-fold replay preserves all ten choices; for metallicity, Feature is the best single axis on every replay fold.

Because the alternatives emerge through repeated reuse of inner feedback rather than from a fixed shortlist, we compare the observed winner count with an exact blocked null. It applies one shared relabeling of inner-feedback choices to outer-holdout interventions within each input regime, preserving each frozen intervention’s identity across tasks. The baseline plus four composition axes admit 5! relabelings, and the baseline plus three structure axes admit 4!, giving 5! × 4! = 2,880 mappings. Chance therefore matches 2.3 outer winners in expectation, and only 4 mappings match at least nine (P = 0.0014). Together, winner count, regret, and ordering measure decision reliability. Nine of ten selections and 89.3% of non-tied orderings survive outside the loop; median task-wise Spearman correlation is 0.95.

Searchdynamics. Of699scoredattempts,131improveon their parent. Composition yields 33 Model, 21 Feature, 13 Representation, and 6 Data improvements; structure yields 31 Feature, 17 Model, and 10 Representation improvements. Choices stabilize by attempt 50, while final code appears at attempts 47–100 (median 96).

Mean gain Breadth

Input Axis Frozen output

Composition Feature Physics descriptors +6.6% 4/4 Model Tree ensembles +6.0% 4/4 Repr. Property-matched

+4.8% 3/4 Data Screened candidate

element pools

+0.2% 3/4

rows

Structure Feature Coordination, geometry, strain, and bond chemistry

+14.6% 5/6

Model CatBoost–LightGBM ensemble

+7.1% 5/6 Repr. Additional

−3.0% 3/6

composition embeddings

- Table 2: Frozen technical outputs, mean normalized outerholdout improvement, and endpoint breadth. Breadth counts endpoints with positive outer-holdout effect. MAE uses relative error reduction and ROC-AUC uses relative gain against the corresponding baseline. Repr. denotes Representation.


##### Intervention Hierarchies Depend on Input

- Figure 3 aggregates the frozen intervention from each axis relative to its baseline. On the four composition tasks, Feature, Model, and Representation interventions improve the outer-holdout mean by 6.6%, 6.0%, and 4.8%, respectively. The Data intervention adds only 0.2%. No single axis dominates composition prediction.


A different hierarchy appears on the structure-informed tasks. Across the six structure tasks, richer Feature code lowersmeanouter-holdoutMAEby14.6%,andModelcodelowersitby7.1%.Addedcompositionembeddingsincreaseerror by 3.0%. These are the two strongest tested axes in this setting. Geometry features reduce phonon MAE by 33.6% and perovskite formation-energy MAE by 47.9%. Model and calibration changes reduce bulk-modulus, shear-modulus, and refractive-index errors by 12.2%, 13.0%, and 9.6%.

Outer evidence rejects the selected Representation. The structure Representation intervention gains 1.4% under inner five-fold feedback but raises outer-holdout error by 3.0%. Losses concentrate on phonons and two-dimensional exfoliation, the two smallest structure datasets, where it adds formula encodings but no local geometry. The controlled comparison below holds the task and estimator fixed.

Input type, not input dimension. Holding the phonon and bulk-modulus endpoints, CatBoost estimator, and official five-fold protocol fixed, we compare three input blocks. The 132-dimensional Magpie baseline has errors of 66.05 cm−1 and 0.0837 in log10(GPa). A 348-dimensional composition encoding formed by adding mat2vec and MEGNet element embeddings changes them to 79.26 cm−1 and 0.0847. Magpie with nine light structure descriptors, including packing efficiency, instead has 141 inputs and errors of 54.98 cm−1 and 0.0655, reductions of 17% and 22%. More

formula-derived capacity does not replace direct structural information.

The 100-attempt Data campaign curates, filters, and recombines candidate rows under strict formula and source checks. Its best intervention improves mean outer-holdout performance by 0.2%, compared with 4.8–6.6% for the other composition axes. Data curation is therefore the least productive tested action in this regime. Axis isolation places this focus of data-centric AI (Zha et al. 2025) on the same quantitative footing as model and representation changes.

Reusable interventions. The frozen interventions are inspectablecode.Compositioninterventionsroutetasksamong element identity, alloy descriptors, compact Magpie statistics, tuned estimators, and tree ensembles. Structure Feature combines coordination, bond geometry, strain, oxidation state, electronegativity, and d-electron statistics; Model combines CatBoost and LightGBM with fitted MAE weights (Prokhorenkova et al. 2018; Ke et al. 2017). Each file-level change can be replayed, ablated, and combined.

The results suggest an allocation principle based on information rather than model brand. Composition descriptors, elementrepresentations,andtreemodelsreorganizethesame formula evidence, so several routes remain productive. Once coordinates are present, coordination, strain, and bond chemistry supply variables that the tested larger formula encoding cannot reconstruct. The 216 added composition dimensions and the nine geometry descriptors quantify this distinction. The useful next action depends on whether the task lacks information or lacks a suitable mapping of information already available.

##### Feature and Model Changes Remain Compatible

The frozen structure Feature and Model interventions each lower error on five of six outer holdouts and reach all four property families, but they specialize. Feature leads on phonons and perovskite formation energy, while Model leads on elastic and refractive properties. The Model intervention was selected for the 140-input baseline, whereas Feature changes the input distribution and the variables available to every tree. The two changes could therefore be redundant or interfere even when each helps alone.

The complementary profiles in the completed single-axis matrix motivate one deterministic compatibility test without further search or tuning. Their union improves all six structure tasks and reduces mean outer-holdout MAE by 26.3%, compared with 19.0% for the best single intervention and 14.6% for Feature alone. Official-fold replay preserves this ordering at 27.0% versus 20.3%, closes 71.5% of the gap from the CPU tabular baseline to the best archived entry, and places refractive-index MAE within 2.2% of MODNet, without graph-neural-network training.

Figure 3: Intervention hierarchies depend on input. Composition supports several useful changes, while structure separates geometry features and models. Data is tested only for composition, which has screened external rows. Structure Representation gains on inner feedback but loses on the outer holdout. Official replay gives post-selection context.

Task Best axis Single (%) F+M (%) Gain (pp) Phonons F 33.57 48.38 +14.81 Bulk modulus M 12.21 15.80 +3.59 Shear modulus M 12.96 16.96 +4.00 Refractive index M 9.58 12.48 +2.90 2D exfoliation F −2.28 0.94 +3.22 Perovskite energy F 47.90 62.95 +15.05 Mean 19.0 26.3 +7.3

- Table 3: Outer-holdout MAE reduction in the deterministic F+M compatibility test. “Single” is the best single axis without the baseline; Gain is the improvement over that component. Official five-fold gap closure is 56.6–88.2% (mean 71.5%) (Chen et al. 2019; Ruff et al. 2024; De Breuck, Hautier, and Rignanese 2021; Materials Project 2024).


#### 6 Conclusion

We introduced intervention-centered Auto Research, which independently searches declared axes, freezes their selected code, and evaluates every intervention in one outer-holdout matrix. The method makes the research decision, rather than an entangled terminal pipeline, the unit of evidence and measures selection, ordering, breadth, and compatibility.

Across 701 attempts and ten Matbench endpoints, inner feedback selected the best tested intervention on nine outer holdouts, with 0.228 percentage-point mean regret and 89.3% ordering agreement. The matrix also rejected a structure Representation intervention that gained 1.4% inside the loop but lost 3.0% outside it.

The materials evidence identifies an informationdependent hierarchy. Composition-only tasks support several axes, while structure tasks favor geometry Feature and complementary Model changes. Holding endpoints, CatBoost, and official folds fixed, nine structure descriptors reduce errors by 17% and 22%, whereas 216 composition dimensions do not help. A deterministic Feature and Model union improves all six outer holdouts, raising the mean from 19.0% to 26.3%; on official replay it closes 71.5% of the archive gap.

Decision-level validation makes adaptive agent search reusable wherever alternatives meet fixed evaluators.

Generative AI use. Generative AI assisted with language and figure editing; the authors remain responsible for all content.

#### References

- Anonymous. 2026a. Prior Work on Axis-Isolated Auto Research for Molecular Property Prediction. Citation anonymized for double-blind review.
- Anonymous. 2026b. Prior Work on Closed-Loop Auto ResearchforTrainingRecipes. Citationanonymizedfordoubleblind review.


Boiko, D. A.; MacKnight, R.; Kline, B.; and Gomes, G. 2023. Autonomous Chemical Research with Large Language Models. Nature, 624: 570–578.

Cawley, G. C.; and Talbot, N. L. C. 2010. On Over-Fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. Journal of Machine Learning Research, 11: 2079–2107.

Chan, J. S.; Chowdhury, N.; Jaffe, O.; Aung, J.; Sherburn, D.; Mays, E.; Starace, G.; Liu, K.; Maksin, L.; Patwardhan, T.; Weng, L.; and Mądry, A. 2025. MLE-Bench: Evaluating Machine Learning Agents on Machine Learning Engineering. In The Thirteenth International Conference on Learning Representations.

Chen, C.; Ye, W.; Zuo, Y.; Zheng, C.; and Ong, S. P. 2019. Graph Networks as a Universal Machine Learning Framework for Molecules and Crystals. Chemistry of Materials, 31(9): 3564–3572.

Choudhary, K.; and DeCost, B. 2021. Atomistic Line Graph Neural Network for Improved Materials Property Predictions. npj Computational Materials, 7: 185.

De Breuck, P.-P.; Hautier, G.; and Rignanese, G.-M. 2021. Materials Property Prediction for Limited Datasets Enabled by Feature Selection and Joint Learning with MODNet. npj Computational Materials, 7: 83.

DeepSeek-AI.2026. DeepSeek-V4:TowardsHighlyEfficient Million-Token Context Intelligence. arXiv:2606.19348.

Dunn,A.;Wang,Q.;Ganose,A.;Dopp,D.;andJain,A.2020. Benchmarking Materials Property Prediction Methods: The Matbench Test Set and Automatminer Reference Algorithm. npj Computational Materials, 6(1): 138.

Dwork, C.; Feldman, V.; Hardt, M.; Pitassi, T.; Reingold, O.; and Roth, A. 2015. The Reusable Holdout: Preserving Validity in Adaptive Data Analysis. Science, 349(6248): 636–638.

Erickson, N.; Mueller, J.; Shirkov, A.; Zhang, H.; Larroy, P.; Li, M.; and Smola, A. 2020. AutoGluon-Tabular: Robust and Accurate AutoML for Structured Data. arXiv:2003.06505.

Feurer, M.; Klein, A.; Eggensperger, K.; Springenberg, J. T.; Blum, M.; and Hutter, F. 2015. Efficient and Robust AutomatedMachineLearning. InAdvancesinNeuralInformation Processing Systems, volume 28, 2962–2970.

Gao, S.; Fang, A.; and Zitnik, M. 2026. AutoScientists: Self-Organizing Agent Teams for Long-Running Scientific Experimentation. arXiv:2605.28655.

Ghafarollahi, A.; and Buehler, M. J. 2026. Autonomous In-Silico Inorganic Materials Discovery via Multi-Agent Physics-AwareScientificReasoning. npjComputationalMaterials, 12. Advance online publication.

Goodall, R. E. A.; and Lee, A. A. 2020. Predicting Materials Properties without Crystal Structure: Deep Representation Learning from Stoichiometry. Nature Communications, 11: 6280.

Huang, Q.; Vora, J.; Liang, P.; and Leskovec, J. 2024. MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation. In Proceedings of the 41st International Conference on Machine Learning, volume 235 of Proceedings of Machine Learning Research, 20271–20309.

Huang, Z.; Cao, Y.; Shargh, A. K.; Luo, J.; Mei, R.; Zaki, M.; Liu, Z.; Bunstine, W.; Jurayj, W.; Goswami, S.; McQueen, T.; Shields, M.; El-Awady, J.; Clancy, P.; Van Durme, B.; Andrews, N.; Walden, W.; and Khashabi, D. 2026. Can Coding Agents Reproduce Findings in Computational Materials Science? arXiv:2605.00803.

Jia, S.; Zhang, C.; and Fung, V. 2024. LLMatDesign: Autonomous Materials Discovery with Large Language Models. arXiv:2406.13163.

Jiang, Z.; Schmidt, D.; Srikanth, D.; Xu, D.; Kaplan, I.; Jacenko, D.; and Wu, Y. 2025. AIDE: AI-Driven Exploration in the Space of Code. arXiv:2502.13138.

Ke, G.; Meng, Q.; Finley, T.; Wang, T.; Chen, W.; Ma, W.; Ye, Q.; and Liu, T.-Y. 2017. LightGBM: A Highly Efficient Gradient Boosting Decision Tree. In Advances in Neural Information Processing Systems, volume 30, 3146–3154.

Lu, C.; Lu, C.; Lange, R. T.; Yamada, Y.; Hu, S.; Foerster, J.; Ha, D.; and Clune, J. 2026. Towards End-to-End Automation of AI Research. Nature, 651: 914–919.

Malik, S. A.; Doherty, T.; Tigas, P.; Razzak, M.; Roberts, S.; Walsh, A.; and Gal, Y. 2026. MADE: Benchmark Environments for Closed-Loop Materials Discovery. In Proceedings of the 43rd International Conference on Machine Learning. Martinek, V.; Gariboldi, A.; Tzimotoudis, D.; Galea, M.; Zacharopoulou, E.; Alberdi Escudero, A.; Blake, E.; Čechák, D.; Cassar, L.; Balestrucci, A.; and Alexiou, P. 2026. Agentomics: An Agentic System that Autonomously Develops Novel State-of-the-Art Solutions for Biomedical Machine Learning Tasks. Bioinformatics, 42(Supplement 1): btag250. Materials Project. 2024. Official Matbench v0.1 Benchmark SubmissionsandLeaderboard. OfficialMatbenchrepository, https://github.com/materialsproject/matbench. Benchmark archive revision 936176d, dated 20 January 2024; accessed 10 July 2026.

Ning, J.; Li, X.; and Yu, C. 2026. Revision or Re-Solving? Decomposing Second-Pass Gains in Multi-LLM Pipelines. arXiv:2604.01029.

Novikov, A.; Vu, N.; Eisenberger, M.; Dupont, E.; Huang, P.-S.; Wagner, A. Z.; Shirobokov, S.; Kozlovskii, B.; Ruiz, F. J. R.; Mehrabian, A.; Kumar, M. P.; See, A.; Chaudhuri, S.; Holland, G.; Davies, A.; Nowozin, S.; Kohli, P.; and Balog, M. 2025. AlphaEvolve: A Coding Agent for Scientific and Algorithmic Discovery. arXiv:2506.13131.

Olson, R. S.; and Moore, J. H. 2016. TPOT: A Tree-Based Pipeline Optimization Tool for Automating Machine Learning. In Proceedings of the Workshop on Automatic Machine Learning, volume 64 of Proceedings of Machine Learning Research, 66–74. PMLR.

Prokhorenkova, L.; Gusev, G.; Vorobev, A.; Dorogush, A. V.; and Gulin, A. 2018. CatBoost: Unbiased Boosting with Categorical Features. In Advances in Neural Information Processing Systems, volume 31, 6638–6648.

Real, E.; Liang, C.; So, D. R.; and Le, Q. V. 2020. AutoMLZero: Evolving Machine Learning Algorithms From Scratch. In Proceedings of the 37th International Conference on Machine Learning, volume 119 of Proceedings of Machine Learning Research, 8007–8019. PMLR.

Recht, B.; Roelofs, R.; Schmidt, L.; and Shankar, V. 2019. Do ImageNet Classifiers Generalize to ImageNet? In Proceedings of the 36th International Conference on Machine Learning, volume 97 of Proceedings of Machine Learning Research, 5389–5400. PMLR.

Riebesell, J.; Goodall, R. E. A.; Benner, P.; Chiang, Y.; Deng, B.; Ceder, G.; Asta, M.; Lee, A. A.; Jain, A.; and Persson, K. A. 2025. A Framework to Evaluate Machine Learning Crystal Stability Predictions. Nature Machine Intelligence, 7(6): 836–847.

Romera-Paredes, B.; Barekatain, M.; Novikov, A.; Balog, M.; Kumar, M. P.; Dupont, E.; Ruiz, F. J. R.; Ellenberg, J. S.; Wang, P.; Fawzi, O.; Kohli, P.; and Fawzi, A. 2024. Mathematical Discoveries from Program Search with Large Language Models. Nature, 625: 468–475.

Rothfarb, S.; Davis, M. C.; Matanovic, I.; Li, B.; Holby, E. F.; and Kort-Kamp, W. J. M. 2026. Hierarchical Multi-Agent Large Language Model Reasoning for Autonomous Heterogeneous Catalyst Discovery. npj Computational Materials, 12. Advance online publication.

Ruff, R.; Reiser, P.; Stühmer, J.; and Friederich, P. 2024. Connectivity Optimized Nested Line Graph Networks for Crystal Structures. Digital Discovery, 3: 594–601.

Szymanski, N. J.; Rendy, B.; Fei, Y.; Kumar, R. E.; He, T.; Milsted, D.; McDermott, M. J.; Gallant, M.; Cubuk, E. D.; Merchant, A.; Kim, H.; Jain, A.; Bartel, C. J.; Persson, K.; Zeng, Y.; and Ceder, G. 2023. An Autonomous Laboratory for the Accelerated Synthesis of Novel Materials. Nature, 624: 86–91.

Tshitoyan, V.; Dagdelen, J.; Weston, L.; Dunn, A.; Rong, Z.; Kononova, O.; Persson, K. A.; Ceder, G.; and Jain, A. 2019. Unsupervised Word Embeddings Capture Latent Knowledge from Materials Science Literature. Nature, 571: 95–98.

Wang, A. Y.-T.; Kauwe, S. K.; Murdock, R. J.; and Sparks, T.D.2021. CompositionallyRestrictedAttention-BasedNetwork for Materials Property Predictions. npj Computational Materials, 7: 77.

Ward, L.; Agrawal, A.; Choudhary, A.; and Wolverton, C. 2016. A General-Purpose Machine Learning Framework for Predicting Properties of Inorganic Materials. npj Computational Materials, 2: 16028.

Ward, L.; Dunn, A.; Faghaninia, A.; Zimmermann, N. E. R.; Bajaj, S.; Wang, Q.; Montoya, J.; Chen, J.; Bystrom, K.; Dylla, M.; Chard, K.; Asta, M.; Persson, K.; Snyder, G. J.; Foster, I.; and Jain, A. 2018. Matminer: An Open Source Toolkit for Materials Data Mining. Computational Materials Science, 152: 60–69.

Xie, T.; and Grossman, J. C. 2018. Crystal Graph Convolutional Neural Networks for an Accurate and Interpretable Prediction of Material Properties. Physical Review Letters, 120(14): 145301.

Zha, D.; Bhat, Z. P.; Lai, K.-H.; Yang, F.; Jiang, Z.; Zhong, S.; and Hu, X. 2025. Data-Centric Artificial Intelligence: A Survey. ACM Computing Surveys, 57(5): 1–42.

Zhong, S.; Lu, Y.; Ning, J.; Wan, Y.; Feng, L.; Ao, Y.; Ribeiro, L. F. R.; Dreyer, M.; Ammirati, S.; and Xiong, C. 2026. SkillLearnBench: Benchmarking Continual Learning Methods for Agent Skill Generation on Real-World Tasks. arXiv:2604.20087.

