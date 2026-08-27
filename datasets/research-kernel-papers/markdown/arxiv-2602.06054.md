## Are We Truly Innovating? A Qualitative and Quantitative Study of Originality in AI Research Papers

Abeer Mostafa1, Thi Huyen Nguyen2 and Zahra Ahmadi1,3 1Peter L. Reichertz Institute for Medical Informatics, Hannover Medical School, Hannover, Germany 2L3S Research Center, Hannover, Germany 3Lower Saxony Center for Artificial Intelligence and Causal Methods in Medicine (CAIMed), Hannover, Germany

# arXiv:2602.06054v3 [cs.CL] 27 May 2026

### Abstract

Assessing originality in AI research is arguably the most consequential yet least reliable step in peer review. Reviewer judgments of originality remain opaque, inconsistent, and dependent on comparisons to prior work that are often incomplete. In this paper, we present a large-scale, data-driven qualitative and quantitative analysis of research originality based on over 100,000 peer-review reports from leading AI venues, spanning a period of rapid growth in the field. Leveraging structured, semantically retrieved prior work and signals embedded in expert reviewer assessments, we systematically characterize how originality is perceived in practice and identify the key dimensions that most strongly influence novelty judgments. Our analysis yields a fine-grained, evidence-based framework that equips both authors and reviewers with actionable insights into how originality is evaluated. In addition, we evaluate the reliability of current large language model (LLM) agents in assessing originality. We find that these models tend to systematically overestimate novelty and struggle to detect conceptual plagiarism, particularly in the presence of paraphrasing. We release our dataset, trained models, and code at: https://anonymous.4open. science/r/Novelty-Reviewer-365C/.

### 1 Introduction

The rapid growth of AI research has fundamentally challenged our ability to assess originality at scale. In 2022, ICLR received 3,391 submissions1; by 2025, this number had surged to 11,603, representing a more than threefold increase in only three years2. As publication volume accelerates and reviewer workload intensifies in parallel, the assessment of research originality becomes not only more difficult, but structurally compromised.

- 1https://iclr.cc/media/Press/ICLR_2022_Fact_

Sheet.pdf

- 2https://media.iclr.cc/Conferences/ICLR2025/


ICLR2025_Fact_Sheet.pdf

On the other hand, reviewer guidelines for major venues explicitly require novelty judgments to be supported by concrete comparisons to prior work3. As a result, such assessments vary substantially across reviewers and are often constrained by incomplete coverage of the rapidly expanding literature (Lin et al., 2023; Sizo et al., 2025). Empirical studies further confirm that reviewer judgments of originality can diverge considerably even for the same submission, exposing a structural inconsistency in the review process (Teplitskiy et al., 2022). Despite these limitations, novelty remains a central criterion in acceptance decisions, shaping research directions and determining what is recognized as a meaningful scientific contribution. A particularly concerning consequence is the silent acceptance of conceptually derivative work that repackages existing ideas through superficial reframing or terminological variation. Such work can evade conventional detection while presenting borrowed contributions as original, thereby distorting the research landscape. Addressing this issue is not merely a matter of improving reviewer efficiency; it is essential for preserving the integrity and long-term credibility of AI research.

Recent advances in LLMs have shown promise in automating aspects of peer review (Dycke et al., 2023; Kuznetsov et al., 2024; Yu et al., 2024). Existing automatic review-generation systems can generate fluent, human-like reviews, yet their outputs tend to be overly positive and often lack deep conceptual critique and explicit reasoning about novelty (Du et al., 2024; Li et al., 2025b; Idahl and Ahmadi, 2025). In particular, they do not generate structured originality assessments grounded in systematic comparisons with prior work. In parallel, prior approaches to novelty evaluation typically rely on embedding-based similarity (Shibayama

3https://iccv.thecvf.com/Conferences/2025/ ReviewerGuidelines

et al., 2021; Shahid et al., 2025) or classification signals (Yan et al., 2025; Zhao and Zhang, 2025). While useful, these methods neither generate human-like analytical commentary nor provide interpretable comparison-based explanations that reflect how reviewers assess novelty in practice.

This paper addresses these challenges by introducing a reviewer-oriented framework for originality assessment, designed to generate human-like evaluative commentary that is explicitly grounded in systematic comparisons to relevant prior work. We construct a large-scale dataset of peer review reports, from which we extract and aggregate reviewer discussions of novelty into structured, paperlevel originality assessments accompanied by normalized novelty scores. A critique-generation model is then trained to produce both structured scores and free-text assessments aligned with human reviewing behavior. To ground these judgments, we incorporate a graph-based retrieval module that identifies topically and conceptually related papers based on semantic similarity across ideas, methods, and claimed contributions. This retrieved context enables the model to refine and substantiate its generated assessments, explicitly highlighting conceptual overlaps and genuine advances.

The resulting framework supports reviewers in producing assessments that go beyond binary novelty verdicts by identifying original contributions, pinpointing overlaps with prior work, and articulating the basis for each judgment. Importantly, the framework is designed as a decision-support tool, assisting reviewers rather than replacing them. Our main contributions are as follows:

- We curate and release a large-scale dataset of over 100,000 peer review reports with extracted normalized originality discussions from top-tier AI-focused venues.
- We develop a critique-generation model that produces structured novelty scores and freetext analysis learned from human reviewer judgments.
- We introduce a graph-based retrieval module that identifies conceptually related prior work through semantic similarity across ideas, methods, and contributions.
- We present a framework that generates structured originality reports to support more consistent, transparent, and evidence-grounded peer review.


### 2 Related Work

#### 2.1 Automatic Review Generation

A growing body of work has explored the automation of the peer-review process, as well as tools that assist reviewers, such as OpenReviewer (Idahl and Ahmadi, 2025). Domain-adapted LLMs, finetuned on large-scale peer review corpora, have demonstrated the ability to produce more structured and critical feedback compared to general-purpose LLMs (Dycke et al., 2023). However, these approaches primarily focus on generating high-level review content, including overall ratings, strengths, and weaknesses, rather than providing fine-grained originality assessments grounded in specific prior work (Shin et al., 2025). A key limitation of existing methods is their lack of explanatory depth: while they can indicate limited novelty, they typically fail to identify which prior contributions are being echoed and in what precise way.

#### 2.2 Idea Novelty Evaluation

Recent work has increasingly investigated both the generation and evaluation of novelty using LLMs. On the generative side, Si et al. (2025) conduct a large-scale human evaluation comparing LLMgenerated research ideas with those produced by expert NLP researchers. Their findings suggest that LLM-generated ideas are often perceived as more novel under blind evaluation, although concerns regarding feasibility remain. While this indicates that LLMs can approximate surface-level notions of originality, it does not address their ability to reliably assess or explain novelty, which is a critical and more practically useful task.

On the evaluation side, Lin et al. (2025) introduce SchNovel, a benchmark consisting of paper pairs across multiple domains, where the more recent paper is assumed to exhibit greater novelty. Their results show that retrieval-augmented methods improve novelty assessment by grounding model predictions in relevant literature. Complementary studies on LLM creativity (Zhao et al., 2025; Lu et al., 2024; Li et al., 2025a) further demonstrate that originality remains the most challenging dimension to model, with improvements from multi-agent reasoning or structured prompting still limited by inherent subjectivity.

Another line of research approaches novelty from a computational perspective, leveraging embedding similarity, citation networks, and retrievalaugmented matching to estimate redundancy or

atypicality relative to a corpus (Shibayama et al., 2021; Shahid et al., 2025; Zhao and Zhang, 2025). While effective for screening and ranking, these methods offer limited interpretability: similarity scores alone do not identify which idea or method overlaps, or why such overlap is meaningful. These studies highlight a fundamental gap: existing methods can score or rank novelty, but struggle to produce grounded, contrastive explanations akin to those provided by expert reviewers. In this work, we address this limitation by modeling novelty assessment as a structured analytical task that integrates retrieval, alignment, and explicit comparison between a paper’s contributions and the most relevant prior work, thereby more closely reflecting how human reviewers reason about originality.

### 3 Dataset

#### 3.1 Data Collection

