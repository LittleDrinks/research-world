# Workflow Cards: Structured Summaries of Workflow Executions Using Provenance Data

Nicola Giuseppe Marchioro+∗ Gabriele Padovani+∗ Amal Gueroudji† Rafael Ferreira da Silva‡ Wesley Brewer‡ Valentine Anantharaj‡ Sandro Fiore∗ Renan Souza‡

∗University of Trento, Trento, Italy †Argonne National Laboratory, Lemont, IL, USA ‡Oak Ridge National Laboratory, Oak Ridge, TN, USA

## arXiv:2608.11022v1 [cs.DC] 11 Aug 2026

Abstract—Model Cards and Data Cards have demonstrated the value of structured, human-readable documentation for machine learning artifacts, capturing their context, parameters, limitations, and intended use. However, these practices remain focused on static artifacts (the datasets and trained models themselves) while overlooking the workflow executions that produce, transform, and evaluate them. Such executions hold critical details about data preparation, parameter choice, runtime behavior, resource use, and intermediate transformations, precisely where bias, performance variation, and reproducibility gaps tend to originate. To close this gap, we introduce Workflow Cards: structured summaries that condense the machine-readable provenance data of a workflow execution into a form both humans and large language models (LLMs) can read and analyze. This paper has two main parts. First, it defines a Workflow Card template informed by a representative set of provenance questions that surface from the execution-level data missing from Model and Data Cards. Second, it evaluates how effectively LLMs use Workflow Cards to understand workflow executions compared with querying provenance databases through a schema-based interface. Results show that Workflow Cards provide executionlevel information absent from existing card types, such as Model Cards and Data Cards, thereby filling an important documentation gap; and that Workflow Cards nearly double answer quality compared with schema-based querying, consistently across LLMas-a-Judge and human assessments.

Index Terms—Workflows, Provenance, Agentic workflows, Metadata, Cards, Large Language Models

I. INTRODUCTION

Modern workflows generate increasingly large amounts of provenance data describing execution steps, input and output artifacts, computational environments and infrastructure, workflow parameters, Key Performance Indicators (KPIs), and interactions between components [1]–[3]. This information plays a fundamental role in supporting reproducibility, traceability, auditing, and workflow-level transparency [4], [5], concerns closely aligned with the broader effort to treat computational workflows as FAIR scientific assets [6].

