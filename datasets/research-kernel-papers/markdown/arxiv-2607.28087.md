## Diversifying Personalized Research Ideation against AI-Induced Homogenization

#### Rui Xu1, Yunke Wang2, Linwei Tao2, Wenjie Xuan1, Yong Luo1

1Wuhan University, 2The University of Sydney xurui7943@gmail.com, {yunke.wang, linwei.tao}@sydney.edu.au, {dreamxwj, luoyong}@whu.edu.cn

# arXiv:2607.28087v1 [cs.AI] 30 Jul 2026

###### Abstract

AI-assisted research ideation has emerged as a promising paradigm for accelerating scientific discovery, with systems now capable of generating research directions conditioned on papers, topics, or lightweight researcher contexts. Yet current systems largely optimize individual suggestions in isolation. This leaves two blind spots. First, coarse researcher representations may elicit mainstream directions that appear broadly feasible, but lack sufficient researcher-specific grounding. Second, independent recommendations can concentrate a community’s portfolio around recurring highprobability themes. To address these blind spots, we propose DivAlign, a four-stage pipeline for alignment-preserving dehomogenization. DivAlign extracts fine-grained researcher profiles, generates profile-conditioned candidate directions, scores them along three alignment dimensions (Executability, Comprehensibility, and Growth Potential), and surfaces researcher-local directions while reducing redundancy across the community portfolio. On a benchmark we construct from 95 AI researchers across five subfields, DivAlign reduces community-level redundancy while preserving researcherdirection fit. Compared with coarse single-shot ideation, it lowers average pairwise similarity from 0.331 to 0.294 and nearest-neighbor similarity from 0.704 to 0.608. Compared with the independent top-choice variant, DivAlign reduces nearest-neighbor similarity from 0.663 to 0.608 while retaining 99.9% of the researcher-direction fit score. Code and data are available at https://github.com/Ruixxxx/DivAlign.

#### Introduction

AI-assisted research ideation has become an increasingly plausible way to accelerate scientific discovery. Recent systems can generate, refine, and evaluate research directions frompapers,topics,orresearcher-providedcontexts(Luetal. 2026; Yamada et al. 2025; Baek et al. 2025; Hu et al. 2025; Yu et al. 2025a). As these systems begin to influence not only individualsuggestionsbutalsothesetofdirectionsaresearch community may collectively explore, their portfolio-level effects become increasingly important.

Existing ideation systems address important parts of this landscape,butmostlyoperateatthelevelofcandidategeneration, refinement, or simulation. Systems such as ResearchAgent (Baek et al. 2025), SciMON (Wang et al. 2024), and Nova (Hu et al. 2025) improve idea generation through retrieval, planning, or search, with some explicitly promoting diversity among generated ideas. Multi-agent and

Given my profile, suggest one promising research idea.

Given my profile, suggest one promising research idea.

Build an autonomous research agent for hypothesis generation and validation.

Evidence-grounded idea generation from citation trails.

AI for Research | literature-based ideation

AI for Research | literature-based ideation

Given my profile, suggest one promising research idea.

Given my profile, suggest one promising research idea.

Build an autonomous research agent for hypothesis generation and validation.

Experiment-planning agents for reproducible ablation studies.

AI for Research | experiment automation

AI for Research | experiment automation

(a) (b)

Figure 1: (a) Simple profile-conditioned ideation can still generate the same generic high-probability idea to researchers with different expertise, leading to directions that areplausiblebutnotnecessarilytailoredordeeplyactionable. (b) DivAlign aims to surface researcher-aligned directions while improving community-level diversity, so researchers in the same broad area receive distinct suggestions that better match their own backgrounds.

community-simulation systems such as IDVSci (Yu et al. 2025b) and ResearchTown (Yu et al. 2025a) introduce collaboration, knowledge exchange, or researcher-paper representations. These systems can improve idea quality, novelty, or generation-side diversity, but they do not directly address the recipient-side portfolio question: when a community of researchers uses an ideation system, how should researcherlocal directions be surfaced so that the resulting portfolio remains both aligned and non-redundant?

This exposes two blind spots in AI-assisted research ideation. The first is insufficient researcher-specific grounding. Many systems condition on a paper, topic, or lightweight researcher context, but such context may be too coarse to determine whether a specific researcher can critically situate, defend, and develop a suggested direction. A direction may appear broadly executable in a technical sense while still being weakly grounded in the researcher’s trajectory, artifacts, or literature ownership. Recent execution studies further suggest that promising AI-generated research ideas may degrade after actual implementation, highlighting the gap between plausible ideation and executable research outcomes (Si, Hashimoto, and Yang 2026; Wu et al. 2026). The

second blind spot is portfolio-level homogenization. Prior work has shown that large language model (LLM) assistance can improve individual outputs while reducing collective diversity (Doshi and Hauser 2024), and that LLM-generated research ideas can be judged novel while remaining weaker in feasibility and limited in generation diversity (Si, Yang, and Hashimoto 2025). Moreover, diversity collapse can also arise in multi-agent LLM ideation when interaction patterns cause premature convergence (Chen et al. 2026). These findings suggest that AI ideation should be evaluated not only by whether each idea is individually plausible, but also by whether the surfaced portfolio reduces redundancy while preserving researcher-direction fit.

- Figure 1 illustrates this failure mode. Researchers with


different technical trajectories may receive directions centered on the same high-probability theme when they query an ideation system independently. The issue is not that any individual suggestion is unreasonable; each may be broadly aligned with its intended researcher. Rather, the communitylevel portfolio can become semantically concentrated: the same themes are repeatedly surfaced, while adjacent but viable alternatives remain under-explored. This phenomenon is later quantified in a diagnostic pilot study, which shows that repeated directions emerge even in a small community under lightweight researcher-context ideation.

We propose DivAlign, a four-stage pipeline for alignmentpreserving de-homogenization in AI-assisted research ideation.First,DivAlignextractsfine-grainedresearcherprofiles, including research lineage, owned artifacts, and known gaps. Second, it generates a local pool of candidate directions conditioned on each profile. Third, it scores each candidate along three alignment dimensions: Executability, measuring whether the researcher can realistically implement the direction; Comprehensibility, measuring whether the researcher can critically engage with the relevant literature and methodological choices; and Growth Potential, measuring whether the direction provides a productive stretch beyond prior work. Fourth, DivAlign surfaces researcher-local directions with a portfolio-level redundancy penalty. This design keeps each surfaced direction within the researcher’s own candidate pool, while making community-level redundancy visible during selection.

We make the following contributions:

- We identify portfolio-level homogenization as a failure mode in AI-assisted research ideation: independently surfaced directions can be individually plausible yet collectively redundant.
- We propose DivAlign, a training-free four-stage pipeline that combines fine-grained profile extraction, conditioned directiongeneration,three-componentalignmentscoring, and community-aware selection.
- We introduce a researcher-direction fit rubric that decomposes alignment into Executability, Comprehensibility, and Growth Potential, moving beyond topical matching.
- We construct a 95-researcher benchmark across five AI subfields and show that DivAlign reduces both average and nearest-neighbor redundancy while preserving researcher-direction fit.


#### Related Works