We construct a large-scale benchmark for evaluating research originality by curating peer-review data from OpenReview4, following the data crawling and preprocessing procedure established by Idahl and Ahmadi (2025). The resulting dataset comprises 102,021 review reports associated with 37,899 paper submissions to two top-tier AI conferences (NeurIPS and ICLR) from 2022 onwards. Each record includes the full review text, numerical ratings, and rich metadata provided by reviewers during the official peer-review process, making it one of the largest and most structured collections of expert scientific evaluations available for research purposes. We subsequently apply a series of processing techniques to extract and standardize novelty-related discussions, as detailed below.

#### 3.2 Novelty-Related Text Extraction and Aggregation

To isolate originality-related content from discursive peer reviews, we employ a two-stage extraction and aggregation procedure. This pipeline transforms multi-reviewer, multi-perspective review sets into a unified, paper-centric originality assessment grounded in human expert judgments.

Extraction. For each individual review, we prompt an instruction-tuned LLM to identify and extract all textual segments that bear on novelty, encompassing both explicit statements such as direct assessments of originality, references to prior

4https://openreview.net/

art, or comparisons with related work, and implicit signals, such as praise for a conceptually new formulation or criticism of incremental contribution. The extractor operates on the full review text and returns a set of novelty-relevant passages, preserving the reviewer’s original wording to avoid paraphraseinduced distortion. Both the full review text and the extracted novelty segments are retained and passed jointly to the aggregation stage, providing the model with both the focused signal and its context.

Aggregation. Since most submissions receive multiple reviews, we aggregate the extracted novelty segments across all reviewers for a given paper into a single, coherent, paper-level assessment. To reflect varying levels of reviewer agreement, we consider three aggregation scenarios:

- 1. Consensus: All reviewers express consistent views on novelty. This applies to 18,727 papers in our dataset. The model summarizes the shared opinion into a unified assessment that reflects the collective judgment.
- 2. Majority agreement: Reviewers express conflicting assessments, but a clear majority supports one position. This applies to 12,477 papers. The model adopts the majority stance as the primary assessment.
- 3. Tie: Reviewer opinions are evenly split between positive and negative novelty assessments (6,695 papers). In this case, the model evaluates the strength and specificity of arguments from both sides, incorporating reviewer confidence when available. If neither side presents sufficiently strong evidence, a marginal novelty rating is assigned to reflect uncertainty.


In addition to the textual summaries, the model assigns a discrete novelty score in the range [−1,2] based on reviewers opinions, corresponding to four ordered categories: −1 (Not novel): the work is incremental or derivative, largely replicating existing approaches with minimal innovation; 0 (Limited novelty): the work introduces minor variations of known methods without substantial conceptual or technical advancement; 1 (Moderately novel): it exhibits meaningful originality but shows notable overlap with prior research or primarily extends existing ideas; and 2 (Highly novel): the work introduces fundamentally new ideas, methods, problem formulations, or insights that significantly advance the state of the art. These labels are derived solely from the stance expressed in the human reviews

Dataset Construction Search Queries Semantic Search and Retrieval

###### Structured Knowledge Extraction

Knowledge Extraction Agent

###### New Paper

Human Peer-Review Texts

Core Ideas Methods

###### Extract Knowledge from Retrieved Papers

Keywords Data Used

NoveltyRelated Text Extraction

Full Originality Analysis Report

Aggregate and Summarize

Contributions

###### Knowledge for All Papers

Experiments Calculate similarity

| | |
|---|---|
| | |


###### Top-k similar papers

Papers Similarity and Overlap Analysis

Fine-Tuned LLM

Construct Graph

Knowledge Graph

Figure 1: End-to-end framework for originality analysis. Peer-review data is aggregated to construct a large-scale dataset reflecting expert novelty evaluations. A semantic retrieval module then identifies the most relevant prior work, and the final model produces a comprehensive, structured originality report highlighting conceptual overlap and differences with retrieved literature.

rather than from external annotations or author selfreports. All extraction and aggregation steps are performed using Llama 3.1-8B-Instruct, configured deterministically (temperature = 0) to ensure reproducibility. Preliminary experiments verified that alternative prompt formulations produced qualitatively similar aggregated novelty assessments, indicating robustness to minor prompt variations.

Quality Validation. To validate that the aggregation process preserves the novelty-related content expressed by reviewers without introducing hallucinated or distorted assessments, we conduct a twostep evaluation on a sample of 500 papers. First, we replicate the data processing pipeline with an alternative LLM (google/gemini-2.0-flash-lite-001) and conduct a comparison of the resulting outputs. Llama 3.1-8B-Instruct demonstrated superior alignment with reviewer intent and is therefore used as the backbone for all data processing stages. Second, we quantify semantic fidelity for each paper by computing sentence-level embeddings (Reimers and Gurevych, 2019) for both aggregated summaries and original review texts. Each summary sentence is matched to its most similar source sentence via cosine similarity, yielding an average similarity of 0.78, the mean of these pairwise similarities across all sentences. Additionally, we compute an entailment–contradiction (E-C) score using a natural language inference model, obtaining 0.79 between the aggregated assessments and the original reviews. These results indicate strong semantic alignment between aggregated outputs and source reviews, supporting the reliability of the

constructed benchmark.

### 4 Methodology

Our framework for research originality analysis consists of two complementary stages. First, we learn patterns of novelty assessment from human expert reviews by training on the large-scale peerreview dataset. Second, we apply this learned signal to new manuscripts, combining retrievalaugmented reasoning with structured contrastive analysis against semantically related prior work. The overall pipeline is illustrated in Figure 1.

#### 4.1 Structured Knowledge Extraction

Given a target manuscript, we first transform its unstructured scientific prose into a structured semantic representation to enable principled comparison. We employ a knowledge-extraction agent based on Llama-3.1-8B-Instruct, which parses the full manuscript text and produces a structured tuple: Kms = ⟨C, M, R, D, E⟩, where C denotes the set of core ideas, M methods, R contributions, D data sources, and E experimental components. Each element in the tuple is a collection of semantically meaningful descriptors extracted directly from the manuscript. This representation serves two purposes: (i) it makes the manuscript’s intellectual content explicit and machine-comparable, and (ii) it provides fine-grained query terms for the subsequent retrieval stage. The extraction prompt used to elicit this structured output is provided in Figure 9.

- 4.2 Semantic Retrieval and Knowledge Graph Construction


Retrieval. To contextualize the manuscript within the existing literature, we perform semantic retrieval using the Semantic Scholar API (Fricke, 2018). Each component of Kms is issued as an independent query, retrieving up to five candidate papers per query. The union of retrieved documents forms the candidate set P = {p1,...,pn}. For each pi ∈ P, the same knowledge-extraction agent is applied to obtain a structured representation Ki using an identical schema to Kms. This ensures that pairwise comparisons between the manuscript and each candidate paper are conducted at the same semantic level, mitigating surface-level lexical bias in raw text comparisons.

Knowledge Graph Construction. We construct a knowledge graph G = (V,E) where the node set V = {m} ∪ P contains the manuscript m and all retrieved papers, and the edge set E encodes pairwise semantic similarity. An edge eij between nodes (vi,vj) is included if their similarity exceeds a threshold τ:

eij = 1 Sim(Ki,Kj) ≥ τ , (1)

weighted by the similarity score wij = Sim(Ki,Kj). To enable distance-based graph analysis, we define a complementary edge distance:

1 Sim(Ki,Kj)

wijdist =

, ∀eij ∈ E, (2)

which is well-defined since all retained edges satisfy Sim(Ki,Kj) ≥ τ &gt; 0, where shorter distances reflect stronger conceptual proximity. Similarity is computed as the mean cosine similarity across all shared structured fields:

1 |F| f∈F

cos ϕ(Kif), ϕ(Kjf) ,

Sim(Ki,Kj) =

(3) where F = {C,M,R,D,E} is the set of knowledge fields and ϕ(·) denotes the sentence embedding of a field’s concatenated descriptors.

The manuscript-centered subgraph Gm ⊆ G, comprising only edges incident to m, is used to rank retrieved papers with respect to m. The threshold τ defines a similarity radius around m: only papers within this radius are admitted as neighbors in Gm, ensuring that Ptop is drawn exclusively from papers with meaningful conceptual overlap. Papers are ranked by a composite score combining

###### Manuscript-centered Subgraph

###### Full Knowledge Graph

Rank

𝑝3

Higher similarity

0.98 1.1

- 𝑝1
- 𝑝2

𝑝4

𝑝9

- 𝑝3


0.82 0.73 0.60 0.45

1.4

𝟏