This manuscript has been authored in part by UT-Battelle, LLC, under contract DE-AC05-00OR22725 with the US Department of Energy (DOE). The publisher, by accepting the article for publication, acknowledges that the U.S. Government retains a non-exclusive, paid up, irrevocable, worldwide license to publish or reproduce the published form of the manuscript, or allow others to do so, for U.S. Government purposes. The DOE will provide public access to these results in accordance with the DOE Public Access Plan (http://energy.gov/downloads/doe-public-access-plan).

+These authors contributed equally to this work. Work done while at ORNL.

Several provenance-aware systems and workflow systems have been developed to record detailed execution traces and data lineage (i.e., data provenance) in workflow runs [7]–[10]. These systems commonly expose the captured provenance through graph-based representations, structured databases, or machine-readable serialization formats such as those defined by the W3C PROV family of specifications [11]. Although such representations provide extensive traceability, extracting meaningful workflow-level information from them typically requires specialized query tooling, familiarity with graph traversal techniques, and a deep understanding of the underlying provenance schema, barriers that substantially limit the practical accessibility of provenance information [12].

A parallel line of research has introduced human-readable artifacts such as Model Cards [13] and Data Cards [14] to document AI components [15]–[18]. However, these frameworks focus on static artifacts and offer limited insight into the executions that produce them, even though many critical provenance questions arise at runtime, when users must understand how outputs were derived, what infrastructure was employed, and how parameter choices influenced the result [1], [2], [19], [20]. The captured provenance holds these answers, but reaching them has required those mentioned specialized query tooling. Recent works explore LLM agents that translate naturallanguage questions into structured provenance queries [21]; this interactive querying improves accessibility, yet it still requires the LLM agents to locate and assemble the relevant records on demand, leaving a gap for a compact, directly readable summary of the same provenance that humans and LLMs can consume.

To address this gap, we introduce Workflow Cards, whose primary objective is to lower the barrier to accessing workflow provenance for both human users and LLMs. Each card is a structured documentation artifact that represents workflow execution provenance through a question-oriented template. The template is derived from recurring provenance questions drawn from prior work [2], [21]–[27] and from our experiments, which reveal the fields that contribute workflow-level provenance beyond what other card types, such as Model and Data Cards, already capture. This question-oriented approach follows user-centered design, where framing outputs around user questions improves interpretability [28]. A Workflow

Card surfaces a workflow execution’s data flow provenance, execution context, infrastructure, workflow activities, and generated artifacts. Because LLMs excel at document-based question answering [29], the same card serves as ready context for answering provenance questions. Workflow Cards complement rather than replace provenance traces and databases: they can be generated automatically from provenance systems yet remain independent of any storage backend, and may be produced via manual curation or metadata extraction pipelines.

The contributions of this work are as follows. We (i) introduce Workflow Cards as workflow-oriented documentation artifacts for exposing workflow provenance in a human- and LLM-readable format. We (ii) organize common workflow provenance questions from the literature into three categories (input/dataset, workflow, output/model) that guide the Workflow Card design. We (iii) implement an open-source provenance-aware Workflow Card generation approach integrated with the provenance systems yProv4ML [30], [31] and Flowcept [10], [32]. We (iv) evaluate Workflow Cards both as complementary documentation artifacts alongside Model and Data Cards and as an LLM-facing provenance representation, showing on a real HPC ML workflow that Workflow Cards nearly double answer quality for LLM-based provenance question answering compared with schema-based querying.

II. RELATED WORK

- A. Documentation Artifacts for AI Systems

Structured documentation artifacts significantly improve AI system transparency. Frameworks such as Datasheets for Datasets [15], Model Cards [13], Data Cards [14], and FactSheets [16] establish standard reporting practices for data collection, model behavior, and service pipelines. Recent efforts explore deeper interaction through Interactive Model Cards [33] and qualitative natural-language summaries via Report Cards [34]. These artifacts enjoy broad adoption as lightweight metadata interfaces, evidenced by analyses of thousands of repositories on platforms such as Hugging Face [35]. However, their focus remains primarily on static inputs and outputs, leaving the execution workflows connecting them largely undocumented.

- B. Capturing, Querying, and Representing Provenance


Provenance systems track data lineage, parameters, and component interactions to ensure reproducibility and traceability [1], [12], [36]. Workflow frameworks like Taverna [8], Pegasus [7], and provenance-aware ML tooling [9], [37] automatically record these traces, often utilizing the W3C PROV specifications [11] for interoperability. Building on these foundations, researchers have formalized provenance querying to extract derivation relationships and outcomes [19], [20], expanding recently into machine learning lifecycles [2], [38] and agentic workflows [22], [39], [40].

Although provenance-aware systems provide extensive traceability capabilities, prior surveys consistently identify accessibility and usability as major limitations of existing

provenance representations [12], since provenance is typically exposed through graph structures, database schemas, or low-level serialization formats optimized for storage and machine querying rather than for human interpretation. Consequently, while provenance systems preserve workflow information faithfully, they rarely offer lightweight interfaces for communicating provenance semantics to human users or LLM-based systems. A complementary line of work packages an entire workflow run together with its provenance. The Workflow Run RO-Crate profile [41] standardizes machinereadable, FAIR packaging of workflow executions. Workflow Cards are orthogonal to, not a replacement for, such formats: rather than exhaustively packaging a run, a Workflow Card extracts its provenance into a compact, query-driven summary intended for direct human reading and LLM consumption. This positioning distinguishes Workflow Cards from the broader ecosystem of machine-oriented metadata schemas for ML assets, such as Croissant [42] for datasets, FAIR4ML [43] for models, and PROV-ML [2] for ML provenance, which standardize structured, machine-readable descriptions. Workflow Cards are complementary to these schemas: they sit one layer above by condensing the provenance data that such schemas help represent into a compact, human- and LLMreadable summary of workflow executions, and can coexist with them [44].

III. METHODOLOGY

We propose Workflow Cards to summarize workflow execution provenance data in a lightweight, interpretable format, and evaluate them across two independent benchmarks sharing the same protocol. Benchmark I assesses whether Workflow Cards provide execution-level information absent from existing Model and Data Cards. Benchmark II evaluates their accessibility advantage for LLMs compared to a lightweight schema-based interface to a provenance database. Two LLMs act as judges throughout: a smaller model, nemotron-nano3 [45] (∼30B parameters), and a substantially larger one, gpt-oss-120b [46](∼120B parameters). We use an LLM-asa-Judge approach because it scales evaluation across the full question set and has been shown to correlate strongly with human judgment on answer-rating tasks [47], [48], and we additionally validate it against an independent human rater in Benchmark II. The answering LLMs, however, differ by design. In Benchmark I, a single separate model (gpt-4o [49]) answers every card configuration, so that performance differences reflect the cards rather than the model. In Benchmark II, the two judge models also serve as answering models, spanning model scale to test whether the Workflow Card advantage holds for both a smaller and a larger model.

A. Categorizing Workflow Provenance Questions

Workflow Cards organize relevant information around common provenance access patterns rather than exposing exhaustive traces. To identify these patterns, we analyzed prior work [2], [21]–[27] and extracted recurring questions, grouping them into three macro-categories: input (dataset), work-

flow, and output (model) provenance. These categories served as a conceptual guide for the template design. Starting from these categories, we iteratively refined the Workflow Card template and manually designed a new question set of 33 questions spanning workflow (13), model (10), and data (10) aspects, released with our templates and reproduction code [50]. These questions examine which information is common across documentation artifacts and which information is specific to particular artifact types. During the design process, we established three principles for the Workflow Card. First, it should expose workflow-level provenance rather than replicate metadata already documented in Model or Data Cards. For the representative use case of foundation model fine-tuning, with an input Model Card, one or more Data Cards, and an output Model Card, this means information already held by those cards, such as a detail in the pretrained Model Card, need not be repeated in the Workflow Card. Second, it should represent an immutable execution, so each Workflow Card reflects one specific run and does not evolve after generation. Metadata unrelated to the run itself, such as administrative or policy information that may change independently, is therefore excluded. Third, like the model and Data Cards, it should offer a high-level overview with the smallest footprint possible while maintaining strong question-answering performance.

B. Benchmark I: Cross-Artifact Information Complementarity

The first benchmark focused on evaluating the amount of provenance information exposed by Workflow Cards and measuring the overlap between Workflow Cards and existing documentation artifacts. While many different types of cards have been proposed in the literature, this study was restricted to machine learning workflows and focused exclusively on Model Cards and Data Cards, with one card per pipeline artifact: a pretrained Model Card, a fine-tuning Data Card, and a fine-tuned Model Card. To evaluate informational overlap across documentation artifacts, we constructed a set of simulated machine learning fine-tuning workflows using publicly available Hugging Face repositories, referenced in Table I.

For each workflow configuration, we collected the pretrained Model Card, associated Data Cards, and fine-tuned Model Card. Since public Workflow Cards do not yet exist, we simulated executions and generated Workflow Cards with the proposed template. Workflow-level fields were synthetically generated using Claude Sonnet 4.6, constrained by the real Model and Data Cards. Benchmark I is therefore a structural complementarity analysis: it tests whether the template can represent execution-level information absent from Model and Data Cards, not the factual correctness of synthetic fields. Benchmark II complements it with real provenance captured by Flowcept and yProv4ML (Figure 2).

We evaluated provenance question answering under three different information settings: (i) Full Knowledge, in which all documentation artifacts were concatenated and provided simultaneously to the LLM. This configuration provides complete workflow-level context and is considered the top-level answer; (ii) Single-card, in which each card was evaluated

TABLE I OVERVIEW OF BENCHMARKED USE CASES, DIVIDED BETWEEN INPUT MODEL CARDS, DATA CARDS, AND OUTPUT MODEL CARDS

#### Input Model Data Card Output Model

meta-llama/ Llama-3.23B-Instruct

avaliev/ chat_doctor

prithivMLmods/ Llama-Doctor-3.23B-Instruct

nvidia/ Nemotron-Cascade2-30B-A3B

nvidia/ Nemotron-Cascade2-RL-data

empero-ai/ openNemo-Cascade2-30B-A3B

ibm-nasageospatial/ Prithvi-100M

ANI00/ Crop-Health-Monitor

ibm-nasa-geospatial/ Prithvi-100M-multitemporal-cropclassification

distilbert/ distilbert-baseuncased

cybersectony/ PhishingEmail Detectionv2.0

cybersectony/ phishing-emaildetectiondistilbert_v2.4.1

meta-llama/ Llama-3.2-3B

ai4privacy/ pii-masking-200k

chinu-codes/ llama-3.2-3bpii-redactor-lora

independently by providing only that documentation artifact; (iii) Leave-one-out, where all cards except one were provided to the LLM. This configuration evaluates the informational contribution of the omitted artifact.

In the context of this benchmark, information is defined in terms of the ability to answer a question. A documentation artifact is considered informative with respect to a question if an LLM can correctly answer that question using only the information contained within the artifact itself. The prompts instructed the LLMs to avoid inferring or hallucinating.

The Full Knowledge configuration establishes the upperbound informational context available for each workflow execution and was additionally double-checked, corrected, and improved with any missing information. This reference therefore represents the best answer obtainable from the full documentation set, curated and completed by the authors, and serves as the comparison target for the other configurations. Generated answers were evaluated by the two LLM judges. Each LLM rated the answer from 0.0 to 1.0 against the reference answer, where 1.0 denotes full consistency with the reference, 0.0 an incorrect or unsupported answer, and intermediate values partial correctness. Each LLM had its temperature set to 0.0 for the queries, and an additional statistical check was repeated five times to ensure that answer variability did not produce outliers. To additionally characterize the information carried by each card, we computed the pairwise cross-entropy across the documentation artifacts.

C. Benchmark II: Workflow Cards vs. Schema-based Provenance Querying

Benchmark II evaluates whether Workflow Cards improve accessibility compared to schema-based querying of the underlying provenance data. It uses the Workflow Card template to describe a scientific machine learning pipeline for the DLESyM [51] climate forecasting model. The workflow spans four steps: (i) pre-processing raw data using the REDI [52]

tool, (ii) fine-tuning DLESyM, (iii) forecasting, and (iv) evaluating forecasts via Empirical Orthogonal Function [53].

The workflow was instrumented using both Flowcept and yProv4ML to capture provenance across all steps. The card generator maps captured entities, activities, agents, task timestamps, resource records, and I/O metadata into the template blocks. Fine-grained task records are grouped by workflow stage, start and end times are reduced to activity durations, status values are summarized as counts, resource telemetry is aggregated at run and activity level, and selected inputs and outputs populate the Significant Workflow Artifacts block.

From the benchmark question set, a 17-question subset targeting mainly workflow provenance was used, since questions outside that scope would have shifted the comparison away from information accessibility. We compared two representations of this same captured provenance, differing only in how it is presented to the LLM. The first is a lightweight schema-based querying approach [21], where the LLM is only given the schema and structural provenance rather than the raw records. Data, in this case, is stored into JSONL buffers, and retrieved from a MongoDB database. The second is a Workflow Card generated from the same provenance data and supplied directly as context. This comparison contrasts a pre-computed representation with on-demand retrieval: the Workflow Card packages the relevant provenance ahead of time as static context, whereas schema-based querying requires the model to navigate the interface and assemble the necessary provenance per question. Both representations were answered by the two models and scored under the same LLM-as-a-Judge protocol. A human expert evaluator independently assessed the Benchmark II answers as a calibration check for the automated judges. The human ratings are used to measure whether the LLM-as-a-Judge scores follow the same trend as manual assessment, while the LLM judges provide scalable scoring across the benchmark.

IV. RESULTS

The results are organized into three parts. Section IV-A presents the final template. Section IV-B reports Benchmark I, comparing the information carried by Dataset, Model, and Workflow Cards. Section IV-C reports Benchmark II, comparing Workflow Cards with schema-based provenance querying.

A. Workflow Card Template

The template was produced through an iterative process of drafting, testing on both benchmarks, and analyzing the results. The final Workflow Card template is shown in Figure 1 and is organized as a top-down summary that begins with a high-level view of the run and progressively descends into per-activity detail. It opens with a short Workflow block that names and describes the run in plain language, followed by a Summary block that records the identity and lifecycle of the execution, including a unique execution identifier, the workflow version, start and end timestamps, total duration, overall status, and the entrypoint repository, branch, and commit that pin the exact code used. An Infrastructure block then captures the

computational environment, covering the operating system, hardware, runtime, resource manager, and a snapshot of the software dependencies, so that the run can be situated and, where possible, reproduced. The Workflow Overview gathers run-level aggregates such as activity and task counts, governing arguments, aggregate resource usage across CPU, memory, GPU, disk, and network, and a free-text Observations field for anomalies or decisions made mid-run, before the Activities block repeats a compact record for each stage that reports its tasks, timing, status, hosts, and summarized inputs and outputs. A final Significant Workflow Artifacts block lists only the inputs and outputs needed to reproduce or interpret the run, each identified by a short name and a resolvable reference. Every field is marked as Required or Optional, and a tilde denotes a value that was not captured, which keeps the card lightweight while signaling missing information rather than hiding it. Because each card describes a single immutable execution, it deliberately omits metadata that may evolve independently of the run, and it favors aggregate, highlevel descriptions over exhaustive traces so that it stays small enough to read directly and to pass to an LLM as context.

B. Benchmark I

The first benchmark quantifies the drop in performance when only a single card is provided (the Data Card, pretrained or fine-tuned Model Card, or Workflow Card), compared to the full set of all of them concatenated. The least informative card, the one with the largest average drop from the allcards reference, is the pretrained Model Card. The Workflow Card, by contrast, matches the full set (Figure 3), reaching 0.619 against the all-cards reference of 0.611 while being, on average, 33.2 kB smaller, showing the same answer quality at a fraction of the context size, roughly 8k fewer tokens at about four characters per token.

In these figures, the score is calculated as the average of the LLM-as-a-Judge ratings. Variability for these two initial charts is high, as each column encodes a large number of disparate questions, repeated for five different use cases.

Then, we tested the inverse: the drop when all cards but one are provided (Figure 4), e.g., leaving out one of the Model, Data, or Workflow cards compared to the reference set. Although higher scores generally indicate better performance, in this analysis, the focus is on the impact of removing individual artifacts. A larger decrease in score when an artifact is omitted suggests information that is not easily recovered from the remaining artifacts, making it more informative.

In this leave-one-out setting, removing the Workflow Card produces the largest drop-off, followed by the Fine-tuned Model Card, which contains information about the workflow’s final output. Quantitatively, the execution-level information unique to the Workflow Card more than doubles accuracy over the remaining cards: removing it drops the mean score from the all-cards reference of 0.611 to 0.265 (a 2.3× drop), by far the largest effect of any artifact; removing the Data Card or the Pretrained Model Card, by contrast, changes the score only marginally. To explain these differences, we computed the

### Fig. 1. Template structure of a Workflow card, illustrating the key fields and layout used to represent workflow information. Available online [50].

- Fig. 2. Example Workflow card describing an inference step, performing weather forecasting based on an initial atmospheric condition. Available online [50].


pairwise cross-entropy between cards (Figure 5). It accounts for the small effect of removing the Pretrained Model Card: much of its information is also captured by the Fine-tuned Model Card, but not the reverse, an asymmetry reflected in the cross-entropy between the two cards.

Finally, we quantified how well the answering models perform when given only one artifact type and asked questions targeting a specific card type (e.g., dataset-related questions given a Data Card). Table II reports this setting; its columns are the all-cards reference (All Cards) and the four single-

LLM-Judge Score vs. Full Reference (Single-Card)

0.8

|optimum<br><br>Reference all cards (0.611)<br><br>| | | | |
|---|---|---|---|---|
|0.619| | | | |
| | | | | |
|0.490| | | | |
|0.400| | | | |
| | | | | |
|0.227| | | | |
| | | | | |
| | | | | |
| | | | | |


0.7

0.6

Mean LLM-as-Judge Score

0.5

0.4

0.3

0.2

0.1

0.0

DataCard Only

Finetuning MC Only

Pretraining MC Only

Workflow Card Only

- Fig. 3. Degradation of the mean of LLM as judge score across different single-card contexts, compared to the all-cards reference. Higher is better.

Without DataCard

Without Finetuning Model Card

Without Pretraining Model Card

Without Workflow Card

0.0

0.1

0.2

0.3

0.4

0.5

0.6

0.7

0.8

Mean LLM-as-Judge Score

0.624

0.453

0.621

0.265

optimum

LLM-Judge Score When Each Card Is Removed (Leave-One-Out)

Reference all cards (0.611)

- Fig. 4. Leave-one-out performance analysis. Although higher scores indicate better performance, the key signal is the drop relative to the full setup. Removing the Data Card or pretrained Model Card has minimal impact, and removing the fine-tuned Model Card a moderate one, whereas excluding the Workflow Card causes the largest decrease, indicating it contains the most unique and relevant information for answering the evaluation questions.


card conditions: the Data Card, the fine-tuned Model Card (FT MC), the pretrained Model Card (PT MC), and the Workflow Card. Among the Data and Model Cards, the card matching a question’s focus performs best (e.g., the Data Card on data questions). However, the Workflow Card alone matches or exceeds the All-Cards reference on every question type (Data, Model, and Workflow), despite using less context. Two checks guarded the comparison. First, no artifact exceeded 25 kB, keeping card sizes comparable. Second, the models maintained their answer quality on questions a human rater judged difficult. The reported scores are means over the five use cases: single-card results are stable across them (standard deviations near 0.06, with the pretrained Model Card more variable at 0.13), while the leave-one-out conditions vary more (standard deviations up to 0.27), since the effect of removing a card depends on the specific workflow.

Mean cross-entropy across use cases

18

Data Card

4.907 16.331 15.171 16.229

16

14

Finetuned Model Card

16.882 5.033 13.724 15.343

12

Pretrain Model Card

19.109 17.313 5.765 18.966

10

8

Workflow Card

18.895 17.839 17.759 4.777

6

DataCardFinetunedModelCardPretrainModelCardWorkflowCard

Fig. 5. Matrix of mean cross-entropy scores across all use cases evaluated between different pairs of provenance card types. A lower score indicates less ”surprising” information.

TABLE II PERFORMANCE ISOLATED PER QUESTION FOCUS, COMPARED AGAINST THE ALL-CARDS REFERENCE. HIGHER IS BETTER.

Question Focus

All Cards

Only DataCard

Only FT MC

Only PT MC

Only Workflow

Data 0.6612 0.6154 0.4744 0.2736 0.6884 Model 0.6035 0.4190 0.5716 0.3488 0.6688 Workflow 0.3999 0.1172 0.2626 0.1088 0.4005

C. Benchmark II

We first checked for large self-preference effects in the LLM-as-a-Judge ratings. Each model rated both systems’ responses on a 0.0 to 1.0 scale, and an independent human rating was included as a calibration reference. Figure 6 shows no clear self-preference pattern: nemotron-nano-3 rates its own answers lower than gpt-oss-120b’s, while gpt-oss-120b grades slightly more generously overall. The human ratings follow the same trend as the model judges, supporting the use of the LLM judges as a calibrated automated evaluation.

We then compared question answering under schema-based querying and under Workflow Cards. On average, the card setting is noticeably better (Figure 7): across both answering models, moving from schema-based querying to Workflow Cards nearly doubles the mean rating (from ≈0.45 to ≈0.87), an improvement on which the LLM-as-a-Judge and human evaluations agree. The spread of ratings is similar for both. Agreement among judges is strongest when cards are the input. For the schema-based approach, the LLM judges score considerably harsher than the human rater, likely because raw schema-and-structure responses are harder for an LLM to interpret than a pre-generated card.

##### Self-rating vs. cross-rating vs. human baseline

GPT-OSS-120b judge

Nemotron-nano-3 judge

Human judge

1.0

Self-rating

0.8

Mean rating (01)

0.6

0.4

0.2

0.0

GPT-OSS-120b answers Nemotron-nano-3 answers

- Fig. 6. Comparison of mean ratings between gpt-oss-120b answers and nemotron-nano-3 answers across different judges and human baselines.

GPT-OSS-120b (Schema query)

Nemotron-nano-3 (Schema query)

GPT-OSS-120B (Workflow card)

Nemotron-nano-3 (Workflow card)

0.0

0.2

0.4

0.6

0.8

1.0

Mean rating (0-1)

Overall mean ratings by condition &amp; rater

GPT-OSS-120b judge

Nemotron-nano-3 judge

Human judge

- Fig. 7. Overall mean ratings for gpt-oss-120b and nemotron-nano-3 responses under the two provenance representations (schema-based querying vs. Workflow Card), as evaluated by both models with the LLM-as-a-Judge framework and by human raters.


V. DISCUSSION, FUTURE WORK, AND ARTIFACT AVAILABILITY

Our results show that pre-summarizing provenance into a card substantially eases LLM consumption compared to navigating raw schemas. Because Workflow Cards are themselves generated from the provenance captured by systems such as Flowcept, the two representations are complementary rather than competing: a provenance agent can emit a Workflow Card and use it as context, or consume one to answer queries. Integrating on-demand card generation into interactive provenance agents is a promising direction for future work.

Our study has limitations. Benchmark I evaluates the informational structure of Workflow Cards on synthetically generated content rather than factual provenance, while Bench-

mark II complements it by validating on an instrumented HPC workflow. Benchmark II, in turn, covers a single workflow assessed by one human evaluator, and because the LLM judges also produced the answers they rate, the human ratings (Fig. 6) serve to validate the automated judgments. Quantitatively, the human ratings agree closely with the LLM judges (Pearson r = 0.74 for the mean of the two judges, and

- 0.66 and 0.77 individually; mean absolute difference 0.13 on the 0 to 1 scale). Finally, both benchmarks target machinelearning workflows: fine-tuning pipelines and one climateML workflow. The template is designed around execution concepts shared by many workflow systems, including run identity, infrastructure, activities, timing, status, parameters, and input/output artifacts. In non-ML domains such as genomics, computational fluid dynamics, or weather simulation, the Significant Workflow Artifacts block would document domain outputs such as FASTA, HDF5, Zarr, or NetCDF files rather than model weights. Validating these adaptations on non-ML scientific workflows remains future work.

To support reproducibility, the Workflow Card template, benchmark question sets, LLM prompts, and the code to reproduce the benchmarks are publicly available [50]. Additionally, the updated versions of Flowcept [32] and yProv4ML [31] featuring Workflow Card generation support are open-source.

VI. CONCLUSION

Understanding how artifacts were created is critical for identifying biases, preventing misuse, and improving overall explainability. We introduced Workflow Cards as interpretable documents of execution processes connecting datasets and models, filling a vital gap in current reporting standards. Our evaluation demonstrates that Workflow Cards capture unique, process-level provenance absent from existing artifacts and, on a real HPC workflow, nearly double LLM answer quality on provenance questions compared with schema-based querying. By making execution provenance directly readable to both people and LLMs, this work takes one more step toward the transparency and reproducibility of scientific workflows.

ACKNOWLEDGMENT

This work was partially funded under the National Recovery and Resilience Plan (NRRP), Mission 4 Component 2 Investment

- 1.4 - Call for tender No. 1031 of 17/06/2022 of Italian Ministry for University and Research funded by the European Union – NextGenerationEU (proj. nr. CN 00000013), and the RI-SCALE project (Grant Agreement 101188168). This research used resources of the Oak Ridge Leadership Computing Facility at the Oak Ridge National Laboratory, supported by the Office of Science of the U.S. Department of Energy under Contract No. DE-AC05-00OR22725. This material is based upon work supported by the U.S. Department of Energy (DOE), Office of Science, Office of Advanced Scientific Computing Research, under Contract DE-AC02-06CH11357. The authors used LLMs (Claude Sonnet 4.6 and GPT-5.5) to assist with grammar, sentence structure, and length control across sections. As described in the paper, an LLM was additionally used to generate synthetic metadata for the Benchmark I. These LLMs produced no scientific analyses, interpretations, or conclusions.


REFERENCES

- [1] Y. L. Simmhan, B. Plale, and D. Gannon, “A survey of data provenance in e-science,” ACM SIGMOD Record, vol. 34, no. 3, pp. 31–36, 2005.
- [2] R. Souza, L. G. Azevedo, V. Lourenc¸o, E. Soares, R. Thiago, R. Brand˜ao, D. Civitarese, E. V. Brazil, M. Moreno, P. Valduriez, M. Mattoso, R. Cerqueira, and M. A. S. Netto, “Workflow provenance in the lifecycle of scientific machine learning,” Concurrency and Computation: Practice and Experience, vol. 34, no. 14, p. e6544, 2022.
- [3] A. Gueroudji, C. Phelps, T. Z. Islam, P. Carns, S. Snyder, M. Dorier, R. B. Ross, and L. C. Pouchard, “Performance characterization and provenance of distributed task-based workflows on hpc platforms,” in SC24-W: Workshops of the International Conference for High Performance Computing, Networking, Storage and Analysis, 2024, pp. 2032– 2039.
- [4] P. Missier, S. Woodman, H. Hiden, and P. Watson, “Provenance and data differencing for workflow reproducibility analysis,” Concurrency and Computation: Practice and Experience, vol. 28, no. 4, pp. 995– 1015, 2016.
- [5] W. M. d. Oliveira, D. de Oliveira, and V. Braganholo, “Provenance analytics for workflow-based computational experiments: A survey,” ACM Computing Surveys, vol. 51, no. 3, pp. 53:1–53:25, 2018.
- [6] S. R. Wilkinson, M. Aloqalaa, K. Belhajjame, M. R. Crusoe, B. de Paula Kinoshita, L. Gadelha, D. Garijo, O. J. R. Gustafsson, N. Juty, S. Kanwal, F. Z. Khan, J. K¨oster, K. Peters-von Gehlen, L. Pouchard, R. K. Rannow, S. Soiland-Reyes, N. Soranzo, S. Sufi, Z. Sun, B. Vilne, M. A. Wouters, D. Yuen, and C. Goble, “Applying the FAIR principles to computational workflows,” Scientific Data, vol. 12, no. 1, p. 328, 2025.
- [7] E. Deelman, K. Vahi, G. Juve, M. Rynge, S. Callaghan, P. J. Maechling, R. Mayani, W. Chen, R. Ferreira da Silva, M. Livny, and K. Wenger, “Pegasus, a workflow management system for science automation,” Future Generation Computer Systems, vol. 46, pp. 17–35, 2015.
- [8] T. Oinn, M. Addis, J. Ferris, D. Marvin, M. Senger, M. Greenwood, T. Carver, K. Glover, M. R. Pocock, A. Wipat, and P. Li, “Taverna: A tool for the composition and enactment of bioinformatics workflows,” Bioinformatics, vol. 20, no. 17, pp. 3045–3054, 2004.
- [9] M. Schlegel and K.-U. Sattler, “MLflow2PROV: Extracting provenance from machine learning experiments,” in Proceedings of the Seventh Workshop on Data Management for End-to-End Machine Learning (DEEM @ SIGMOD). ACM, 2023.
- [10] R. Souza, T. J. Skluzacek, S. R. Wilkinson, M. Ziatdinov, and R. F. da Silva, “Towards lightweight data integration using multi-workflow provenance and data observability,” in IEEE International Conference on e-Science, 2023.
- [11] P. Missier, K. Belhajjame, and J. Cheney, “The W3C PROV family of specifications for modelling provenance metadata,” in Proceedings of the 16th International Conference on Extending Database Technology (EDBT). ACM, 2013, pp. 773–776.
- [12] J. F. Pimentel, J. Freire, L. Murta, and V. Braganholo, “A survey on collecting, managing, and analyzing provenance from scripts,” ACM Computing Surveys, vol. 52, no. 3, pp. 47:1–47:38, 2019.
- [13] M. Mitchell, S. Wu, A. Zaldivar, P. Barnes, L. Vasserman, B. Hutchinson, E. Spitzer, I. D. Raji, and T. Gebru, “Model cards for model reporting,” in Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT*). ACM, 2019, pp. 220–229.
- [14] M. Pushkarna, A. Zaldivar, and O. Kjartansson, “Data cards: Purposeful and transparent dataset documentation for responsible AI,” in Proceedings of the 2022 ACM Conference on Fairness, Accountability, and Transparency (FAccT). ACM, 2022, pp. 1776–1826.
- [15] T. Gebru, J. Morgenstern, B. Vecchione, J. W. Vaughan, H. Wallach, H. Daum´e III, and K. Crawford, “Datasheets for datasets,” Communications of the ACM, vol. 64, no. 12, pp. 86–92, 2021.
- [16] M. Arnold, R. K. E. Bellamy, M. Hind, S. Houde, S. Mehta, A. Mojsilovi´c, R. Nair, K. Natesan Ramamurthy, A. Olteanu, D. Piorkowski, D. Reimer, J. Richards, J. Tsay, and K. R. Varshney, “FactSheets: Increasing trust in AI services through supplier’s declarations of conformity,” IBM Journal of Research and Development, vol. 63, no. 4/5, pp. 6:1–6:13, 2019.
- [17] X. Yang, W. Liang, and J. Zou, “Navigating dataset documentations in AI: A large-scale analysis of dataset cards on Hugging Face,” arXiv preprint arXiv:2401.13822, 2024.