Research Ideation. A growing ecosystem of systems attempts to automate research ideation and scientific discovery (Lu et al. 2026; Wan et al. 2026). AI-Scientist (Lu et al. 2026; Yamada et al. 2025), AI-Researcher (Tang et al. 2025), and Sibyl-AutoResearch (Wang et al. 2026) study increasingly autonomous research loops, covering idea generation, experimental validation, and trial-and-error harnesses for accumulating research judgment. ResearchAgent (Baek et al. 2025), EvoScientist (Lyu et al. 2026), and SciMON (Wang

- et al. 2024) improve idea generation through iterative refinement or literature-grounded inspiration. Nova (Hu et al.

2025) further uses iterative planning and search to promote novelty and diversity among generated ideas. Multi-agent and community-simulation systems such as VirSci (Su et al. 2025), IDVSci (Yu et al. 2025b), and ResearchTown (Yu

- et al. 2025a) introduce collaboration, knowledge exchange, diversity-aware review, or researcher-paper representations. These systems substantially improve research idea generation, evaluation, and simulation, but they mostly focus on generation-side quality or diversity. Researcher profiles, when used, are typically lightweight conditioning signals or simulation states rather than fine-grained objects for explicit researcher-direction fit scoring. DivAlign studies a complementary setting: surfacing researcher-local directions for a community of researchers, while preserving researcherdirection fit and reducing portfolio redundancy.


Homogenization. Recent work has shown that AI assistance can improve individual outputs while reducing diversity at the collective level. Doshi and Hauser (Doshi and Hauser 2024) find this effect in creative writing: access to generative AI improves individual creativity ratings, but makes stories more similar to one another. Related work on algorithmic monoculture and epistemic diversity further suggests that shared models or information sources can produce correlated behavior and narrower knowledge exposure at the group level (Ballestero et al. 2026; Hodel and West 2025; Wright et al. 2025). Recent studies refine this picture for LLM outputs and ideation. Output homogenization is task-dependent, so diversity should be evaluated with respect to the function of the task rather than only generic lexical or embedding variation (Jain et al. 2025). In open-ended ideation,diversitycollapsecanalsoariseinmulti-agentLLM systems when interaction structures induce premature convergence (Chen et al. 2026). Complementary work identifies generation-side barriers to idea diversity, such as fixation and the lack of human-like knowledge partitioning across independentsamples(Deng,Brucks,andToubia2026).DivAlign studies the corresponding portfolio problem in AI-assisted research ideation. Rather than treating diversity only as a generation-time objective, DivAlign combines researcherlocal candidate generation with alignment-aware portfolio de-homogenization.

#### Pilot Study

We begin with a pilot study to examine two basic questions in AI research idea generation. First, when research directions are produced for a community of researchers, do

Metric Value HS ↓ 0.316 Distinct idea groups ↑ 22/24 Non-singleton groups 2 Researchers in repeated groups 4/24 Largest group size 2

Table 1: Repeated idea exposure in small-scale research idea generation.

repeated ideas emerge across different researchers? Second, if repeated ideas are undesirable, can we simply make the generated directions more diverse, or must diversity be constrained by whether each direction still fits the researcher who receives it?

Setup. We sample N = 24 researchers from three AIrelated areas: efficient AI, medical AI, and video understanding,witheightresearchersineacharea.Followingtheprofilebased researcher representation used in (Yu et al. 2025a), each researcher is represented by biography and publication titles only. For each researcher, we prompt an LLM (Claude Haiku) once (K = 1) to generate one future research direction. We then use the same set of directions to measure community-level homogenization and researcherdirection fit.

For homogenization, we report HS, the mean pairwise cosine similarity among the generated directions. Each generated direction di is encoded into a sentence embedding vi using Sentence-BERT (SBERT) (Reimers and Gurevych 2019) before similarity computation. Higher HS indicates stronger semantic concentration. We also report Distinct, the number of distinct idea groups after near-duplicate merging. Following (Si, Hashimoto, and Yang 2026), we link two directions if their embedding cosine similarity is at least 0.8.

For researcher-direction fit, we use our rubric-defined alignment score A(r,d), which summarizes three complementary aspects: whether direction d is executable by researcher r, whether it is comprehensible given r’s background, and whether it provides a feasible growth opportunity beyond r’s existing work. The full scoring rubric is describedinthemethoddescription.Givenadirectiondi generated for researcher ri, Aligned denotes the score A(ri,di), while Misaligned denotes the average score A(rj,di) over other researchers j ̸= i. We report the aligned score, the misaligned score, and their absolute gap.

Finding 1. Repeated ideas emerge even in a small community of researchers.

- As shown in Table 1, the 24 generated directions yield


HS = 0.316 and 22 distinct idea groups after near-duplicate merging. Two non-singleton groups cover 4 of the 24 researchers; both consist of pairs within the same sub-area whose directions converge on uncertainty quantification in clinical image analysis, a high-citation theme that LLMs tend tosurfacewhenresearcherprofilesarecoarse.Thisillustrates a key limitation of coarse profiling: researchers with partially overlapping expertise receive directions that are thematically indistinguishable, motivating the use of fine-grained pro-

Dimension Aligned Misaligned Gap

Executability 0.865 0.605 +0.260 Comprehensibility 0.845 0.583 +0.262 Growth Potential 0.585 0.594 −0.009

Aggregate 0.765 0.594 +0.171

Table 2: Aligned vs. misaligned researcher-direction fit in small-scale research idea generation.

files. Thus, while the idea pool does not collapse completely, repeated exposure already appears in a small N = 24 community.

Finding 2. Diversity must preserve researcher-direction alignment.

Table 2 shows that directions are substantially better aligned with the researchers for whom they were generated. The aggregate score drops from 0.765 to 0.594 when directions are scored against other researchers, giving an absolute gap of 0.171. This gap is mainly driven by executability and comprehensibility, while growth potential is near neutral (−0.009), suggesting that directions from other researchers may appear equally novel but are less executable and less comprehensible for the recipient.

Implication. Finding 1 shows that repeated idea exposure can emerge even in a small research community under lightweight researcher-context ideation. Finding 2 shows that this redundancy cannot be addressed by treating directions as interchangeable: when directions are scored against other researchers, aggregate alignment drops from 0.765 to 0.594, with the largest penalties appearing in executability and comprehensibility. Together, these findings suggest that de-homogenization cannot be reduced to generic diversity maximization. This motivates our core design goal: reducing repeatedideaexposurewhilekeeping each surfaceddirection within the intended researcher’s alignment-feasible region.

#### DivAlign

Problem Setup. We consider a community of N researchersR = {r1,...,rN}.AnAIideationsystemsurfaces one research direction si for each researcher ri, forming a community portfolio S = {si}Ni=1.

The goal is alignment-preserving de-homogenization: each surfaced direction should be appropriate for its intended researcher,whiletheportfolioasawholeshouldavoidrepeatedly exposing different researchers to semantically similar directions. Unlike generic diversity maximization, the objective is to reduce redundancy without sacrificing researcherdirection fit.

To satisfy this goal, DivAlign proceeds in four stages. It first extracts fine-grained researcher profiles, then generates a local candidate pool of conditioned directions, scores each candidate with a three-component alignment rubric, and finally performs community-aware selection with a portfolio redundancy penalty.