𝑝5

0.65 1.2

3.03

𝟐

𝑝4

𝑝2

𝑝10

0.8 1.4

𝟑

1.6 1.3

0.92

7.2

𝑝7

𝟒

𝑝1

2.2

m

0.33 0.24

1.5

m

𝑝9

1.2

8.3

𝑝6

1.7

4.1 11.1

0.12

Not selected

𝑝8

𝑝8

𝑝6

0.09

…

𝑝𝑁

…

Lower similarity

𝑝𝑁

m (Manuscript) 𝒑𝒊 (Retrieved paper) Edge kept Edge ignored

Figure 2: Knowledge graph construction and manuscript-centered ranking. Left: The full graph over the manuscript m and all retrieved papers, with edges weighted by wijdist. Right: Papers are ranked by weighted similarity to m; the top-k (solid) form the comparative context Ptop, while lower-ranked papers (dashed) are excluded.

70% direct similarity to m and 30% within-graph centrality computed over inter-paper edges in G, prioritising papers that are both semantically close to the manuscript and central within the retrieved literature. The top-k papers by this score form the comparative context Ptop.

#### 4.3 Fine-Tuning for Novelty Estimation

Motivation and Setup. To model expert reasoning about originality, we fine-tune Llama-3.1-8BInstruct on our large-scale novelty benchmark. Unlike zero-shot prompting approaches, where the model’s prior is shaped by generic pre-training rather than the norms of scientific peer review, finetuning aligns the model with its judgments with the vocabulary, reasoning structure, and calibration of expert reviewers. Each training instance consists of the full manuscript text as input and a structured target comprising the aggregated novelty assessment, the extracted novelty-relevant reviewer statements, and a normalized novelty score in [−1,2], as described in Section 3. The instruction format is explicitly designed to elicit paper-centric originality judgments rather than reviewer-centric opinion summaries, enforcing a consistent evaluative perspective across all training examples.

#### 4.4 Originality Report Generation

At inference time, the manuscript text, together with the structured knowledge representations of Ptop, is passed as input to the fine-tuned model. Conditioning on both the manuscript content and the explicitly retrieved comparative context al-

lows the model to produce novelty judgments that are grounded in concrete prior-work comparisons rather than parametric memory alone. The model outputs a calibrated novelty score in [−1,2] and a structured natural-language justification that identifies and describes the specific conceptual contrasts between the manuscript and the most relevant retrieved papers.

The final originality report integrates all analytical components of the pipeline into a unified document comprising: (i) a novelty score with a short evidence-grounded justification summarizing the manuscript’s originality relative to the retrieved literature; (ii) a structured knowledge summary of the manuscript’s core ideas, methods, and keywords; (iii) a ranked list of the most similar prior works, each presented with their similarity score, publication year, citation count, and a summary of their core ideas and methods to enable direct comparison with the manuscript.

### 5 Experiments

#### 5.1 Experimental Setup

We evaluate our framework on a held-out test set of 500 papers drawn from our novelty benchmark, covering the full range of novelty categories. Our evaluation targets two complementary capabilities: (i) discrete novelty score prediction, measuring the model’s ability to assign calibrated categorical judgments aligned with human reviewer consensus, and (ii) free-text originality assessment quality, measuring the semantic fidelity and logical consistency of generated justifications relative to groundtruth reviewer rationales. We refer to our proposed approach as Novelty Reviewer and evaluate it in two configurations: without retrieval augmentation (w/o retrieval), which isolates the effect of fine-tuning, and with the full retrieval-augmented pipeline (full framework), which incorporates retrieval augmentation.

Baselines. We compare against a diverse and competitive baseline. General-purpose LLMs include GPT-OSS-20B (Agarwal et al., 2025), Llama-3.1-8B-Instruct (Grattafiori et al., 2024), Mistral-7B-Instruct-v0.1 (Jiang et al., 2023), and Qwen2.5-14B-Instruct-1M (Yang et al., 2025), collectively covering a range of scales and architectures. Domain-adapted baselines include SciLlama (Senthil Kumar, N., 2025), a science-focused language model; Paper Reviewer (Weathon, 2025),

a Qwen3-8B model fine-tuned for review generation; and OpenReviewer (Idahl and Ahmadi, 2025).

Evaluation Metrics. For discrete novelty score prediction, we report Accuracy, Precision, Recall, and F1 score across the four novelty categories. Given the naturally skewed label distribution, where most peer-reviewed papers fall into moderate novelty levels, Precision and F1 are particularly informative metrics, as they better capture discriminative performance on minority classes without rewarding majority-class prediction. For free-text evaluation, we adopt two complementary metrics: an Entailment–Contradiction Natural Language Inference (NLI) score, which measures logical consistency between generated justifications and ground-truth reviewer rationales, and an LLMas-a-Judge score using Llama-3.1-8B-Instruct as the evaluator, which assesses the correctness, coverage, and consistency between the generated answer and the ground truth.

Entailment–Contradiction (E–C) NLI Evaluation Metric: To quantify semantic alignment between model-generated novelty assessments and reference novelty summaries, we adopt a discriminative NLI–based metric. Each model-generated output is treated as the premise and the corresponding reference summary as the hypothesis. A pretrained Roberta-based NLI classifier produces probabilities over entailment, neutral, and contradiction for each pair (pi,hi): qi = [qicontra,qineutral,qientail].

We aggregate these scores across the evaluation set and compute the E–C score as

- 1

- 2


E-C =

N

1 N

i=1

qientail − qicontra + 1 , (4)

where N denotes the number of evaluated samples. The affine transformation normalizes the metric to [0,1], with higher values indicating stronger entailment and lower contradiction between the model output and the reference. Intuitively, this metric rewards outputs that are semantically supported by the reference novelty summary while penalizing contradictory statements.

LLM-as-a-Judge: We further evaluate generation quality using an LLM-based judge. As illustrated in Figure 10, the evaluator model compares generated outputs against the ground truth reference text.

Table 1: Performance comparison of different models on novelty score prediction and free text evaluation.

Data Model Accuracy Precision Recall F1 Score (E−C) NLI LLM Judge

GPT-OSS-20B 0.53 0.2053 0.2950 0.2268 0.6659 7.033 Llama-3.1-8B-Instruct 0.15 0.1621 0.2797 0.0894 0.4832 5.492 Mistral-7B-Instruct-v0.1 0.07 0.1537 0.2574 0.0389 0.5529 3.566 Qwen2.5-14B-Instruct-1M 0.05 0.2620 0.2516 0.0261 0.4498 6.992 SciLlama 0.06 0.2121 0.2531 0.0294 0.5436 5.614 Paper Reviewer 0.33 0.1720 0.2893 0.1613 0.6816 5.871 OpenReviewer 0.08 0.1991 0.2026 0.0850 0.5139 6.186 Novelty Reviewer (w/o retrieval) 0.60 0.3125 0.3066 0.3012 0.7421 7.523 Novelty Reviewer (full framework) 0.62 0.3777 0.3187 0.3231 0.7603 7.824

Novelty Benchmark

GPT-OSS-20B 0.61 0.2384 0.2417 0.2479 0.6913 7.184 Llama-3.1-8B-Instruct 0.22 0.1815 0.2268 0.1176 0.5214 5.883 Mistral-7B-Instruct-v0.1 0.11 0.1692 0.2143 0.0621 0.5741 4.021 Qwen2.5-14B-Instruct-1M 0.09 0.2718 0.2331 0.0413 0.4687 7.102 SciLlama 0.10 0.2264 0.2299 0.0482 0.5568 5.947 Paper Reviewer 0.41 0.2017 0.2476 0.1891 0.7034 6.214 OpenReviewer 0.14 0.2146 0.1984 0.0938 0.5362 6.447 Novelty Reviewer (w/o retrieval) 0.73 0.2921 0.2552 0.2801 0.7422 7.613 Novelty Reviewer (full framework) 0.76 0.3033 0.2721 0.2902 0.7512 7.664

MIDL 2026

#### 5.2 Quantitative Results

Table 1 presents the full quantitative comparison across all models and metrics. The proposed Novelty Reviewer achieves the strongest performance across all evaluation dimensions in both configurations, with the full retrieval-augmented variant yielding the best overall results. The improvements in Precision and F1 over the retrieval-free variant highlight the importance of grounding predictions in explicitly retrieved prior work. In particular, retrieval augmentation enhances discriminative performance under label imbalance, enabling more reliable separation between genuinely novel contributions and incremental ones.