- [18] E. Ozoani, M. Gerchick, and M. Mitchell, “Model card guidebook,” 2022. [Online]. Available: https://huggingface.co/docs/ hub/model-card-guidebook
- [19] J. Cheney, L. Chiticariu, and W. C. Tan, “Provenance in databases: Why, how, and where,” Foundations and Trends in Databases, vol. 1, no. 4, pp. 379–474, 2009.
- [20] P. Buneman, S. Khanna, and W. C. Tan, “Why and where: A characterization of data provenance,” in Proceedings of the 8th International Conference on Database Theory (ICDT). Springer, 2001, pp. 316–330.
- [21] R. Souza, T. Poteet, B. Etz, D. Rosendo, A. Gueroudji, W. Shin, P. Balaprakash, and R. F. Da Silva, “LLM agents for interactive workflow provenance: Reference architecture and evaluation methodology,” in Workflows in Support of Large-Scale Science (WORKS) co-located with the ACM/IEEE International Conference for High Performance Computing, Networking, Storage, and Analysis (SC), St Louis, MO, USA, 2025, pp. 2257–2268.
- [22] R. Souza, A. Gueroudji, S. DeWitt, D. Rosendo, T. Ghosal, R. Ross, P. Balaprakash, and R. F. Da Silva, “PROV-AGENT: Unified provenance for tracking AI agent interactions in agentic workflows,” in 2025 IEEE International Conference on eScience (eScience). IEEE, 2025, pp. 467– 473.
- [23] M. Schlegel and K.-U. Sattler, “Capturing end-to-end provenance for machine learning pipelines,” Information Systems, vol. 132, p. 102495, 2025.
- [24] D. Pina, L. Kunstmann, A. Chapman, D. de Oliveira, and M. Mattoso, “DLProv: A suite of provenance services for deep learning workflow analyses,” PeerJ Computer Science, vol. 11, p. e2985, 2025.
- [25] K. Belhajjame, H. Mezrioui, and Y. Zhao, “In-memory indexing and querying of provenance in data preparation pipelines,” 2025.
- [26] A. Chebotko, E. De Hoyos, C. Gomez, A. Kashlev, X. Lian, and C. Reilly, “Utpb: A benchmark for scientific workflow provenance storage and querying systems,” in 2012 IEEE Eighth World Congress on Services, 2012, pp. 17–24.
- [27] T. Auge, G. Bali, M. Klettke, B. Lud¨ascher, W. S¨oldner, S. Weish¨aupl, and T. Wettig, “Provenance for lattice qcd workflows,” in Companion Proceedings of the ACM Web Conference 2023, ser. WWW ’23 Companion. New York, NY, USA: Association for Computing Machinery, 2023, p. 1524–1530.
- [28] Q. V. Liao, D. Gruen, and S. Miller, “Questioning the AI: Informing design practices for explainable AI user experiences,” in Proceedings of the 2020 CHI Conference on Human Factors in Computing Systems. ACM, 2020, pp. 1–15.
- [29] T. B. Brown, B. Mann, N. Ryder, M. Subbiah, J. Kaplan, P. Dhariwal,