Researchers

1 Fine-GrainedProfile Extraction

- r1
- r2
- r3


Researcher ri

- Name
- Affiliation
- Bio
- Publications
- …


Profile pi Background

### ⋮

Research Lineage Owned Artifacts Known Gaps

ri

###### Conditioned Direction Generation

###### 3 Three-ComponentAlignment Scoring

4 Community-AwareSelection

###### 2

Final portfolio S={si}

- D1

- D2

- D3


Executable

Candidate pool Di

Profile pi

Profile pi

Comprehensible

- s1

- s2

- s3


Growth-enabling

A(ri,d)=(E+C+G)/3

### ⋮ ⋮

###### Candidate pool Di d¹ d² d³ ... dK

Di

si

E Executability

C Comprehensibility

Score=A(ri,d)− λ·max simd′∈S(d, d′)

G Growth Potential

- Figure 2: Overview of DivAlign. The colored researcher cards on the left denote a set of researchers R = {ri}Ni=1, and the stacked colored frames indicate that Stages 1-3 are applied independently to each researcher. Stage 1 extracts a structured profile pi from


researcher ri’s background and publication history. Stage 2 uses pi to generate a local candidate pool Di = {d1i,...,dKi } of profile-conditioned research directions. Stage 3 scores each candidate direction d ∈ Di using a three-component alignment score A(ri,d) = (E + C + G)/3, where E, C, and G denote Executability, Comprehensibility, and Growth Potential, respectively. Stage 4 is the only community-level step: it considers all local candidate pools and selects a final surfaced portfolio S = {si}Ni=1 with si ∈ Di, penalizing redundancy with already surfaced directions.

##### Stage 1: Fine-Grained Profile Extraction

For each researcher ri, a structured fine-grained profile pi is constructed from observable researcher evidence. The evidence includes the researcher’s name, affiliation, biography, and up to 15 recent publications represented by titles and abstracts. An LLM is used to extract three profile components from this evidence: research lineage, owned artifacts, and known gaps. These components capture the researcher’s trajectory, accumulated technical assets, and open problems surfaced from prior work. The profile pi is serialized into separate sections for background, research lineage, owned artifacts, and known gaps. This structured profile serves as the observable representation of researcher ri: it is used to condition candidate direction generation in Stage 2 and to evaluate candidate directions along the three alignment dimensions in Stage 3. The exact extraction prompt is shown in the appendix.

##### Stage 2: Conditioned Direction Generation

For each researcher ri, we condition an LLM on the finegrained profile pi and generate a local candidate pool Di = {d1i,...,dKi }. The generation prompt asks each candidate directiontosatisfythreeresearcher-specificalignmentconditions: executable, meaning achievable using the researcher’s existing and naturally transferable skills; comprehensible, meaningtheresearchercancriticallyengagewiththerelevant literature and methodological choices; and growth-enabling, meaning the direction productively stretches the researcher’s frontier without merely repeating prior work or jumping to an unreachable domain.

Each generated direction contains two types of fields. The title, proposal, and keywords provide a researcher-agnostic

representation of the direction and are used for Stage 3 scoring. The researcher-specific description is retained as an explanatory pitch for the intended researcher, explaining why the direction fits their background and what new capability it would require. The exact generation prompt and output format are provided in the appendix.

This stage builds researcher-direction fit into candidate generation,ratherthandeferringittopost-hocfiltering.However,becausecandidatepoolsaregeneratedindependentlyfor each researcher, local candidate diversity does not by itself prevent community-level homogenization. Stage 4 therefore handles portfolio-level redundancy explicitly.

##### Stage 3: Three-Component Alignment Scoring

Stage 3 provides an independent post-generation quantitative assessment of how well the Stage 2 directions fit their intended researchers. The resulting researcher-direction alignment score allows Stage 4 to compare candidates on a common scale and trade off individual fit against portfolio-level redundancy.

For researcher ri with profile pi and candidate direction d, the alignment score is

1 3

[E(ri,d) + C(ri,d) + G(ri,d)] ∈ [0,1],

A(ri,d) =

(1) where E, C, and G denote Executability, Comprehensibility, and Growth Potential, respectively. The notation uses ri to emphasize researcher-level fit; the score is estimated from the observable profile pi.

Executability measures whether the researcher can implement the direction using existing technical skills and naturally transferable competencies. It rewards directions whose

core algorithmic and engineering requirements are within reach, and penalizes directions requiring incompatible infrastructure or an unrelated technical paradigm.

Comprehensibility measures whether the researcher can criticallyengagewiththerelevantliterature:identifyinggaps, comparing methodological choices, and defending the direction under peer review. This differs from executability: a researcher may be able to implement a method but lack sufficient grounding to situate it within the field.

Growth Potential measures whether the direction provides a productive stretch beyond the researcher’s existing work. Unlike Executability and Comprehensibility, which reward fit, Growth Potential is modeled as an inverted-U function of skill overlap: it is low for directions that merely repeat prior work, low for directions that are too distant, and highest near the researcher’s Zone of Proximal Development (Vygotsky 1978).

All three component scores for each candidate direction are elicited together using a dedicated LLM evaluation prompt. The exact scoring prompt is in the appendix.

##### Stage 4: Community-Aware Selection

After Stages 1-3 have produced researcher-specific candidate pools and alignment scores, Stage 4 selects one surfaced direction for each researcher while penalizing redundancy with the directions already selected for the community. Selection is restricted to each researcher’s own candidate pool Di.

Let S denote the set of directions selected so far. For a

candidate direction d ∈ Di, we define its redundancy with the current portfolio as

0, S = ∅, maxd′∈S sim(d,d′), otherwise,

(2) wheresimiscosinesimilaritybetweensentenceembeddings.

ρ(d,S) =

- At each greedy step, Stage 4 selects


[A(ri,d) − λρ(d,S)], (3)

(i∗,d∗) = arg max i∈U, d∈Di

where U is the set of researchers not yet assigned a surfaced direction. Unlike fixed-order sequential selection, this greedy rule does not impose an arbitrary researcher order: each step maximizes over all remaining researcher-direction pairs, with redundancy evaluated against the portfolio constructed so far. This Maximal Marginal Relevance (MMR)style rule (Carbonell and Goldstein 1998) favors candidates with high researcher-direction alignment and low redundancy with the current community portfolio. We use maxsim redundancy because repeated idea exposure is driven by near-duplicates: a candidate should be penalized if it closely resembles any already surfaced direction, whereas mean-sim can dilute a single strong overlap among many unrelated directions. The trade-off parameter λ ≥ 0 controls the strength of the redundancy penalty; λ = 0 recovers independent local top-choice selection.

#### Experiments

##### Experimental Setup

Benchmark. We construct a multi-researcher benchmark of N = 95 AI researchers drawn from five subfields: video

Algorithm 1: DivAlign Require: Researchers{ri}Ni=1,candidatesperresearcherK,

trade-off λ

Ensure: Portfolio S = {si}Ni=1 with si ∈ Di