Distributional Analysis. Figure 3 compares the distribution of predicted novelty scores across all models with the human-derived ground truth. All baseline models exhibit a pronounced bias toward assigning moderate or high novelty scores (1 or 2), resulting in a collapse of the predictive distribution toward the upper end of the novelty scale, irrespective of the actual contribution. This bias indicates a systematic overestimation of originality, limiting the models’ ability to adequately penalize incremental or derivative work and reducing discriminative power in cases where accurate novelty assessment is most critical. In contrast, the Novelty Reviewer demonstrates substantially greater sensitivity to low-novelty cases (−1 and 0), producing a distribution that closely aligns with the empirical class proportions observed in human peer-review

annotations. This improved calibration likely stems from the model’s exposure to the full spectrum of reviewer novelty judgments during fine-tuning, including critical and negative assessments that are often underrepresented or suppressed in generalpurpose models.

#### 5.3 Free-Text Quality Assessment

Beyond scalar prediction, qualitative evaluation via E–C NLI and LLM-as-a-Judge metric (Table 1) confirms that the Novelty Reviewer generates justifications that are more consistently grounded in reference rationales than all baselines. This advantage extends beyond score calibration to the coherence and explanatory quality of the generated assessments, an important property for real-world deployment, where actionable originality judgements must be both accurate and well-justified. A full example of a generated report is provided in Appendix H.

#### 5.4 Generalization to Unseen Venues

To assess whether the proposed framework generalizes to other venues in a different domain, we conduct an evaluation experiment on submissions from the Medical Imaging with Deep Learning (MIDL) 2026 conference. MIDL represents a substantively different venue from the NeurIPS and ICLR data used during training: it targets a specialized interdisciplinary community at the intersection of computer vision, deep learning, and clinical medicine, with distinct domain vocabulary and novelty crite-

Ground Truth

Novelty Reviewer

Paper Reviewer

SciLlama

Qwen 2.5 14B

Mistral 7B

Llama 3.1 8B

OpenReviewer

GPT-OSS-20B

0 20 40 60 80 100

Percentage (%)

Not novel (-1) Limited Novelty (0)

Moderate Novelty (1) High Novelty (2)

| |
|---|


| |
|---|


| |
|---|


Figure 3: Predicted novelty score distribution across models.

ria. We collect all 255 publicly available submissions from MIDL 2026 via the OpenReview API and extract all associated official reviews following the procedure described in Section 3. Results are reported in the MIDL 2026 section of Table 1. Across all evaluation dimensions, the Novelty Reviewer consistently outperforms all baselines, despite never having been trained on this venue’s data. Additionally, the consistent cross-domain gains of the full framework over the retrieval-free ablation underscore the central role of retrieval and knowledge graph construction in grounding originality judgments in concrete prior-work evidence.

5.5 Case Study: Idea-Level Plagiarism Detection

To evaluate the practical utility of the retrievalaugmented framework beyond standard benchmarks, we conduct a case study on concept-level plagiarism detection, a setting directly relevant to academic integrity and editorial workflow. We randomly select 10 papers published in 2023 and construct paraphrased versions that preserve underlying ideas, methods, and experimental claims while altering vocabulary and sentence structure. These paraphrased manuscripts are semantically equivalent to the originals but lexically distinct. This setting enables us to test whether models reason about conceptual content or solely perform surfacelevel lexical matching. Each model is prompted to evaluate the novelty of the paraphrased paper and to identify any potentially overlapping prior work. We report two outcome measures: the number of cases in which the original paper is correctly identified (Recognized), and the number of cases assigned a negative novelty score −1 or 0 (Negative).

As shown in Table 2, the performance gap between the Novelty Reviewer and all baselines is substantial. The strongest general-purpose base-

Table 2: Evaluating the model’s ability to detect paraphrasing plagiarism on 10 case studies.

Model Recognized Negative

GPT-OSS-20B 4/10 3/10 Llama-3.1-8B-Instruct 1/10 1/10 Mistral-7B-Instruct-v0.1 0/10 0/10 Qwen2.5-14B-Instruct-1M 4/10 2/10 SciLlama 1/10 0/10 Paper Reviewer 1/10 1/10 OpenReviewer 2/10 2/10 Novelty Reviewer 9/10 9/10

line (GPT-OSS-20B) correctly identifies 4 out of 10 source papers and assigns a negative score in only 3 cases, while all domain-adapted baselines recognize at most 2 cases. In contrast, the Novelty Reviewer correctly identifies 9 out of 10 source papers and assigns a negative novelty score in all 9 recognized instances.

Additionally, we submitted the same set of paraphrased papers to the recently proposed Stanford Agentic Reviewer (StanfordMLgroup, 2025). In all 10 cases, the model described the submissions as novel or original, without detecting any overlap with the source publications despite their being direct lexical reformulations of previously published work. We do not include this model in Table 2 because no prompting was allowed, as neither the model nor its implementation was publicly available at the time of submission.

### 6 Conclusion

We present a human-aligned, literature-aware framework for automated novelty assessment. By constructing a large-scale benchmark and finetuning a language model on human novelty judgments, our model captures reviewer-like evaluation behavior. Combined with structured contribution extraction and graph-based retrieval over related work, the model produces calibrated novelty scores alongside interpretable, evidence-grounded justifications. Extensive experiments show consistent improvements over strong baselines and enable reliable detection of idea-level plagiarism. Crucially, the framework generalizes beyond its training distribution, maintaining strong performance on an unseen venue without any domain-specific adaptation. We believe this work serves as a step toward more consistent, transparent, and scalable peer review in an era of rapidly growing submission volumes.

### 7 Limitations

While our framework provides a structured and human-aligned approach to assessing research novelty, it is subject to some limitations that should be acknowledged. The retrieval pipeline currently depends on the coverage and quality of external scholarly databases (Semantic Scholar), which may lead to an incomplete comparison set. Additionally, our framework is based on the fine-tuned model, which was trained on data from NeurIPS and ICLR. This makes the model more suitable for AI and ML research themes.

### 8 Ethical Considerations

This work addresses the sensitive task of assessing research novelty and originality, which has potential implications for scientific evaluation and decision-making. Our system is designed to support, rather than replace, human judgment. Rather than acting as an automated final decision-maker, the framework serves as a complementary analytical tool that promotes consistency and transparency in novelty evaluation.

The benchmark dataset is constructed exclusively from publicly available peer-review reports, and no personally identifiable information beyond what is already disclosed in the source data is intentionally used. We would like to emphasize that the system evaluates novelty relative to accessible prior work and learned reviewer patterns in which the review process was completely double-blinded. No author names or organizational info were taken into account when fine-tuning or testing the model.

### References

Sandhini Agarwal, Lama Ahmad, Jason Ai, Sam Altman, Andy Applebaum, Edwin Arbus, Rahul K Arora, Yu Bai, Bowen Baker, Haiming Bao, and 1 others. 2025. gpt-oss-120b &amp; gpt-oss-20b model card. arXiv preprint arXiv:2508.10925.

Jiangshu Du, Yibo Wang, Wenting Zhao, Zhongfen Deng, Shuaiqi Liu, Renze Lou, Henry Peng Zou, Pranav Narayanan Venkit, Nan Zhang, Mukund Srinath, and 1 others. 2024. Llms assist nlp researchers: Critique paper (meta-) reviewing. In Proceedings of the 2024 conference on empirical methods in natural language processing, pages 5081–5099.

Nils Dycke, Ilia Kuznetsov, and Iryna Gurevych. 2023. Nlpeer: A unified resource for the computational study of peer review. In Proceedings of the 61st annual meeting of the Association for Computational

Linguistics (volume 1: Long papers), pages 5049– 5073.

Suzanne Fricke. 2018. Semantic scholar. Journal of the Medical Library Association: JMLA, 106(1):145.

Aaron Grattafiori, Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad AlDahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Alex Vaughan, and 1 others. 2024. The llama 3 herd of models. arXiv preprint arXiv:2407.21783.

Maximilian Idahl and Zahra Ahmadi. 2025. Openreviewer: A specialized large language model for generating critical scientific paper reviews. In Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (System Demonstrations), pages 550–562.