- A. Neelakantan, P. Shyam, G. Sastry, A. Askell, S. Agarwal, A. HerbertVoss, G. Krueger, T. Henighan, R. Child, A. Ramesh, D. M. Ziegler, J. Wu, C. Winter, C. Hesse, M. Chen, E. Sigler, M. Litwin, S. Gray,
- B. Chess, J. Clark, C. Berner, S. McCandlish, A. Radford, I. Sutskever, and D. Amodei, “Language models are few-shot learners,” in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 1877–1901.


- [30] G. Padovani, V. Anantharaj, and S. Fiore, “yProv4ML: Effortless provenance tracking for machine learning systems,” SoftwareX, vol. 31, p. 102298, 2025.
- [31] G. Padovani et al., “yProv4ML: A unified interface for logging and tracking provenance information in machine learning experiments.” GitHub, 2026, v3.0.
- [32] R. Souza et al., “Flowcept: A multiworkflow provenance integration and observability system,” https://github.com/ORNL/flowcept, 2026, v0.10.6.
- [33] A. Crisan, M. Drouhard, J. Vig, and N. Rajani, “Interactive model cards: A human-centered approach to model documentation,” in Proceedings of the 2022 ACM Conference on Fairness, Accountability, and Transparency. ACM, 2022, pp. 427–439.
- [34] B. Yang, F. Cui, K. Paster, J. Ba, P. Vaezipoor, S. Pitis, and M. R. Zhang, “Report cards: Qualitative evaluation of llms using natural language summaries,” in Workshop on Socially Responsible Language Modelling Research (SoLaR), 2024, spotlight.
- [35] W. Liang, N. Rajani, X. Yang, E. Ozoani, E. Wu, Y. Chen, D. S. Smith, and J. Zou, “What’s documented in AI? systematic analysis of 32K AI model cards,” arXiv preprint arXiv:2402.05160, 2024.
- [36] J. Freire, D. Koop, E. Santos, and C. T. Silva, “Provenance for computational tasks: A survey,” Computing in Science &amp; Engineering, vol. 10, no. 3, pp. 11–21, 2008.