- 1: for each researcher ri do
- 2: Stage 1: extract structured profile pi
- 3: Stage 2: generate candidate pool Di = {d1i,...,dKi } conditioned on pi
- 4: Stage 3: score candidates {A(ri,d) : d ∈ Di}
- 5: end for
- 6: S ← ∅; U ← {1,...,N}
- 7: while U ̸= ∅ do
- 8: (i∗,d∗) ← arg maxi∈U, d∈D

i

[A(ri,d) − λρ(d,S)]

- 9: si∗ ← d∗; S ← S ∪ {d∗}; U ← U \ {i∗}
- 10: end while
- 11: return S


understanding (20), medical AI (20), 3D vision (20), embodied AI (20), and efficient AI (15). Each researcher is represented by a profile of publications from 2018-2022 (3-15 papers per researcher, 930 in total). Biographies are collected from researcher homepages.

Metrics. HS is the mean pairwise cosine similarity among the N surfaced directions (defined in the pilot study); it measures community-level semantic concentration and follows the common practice of using intra-set similarity to evaluate diversity (Tevet and Berant 2021; Padmakumar and He 2024). NS is the average nearest-neighbour cosine sim-

ilarity: N1 i maxj̸=i cos(vi,vj); it directly measures nearduplicate exposure for each surfaced direction and is more

sensitive to redundant pairs than HS. VS is the normalized Vendi Score (Friedman and Dieng 2023; Chen et al. 2026), computed from the similarity matrix of the surfaced directions. It provides a set-level effective-diversity measure that complements pairwise concentration metrics. We also report E, C, and G for Executability, Comprehensibility, and Growth Potential, with their mean denoted as Align.. They are measured using a batched rubric-based LLM-as-ajudge protocol: directions compared within the same table are judged against the same researcher profile, with randomized order and hidden method labels.

Implementation. We use claude-haiku-4-5 for all LLM calls and compute sentence embeddings using all-mpnet-base-v2 (Reimers and Gurevych 2019). We generate K = 5 candidate directions per researcher and set λ = 0.2 as the default redundancy weight.

##### Main Results

We compare DivAlign with two baselines and two limiting variants. Coarse-K1 uses a lightweight ResearchTownstyle (Yu et al. 2025a) context, biography and publication titles only, to generate one direction per researcher; for fair evaluation, the surfaced directions are scored against the full fine-grained profile. Random uniformly samples one direction from each researcher’s fine-profile candidate pool Di. We also evaluate two limits of DivAlign’s redundancy

###### Method HS↓ NS↓ VS↑ E↑ C↑ G↑

Coarse-K1 0.331 0.704 0.220 0.803 0.765 0.687 Random 0.302 0.640 0.269 0.795 0.768 0.727

Ours (λ = 0) 0.303 0.663 0.262 0.817 0.793 0.711 Ours (λ = 0.2) 0.294 0.608 0.289 0.822 0.801 0.696 Ours (λ → ∞) 0.265 0.555 0.328 0.802 0.777 0.701

Table 3: Main results on the multi-researcher benchmark. HS ↓ and NS ↓ measure community-level redundancy; VS ↑ measures semantic spread. E/C/G are the alignment components (all ↑). Bold = best; underline = second best; gray italic = worst.

weight. Independent sets λ = 0, so each researcher receives the highest-alignment candidate from their own pool. Diversity-Only corresponds to the λ → ∞ limit, where selection is driven only by redundancy.

Table 3 reveals the core redundancy-alignment trade-off. Coarse-K1 yields the most redundant portfolio, although its directions remain reasonably executable and growthoriented: broad high-level suggestions can look feasible in isolation, but they also recur across researchers and provide weaker researcher-specific grounding. Random can improve over coarse prompting, but it ignores both alignment scores and portfolio redundancy, showing that a richer candidate pool alone is insufficient.

The DivAlign variants further isolate the role of selection. Independent selection preserves the strongest researcherdirection fit but remains redundant, while Diversity-Only improves raw diversity at a clear alignment cost. DivAlign with λ = 0.2 achieves the best observed balance: it substantially reduces cross-researcher redundancy and improves effective diversity over Independent, while retaining 99.9% of its alignment score (0.773 vs. 0.774). This suggests that fine-profiled candidates expand each researcher’s local direction space, and community-aware selection can then choose among these researcher-aware alternatives to de-homogenize the community portfolio while preserving alignment.

##### Ablation Study

Design Progression. Table 4 shows that Coarse-K1 and Fine K = 1 have similar HS and NS, but likely for different reasons: coarse prompting induces broad generic repetition, whereas fine-grained profiling can still produce local repetition among researchers sharing similar subfield contexts. In other words, fine-grained profiling improves researcherdirection fit, but does not by itself reduce portfolio-level redundancy. Multiple candidates can expand each researcher’s local direction space, and DivAlign uses community-aware selection to choose among these researcher-aligned alternatives. The improvement therefore comes from combining fine-grained researcher modeling with community-level redundancy control, reducing local repetition without leaving the alignment-feasible region.

Alignment Scoring. We next ablate the score used for A(ri,d) while keeping the candidate pools and the community-aware selection procedure fixed. The TF-IDF

Profile K Selection HS↓ NS↓ VS↑ Align.↑

Coarse 1 – 0.331 0.704 0.220 0.752 Fine 1 – 0.330 0.706 0.221 0.772

Fine 5 Independent 0.303 0.663 0.262 0.774 Fine 5 DivAlign 0.294 0.608 0.289 0.773

Table 4: Design progression. The K = 1 rows are single-shot generation settings where selection is trivial.

Alignment Signal HS↓ NS↓ VS↑ Align.↑

TF-IDF cosine (no LLM) 0.288 0.619 0.283 0.769 Executability only 0.296 0.636 0.277 0.767 Comprehensibility only 0.299 0.655 0.268 0.768 Growth Potential only 0.310 0.650 0.259 0.770

3-Component 0.294 0.608 0.289 0.773

Table5:Ablationofthealignmentscoringsignal.Allvariants use the same candidate pools and selection algorithm.

Penalty HS↓ NS↓ VS↑ Align.↑

mean-sim 0.288 0.660 0.279 0.812 max-sim 0.294 0.608 0.289 0.809

Table 6: Ablation of the redundancy penalty function.

variant serves as a non-LLM baseline, replacing the LLM rubric with researcher-direction cosine similarity in TFIDF space. Table 5 shows that the three-component scorer achieves the best performance in all metrics, reducing portfolio redundancy while preserving researcher-direction fit. TFIDF cosine obtains the lowest HS because it favors surfacelevel text dispersion. Single-component LLM signals also underperform: optimizing only Executability, Comprehensibility, or Growth Potential captures one aspect of researcherdirection fit, but yields a less balanced selection landscape.

PenaltyFunction. Wecomparemax-simandmean-simredundancy penalties while keeping the same candidate pools and alignment scores. Table 6 shows that the two penalties emphasize different forms of redundancy. Mean-sim obtains slightly lower HS and a comparable reported Align. score, suggesting that penalizing average similarity can spread directions at the global portfolio level without strongly affecting the alignment proxy. Contrarily, max-sim directly penalizes the closest selected direction, leading to lower NS and higher VS. Since repeated idea exposure is driven primarily by close semantic overlaps, max-sim better matches our dehomogenization objective and is used as the default penalty.