Albert Q. Jiang, Alexandre Sablayrolles, Arthur Mensch, Chris Bamford, Devendra Singh Chaplot, Diego de las Casas, Florian Bressand, Gianna Lengyel, Guillaume Lample, Lucile Saulnier, Lélio Renard Lavaud, Marie-Anne Lachaux, Pierre Stock, Teven Le Scao, Thibaut Lavril, Thomas Wang, Timothée Lacroix, and William El Sayed. 2023. Mistral 7b. arXiv preprint arXiv:2310.06825.

Ilia Kuznetsov, Osama Mohammed Afzal, Koen Dercksen, Nils Dycke, Alexander Goldberg, Tom Hope, Dirk Hovy, Jonathan K Kummerfeld, Anne Lauscher, Kevin Leyton-Brown, and 1 others. 2024. What can natural language processing do for peer review? arXiv preprint arXiv:2405.06563.

Ruizhe Li, Chiwei Zhu, Benfeng Xu, Xiaorui Wang, and Zhendong Mao. 2025a. Automated creativity evaluation for large language models: A reference-based approach. Findings of the Association for Computational Linguistics: EMNLP 2025.

Ruochi Li, Haoxuan Zhang, Edward Gehringer, Ting Xiao, Junhua Ding, and Haihua Chen. 2025b. Unveiling the merits and defects of llms in automatic review generation for scientific papers. In the 25th IEEE International Conference on Data Mining.

Ethan Lin, Zhiyuan Peng, and Yi Fang. 2025. Evaluating and enhancing large language models for novelty assessment in scholarly publications. In Proceedings of the 1st Workshop on AI and Scientific Discovery: Directions and Opportunities, pages 46–57.

Jialiang Lin, Jiaxin Song, Zhangping Zhou, Yidong Chen, and Xiaodong Shi. 2023. Automated scholarly paper review: Concepts, technologies, and challenges. Information fusion, 98:101830.

Li-Chun Lu, Shou-Jen Chen, Tsung-Min Pai, ChanHung Yu, Hung-yi Lee, and Shao-Hua Sun. 2024. Llm discussion: Enhancing the creativity of large language models via discussion framework and roleplay. In First Conference on Language Modeling.

Nils Reimers and Iryna Gurevych. 2019. Sentence-bert: Sentence embeddings using siamese bert-networks. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics.

Senthil Kumar, N. 2025. Scillama-3.2-3b. Hugging Face model repository. Accessed: 2025-12-31.

Simra Shahid, Marissa Radensky, Raymond Fok, Pao Siangliulue, Daniel S Weld, and Tom Hope. 2025. Literature-grounded novelty assessment of scientific ideas. In Proceedings of the Fifth Workshop on Scholarly Document Processing (SDP 2025).

Sotaro Shibayama, Deyun Yin, and Kuniko Matsumoto.

2021. Measuring novelty in science with word embedding. PloS one, 16(7):e0254034.

Hyungyu Shin, Jingyu Tang, Yoonjoo Lee, Nayoung Kim, Hyunseung Lim, Ji Yong Cho, Hwajung Hong, Moontae Lee, and Juho Kim. 2025. Automatically evaluating the paper reviewing capability of large language models. arXiv e-prints, pages arXiv–2502.

Chenglei Si, Diyi Yang, and Tatsunori Hashimoto. 2025. Can llms generate novel research ideas? a largescale human study with 100+ nlp researchers. In The Thirteenth International Conference on Learning Representations.

Amanda Sizo, Adriano Lino, Álvaro Rocha, and Luís Paulo Reis. 2025. Defining quality in peer review reports: a scoping review. Knowledge and Information Systems, pages 1–48.

StanfordMLgroup. 2025. Stanford agentic reviewer. https://paperreview.ai/. Accessed: May 2026.

Misha Teplitskiy, Hao Peng, Andrea Blasco, and Karim R Lakhani. 2022. Is novel research worth doing? evidence from peer review at 49 journals. Proceedings of the National Academy of Sciences, 119(47):e2118046119.

Weathon. 2025. paper_reviewer. Hugging Face model repository.

Zhengxu Yan, Han Li, and Yuming Feng. 2025. Noveltyrank: Estimating conceptual novelty of ai papers. arXiv preprint arXiv:2512.14738.

An Yang, Bowen Yu, Chengyuan Li, Dayiheng Liu, Fei Huang, Haoyan Huang, Jiandong Jiang, Jianhong Tu, Jianwei Zhang, Jingren Zhou, Junyang Lin, Kai Dang, Kexin Yang, Le Yu, Mei Li, Minmin Sun, Qin Zhu, Rui Men, Tao He, and 9 others. 2025. Qwen2.5-1m technical report. arXiv preprint arXiv:2501.15383.

Jianxiang Yu, Zichen Ding, Jiaqi Tan, Kangyang Luo, Zhenmin Weng, Chenghua Gong, Long Zeng, Renjing Cui, Chengcheng Han, Qiushi Sun, and 1 others. 2024. Automated peer reviewing in paper sea: Standardization, evaluation, and analysis. In Findings of the Association for Computational Linguistics: EMNLP.

Yi Zhao and Chengzhi Zhang. 2025. A review on the novelty measurements of academic papers. Scientometrics, 130(2):727–753.

Yunpu Zhao, Rui Zhang, Wenyi Li, and Ling Li. 2025. Assessing and understanding creativity in large language models. Machine Intelligence Research, 22(3):417–436.

### A Reproducibility Statement

We are committed to ensuring that all components of this work are fully reproducible. To this end, we provide documentation of all design decisions, prompts, hyperparameters, and implementation details across the dataset construction, model training, and evaluation pipelines. The dataset, trained models, and source codes are publicly available at: https://anonymous.4open.science/r/ Novelty-Reviewer-365C/.

### B Dataset Composition and Statistics

This appendix provides supplementary details on the dataset composition, preprocessing, and experimental configuration to ensure full reproducibility of all reported results.

Table 3 presents the distribution of the number of review reports across conference venues and publication years. The benchmark is constructed from two leading machine learning conferences, ICLR and NeurIPS, covering the period from 2022 to 2025. The number of collected papers increases substantially over the years, reflecting the rapid growth of research activity in the machine learning community. In total, the benchmark comprises 37,899 papers and 102,021 peer-review reports, making it one of the largest structured novelty evaluation datasets available.

Table 3: Dataset distribution by venue and year.

Venue 2022 2023 2024 2025

ICLR 6,056 7,908 16,102 26,842 NeurIPS 5,587 8,131 9,347 22,048

- Figure 4 illustrates the distribution of review


counts across all 37,899 papers in the benchmark. The majority of submissions received between two and four reviews, consistent with standard peerreview practice across both venues. Papers with two or three reviews predominate in the ICLR and NeurIPS 2022–2024 subsets, while the NeurIPS 2025 addition shifts the distribution toward four reviews, reflecting that venue’s review assignment conventions. The long tail toward five or more reviews corresponds to submissions requiring additional evaluation during the discussion or rebuttal phase.

Table 4 reports the distribution of reviewer agreement across all 37,899 papers in the dataset. More than half of papers fall under the Consensus category, where all reviewers reached full agreement

Number of papers

1.6 ·104

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |


1.4

10,294

9,986

1.2

9,563

1

6,778

0.8

0.6

0.4

1,229

0.2

43

6

0

1 2 3 4 5 6 7

Number of reviews per paper

Figure 4: Distribution of the number of reviews per paper in the benchmark dataset (N = 37,899 papers, 102,021 total reviews). The majority of papers received between two and four reviews, consistent with standard practice at NeurIPS and ICLR.

on the novelty assessment. Majority Agreement covers cases where most reviewers shared a common stance despite some dissent. Tie cases reflect evenly divided reviewer opinions, representing the most challenging aggregation scenario.

Table 4: Breakdown of papers by reviewer agreement scenario.

Scenario Papers Proportion

Consensus 18,727 49.4% Majority Agreement 12,477 32.9% Tie 6,695 17.7%

Total 37,899 100%

### C Experimental Details

The Novelty Reviewer model is obtained by finetuning meta-llama/Llama-3.1-8B-Instruct on our novelty benchmark dataset. It will be publicly available after the blind review phase. Training is performed on the full tokenized dataset, which contains aggregated peer-review supervision instances derived from our dataset construction pipeline. The model is trained to generate reviewer-aligned novelty scores and structured justifications conditioned on manuscript content and retrieved contextual evidence. The training corpus consists exclusively of peer-review–derived supervision, where each example includes the manuscript text, extracted novelty-related review statements, and normalized novelty labels. All evaluations are conducted on a held-out test set.