- [37] G. Padovani, V. Anantharaj, and S. Fiore, “Provenance tracking in largescale machine learning systems,” in Workshop Proceedings of the 54th International Conference on Parallel Processing, 2025, pp. 167–174.
- [38] M. Schlegel and K.-U. Sattler, “Management of machine learning lifecycle artifacts: A survey,” ACM SIGMOD Record, vol. 51, no. 4, pp. 18–35, 2022.
- [39] A. Gueroudji, A. Kamatar, S. Chaouche, R. Ross, K. Chard, and

I. Foster, “Beyond centralized labs: Federating the co-scientist,” in Proceedings of the Supercomputing Asia and International Conference on High Performance Computing in Asia Pacific Region Workshops, ser. SCA/HPCAsiaWS ’26. New York, NY, USA: Association for Computing Machinery, 2026, p. 443–449.

- [40] A. Gueroudji, T. Mallick, R. Souza, R. F. Da Silva, R. Ross, M. Dorier, P. Carns, K. Chard, and I. Foster, “Controla: Agentic workflow control mechanisms for reliable science,” in 2025 IEEE International Conference on eScience (eScience), 2025, pp. 415–426.
- [41] S. Leo, M. R. Crusoe, L. Rodr´ıguez-Navas, R. Sirvent, A. Kanitz, P. De Geest, R. Wittner, L. Pireddu, D. Garijo, J. M. Fern´andez,