Redundancy Weight. Figure 3 shows the redundancyalignment trade-off controlled by the redundancy weight λ. Increasing λ strengthens the redundancy penalty, which generally lowers HS and NS while increasing VS; together, these trends indicate that the surfaced portfolio becomes less homogeneous. The reported Align. score remains nearly stable for moderate λ, but decreases when the objective becomes

###### HS ↓ NS ↓ VS ↑ Align. ↑

0.80

| | |
|---|---|
| | |
| | |
| | |
| | |


0.75

0.70

0.65

0.60

0.55

0.32

0.30

0.28

0.26

0 0.2 0.5 1 2 ∞

λ

Figure 3: Sensitivity to the redundancy weight λ.

Selection Generator HS↓ NS↓ VS↑ Align.↑

Independent Haiku 0.303 0.663 0.262 0.779 Independent Sonnet 0.319 0.689 0.244 0.784

DivAlign Haiku 0.294 0.608 0.289 0.776 DivAlign Sonnet 0.296 0.620 0.282 0.785

Table 7: Ablation of the generator strength.

dominated by redundancy reduction. We use λ = 0.2 as a conservative default, as it achieves a favorable balance.

Generator Strength. We examine whether using a stronger Stage 2 generator naturally produces a less redundant set of surfaced directions. To isolate generation strength, we replace claude-haiku-4-5 with claude-sonnet-4-6 only for direction generation, while keeping Stage 1, Stage 3, and Stage 4 procedures fixed. Table 7 shows that Sonnet yields higher HS and NS and lower VS than Haiku, indicating that a stronger generator may favor more polished but thematically concentrated highprobability directions rather than broader portfolio coverage.

##### Scaling with Community Size

We evaluate how DivAlign scales as the community portfolio grows. For each N ∈ {20,40,60,75,95}, we sample cluster-balanced researcher subsets from the full benchmark and report the mean and standard deviation over 10 random samples, except for N=95. Figure 4 shows that surfaced portfolios become more homogeneous as N grows, especially for Coarse-K1: larger communities create more opportunities for semantically similar directions to appear. Across all community sizes, DivAlign maintains lower HS/NS and higher VS than Coarse-K1. In contrast, the mean reported Align. score remains comparatively stable across N, suggesting that researcher-direction fit is mainly a local property rather than a direct function of portfolio size. The variance of HS and reported Align. is larger for smaller communities because each sample is more sensitive to the particular researchers and clusters included; as N grows, the estimates become more stable.

Coarse-K1 DivAlign

###### HS ↓

###### NS ↓

0.34

| | | | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |


| | | | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |


0.70

0.32

0.65

0.30

0.60

0.28

0.55

0.50

0.26

20 40 60 75 95

20 40 60 75 95

###### VS ↑

Align. ↑

0.79

| | | | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |


| | | | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |


0.60

0.78

0.50

0.77

0.40

0.76

0.30

0.75

0.20

20 40 60 75 95

20 40 60 75 95

Figure 4: Scaling with community size.

|19|11|34|
|---|---|---|


Coverage Distinctness Quality

|19|13|32|
|---|---|---|


|18|16|30|
|---|---|---|


Coarse-K1 Tie DivAlign

Figure 5: Human evaluation results.

##### Human Evaluation

We further conduct a blind pairwise human evaluation. Since researcher-specific alignment is difficult for external evaluators to assess, we focus on portfolio-level diversity and perceived quality. Evaluators are asked to compare clusterspecific portfolio subsets (5 directions each) on Coverage (breadth of covered research directions), Distinctness (less internal overlap), and Quality (average clarity, feasibility, and potential impact). We recruit 16 experienced AI researchers from the corresponding subfields, yielding 64 comparisons between DivAlign and Coarse-K1. Figure 5 shows that DivAlign is preferred more often across all three dimensions.

#### Conclusion

We presented DivAlign, a four-stage pipeline for alignmentpreserving de-homogenization in AI-assisted research ideation. It addresses two blind spots in existing systems: insufficient researcher-specific grounding from coarse profiles, and portfolio-level concentration from independent recommendations. DivAlign combines fine-grained profile extraction, profile-conditioned direction generation, threecomponent alignment scoring, and community-aware selection to reduce portfolio homogenization while preserving researcher-directionfit.Experimentsonabenchmarkweconstruct from 95 AI researchers across five subfields demonstrate the effectiveness of our method.

#### References

Baek, J.; Jauhar, S. K.; Cucerzan, S.; and Hwang, S. J. 2025. ResearchAgent: Iterative Research Idea Generation over Scientific Literature with Large Language Models. In NAACL, 6709–6738.

Ballestero, G.; Hosseini, H.; Khanna, S.; and Shorrer, R. I. 2026. Strategic Algorithmic Monoculture: Experimental Evidence from Coordination Games. arXiv preprint arXiv:2604.09502.

Carbonell, J.; and Goldstein, J. 1998. The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries. In SIGIR, 335–336.

Chen, N.; Tong, Y.; Yang, Y.; He, Y.; Zhang, X.; Zou, Q.; Wang, Q.; and He, B. 2026. Diversity Collapse in MultiAgent LLM Systems: Structural Coupling and Collective Failure in Open-Ended Idea Generation. In Findings of ACL, 251–306.

Deng, Y.; Brucks, M.; and Toubia, O. 2026. Examining and Addressing Barriers to Diversity in LLM-Generated Ideas. arXiv preprint arXiv:2602.20408.

Doshi, A. R.; and Hauser, O. P. 2024. Generative AI Enhances Individual Creativity but Reduces the Collective Diversity of Novel Content. Science Advances, 10(28): eadn5290.

Friedman, D.; and Dieng, A. B. 2023. The Vendi Score: A Diversity Evaluation Metric for Machine Learning. Transactions on Machine Learning Research.

Hodel, D.; and West, J. D. 2025. Epistemic Diversity Across Language Models Mitigates Knowledge Collapse. arXiv preprint arXiv:2512.15011.

Hu, X.; Fu, H.; Wang, J.; Wang, Y.; Li, Z.; Xu, R.; Lu, Y.; Jin, Y.; Pan, L.; and Lan, Z. 2025. NOVA: An Iterative Planning Framework for Enhancing Scientific Innovation with Large Language Models. In Findings of ACL, 21330–21359.

Jain, S.; Lanchantin, J.; Nickel, M.; Ross, C.; Ullrich, K.; Wilson, A.; and Watson-Daniels, J. 2025. Task-Dependent Evaluation of LLM Output Homogenization: A TaxonomyGuided Framework. arXiv preprint arXiv:2509.21267.

Lu, C.; Lu, C.; Lange, R. T.; Yamada, Y.; Hu, S.; Foerster, J.; Ha, D.; and Clune, J. 2026. Towards End-to-End Automation of AI Research. Nature, 651: 914–919.

Lyu, Y.; Zhang, X.; Yi, X.; Zhao, Y.; Guo, S.; Hu, W.; Piotrowski, J.; Kaliski, J.; Urbani, J.; Meng, Z.; Zhou, L.; and Yan, X. 2026. EvoScientist: Towards Multi-Agent Evolving AI Scientists for End-to-End Scientific Discovery. arXiv preprint arXiv:2603.08127.