#### C.1 Training Procedure

Fine-tuning is performed for three epochs using the AdamW optimizer with a cosine learning rate schedule. The learning rate is set to 2 × 10−5 with a warmup of 50 steps. Each micro-batch contains a single sequence, and distributed training is used to achieve an effective batch size of 32 across 32 GPUs.

To support long-context modeling, we set the maximum sequence length to 32,120 tokens, enabling the model to process full manuscripts and aggregated review contexts without truncation, and sample packing is disabled to preserve document boundaries. We enable gradient checkpointing to reduce memory usage, along with Flash Attention for improved computational efficiency. Training is conducted in mixed precision with automatic bfloat16 support and TensorFloat-32 acceleration. Weight decay is disabled, following standard practice for instruction fine-tuning of large language models.

#### C.2 Infrastructure and Efficiency

Training is executed using multi-GPU distributed execution (32 A100 GPUs with 80 GB memory each) with DeepSpeed ZeRO Stage-3 optimization. Additional efficiency improvements are provided via Liger kernel integrations, including optimized rotary embeddings, RMS normalization, GLU activations, and fused linear cross-entropy operations. The model follows the Llama-3.1-8BInstruct chat template and uses custom padding and end-of-sequence tokens. All experiments are conducted using Transformers 4.55.2, PyTorch 2.6.0, Datasets 4.0.0, and Tokenizers 0.21.4. Checkpoints are saved twice per epoch, and only model weights are retained to reduce storage overhead.

### D Knowledge Graph Construction Algorithm

Algorithm 1 provides a formal description of the knowledge graph construction pipeline introduced in Section 4. The algorithm takes as input the manuscript m, the set of retrieved candidate papers P, a similarity threshold τ, and the number of top papers k to select for the comparative context. Edges between retrieved papers are used to compute within-graph centrality, which is combined with direct manuscript similarity in a 70%/30% composite score to rank candidate papers, prioritising those that are both semantically close to the

manuscript and central within the retrieved literature.

Algorithm 1: Knowledge Graph Construction and Context Retrieval

Input: Manuscript m, retrieved papers

P = {p1,...,pn}, threshold τ

Output: Knowledge graph G = (V,E), manuscript-centered subgraph Gm, comparative context Ptop

- 1 Km ← EXTRACT(m)
- 2 for i ← 1 to n do

- 3 Ki ← EXTRACT(pi)
- 4 end
- 5 V ← {m} ∪ P
- 6 E ← ∅
- 7 for i ← 1 to n do

- 8 si ← |F1| f∈F cos(ϕ(Kmf ),ϕ(Kif))

- 9 if si ≥ τ then

- 10 wmi ← si
- 11 wmidist ← 1/si
- 12 E ← E ∪ {(m,pi,wmi,wmidist)}
- 13 end
- 14 for j ← i + 1 to n do

- 15 sij ← 1

|F| f∈F cos(ϕ(Kif),ϕ(Kjf))

- 16 if sij ≥ τ then

- 17 E ← E ∪ {(pi,pj,sij,1/sij)}
- 18 end
- 19 end
- 20 end
- 21 G ← (V,E)
- 22 Gm ← (V, {e ∈ E | m ∈ e})
- 23 for pi ∈ {pi | (m,pi) ∈ E} do

- 24 ci ← pj̸=m,(pi,pj)∈E wij c¯i ← ci / maxpl cl scorei ← 0.7 · wmi + 0.3 · c¯i
- 25 end
- 26 Pranked ← SORTDESC({pi | (m,pi) ∈ E}, scorei)
- 27 Ptop ← Pranked[1 : k]
- 28 return G, Gm, Ptop


### E Scores Distribution

Figure 5 compares the distribution of novelty scores produced by different automated reviewers against the ground-truth annotations. Most baseline LLMs

###### GPT-OSS-20B

Mean: 1.10

Median: 1.00

400

350

300

250

Count

Count

200

150

100

50

0

1 0 1 2

Novelty Score

###### Mistral 7B

Mean: 1.92

Median: 2.00

400

300

Count

Count

200

100

0

1 0 1 2

Novelty Score

###### Paper Reviewer

Mean: 1.52

250

Median: 2.00

200

150

Count

Count

100

50

0

1 0 1 2

Novelty Score

###### OpenReviewer

Mean: 1.58

Median: 2.00

300

250

200

Count

150

100

50

0

1 0 1 2

Novelty Score

###### Qwen 2.5 14B

| | | | | |M M<br><br>|ean: 2.00 edian: 2.0|0| |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |


500

400

300

Count

200

100

0

1 0 1 2

Novelty Score

###### Novelty Reviewer

400

Mean: 0.78

Median: 1.00

350

300

250

Count

200

150

100

50

0

1 0 1 2

Novelty Score

###### Llama 3.1 8B

Mean: 1.83

400

Median: 2.00

350

300

250

200

150

100

50

0

1 0 1 2

Novelty Score

###### SciLlama

| | | | | |M M<br><br>|ean: 1.98 edian: 2.0|0| |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |


500

400

300

200

100

0

1 0 1 2

Novelty Score

###### Ground Truth

Mean: 0.63

300

Median: 1.00

250

200

150

100

50

0

1 0 1 2

Novelty Score

- Figure 5: Distribution of predicted novelty scores across different models compared to ground truth. Histograms show the frequency of novelty scores assigned by various LLM-based reviewers and baselines. Red dashed lines indicate the mean score, while blue dotted lines denote the median for each model.


exhibit a strong bias toward high novelty scores, with distributions sharply concentrated near the upper end of the scale and medians close to 2. This indicates a systematic tendency to overestimate novelty and collapse predictions into a narrow, overly optimistic range. In contrast, the Novelty Reviewer produces a broader and more balanced distribution, closely matching the shape, mean, and median of the ground-truth scores. The alignment suggests better calibration across the full novelty spectrum and a higher sensitivity to distinguishing incremental contributions from genuinely novel work.

### F Illustrative Samples of Extracted Reviewer Statements

To make the annotation process concrete and demonstrate the quality of the extracted novelty signals, we present representative examples of raw reviewer statements extracted from our dataset for each novelty category. These examples illustrate the range of language through which expert review-

ers express novelty judgments, from direct categorical assertions to implicit evaluative commentary, and highlight why an LLM-based extraction step is necessary to surface these signals reliably from discursive review texts.

Score (-1): Limited Novelty (Consensus). The following statements are drawn from a paper receiving unanimous low-novelty assessments from reviewers:

- Reviewer 1: “The conclusions from the experimental evaluation are very well known to the community. The main conclusion of the paper that pre-training deep networks on large amounts of labeled data allows to outperform handcrafted features hasn’t been novel since 2014.”
- Reviewer 2: “Datasets that focus on both human body movement and controlling camera motion have already existed.


For example, the PKU Multi-Modality Dataset is a large-scale multi-modalities action detection dataset containing 51 action categories in 3 camera views. The contributions are only marginally significant or novel.”

- Reviewer 3: “Lack of novelty. This paper proposes a new dataset without additional innovation in terms of methods for this particular problem.”
- Reviewer 4: “There is no novelty as such in terms of technical contribution.”


This example is instructive because it demonstrates how reviewers ground low-novelty judgments in specific prior work references and dated precedents; precisely the kind of contrastive reasoning our framework is designed to emulate.

Score (2): High Novelty (Consensus). The following statements are drawn from a paper on masked pretraining for generalizable Neural Radiance Fields (NeRF), receiving uniformly positive novelty assessments:

- Reviewer 1: “This work firstly attempts to introduce mask-based pretraining into the NeRF field. This is the first attempt to incorporate mask-based pretraining into the NeRF field.”
- Reviewer 2: “The paper presents several significant improvements to the standard generalizable-NeRF framework, in which a NeRF is trained on a set of scenes and is used at inference on a novel scene without training. These improvements show very good performance compared to the baselines, both significant and consistent, across all experimentation.”
- Reviewer 3: “The proposed masked ray and view modeling is sound. Experiments demonstrate the effectiveness and superiority of the proposed method.”


High-novelty reviewer statements tend to emphasize firsts, fundamental departures from prior paradigms, and consistent empirical superiority; a pattern the fine-tuned model learns to associate with score 2 assignments.