I. Colonnelli, M. Gallo, T. Ohta, H. Suetake, S. Capella-Guti´errez, R. de Wit, B. de Paula Kinoshita, and S. Soiland-Reyes, “Recording provenance of workflow runs with RO-Crate,” PLOS ONE, vol. 19, no. 9, p. e0309210, 2024.

- [42] M. Akhtar, O. Benjelloun, C. Conforti, L. Foschini, J. Giner-Miguelez, P. Gijsbers, S. Goswami, N. Jain, M. Karamousadakis, M. Kuchnik, S. Krishna, S. Lesage, Q. Lhoest, P. Marcenac, M. Maskey, P. Mattson, L. Oala, H. Oderinwale, P. Ruyssen, T. Santos, R. Shinde, E. Simperl, A. Suresh, G. Thomas, S. Tykhonov, J. Vanschoren, S. Varma, J. van der Velde, S. Vogler, C.-J. Wu, and L. Zhang, “Croissant: A metadata format for ml-ready datasets,” in Advances in Neural Information Processing Systems, Datasets and Benchmarks Track, 2024, spotlight.
- [43] L. J. Castro, D. Garijo, D. Rebholz-Schuhmann, D. Solanki, J. T. Ciuciu-Kiss, D. Katz, L. Eklund, G. Bharathy, and Research Data Alliance FAIR4ML Task Force, “FAIR4ML-schema,” 2024, research Data Alliance. [Online]. Available: https://zenodo.org/records/14002310
- [44] O. J. R. Gustafsson, S. R. Wilkinson, F. Bacall, S. Soiland-Reyes, S. Leo, L. Pireddu, S. Owen, N. Juty, J. M. Fern´andez, T. Brown et al., “Workflowhub: a registry for computational workflows,” Scientific Data, vol. 12, no. 1, p. 837, 2025.
- [45] NVIDIA, A. Blakeman, A. Grattafiori, A. Basant, A. Gupta, A. Khattar, A. Renduchintala, A. Vavre, A. Shukla, A. Bercovich et al., “Nemotron 3 nano: Open, efficient mixture-of-experts hybrid mamba-transformer model for agentic reasoning,” 2025.
- [46] OpenAI, S. Agarwal, L. Ahmad, J. Ai, S. Altman, A. Applebaum, E. Arbus, R. K. Arora, Y. Bai, B. Baker et al., “gpt-oss-120b &amp; gptoss-20b model card,” 2025.
- [47] H. Li, Q. Dong, J. Chen, H. Su, Y. Zhou, Q. Ai, Z. Ye, and Y. Liu, “LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods,” 2024.
- [48] L. Zheng, W.-L. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Lin, Z. Li, D. Li, E. P. Xing, H. Zhang, J. E. Gonzalez, and I. Stoica, “Judging LLM-as-a-Judge with MT-Bench and chatbot arena,” 2023.
- [49] OpenAI, “GPT-4o system card,” 2024.
- [50] G. Padovani, N. G. Marchioro, R. Souza et al., “Workflow cards: Template, examples, question sets, LLM prompts, and benchmark code,” https://github.com/data-cards/workflow-provenance-card, 2026, v0.0.1.
- [51] N. Cresswell-Clay, B. Liu, D. R. Durran, Z. Liu, Z. I. Espinosa, R. A. Moreno, and M. Karlbauer, “A deep learning earth system model for efficient simulation of the observed climate,” AGU Advances, vol. 6, no. 4, p. e2025AV001706, 2025.
- [52] W. Brewer, P. Widener, V. Anantharaj, F. Wang, T. Beck, A. Shankar, and S. Oral, “Data readiness pipeline patterns for scientific ai at scale: Insights from climate, fusion, life sciences, and materials,” AI Magazine, vol. 47, no. 1, p. e70056, 2026.
- [53] A. Hannachi, I. T. Jolliffe, and D. B. Stephenson, “Empirical orthogonal functions and related techniques in atmospheric science: A review,” International Journal of Climatology, vol. 27, no. 9, pp. 1119–1152, 2007.