Padmakumar, V.; and He, H. 2024. Does Writing with Language Models Reduce Content Diversity? In ICLR.

Reimers, N.; and Gurevych, I. 2019. Sentence-BERT: Sentence Embeddings Using Siamese BERT-Networks. In EMNLP-IJCNLP, 3982–3992.

Si, C.; Hashimoto, T.; and Yang, D. 2026. The IdeationExecutionGap:ExecutionOutcomesofLLM-Generatedversus Human Research Ideas. In ICLR.

Si, C.; Yang, D.; and Hashimoto, T. 2025. Can LLMs Generate Novel Research Ideas? A Large-Scale Human Study with 100+ NLP Researchers. In ICLR.

Su, H.; Chen, R.; Tang, S.; Yin, Z.; Zheng, X.; Li, J.; Qi, B.; Wu, Q.; Li, H.; Ouyang, W.; Torr, P.; Zhou, B.; and Dong, N.

- 2025. ManyHeadsAreBetterThanOne:ImprovedScientific Idea Generation by a LLM-Based Multi-Agent System. In ACL, 28201–28240.

Tang, J.; Xia, L.; Li, Z.; and Huang, C. 2025. AI-Researcher: Autonomous Scientific Innovation. In NeurIPS, volume 38. Tevet, G.; and Berant, J. 2021. Evaluating the Evaluation of Diversity in Natural Language Generation. In EACL, 326– 346. Vygotsky, L. S. 1978. Mind in Society: The Development of Higher Psychological Processes. Harvard University Press. Wan, H.; Yang, C.; Yu, J.; Tu, M.; Lu, J.; Yu, D.; Cao, J.; Gao, B.; Xie, J.; Wang, A.; Zhang, W.; Torr, P.; and Zhou, D. 2026. Deep Research Arena: The First Exam of LLMs’ Research Abilities via Seminar-Grounded Tasks. In AAAI, volume 40, 33341–33349. Wang, C.; Xie, Q.; He, W.; Guo, J.; Wang, S.; and Xu, C.

- 2026. Sibyl-AutoResearch: Autonomous Research Needs Self-Evolving Trial-and-Error Harnesses, Not Paper Generators. arXiv preprint arXiv:2605.22343.


Wang, Q.; Downey, D.; Ji, H.; and Hope, T. 2024. SciMON: Scientific Inspiration Machines Optimized for Novelty. In ACL, 279–299.

Wright, D.; Masud, S.; Moore, J.; Yadav, S.; Antoniak, M.; Christensen, P. E.; Park, C. Y.; and Augenstein, I. 2025. Epistemic Diversity and Knowledge Collapse in Large Language Models. arXiv preprint arXiv:2510.04226.

Wu, S.; Lu, P.; Chen, Y.; Bragg, J.; Yamada, Y.; Clark, P.; Clifton, D.; Torr, P.; Zou, J.; and Yu, J. 2026. Scientific Reasoning Does Not Reliably Translate into Scientific Forecasting in Frontier AI. arXiv preprint arXiv:2605.22681.

Yamada, Y.; Lange, R. T.; Lu, C.; Hu, S.; Lu, C.; Foerster, J.; Clune, J.; and Ha, D. 2025. The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search. arXiv preprint arXiv:2504.08066.

Yu,H.;Hong,Z.;Cheng,Z.;Zhu,K.;Xuan,K.;Yao,J.;Feng, T.; and You, J. 2025a. ResearchTown: Simulator of Human Research Community. In ICML, volume 267, 73051–73096. Yu, W.; Tang, S.; Huang, Y.; Dong, N.; Fan, L.; Qi, H.; Liu, W.; Diao, X.; Chen, X.; and Ouyang, W. 2025b. Dynamic Knowledge Exchange and Dual-Diversity Review: Concisely Unleashing the Potential of a Multi-Agent Research Team. arXiv preprint arXiv:2506.18348.

#### Positioning

DivAlign is complementary to generation-focused AI research ideation systems. Prior systems such as Nova (Hu et al. 2025) and ResearchAgent (Baek et al. 2025) primarily improve candidate generation: they start from seed or core papers, and use planning, literature and knowledge retrieval, and review-based refinement to generate and refine research ideas. ResearchTown (Yu et al. 2025a) moves toward a broader community setting by modeling researchers and papers in an agent-data graph to simulate collaborative research activities, but does not explicitly examine the community-level distribution of research directions.

DivAlign therefore complements idea generation by addressingaportfolio-levelproblem:constructingacommunity portfolio from researcher-local candidate pools while jointly accounting for researcher-direction fit and cross-researcher redundancy.

In our implementation, Stage 2 uses profile-conditioned direction generation to keep the generation component controlled, avoiding conflating DivAlign’s gains with those of a more elaborate ideation engine. Alternative paper-centric or agentic generators can be incorporated into this stage without changing the overall formulation. The contribution of DivAlign lies in uncovering researcher-local alternatives, explicitly evaluating researcher-direction fit, and surfacing a community portfolio that is both well aligned and less redundant.

#### Experimental Details

##### Benchmark Construction

We construct a multi-researcher benchmark containing N = 95 AI researchers from five subfields: video understanding (20), medical AI (20), 3D vision (20), embodied AI (20), and efficient AI (15). The benchmark is constructed in four steps:

- Researcher selection: We identify researchers with established publication activity in the corresponding subfield during 2018-2022, covering a range of research topics and seniority levels.
- Entityverification:Eachresearcherismatchedtoaunique OpenAlex entity ID and verified using at least one known publication. This reduces author-disambiguation errors.
- Data collection: For each researcher, we retrieve 3-15 publications from 2018-2022 that are relevant to the corresponding subfield. Titles, abstracts, venues, and DOIs arecollectedprimarilythroughtheOpenAlexandSemantic Scholar APIs, and supplemented with public academic records when necessary, resulting in 930 papers in total. Affiliation metadata is obtained from the API, and a biographical summary is collected from the researcher’s public homepage.
- Quality control: We remove incorrectly attributed publications by cross-checking author lists, titles, abstracts, venues, DOIs, and original publication pages. Duplicate records and papers clearly outside the target subfield are also removed.


The resulting researcher profiles are partial representations based on publicly available records rather than exhaustive publication histories. The complete benchmark will be publicly released upon publication.

Data Usage and Ethics. The benchmark is constructed exclusively from publicly available academic and professional information, including publication metadata from OpenAlex and Semantic Scholar and biographical information from researcher homepages. No private information or sensitive personal attributes are collected or used.

Researcher names and OpenAlex entity IDs are included in the benchmark to support entity verification and reproducibility. The resulting profiles are based on 3-15 publications from a fixed five-year window and should not be interpreted as complete or authoritative representations of the corresponding researchers. Generated directions and alignment scores are computational outputs and do not represent the researchers’ actual views, preferences, plans, or future work. All results are reported in aggregate, without ranking or comparing individual researchers.

##### Implementation Details