Score (1): Moderate Novelty (Disagreement with Majority Opinion). The following example illustrates the majority-agreement aggregation scenario, in which reviewers hold conflicting views and the aggregation procedure adopts the majority stance:

- Reviewer 1: “The application of evolutionary algorithms in this context is indeed novel, to the best of my knowledge.”
- Reviewer 2: “This is a unique problem that arises in federated learning and I appreciate the authors addressing it.”
- Reviewer 3: “The method seems to be a straightforward application of evolutionary algorithms to hyperparameter optimization. Thus, it is hard to believe the proposed method can actually tune hyperparameters well.”


In this case, two reviewers express positive novelty assessments while one is skeptical. The aggregation model adopts the majority view while explicitly acknowledging the dissenting perspective, producing a moderate novelty score that reflects the balance of expert opinion rather than suppressing minority voices.

Score (1): Moderate Novelty (Tie Scenario). The following example illustrates the most challenging aggregation case, in which an equal number of reviewers express opposing views:

- Reviewer 1: “The paper does not present any novel solutions to the task in the benchmark. The primary contribution of this paper is the creation of a new dataset for evaluating the performance of LLMs; this limits the contribution.”
- Reviewer 2: “I fully expect this to be a high-impact paper, because other practitioners working in this area can now measure the performance of their models against the new benchmark.”


In the absence of a strong preponderance of evidence on either side, the aggregation model is instructed to assign a marginal rating, resulting in a score of 1. This conservative approach to ties is a deliberate design choice: it avoids artificially inflating or deflating novelty scores in genuinely ambiguous cases, preserving the epistemic uncertainty inherent in the original reviewer disagreement.

#### F.1 Knowledge Extraction Output Example

To illustrate the output of the knowledge extraction agent described in Section 4, we present a schematic example of the structured tuple K = ⟨C,M,R,D,E⟩ produced for a representative manuscript on generalizable neural rendering:

- Core Ideas (C): Masked pretraining for generalizable NeRF; self-supervised representation learning for novel view synthesis.
- Methods (M): Masked ray modeling; masked view modeling; encoder-decoder architecture with cross-attention aggregation.
- Contributions (R): First application of maskbased pretraining to generalizable NeRF; improved performance on cross-scene generalization benchmarks.
- Data Sources (D): ShapeNet; DTU; RealEstate10K.
- Experimental Components (E): Novel view synthesis quality (PSNR, SSIM, LPIPS); ablation of masking ratio; cross-dataset generalization study.


Each field of this structured representation is used as an independent semantic query to the Semantic Scholar API during retrieval, ensuring that the retrieved candidate papers are relevant to the specific ideas, methods, and experimental setting of the manuscript rather than to its surface-level vocabulary alone. The same extraction procedure is applied to all retrieved candidate papers, enabling structured field-level overlap profiling between the manuscript and its closest prior work.

### G System Prompts

This appendix documents the full prompt designs used across all LLM agents in our pipeline. Each prompt is carefully engineered to elicit structured, consistent outputs aligned with the specific role of the agent it governs. Together, they form the instructional backbone of both the dataset construction pipeline and the inference-time originality analysis framework.

To construct the plagiarism detection case study, we generate lexically distinct but semantically equivalent variants of published papers using the prompt shown in Figure 6. The prompt enforces complete surface-level reformulation, including replacement of all author-assigned model and system names, while explicitly prohibiting any alteration of the underlying ideas, methods, or experimental claims.

The dataset construction pipeline relies on two sequential prompts. Figure 7 shows the prompt used to guide the LLM in identifying and extracting novelty-relevant segments from individual peer reviews. The prompt instructs the model to capture both explicit novelty statements and implicit assessments of contribution or originality, regardless of whether the reviewer frames them positively or negatively. Figure 8 shows the subsequent aggregation prompt, which takes the extracted novelty segments across all reviews for a given submission and synthesizes them into a single, paper-centric originality assessment. The prompt handles all three aggregation scenarios (consensus, majority agreement, and tie) and instructs the model to assign a normalized novelty score in the range [−1,2] alongside its textual judgment.

At inference time, Figure 9 shows the prompt used by the knowledge extraction agent, which transforms the raw text of a manuscript or retrieved paper into the structured tuple K = ⟨C,M,R,D,E⟩. This structured representation is the foundation for both the semantic retrieval queries and the pairwise overlap profiling described in Section 4.

For free-text quality evaluation, we employ an LLM-as-a-Judge using the prompt shown in Figure 10, which instructs the evaluator to score each generated assessment against the ground-truth reviewer rationale on a scale of 0 to 10 across three criteria: correctness, coverage, and consistency with the assigned novelty score.

### H Output Report Example

We show an example of the manuscript originality analysis report in Figure 11.

###### Conceptual Plagiarism Simulation: Paraphrasing Prompt [SYSTEM]

You are an expert scientific writer assisting a controlled research experiment to evaluate novelty detection robustness. Produce a semantically equivalent restatement of the provided paper text for academic evaluation purposes only.

[INSTRUCTION] Rewrite the paper below such that: Preserved: all core ideas, methods, contributions, experimental settings, results, and claims over prior work. Changed: all sentences fully rewritten; all author-assigned model, system, and dataset names replaced with plausible alternatives. Rules:

- Do not add, remove, or alter any contribution, finding, or claim.
- Do not indicate that the output is a paraphrase; write as a self-contained scientific text.
- Return only the paraphrased text with no annotations or commentary. [INPUT]


{paper_text}

- Figure 6: Prompt used to generate paraphrased paper variants for the conceptual plagiarism detection case study, preserving all intellectual content while enforcing full surface-level reformulation.

Novelty Extraction Agent: System Prompt [SYSTEM] You are an expert scientific analyst specializing in peer review meta-analysis. Your task is to carefully read a peer review and extract all textual segments that bear on the novelty, originality, or contribution of the submitted paper, whether the reviewer expresses these judgments explicitly or implicitly. Do not paraphrase, summarize, or alter the extracted text in any way; return verbatim excerpts only. [INSTRUCTION] Given the peer review text below, extract all sentences or passages that assess the originality or contribution of the reviewed paper. Return your output in the exact JSON format specified. Apply the following extraction guidelines: Extraction guidelines:

- (1) Explicit novelty statements: Extract any sentence containing direct novelty-related vocabulary, including but not limited to: novel, original, new, innovative, first to, breakthrough, unprecedented, pioneering, creative, unique contribution.
- (2) Implicit originality assessments: Extract sentences that evaluate the paper’s relationship to prior work without using explicit novelty keywords. This includes statements such as:

- Comparative positioning: “extends the work of X”, “improves upon prior methods”, “similar to [citation]”
- Negative assessments: “incremental contribution”, “lacks differentiation from existing approaches”, “already explored in prior work”
- Positive assessments: “significant advance over the state of the art”, “fills an important gap”


- (3) Contribution scope statements: Extract sentences that characterize the scope or significance of the paper’s claimed contributions, including statements about whether the problem addressed is important, whether the proposed solution is meaningful, or whether the experimental gains are substantial. Rules:


- Extract verbatim text only. Do not rephrase, merge, or truncate sentences.
- Include both positive and negative assessments — do not filter by sentiment.
- If a passage spans multiple sentences and cannot be understood in isolation, include the full passage.
- If no relevant segments are found, return an empty list [].
- Return only valid JSON with no preamble, explanation, or markdown formatting.


Output format (strict JSON, no additional text): {“novelty_excerpts”: [“...”, “...”] } [INPUT] {review_text}

- Figure 7: System prompt of the novelty extraction agent to identify and isolate originality-relevant segments from individual peer reviews.


###### Novelty Aggregation Agent: System Prompt [SYSTEM]

You are an expert scientific analyst with deep familiarity with peer review norms at top-tier AI and machine learning conferences. Your task is to synthesize multiple peer reviews of a single research paper into one unified, paper-centric originality assessment. You must faithfully reflect the collective perspective of the reviewers — do not introduce your own judgment, add external knowledge, or speculate beyond what the reviews express. Write all assessments as direct statements about the paper itself, not about the reviewers (e.g., “The paper introduces...”, “The work extends...”, “The approach combines...”).

[INSTRUCTION] You will be provided with the full texts of all peer reviews for a paper, together with pre-extracted novelty-relevant segments identified from each review. Read both carefully. Synthesize the collective novelty perspective into a structured assessment following the output format below. Aggregation rules:

- (1) Consensus: If all reviewers agree on the novelty level, summarize the shared position using the full breadth of extracted novelty statements. Reflect both what is novel and any limitations noted.
- (2) Majority agreement: If a majority of reviewers share one position while a minority dissents, adopt the majority stance as the primary assessment.
- (3) Tie: If an equal number of reviewers express opposing novelty assessments, weigh the strength and specificity of the arguments on each side, taking into account the reviewer’s confidence. If one side provides more concrete justification or prior-work references, favor that side. If no strong justification is present on either side, assign a marginal score of 0 or 1 and present both perspectives as contrasting direct statements about the paper. Scoring rubric: Assign a single integer novelty score from {−1, 0, 1, 2} reflecting the aggregated reviewer consensus:


−1 (Not novel): Reviewers consistently describe the work as incremental, derivative, or largely replicating existing approaches with minimal innovation.

- 0 (Limited novelty): Reviewers find the work somewhat standard, introducing minor variations

or applications of known methods without substantial conceptual or technical advancement.

- 1 (Moderately novel): Reviewers acknowledge some originality but note significant overlap with

prior work, or characterize the contribution as a competent extension or combination of existing ideas.

- 2 (Highly novel): Reviewers recognize fundamentally new ideas, approaches, problem formulations,


or insights that significantly advance the field. Rules:

- Write exclusively in a direct voice about the paper. Never write “Reviewer 1 says...” or “According to the reviews...”.
- Be factual, concise, and balanced. Do not inflate or deflate the novelty beyond what the reviews support.
- If reviewers disagree, represent both positions as contrasting direct statements rather than suppressing the minority view.
- Return output strictly in the format below. Do not include preamble, explanation, or any text outside the specified fields.


Output format (strict, no additional text): Novelty Score: [−1 | 0 | 1 | 2]

Score Justification: [2–3 sentences explaining the assigned score as direct statements about the paper’s contributions and their originality relative to prior work.] Detailed Assessment:

[4–6 sentences written as direct statements about the paper covering: (i) the main novel contributions or new ideas introduced; (ii) limitations in originality or areas of incremental advancement; (iii) specific dimensions of novelty across problem formulation, methodological innovation, experimental insight, or theoretical advance.]

[INPUT] Full reviews: {reviews} Extracted novelty segments: {novelty_excerpts}

- Figure 8: System prompt of the novelty aggregation agent to synthesize multi-reviewer novelty signals into a single paper-centric originality assessment and a normalized novelty score in [−1,2].


###### Knowledge Extraction Agent: System Prompt [SYSTEM]

You are a scientific knowledge extraction assistant. Your task is to analyze the text of a research paper and extract its core intellectual content into a structured representation. Be precise, concise, and faithful to what is explicitly stated in the paper. Do not infer or hallucinate content that is not present in the text.

###### [INSTRUCTION]

Given the following research paper text, extract the following five components and return them in the exact JSON format specified below. Each component should contain a list of short, semantically meaningful descriptors (1–2 sentences each). Extract only what is explicitly supported by the paper text.

Components to extract: (C) Core Ideas: The central conceptual contributions or insights introduced by the paper. What new idea, perspective, or formulation does this work propose? (M) Methods: The specific technical methods, algorithms, architectures, or procedures proposed or used. Include key design choices and how they differ from standard approaches. (R) Contributions: The explicit claims of contribution made by the authors. What does this paper claim to offer to the field?

- (D) Data Sources: All datasets, benchmarks, corpora, or data collection procedures used in experiments or evaluation.
- (E) Experimental Components: The evaluation setup, metrics, baselines compared against, and key experimental findings reported.


Output format (strict JSON, no additional text): {

“core_ideas”: [“...”, “...”], “methods”: [“...”, “...”], “contributions”: [“...”, “...”], “data_sources”: [“...”, “...”], “experimental_components”: [“...”, “...”]

}

###### Rules:

- Return only valid JSON. Do not include preamble, explanation, or markdown formatting.
- Each list should contain between 2 and 6 descriptors. Do not pad with generic statements.
- If a component is not present or not discussed in the paper, return an empty list [].
- Descriptors must be self-contained and meaningful out of context — avoid pronouns and vague references.
- Use the paper’s own terminology where precise; paraphrase only when the original is overly verbose.


###### [INPUT]

{paper_text}

- Figure 9: System prompt of the knowledge extraction agent to transform unstructured manuscript text into the structured tuple K = ⟨C,M,R,D,E⟩.


LLM-as-a-Judge Evaluation [INSTRUCTION] Rate how well the Model Output aligns with the Reference Answer on a scale from 0 to 10, taking into account the following criteria:

- Correctness: Does the model output accurately reflect the novelty level and reasoning expressed in the reference?

- Coverage: Does the model output address the same key aspects of originality discussed in the reference?
- Score consistency: Is the model output consistent with the provided novelty score? Reference Answer: {reference} Model Output: {model_output} Respond with ONLY a single integer from 0 to 10. Do not include explanation or any other text.


Figure 10: Prompt used for free-text evaluation via LLM-as-a-Judge.

###### Example Originality Report

Novelty Score: 1 — Moderately Novel Generated: 2026–01–03 Short Novelty Review: The paper addresses an important and timely problem in open-world semantic segmentation by explicitly distinguishing semantic-level (class) shifts from domain-level (covariate) shifts, which is a recognized challenge in OOD detection and domain generalization. The core ideas—generative data augmentation to simulate anomalies and domain shifts, uncertainty-aware training, and feature alignment for domain invariance—are all grounded in well-established research directions. While the proposed combination is thoughtful and well-motivated, each component closely aligns with existing paradigms such as synthetic anomaly generation, uncertainty calibration for OOD detection, and domain-aligned representation learning. The primary novelty lies in integrating these components into a unified framework explicitly designed to disentangle semantic and domain shifts within segmentation models. This integration and the specific training strategy tailored to recalibrate uncertainty for semantic shifts provide some originality beyond straightforward application of prior techniques. However, the paper does not introduce a fundamentally new problem formulation, theoretical insight, or learning principle; instead, it refines and combines known ideas in a systematic way.

Core Ideas: Semantic segmentation under simultaneous semantic and domain distribution shifts; joint anomaly segmentation and domain generalisation via disentangled uncertainty. Methods: Coherent generative-based data augmentation; learnable uncertainty function; relative contrastive loss; two-stage noise-aware training pipeline. Keywords: Semantic segmentation · Anomaly detection · Domain generalisation · Generative augmentation · Uncertainty estimation · Contrastive loss

###### Most Similar Prior Works

- Rank #1 Similarity: 27.9% Title: Show or Tell? Effectively Prompting Vision–Language Models for Semantic Segmentation Year: 2025 Citations: 2 Their Ideas. Effectively prompting vision–language models for semantic segmentation; comparison between textual and visual prompts. Their Methods. Few-shot prompted semantic segmentation; PromptMatcher, a training-free baseline combining text and visual prompts.
- Rank #2 Similarity: 25.6% Title: Confidence-aware Training of Smoothed Classifiers for Certified Robustness

- Year: 2022 Citations: 10

Their Ideas. Use of smoothed classifiers to construct models with provable robustness against ℓ2 adversarial perturbations.

Their Methods. Randomized smoothing; sample-wise control of robustness during training. Rank #3 Similarity: 24.8% Title: Improved Stability and Generalization Guarantees of the Decentralized SGD Algorithm

- Year: 2023 Citations: 8 Their Ideas. Generalization error analysis of decentralized stochastic gradient descent based on algorithmic stability. Their Methods. Decentralized stochastic gradient descent (D-SGD).


- Rank #4 Similarity: 24.8% Title: DockGame: Cooperative Games for Multimeric Rigid Protein Docking Year: 2023 Citations: 2 Their Ideas. Modeling multimeric rigid protein docking as a cooperative game between proteins. Their Methods. Gradient-based learning with surrogate potentials; diffusion-based generative models over protein action spaces.


This report is automatically generated and intended to provide a structured, evidence-grounded overview of semantic and methodological similarity between the analysed manuscript and existing literature, as a decision-support tool for area chairs and reviewers.

Figure 11: Example originality report generated by our framework for a submitted manuscript.