All LLM-based stages use the Anthropic API with claude-haiku-4-5-20251001. Stage 1 performs profile extraction, Stage 2 generates K = 5 candidate directions, and Stage 3 scores all K = 5 candidates for each researcher in a single call. For N = 95 researchers, the main pipeline requires one successful call per researcher at each stage, totaling 285 LLM calls, excluding automatic retries. Sentence embeddings are computed using all-mpnet-base-v2 (Reimers and Gurevych 2019) through the sentence-transformers library. The pipeline requires no task-specific training or model finetuning, and all local computation can be performed on CPU without a GPU. We fix all locally controllable random seeds and keep the prompts and decoding settings unchanged across experiments. The complete code will be publicly released upon publication.

##### Human Evaluation Protocol

Evaluator. The 16 evaluators include PhD students, postdoctoral researchers, and faculty members from the relevant AI subfields. We collect their current role, years of AI/ML research experience, and familiarity with the selected benchmark clusters.

Portfolio. Within each cluster, researchers are randomly partitioned into groups of 5 using a fixed seed. Each group defines a matched comparison between portfolios containing directions for the same 5 researchers: one produced by DivAlign and the other by Coarse-K1. The mapping between methods and the anonymous A/B labels is independently randomized for each pair before survey deployment and remains fixed across evaluators. This produces 19 unique portfolio pairs: 4 for each 20-researcher cluster and 3 for the 15-researcher cluster.

Routing. Evaluators are instructed to rate 1 or 2 familiar clusters on a 5-point scale. The system retains up to 2 clusters

###### K HS ↓ NS ↓ VS ↑ Align. ↑

1 0.345 0.699 0.214 0.769 3 0.317 0.663 0.248 0.768 5 0.294 0.608 0.289 0.759 7 0.298 0.605 0.281 0.761 9 0.288 0.586 0.295 0.753

Table 8: Results of different candidate pool size K.

rated at least 3; if none meets this threshold, the highest-rated clusterisused.If1clusterisassigned,all3or4pairsfromthat cluster are presented in randomized order. If 2 clusters are assigned, 2 pairs are randomly sampled without replacement, yielding 4 comparisons.

Question. Each comparison presents Portfolio A and Portfolio B side by side, showing only the title and a short summary for each direction. Evaluators are instructed to judge each portfolio as a whole, rather than based on personal topic preferences or topic popularity. Evaluators also confirm that they complete the survey independently without AI assistance.

Evaluators answer three pairwise preference questions:

- Q1 (Coverage): Which portfolio covers a broader range of distinct research problems, technical approaches, or application settings?
- Q2 (Distinctness): Which portfolio contains directions that are more distinct from each other, with less overlap?
- Q3 (Quality): Which portfolio contains directions that are stronger on average in terms of clarity, feasibility, and potential impact?


For each question, evaluators choose Portfolio A, Portfolio B, or About the Same. They may optionally provide free-text reasoning (Q4) and must report their confidence as Low, Medium, or High (Q5).

#### Additional Experiments

##### Candidate Pool Size

We vary the Stage 2 candidate pool size over K ∈ {1,3,5,7,9}. As shown in Table 8, expanding the pool from 1 to 5 captures most of the diversity benefit, while alignment decreases only modestly from 0.769 to 0.759. Larger pools yield marginal and mildly non-monotonic gains, although K = 9 achieves the best overall diversity. Because generation and scoring costs scale approximately linearly with pool size, we use K = 5 by default as a practical balance among diversity, alignment, and efficiency.

##### Cross-Scorer Validation

To test sensitivity to the Stage 3 scorer, we use claude-sonnet-4-6 to re-score the five candidates for each of the 95 researchers and rerun Stage 4 with λ = 0.2, while keeping the candidate pool fixed.

- Table 9 shows that Haiku and Sonnet produce similar


alignment score distributions, but differ substantially in how they rank the candidates: their top-ranked candidates overlap

Alignment score and selection agreement

Haiku score (mean ± std.) 0.754±0.047 Sonnet score (mean ± std.) 0.764±0.048 Top-ranked candidate overlap 29/95 (30.5%) Stage 4 assignment agreement 34/95 (35.8%)

Downstream portfolio comparison Scorer HS ↓ NS ↓ VS ↑ Align.-H ↑ Align.-S ↑

Haiku 0.294 0.608 0.289 0.781 0.772 Sonnet 0.294 0.620 0.283 0.780 0.789

Table 9: Results of cross-scorer validation. Align.-H and Align.-S denote evaluations from Haiku and Sonnet, respectively,onthe61researcherswhoseStage4assignmentsdiffer.

for 30.5% of researchers, and their Stage 4 assignments agree in 35.8% of cases. Despite these differences, the resulting portfolios remain comparable. HS is unchanged, NS and VS differ only slightly, and the Align. scores remain close under both evaluation models. This suggests that scorer choice has a substantially larger effect on researcher-level assignments than on the overall redundancy-alignment trade-off. The similar evaluation scores across different assignments further suggest that Stage 2 provides multiple viable candidates for eachresearcher.Togetherwiththealignmentscoringablation in the main paper, these results show that alignment scoring is necessary, while the portfolio-level conclusion is not tied to a specific LLM scorer.

#### Prompt Templates

##### Profile Extraction Prompt

Table10showstheStage1profileextractionprompt.Applied once per researcher to the raw scraped data (bio, affiliation, and publication titles with abstracts), it extracts three structured fields, research lineage, owned artifacts, and known gaps, that together with the raw background form the finegrained profile pi provided verbatim to Stages 2 and 3.

##### Direction Generation Prompt

- Table 11 shows the Stage 2 conditioned direction generation prompt. Alignment Scoring Prompt
- Table 12 shows the Stage 3 batch alignment scoring prompt. Three design choices are highlighted: (a) three-component structure; (b) calibration anchors preventing score inflation; (c) JSON array output for programmatic parsing. Each direction is represented by its title, proposal (researcher-agnostic summary), and keywords only. The description field is intentionally excluded: it is written from the perspective of the generating researcher and would introduce bias when scoring directions against a different researcher’s profile.


You are analyzing a researcher’s publication record to extract structured profile information. Researcher: [name] Affiliation: [affiliation] Biography: [bio] Publications (title + abstract excerpt, up to 15): [pub_titles_and_abstracts] Extract the following three fields as a JSON object: "research_lineage": A 2-3 sentence chronological narrative of how this researcher’s focus has evolved. Be specific about the progression of topics, methods, and scale. "artifacts": List concrete benchmarks, codebases, datasets, or systems they have built (e.g. “nnU-Net”, “EPICKitchens”, “BLIP-2 architecture”). Be specific and grounded in their actual publication record. "known_gaps": List 3-4 specific technical limitations or open problems their papers explicitly address or identify. Respond with a JSON object only. No markdown fences. {"research_lineage": "...", "artifacts": ["...", "..."], "known_gaps": ["...", "..."]}

- Table 10: Profile extraction prompt (Stage 1). Input: bio, affiliation, and publication titles with abstracts (up to 15). Output: research lineage, owned artifacts, and known gaps. Italicised tokens are filled at runtime.


You are a senior scientific advisor generating research directions for a specific researcher. A researcher has the following background: Name: [name] Biography: [bio] Research domain: [cluster] Research lineage (progression of prior work): [lineage] Recent publication titles: [pub_titles] Technical assets and owned artifacts: [artifacts] Known open problems from their prior work: [known_gaps] Generate [k] distinct, specific research directions this researcher could pursue. Each direction MUST satisfy all three alignment conditions:

- Executable — achievable given their existing expertise and naturally transferable skills, including near-transfer to adjacent methods or domains. The bar is NOT “have they used this exact tool/dataset before” but “do their core algorithmic and engineering skills carry over?” An AI/ML researcher can readily extend to neighboring subfields; only fundamentally incompatible infrastructure (wet labs, clinical trials) is out of scope.
- Comprehensible — the researcher can engage CRITICALLY with the relevant literature: articulate what existing methods fail to do and why, compare design choices, and defend methodological decisions under review. They may need 2-3 weeks of focused reading for adjacent-subfield directions — that is fine and expected.
- Growth-enabling — the direction should PRODUCTIVELY STRETCH the researcher’s frontier, NOT merely repeat prior work. Ideal: the researcher has ∼60% of the required skills and must genuinely learn 1-2 new techniques or enter an adjacent subfield. Directions that are pure extensions of their last paper (zero new learning) are LOW value for growth. Directions 3+ subfields away (unreachable prerequisites) are also LOW value. AIM FOR THE ADJACENT-NOVEL SWEET SPOT that opens a new multi-paper research agenda. Each direction must also be:
- Novel — at the frontier; not merely incremental over their last paper
- Specific — concrete enough to immediately start as a research project
- High-impact — targeting a top venue (NeurIPS / ICLR / CVPR / ICML level)


For each direction output a JSON object with keys: "title": short title (10-15 words) "proposal": 2-3 sentence researcher-agnostic summary of the direction (40-60 words): what the direction is, what core technical problem it addresses, and what the proposed approach is. Do not reference the specific researcher or their background. "keywords": list of 5-7 technical keywords "description": researcher-specific pitch (100-140 words) covering: (1) why this researcher is positioned to engage with this problem — what prior knowledge makes them qualified, (2) what new capability or subfield they would need to develop, (3) why this represents a productive stretch — leveraging their existing strengths while pushing into new territory

Return a JSON array of [k] such objects.

- Table 11: Conditioned direction generation prompt (Stage 2). Italicised tokens are filled at runtime from the researcher’s extracted profile.


You are a senior research advisor evaluating research direction fit for a specific researcher. Researcher profile: Name: [name] Biography: [bio] Research domain: [cluster] Research lineage (progression of prior work): [lineage] Recent publication titles: [pub_titles] Technical assets and owned artifacts: [artifacts] Known open problems from their prior work: [known_gaps] Score each direction on THREE alignment dimensions (equal weight):

- (A) EXECUTABILITY [0–1]: Can this researcher implement this direction using their existing technical repertoire and naturally transferable competencies? Interpret transfer BROADLY — the bar is not “have they used this exact dataset or tool before” but “do their core algorithmic and engineering skills carry over.” A 3D medical segmentation researcher can execute chest CT, cardiac MRI, or adjacent anatomical segmentation tasks without retraining from scratch. An AI/ML researcher can pick up new neural architectures, datasets, or application domains with moderate effort. Score LOW only when a direction requires FUNDAMENTALLY different scientific infrastructure: wet-lab protocols, clinical trial access, optical telescopes, particle accelerators — not merely an unfamiliar ML subfield.

- 0.8–1.0: Same technical paradigm; skills transfer naturally within weeks
- 0.5–0.8: Adjacent ML/AI area; needs focused effort but core skills apply
- 0.2–0.5: Significant paradigm shift within AI (e.g., pure theory if background is empirical); learnable but costly
- 0.0–0.2: Requires incompatible infrastructure or a completely foreign discipline


- (B) COMPREHENSIBILITY [0–1]: Can this researcher engage CRITICALLY with the relevant literature — not just read about it but: articulate specifically what existing methods fail to do and WHY; compare competing design choices and defend methodological decisions; identify the precise gap this direction addresses vs. prior work? The criterion is depth, not breadth. Do NOT penalize researchers for directions slightly outside their current publication record — researchers actively read beyond their own subfield.


- 0.8–1.0: Deep familiarity demonstrated through own publications in this exact area; can immediately and critically engage with the literature
- 0.6–0.8: Published in adjacent subfields or attends the same conferences; can achieve critical engagement after 2-3 weeks of focused reading
- 0.3–0.6: General awareness of the area but lacks depth; can follow the literature but cannot critically evaluate competing design choices
- 0.0–0.3: Completely separate scientific community with different journals, conferences, and vocabulary; critical engagement would require months of foundational study


- Table 12: Alignment scoring prompt (Stage 3). Italicised tokens are filled at runtime from the researcher’s extracted profile.


(C) GROWTH POTENTIAL [0–1]: How much would this researcher GROW by pursuing this direction? This is an INVERTED-U function — it peaks when the researcher has roughly 50–70% of the required skills (genuine stretch), and drops on BOTH sides: too easy (no growth) AND too hard (unlearnable). Grounded in the Zone of Proximal Development (Vygotsky). SCORING GUIDE (what fraction of required skills does the researcher currently have?):

- 0.9–1.0: ∼50–70% skill coverage. SWEET SPOT. Researcher has a strong foundation but must genuinely learn 2-3 new techniques or enter an adjacent subfield. Would open a new multi-paper research line.
- 0.6–0.9: ∼70–85% skill coverage (good stretch, moderate learning) or ∼35–50% coverage (ambitious but with a clear path forward).
- 0.3–0.6: Either too comfortable (∼85–95% skill overlap, incremental) or quite distant (∼20–35% coverage, steep learning curve).
- 0.0–0.3: BOTH extremes score low: too easy (direction is essentially a repeat of prior work, ∼95%+ overlap) OR too hard (direction requires skills 3+ hops away; progress would be blocked by missing prerequisites). CRITICAL: A direction the researcher already masters scores LOW on growth even if it would produce a publishable paper. A direction in an adjacent subfield scores HIGH even if it requires learning new domain knowledge. Rate EACH of the following [n_dirs] research directions (each shown as Title / Proposal / Keywords):


- 1. Title: [title] Proposal: [proposal] Keywords: [keywords]
- 2. Title: [title] . . . Important calibration philosophy:


- Executability and Comprehensibility: score by what the researcher CAN DO and CAN LEARN, not just what they have already done.
- Growth Potential: this is NOT about fit — it rewards productive MISMATCH. Score LOW for both “this is exactly what I already do” AND “this is completely out of reach.” Score HIGH for “I can do ∼60% of this and would learn the rest.”
- An AI researcher encountering a direction in a neighboring AI subfield should generally score HIGH on Executability and Comprehensibility (core ML skills transfer broadly) and HIGH on Growth Potential (adjacent-novel territory is the ZPD sweet spot) — unless there is a specific reason the direction is incompatible with their background.


Respond with a JSON array of [n_dirs] sub-arrays. Each sub-array has exactly 3 floats in order: [executability, comprehensibility, growth_potential]. All values in [0,1]. Example (for 2 directions): [[0.85, 0.70, 0.80], [0.12, 0.30, 0.20]] Do NOT include the final average — output only the 3-component sub-arrays.

Table 13: Table 12 (continued).

