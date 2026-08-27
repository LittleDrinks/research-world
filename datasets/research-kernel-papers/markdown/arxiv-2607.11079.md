# arXiv:2607.11079v1 [cs.AI] 13 Jul 2026

## Are LLMs Ready for Scientific Discovery? A Capability-Oriented Benchmark for AI Scientists

### Chuhan Shi1, Xiaoquan Ren1, Sicheng Song2, Haobo Li3, Rui Sheng3∗, Yushi Sun3∗

1Southeast University 2East China Normal University 3Hong Kong University of Science and Technology chuhanshi@seu.edu.cn, renxiaoquan987@gmail.com, scsong@dase.ecnu.edu.cn, rshengac@connect.ust.hk, ysunbp@connect.ust.hk

##### Abstract

Existing benchmarks for scientific data analysis evaluate LLMs primarily on code execution or workflow completion, overlooking that scientific analysis serves to support distinct types of scientific claims: hypothesis exploration, statistical inference, mechanistic explanation, each with different assumptions and validity criteria. We introduce SDABench, a benchmark that reorganizes evaluation around six capabilities (descriptive, exploratory, inferential, predictive, causal, and mechanistic) across five domains (Biology, Chemistry, Environment, Geography, Physics). SDABench comprises 527 real-data instances (SDA-Real) and 6,000 synthetic instances (SDA-Synth), each in both multiple-choice and open-ended formats, constructed through an automated pipeline. Evaluating 15 representative LLMs, we find that models handle descriptive analysis well but degrade sharply on tasks requiring assumption selection, latent-processmodeling, or mechanistic reasoning. SDABench further provides a five-stage error analysis framework that locates where LLMs fail: more advanced modelsmorereliablyidentifytherelevantscopeandvariables, but still struggle to select appropriate analytical procedures, model variable relationships, and draw valid conclusions.

### 1 Introduction

Large language models (LLMs) are increasingly transforming scientific discovery by assisting researchers with tasks rangingfromproteinstructureprediction(Jumperetal.2021) to automated hypothesis generation (Kumbhar et al. 2025; Tang et al. 2025). At the core of this discovery pipeline is scientific data analysis (Shi et al. 2026), the phase that converts raw experimental, simulated, or observational data into validated scientific knowledge (Majumder et al. 2024a,b). Ensuring the reliability of AI-driven science therefore requires systematically evaluating how effectively LLMs analyze and reason with scientific data.

However, existing benchmarks such as DataSciBench (Zhang et al. 2024a), KramaBench (Lai et al. 2026), and ScienceAgentBench (Chen et al. 2025) primarily evaluate scientific data analysis from a computational perspective. They assess whether a system can generate and execute analysis code or pipelines, such as selecting features and building models, scoring the results against

∗Corresponding author.

ground-truth answers or task-specific success criteria. While these benchmarks have expanded the realism and scope of data analysis evaluation, they carry two critical limitations. First, they can mistake successful execution for scientific validity: computing the requested result does not mean that the result supports the intended scientific claim. Second, they hide specific reasoning failures behind aggregate scores: a single workflow score cannot reveal whether a model fails at basic description or at complex causal inference. Scientific data analysis ultimately serves not merely to build models or maximize accuracy but to support the scientific claims drawn from data. These claims take different forms, including description, hypothesis exploration, statistical inference, prediction, causal estimation, and mechanistic explanation (Leek and Peng 2015). They require different assumptions, evidence boundaries, and validity criteria, even when they rely on similar analytical procedures. Therefore, the evaluation for scientific data analysis should be organized around the claim types a model can reason about, rather than only the operations it can perform. This motivates a capability-oriented framework that evaluates LLMs by the types of scientific questions they can reason about from data, so as to characterize their strengths and weaknesses across distinct modes of scientific reasoning.

To address this problem, we adopt the six-question framework of Leek and Peng (Leek and Peng 2015) and reinterpret its data analysis question types as six scientific discovery capabilities: descriptive, exploratory, inferential, predictive, causal, and mechanistic. Based on this taxonomy, we construct SDABench across five core scientific domains: Biology, Chemistry, Environment, Geography, and Physics. It consists of two complementary components: SDA-Real, a curated collection of real-world scientific datasets, and SDASynth, which contains synthetic datasets generated through the construction of semantic graphs. Utilizing a three-stage construction pipeline of LLM-based template construction, programmatic ground-truth derivation, and option generation, SDABench includes 527 instances in SDA-Real and 6,000 instances in SDA-Synth. Each instance is provided in both multiple-choice question (MCQ) and open-ended question (OEQ) formats. Furthermore, we evaluate 15 representative LLMs and analyze how model errors vary across task types, domains, and model scales. Two findings stand

Benchmarks Ours QRData LLM-SR DSBench DA-Code Krama BLADE SciAgent Ability Coverage

Descriptive reasoning ✓ ✓ ✗ ✓ ✓ ✓ ✓ ✓ Exploratory reasoning ✓ ✗ ✗ ✗ ✓ ✓ ✗ ✗ Inferential reasoning ✓ ✓ ✗ ✗ ✓ ✗ ✓ ✓ Predictive reasoning ✓ ✗ ✗ ✓ ✓ ✓ ✗ ✓ Causal reasoning ✓ ✓ ✗ ✗ ✗ ✗ ✗ ✗ Mechanistic reasoning ✓ ✗ ✓ ✗ ✗ ✗ ✗ ✗

Benchmark Characteristics Format MCQ+OEQ MCQ+OEQ OEQ Exec Exec Exec MCQ+OEQ Exec Scale (#inst.) 6,527 411 239 540 500 104 724 102 Data source Real+Synth Real Real+Synth Real Real Real Real Real Evaluation Auto+LLM Auto Auto+LLM Auto+LLM Auto Auto+LLM Auto+LLM Auto+LLM Error analysis ✓ ✓ ✗ – – – – ✓

- Table 1: Comparison with representative data analysis benchmarks. Format abbreviations: MCQ = multiple-choice, OEQ = open-ended, Exec = execution-based. “–” indicates partial satisfaction of structured error categorization.


out from this evaluation. First, providing explicit candidate options can degrade performance on certain task types by inducing superficial pattern matching, calling into question the widespread reliance on MCQ-based evaluation. Second, although more advanced models more often identify the task objectives and relevant variables, they continue to encounter difficulties in selecting appropriate analyses, accurately capturing relationships among variables, and ensuring that conclusions are supported by the evidence. Aggregate workflow scores obscure these shortcomings, which become apparent only when evaluations differentiate scientific capabilities and analyze the reasons behind each incorrect response. The main contributions of this work are:

- We introduce SDABench, a benchmark for scientific data analysis encompassing five scientific domains and six scientific discovery capabilities. SDABench includes 527 real-data instances and 6,000 synthetic instances, each provided in both MCQ and OEQ formats.
- We develop an automated benchmark construction pipeline that converts scientific resources into verified analysisinstancesthroughLLM-basedtemplateconstruction, programmatic ground-truth derivation, and option generation.
- We propose a five-stage error analysis framework, which classifies failures along the execution pipeline of scientific data analysis (Scope, Variable, Function, Relationship, Conclusion). This taxonomy reveals that as models improve,earlygroundingerrorsdecreasewhilelater-stage errors persist, making Function, Relationship, and Conclusion Errors the dominant failure modes for stronger models, a diagnostic signal invisible to aggregate accuracy scores.


### 2 Related Work

Benchmarks for Data Analysis. Existing data analysis benchmarks (Table 1) span three settings: executionoriented code generation (DS-1000 (Lai et al. 2023); DSCodeBench(Ouyangetal.2026)),multi-stepdata-science

workflows (DA-Code (Huang et al. 2024); DSBench (Jing et al. 2025); DataSciBench (Zhang et al. 2024a)), and datagrounded scientific reasoning (QRData (Liu et al. 2024); KramaBench (Lai et al. 2026); BLADE (Gu et al. 2024); ScienceAgentBench (Chen et al. 2025); LLM-SRBench (Shojaee et al. 2025)). Most are organized around execution success, pipeline completion, or domain-specific tasks, which blurs failures in basic data manipulation with failures in deeper scientific reasoning and makes it difficult to diagnose which analytical capability a model actually lacks.

LLMs for Data Analysis. Data-analysis assistants have transitioned from basic exploratory tools (Ma et al. 2023; Li et al. 2023; Zhang et al. 2024b) to autonomous agents capable of complex planning and verification (Guo et al. 2024; Hong et al. 2025; Fan et al. 2025; Nam et al. 2026; Zhang et al. 2025). However, successful workflow completion does not guarantee that an agent can validate statistical assumptions, handle uncertainty, or model scientific mechanisms. This shifts the evaluation bottleneck from execution success to distinct analytical capabilities, requiring a diagnostic framework to independently assess these reasoning dimensions.

### 3 Benchmark

#### 3.1 Overview

We introduce SDABench, a benchmark designed to systematically evaluate the scientific data analysis capabilities of LLMs. SDABench covers five scientific domains (Biology, Chemistry, Environment, Geography, and Physics) and six scientific discovery capabilities, which we operationalize as task types: descriptive tasks summarize measurements to characterize a phenomenon; exploratory tasks examine measurements to discover patterns that may suggest testable hypotheses; inferential tasks use sampled measurements to evaluate a scientific claim about a broader phenomenon with quantified uncertainty; predictive tasks use measured variables to estimate unknown observations or future states; causal tasks estimate how a defined intervention, exposure,

Scientific scenarios Variables

Parents + Mechanism

Construction LLM

Source

Internal

Target

Add SDA-Synth perturbations

Semantic graph

Causal layer (iSCM)

Figure 1: The SDA-Synth construction pipeline.

or perturbation changes an outcome; and mechanistic tasks use data and domain theory to explain the process that produces an observed scientific outcome.

Each benchmark instance is formalized as z = (d,t,D,Q,g), where d is the scientific domain, t is the task type, D denotes the referenced dataset and its metadata used to answer the question, Q is the question, and g is the ground-truth answer. For every instance, we release two formats: multiple-choice questions QMCQ(z), which support scalable automatic evaluation through plausible distractors, and open-ended questions QOEQ(z), which ask models to produce the answer directly and are better suited for openform reasoning and analysis execution.

#### 3.2 Data Curation

We curate SDABench by screening public scientific datasets and benchmarks using three criteria. First, they should target quantitative scientific analyses with clear objectives. Sec-

- ond, they are required to provide structured data with clear metadata. Third, their answers should be programmatically derivable from the underlying data. Based on these criteria, we select KramaBench (Lai et al. 2026), BLADE (Gu et al.

- 2024), LLM-SRBench (Shojaee et al. 2025), QRData (Liu et al. 2024), DiscoveryBench (Majumder et al. 2024b), SciTS (Wu et al. 2025), and ScienceAgentBench (Chen et al.
- 2025) as seed resources from 24 candidate scientific datasets and benchmarks. We use these resources to construct two dataset components: SDA-Real, a re-curated collection of real scientific datasets, and SDA-Synth, a generated collection of synthetic scientific datasets. Figure 1 summarizes the construction pipeline.


SDA-Real. SDA-Real is constructed from eligible real datasets drawn from the selected seed resources. We retain a dataset only when its schema and metadata support at least

- one of the six task types. Rather than reusing the original questions or answers, we generate new questions and derive their answers using the task taxonomy and construction pipeline described in Section 3.3.


SDA-Synth. Real scientific datasets are typically studyspecific, making it difficult to evaluate all six task types on a single dataset, and using different datasets per task type would confound task difficulty with dataset artifacts. Following prior work (Majumder et al. 2024b; Shojaee et al. 2025; Ormaniec et al. 2025), we construct synthetic datasets shared across task types, as illustrated in Figure 1. 1) Scientific

problem selection. We prompt the construction LLM (GPT4o) to propose candidate scientific scenarios across our five domains (e.g., plant stress physiology, polymerization kinetics), each specifying measurable variables, admissible units, and ranges. 2) Semantic graph construction. For each scenario, we build a semantic DAG G = (V,E) whose nodes are source, internal, and target variables, each annotated with metadata (type, unit, range). For each non-source variable, the construction LLM proposes a mechanism conditioned on its parents, implemented as explicit algebraic equations or numerical solver specifications (e.g., ODEs). Variables with causal semantics are generated on a causal sub-DAG G ⊆ G using internally standardized SCMs (iSCMs) (Ormaniec et al. 2025), modeling how interventions propagate through intermediate variables to the target. 3) Data generation. We generate each dataset in topological order over G: source variables are sampled from metadata, and internal/target variables are computed by executing the retained mechanisms under fixed parameters, followed by controlled measurement noise and distractor columns. To support exact ground-truth derivation (Section 3.3), we store the graph structure, causal sub-DAG, equations, and random seeds as hidden metadata. After execution replay, range checks, and expert review, we obtain 50 validated datasets (10 per domain), each supporting all 6 task types.

#### 3.3 Question Construction

Rather than manually authoring all questions or relying on unconstrainedLLMgeneration,whichcanproducequestions with weak data grounding or unverifiable answers (Zhuang et al. 2023), we use a construction pipeline inspired by automatic and agentic benchmark construction frameworks (Li et al. 2025b; Wang et al. 2025). As shown in Figure 2, the pipeline builds typed templates from seed analysis patterns, instantiates them on SDA-Synth and SDA-Real datasets with executable answer derivation, and adds perturbation-based distractors for MCQ instances. We retain only instances that pass verification, normalization, deduplication, and targeted human review.

- Stage 1: LLM-based Template Construction. We transform seed questions from the selected scientific resources into verified question templates using a four-agent pipeline: a Taxonomist assigns each seed question to a domain and one of the six task types and identifies the required data columns; an Extractor abstracts dataset-specific entities into a typed template τ with typed placeholders and validity constraints (e.g., "Is there a significant correlation between soil moisture and stomatal conductance?” becomes "Is there a significant correlation between {variable_1} and {variable_2}?”); a Generator instantiates τ on a target dataset D by binding each placeholder to a valid column, value, or entity, yielding a candidate question Q; and a Verifier rejects questions with logical inconsistencies, unresolved placeholders, schema mismatches, answer leakage, or near-duplicates.
- Stage 2: Programmatic Ground-Truth Generation. To create accurate answers for generated questions, we imple-


ment a deterministic derivation procedure fτ for each template τ. The procedure takes the reference data D and the

###### Stage 1: LLM-based Template Construction.

###### Extractor

###### Verifier

###### Taxonomist

###### Generator

Seed question: Is there a significant [correlation] between [soil moisture] and [stomatal conductance]?

entities abstracted

Assignment p: Candidate Q

Template τ Dataset D

structure preserved constraints attached otherwise discard

schema matched

valid logic &amp; wording

constraints satisfied

task type is clear

placeholders resolved

otherwise discard

| |
|---|


objective is specified

no leakage / duplicate

Template τ: Is there a significant {correlation} between {variable_1} and {variable_2}?

variables are determined

otherwise discard

Assignment p:

otherwise discard

- {variable_1} → {temperature}
- {variable_2} → {humidity}


Finalized Question:

Candidate Q:

Constraints:

Is there a significant correlation between temperature and humidity?

Is there a significant [correlation] between [temperature] and [humidity]?

{Domain: Biology; Task: Inferential.}

{variable_1} &amp; {variable_2}: type, unit, role

###### Stage 3: Option Generation.

###### Stage 2: Programmatic Ground-Truth Generation.

###### Template τ

Diffusion Confusion Randomize Default

Is there a significant {...} between {...} and {...}?

###### Validation

###### Ground-truth Answer

p

{signficant: "true", p-value: 0.0007}

- {A: signficant: "false", p-value: 0.21},
- {B: signficant: "true", p-value: 0.0007}
- {C: signficant: "false", p-value: 0.0007},
- {D: signficant: "true", p-value: 0.21}


Dataset D

###### Option

{sample_id: 1, humidity: 61.2, temperature: 23.1, ...}

Derivation Procedure

Figure 2: The Question construction pipeline.

instantiated parameters p as input and returns the groundtruth answer g = fτ(D,p). After sampling a valid p, we fill the template to form the question and run the corresponding derivation procedure on D. Since p contains the exact values used in the question, the procedure can replay the requested analysis and automatically compute the correct answer, even when the answer requires multiple reasoning steps. Before instance generation, all derivation procedures are checked through unit tests and manual review. The OEQ format uses g as the final answer directly.

Stage 3: Option Generation. For the MCQ format, we construct plausible but incorrect distractor options through perturbations of variables or intermediate computation steps (Li et al. 2025a). The correct option is the answer from the derivation procedure, while incorrect options are produced by four perturbation strategies: Diffusion (swapping or reassigning values and roles between variables), Confusion (modifying a single local element such as a parameter or operator), Randomization (sampling a new task-compliant assignment that yields a different answer), and Default (applying simple numeric transformations as a fallback). This design evaluates whether a model follows the intended analysis rather than relying on superficial elimination cues. We randomize option order to reduce positional bias.

#### 3.4 Validation and Dataset Statistics

Validation. We apply the same validation pipeline to SDASynth and SDA-Real. We first check the consistency among each instance, dataset, derivation procedure, ground-truth answer, and task definition, removing 779 candidates with underspecified variables, dataset-instance mismatches, taxonomyerrors,orambiguousinterpretations.Wethenconduct a manual quality audit of all 307 typed question templates, their associated programmatic derivation procedures, and

2,000 sampled instances. This process identified and corrected 11 minor issues and filtered out 324 unreliable cases. For multiple-choice instances, we recompute distractors with fτ and remove 86 cases with non-unique correct answers or near-equivalent distractors.

Dataset statistics and splits. After validation, we obtain 6,231 SDA-Synth instances and 527 SDA-Real instances. For controlled evaluation on SDA-Synth, we stratify instances by five domains and six task types, keeping 200 instances for each domain-task pair and forming 6,000 instances. Each coreinstancehasoneMCQversionandoneOEQversion.We split these instances into training (60%) and test (40%) sets whilekeepingpairedformatstogethertopreventleakage.The training split is used only for fine-tuning, and all SDA-Real instances are reserved for independent real-data evaluation.

### 4 Experiments

- 4.1 Experimental Setup

Base-model evaluations on SDABench use a zero-shot setting. To make outputs comparable across models and response formats, we prompt each model to produce a structured JSON response containing two fields: a reasoning field for the step-by-step analysis and a answer field for the final result. Responses are parsed automatically; only the answer field is scored against the reference, while the reasoning field is used for error annotation (Section 4.3). The main results are reported on the held-out SDA-Synth test split, and we additionally evaluate models on SDA-Real under the same protocol.

Models. We evaluate 15 representative LLMs spanning closed-sourceandopen-sourcemodels.Closed-source:GPT-

- 5.4 (OpenAI 2026a), GPT-5.4 mini (OpenAI 2026b), Claude Sonnet 4.6 (Anthropic 2026), Gemini 3.1 Pro (Google


OEQ MCQ

Model

Overall D I E P C M Overall D I E P C M

###### Open-source LLMs

DeepSeek V3.2 51.17 88.50 59.00 41.50 31.00 46.00 41.00 62.21 90.00 69.00 44.00 47.75 45.75 76.75 DeepSeek R1 42.13 85.00 46.50 34.50 23.50 40.00 23.25 56.38 84.25 67.00 42.25 36.50 40.50 67.75 Qwen 3.5-397B-A17B 51.58 89.00 61.50 37.00 37.00 37.00 48.00 62.46 92.00 73.75 44.00 35.25 52.75 77.00 Qwen 3-235B-Instruct 40.46 77.25 34.50 27.75 42.00 38.75 22.50 52.42 85.50 59.25 37.75 49.50 36.50 46.00 Kimi K2.5 50.29 84.50 43.50 29.50 34.50 39.75 70.00 57.04 92.25 73.00 34.50 25.75 36.25 80.50 GLM 5 51.67 87.75 64.75 36.50 42.75 48.00 30.25 60.79 91.50 74.50 38.75 41.00 42.00 77.00 Llama 3.3-70B-Instruct 6.96 12.00 8.00 11.75 2.75 4.50 2.75 30.46 28.00 39.50 23.50 28.25 24.00 39.50 Llama 3.1-8B-Instruct 5.04 10.25 3.50 8.25 0.50 7.75 0.00 25.00 21.50 17.75 21.50 24.75 30.50 34.00

Average (Open-Source) 37.41 66.78 40.16 28.34 26.75 32.72 29.72 50.84 73.13 59.22 35.78 36.09 38.53 62.31 Closed-source LLMs

GPT-5.4 58.33 94.75 67.25 53.75 34.50 52.75 47.00 66.58 93.50 78.50 45.50 58.25 40.75 83.00 GPT-5.4 mini 37.67 81.25 40.25 45.25 17.50 23.00 18.75 58.46 85.75 66.75 36.25 39.75 50.25 72.00 Claude Sonnet 4.6 55.79 93.00 64.50 50.25 36.00 46.00 45.00 66.38 93.75 74.25 51.75 48.00 50.00 80.50 Gemini 3.1 Pro 56.88 94.50 65.50 48.25 53.75 43.50 35.75 69.46 94.25 70.75 49.00 63.75 59.75 79.25 Gemini 3.1 Flash 40.17 91.75 40.00 42.75 23.00 20.00 23.50 57.92 92.25 71.25 39.50 38.00 36.00 70.50

Average (Closed-Source) 49.77 91.05 55.50 48.05 32.95 37.05 34.00 63.76 91.90 72.30 44.40 49.55 47.35 77.05 Fine-tuned LLMs

FT Llama-3.1-8B-Instruct 53.13 92.75 63.50 39.75 36.00 41.50 45.25 61.75 92.25 70.75 41.75 37.00 54.25 74.50 FT Llama-3.1-8B-Instruct (error type) 55.33 87.50 66.25 46.00 31.25 48.25 52.75 62.38 91.25 72.50 46.00 33.50 55.75 75.25

- Table 2: Accuracy (%) of LLMs on SDA-Synth under OEQ and MCQ. Task abbreviations: D=Descriptive, I=Inferential, E=Exploratory, P=Predictive, C=Causal, M=Mechanistic. 1st, 2nd, 3rd highest scores per column are bold-underlined, bold, and underlined. FT=fine-tuned.


DeepMind 2026b), and Gemini 3.1 Flash (Google DeepMind 2026a). Open-source: DeepSeek V3.2 (Liu et al. 2025), DeepSeek R1 (Guo et al. 2025), Qwen 3.5-397BA17B(QwenTeam2026),Qwen3-235B-Instruct(Yangetal. 2025), Kimi K2.5 (Kimi Team et al. 2026), GLM 5 (Zeng et al. 2026), Llama 3.3-70B-Instruct (Grattafiori et al. 2024), and Llama-3.1-8B-Instruct (Grattafiori et al. 2024). We additionally evaluate two LoRA fine-tuned variants of Llama-

- 3.1-8B-Instruct trained on the SDA-Synth training split.

MCQ Evaluation. For multiple-choice questions, we use standard option accuracy: a response is correct only when the extracted option matches the reference label.

OEQ Evaluation. For open-ended questions, we score the normalized final answer using evaluators matched to the answer format: a numerical evaluator (relative-error tolerance), a textual evaluator (exact and structured-field matching), and an LLM evaluator (GPT-4o) as a fallback when deterministic matching fails.

- 4.2 Main Results


To evaluate the scientific data analysis capabilities of frontier LLMs,weanalyzetheirperformanceacrosssixscientifictask types and five scientific domains.

Overall performance. Table 2 reports overall results on the held-out SDA-Synth test split under both OEQ and MCQ formats. Because the four-option MCQ format has a 25% chance floor, OEQ and MCQ accuracies are not directly comparable; we use OEQ as the primary metric and treat MCQ as a complementary signal.

Closed-source models set the strongest range, with GPT5.4 at 58.33%, Gemini 3.1 Pro at 56.88%, and Claude Sonnet 4.6 at 55.79% OEQ accuracy. Fine-tuned Llama-3.18B-Instruct approaches this range under both formats; the error-type objective further raises OEQ to 55.33%, suggesting task-aligned supervision helps smaller models learn the benchmark’s analysis structure.

Comparing the two formats reveals divergent behaviors. Kimi K2.5 on Predictive tasks achieves near-random MCQ accuracy (25.75%) despite solving matched instances under OEQ, suggesting explicit options can induce local pattern matching. Conversely, Llama 3.3-70B-Instruct remains near the random baseline on several MCQ task types (causal 24.00%, exploratory 23.50%), indicating candidate options provide little benefit when the underlying analysis procedure is absent.

Finding 1. Frontier-scale models demonstrate the strongest analytical capabilities; however, open-ended scientific data analysis remains far from solved. Task-specific supervision

###### Task BiologyChemistryEnvironmentGeographyPhysics

Descriptive 71.6 75.8 80.1 75.8 75.5 Inferential 43.6 45.2 49.2 44.9 45.8 Exploratory 35.6 37.4 40.7 30.9 33.8 Predictive 22.5 27.6 34.9 29.6 29.5 Causal 32.5 32.1 40.1 33.2 32.5 Mechanistic 29.6 33.0 36.6 24.9 31.3

Overall 39.2 41.9 46.9 39.9 41.4

- Table 3: Average OEQ accuracy (%) of LLMs on SDA-Synth across scientific data analysis tasks and scientific domains.


can substantially narrow the gap between small open models and frontier closed-source models.

Performance across task types. Table 2 shows a clear hierarchy across task types. Models perform best on Descriptive tasks, as they mainly require summarizing observed variables. Accuracy drops on Inferential and Causal tasks, which require selecting valid assumptions and reasoning over latent structure. The format gap is especially pronounced for Mechanistic tasks: MCQ options help strong models identify plausible mechanisms, whereas OEQ requires building the dependency structure by linking variables, relations, and intermediate causal steps. Exploratory and Predictive tasks remain difficult for different reasons: the former requires search over weakly constrained hypotheses, and the latter requires choosing an appropriate pattern and applying it to unseen cases.

- Finding 2. LLMs are most effective at characterizing observed samples. Performance declines when tasks require selecting assumptions, modeling latent processes, or constructing mechanisms. A central difficulty is linking intermediate dependencies into a coherent chain of reasoning.

Performance across scientific domains. Table 3 shows that domain-level variation reflects different reasoning burdensimposedbytheunderlyingdatastructure,notmerelyterminology. Models achieve the highest overall OEQ accuracy in Environment (46.9%), where many tasks involve smoother continuous variables and direct trend estimation. Biology shows the lowest overall accuracy, with a particularly low Predictive score (22.5%), suggesting high-dimensional nonlinearinteractionsmakeout-of-samplegeneralizationharder. Geography presents a different pattern: performance drops on Exploratory (30.9%) and Mechanistic (24.9%) tasks, requiring spatial reasoning from symbolic data.

- Finding 3. Domain variation reflects different reasoning burdens imposed by underlying data structure rather than mere terminology changes. Environment benefits from smoother continuous variables, while Biology suffers from highdimensional nonlinear interactions. Geography struggles with spatial structure that must be inferred from symbolic data.


Results on SDA-Real. Figure 3 reports MCQ and OEQ accuracy for GPT-5.4, GLM 5, and fine-tuned Llama 3.18B-Instruct (Error type) across scientific data analysis tasks.

GPT-5.4

GLM-5

FT Llama-3.1-8B (Error type)

97.2% 78.7%

95.2% 72.9%

95.0% 75.4%

Descriptive Inferential Exploratory Predictive Causal Mechanistic

96.7% 74.3%

94.1% 68.6%

93.6% 69.0%

Task type

53.2%

56.3% 45.5%

45.5% 43.8%

47.5% 39.9%

27.9%

42.7% 33.5%

59.0% 49.3%

MCQ OEQ

MCQ OEQ

MCQ OEQ

46.7% 34.0%

48.8% 59.4%

59.2% 69.8%

55.2% 58.4%

46.5% 41.3%

79.2%

42.6%

0% 50% 100%

0% 50% 100%

0% 50% 100%

Accuracy (%)

Figure 3: Accuracy (%) of LLMs on SDA-Real across scientific data analysis tasks.

SDA-Realbroadlypreservesthetask-typehierarchyobserved onSDA-Synth.DescriptiveandInferentialtasksremaincomparatively easier, whereas Exploratory and Predictive tasks remain more difficult. The full results are provided in the supplementary material C.

#### 4.3 Error Analysis

Error Analysis Framework. Aggregate accuracy cannot reveal where in the analysis execution process a model fails. We therefore conducted a bottom-up inspection of incorrect responses and identified five recurring failure modes ordered along the execution of scientific data analysis: (1) Scope Error, misinterpreting the analytical target or task scope; (2) Variable Error, selecting the wrong analysis variables; (3) Function Error, choosing or applying an incorrect analytical method; (4) Relationship Error, mischaracterizing the existence, direction, strength, or structure of variable interactions; and (5) Conclusion Error, drawing a final inference unsupported by the preceding analysis. We annotate the first error in the execution. To compare error profiles across tasks, domains, and models, we report the normalized error rate

(NER), NERE(S) = n

oE(S), where S is a task, domain, or model subset; nE(S) is the number of errors labeled as type E; and oE(S) is the number of examples in which type E could occur.

E(S)

Errors across task types. Figure 4(a) shows that different task types exhibit distinct primary failure modes. Function Errors peak in Predictive tasks (37.7%) and remain high in Inferential (23.0%) and Descriptive (13.4%) tasks, reflecting inappropriate method selection or formula implementation. Relationship Errors dominate Mechanistic (32.1%) and Exploratory (29.9%) tasks, where the analytical target is the relational structure itself: models mistake noise for signal in Exploratory tasks and cannot reconstruct effect propagation without knowledge of the governing mechanism in Mechanistic tasks. Conclusion Errors are most prominent in Inferential tasks (10.2%), reflecting misjudged significance under uncertainty.

Finding 4. Function Error dominates descriptive tasks, while Relationship Error becomes primary in more challenging task types, shifting the bottleneck from method selection to variable reasoning.

Errors across scientific domains. Figure 4(b) shows that LLM error patterns vary across scientific domains. In Biology, errors concentrate in Function Errors (29.8%): models identify relevant entities but substitute generic statisti-

Scope Error

Variable Error

Function Error

Relationship Error

Conclusion Error

| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


40%

40%

NER (%)

NER (%)

30%

30%

20%

20%

10%

10%

0%

0%

Descriptive Exploratory Inferential Predictive Causal Mechanistic

Biology Chemistry Environment Geography Physics

(a) Task (b) Domain

40%

NER (%)

30%

20%

10%

0%

DeepSeekV3.2DeepSeekR1 GLM5 KimiK2.5Qwen3.5-397B-A17BQwen3-235B-InstructLlama3.3-70B-InstructLlama3.1-8B-Instruct GPT-5.4GPT-5.4miniClaudeSonnet4.6Gemini3.1ProGemini3.1Flash

(c) Model

Figure 4: Normalized error rates across tasks, domains, and models on SDA-Synth.

cal procedures for domain-specific analyses. Chemistry and Environment show Relationship Errors reaching 24.6% and 27.0%, respectively, as variable interactions depend on coupledprocesses,thresholds,orconfoundersmodelsfailtocapture. Geography shows the highest Scope Error rate (9.9%), reflecting misinterpretations of the analytical target. Physics shows the highest Variable Error rate (14.5%), where models retrieve correct equations but misalign them with variables, units, or physical roles.

- Finding 5. Across domains, models fail not from lack of knowledge but from misapplication. They easily identify formulas and variables, yet overlook constraints like unit consistency, task boundaries, and variable interactions.

Errors across models. Figure 4(c) shows that models fail at different stages. Smaller baseline models (Llama 3.1-8B, Llama 3.3-70B) show the highest Variable Error rates (often above 30%), failing to map questions to correct variables. Stronger models reduce these grounding errors, but their remaining failures move toward method execution: DeepSeek R1, DeepSeek V3.2, Qwen 3.5, and GPT-5.4 are dominated by Function Errors, while Kimi K2.5, Claude Sonnet 4.6, and Gemini 3.1 Pro have lower Function Error rates but higher Relationship Error rates, indicating they execute the intended operation yet still mischaracterize variable relationships.

- Finding 6. As models improve, Scope and Variable errors decrease while Function, Relationship errors persist. This shifts error profiles toward later-stage failures, reflecting better early grounding rather than a decline in reasoning.


### 5 Discussion

SDA-Synth versus SDA-Real. The broad preservation of the task-type hierarchy from SDA-Synth to SDA-Real suggests that synthetic semantic graphs capture the core reasoning demands of real scientific analysis. However, SDA-Real also exposes differences less visible in the controlled synthetic setting: real datasets use canonical variable names that align with pretrained knowledge (inflating mechanistic accuracy), while real exploratory analysis is more sensitive to

heterogeneous schemas and noisy variables. These complementary strengths motivate keeping both components.

Limitations. SDA-Synth relies on synthetic semantic graphs whose mechanisms, while validated by domain experts, may not capture the full complexity of real experimentalconfoundersandmeasurementartifacts.TheMCQformat, despite perturbation-based distractors, can induce superficial pattern matching in some models. Our error taxonomy annotates the first error in the execution, which may undercount cascading failures.

Implications for future LLM development. Because later-stage errors persist even as grounding errors resolve with scale, future work should target three directions: assumption selection under uncertainty, relational reasoning over variable interactions, and iterative verification of intermediate results against task constraints. Beyond evaluation,SDABench’spipeline-orderederrortaxonomycanguide adaptive training curricula that progressively target the capability gaps identified at each analysis stage.

### 6 Conclusion

We introduced SDABench, a capability-oriented benchmark that evaluates LLMs on scientific data analysis across six discovery capabilities and five domains. Evaluating 15 representative LLMs, we find that models handle descriptive analysis well but degrade sharply on tasks requiring assumption selection, latent-process modeling, or mechanistic reasoning. Stronger models do not lack scientific knowledge; rather, they apply it incorrectly. To localize where models fail,wedevelopafive-stageerrortaxonomy(Scope,Variable, Function, Relationship, Conclusion) showing that Scope and Variable Errors decrease with model scale, whereas Function, Relationship, and Conclusion Errors persist, making later-stage reasoning failures the dominant bottleneck. This pipeline-ordered diagnosis enables targeted improvements beyond aggregate accuracy scores.

### References

Anthropic. 2026. Introducing Claude Sonnet 4.6. https: //www.anthropic.com/news/claude-sonnet-4-6.

Chen, Z.; Chen, S.; Ning, Y.; Zhang, Q.; Wang, B.; Yu, B.; Li, Y.; Liao, Z.; Wei, C.; Lu, Z.; Dey, V.; Xue, M.; Baker, F. N.; Burns, B.; Adu-Ampratwum, D.; Huang, X.; Ning, X.; Gao, S.; Su, Y.; and Sun, H. 2025. ScienceAgentBench: Toward Rigorous Assessment of Language Agents for DataDriven Scientific Discovery. In The Thirteenth International Conference on Learning Representations.

Fan, M.; Fan, J.; Tang, N.; Cao, L.; Li, G.; and Du, X. 2025. AutoPrep: Natural Language Question-Aware Data Preparation with a Multi-Agent Framework. Proceedings of the VLDB Endowment.

- Google DeepMind. 2026a. Gemini 3.1 Flash-Lite Model Card. https://deepmind.google/models/model-cards/ gemini-3-1-flash-lite/.
- Google DeepMind. 2026b. Gemini 3.1 Pro Model Card. https://deepmind.google/models/model-cards/gemini-3-1pro/. Grattafiori, A.; Dubey, A.; Jauhri, A.; Pandey, A.; Kadian,


- A.; Al-Dahle, A.; Letman, A.; Mathur, A.; Schelten, A.; Vaughan, A.; et al. 2024. The Llama 3 Herd of Models. arXiv preprint arXiv:2407.21783.


Gu, K.; Shang, R.; Jiang, R.; Kuang, K.; Lin, R.-J.; Lyu, D.; Mao, Y.; Pan, Y.; Wu, T.; Yu, J.; Zhang, Y.; Zhang, T. M.; Zhu, L.; Merrill, M. A.; Heer, J.; and Althoff, T. 2024. BLADE: Benchmarking Language Model Agents for Data-Driven Science. In Findings of the Association for Computational Linguistics: EMNLP 2024.

Guo, D.; Yang, D.; Zhang, H.; Song, J.; Wang, P.; Zhu, Q.; Xu, R.; Zhang, R.; Ma, S.; Bi, X.; et al. 2025. Deepseek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. arXiv preprint arXiv:2501.12948.

Guo, S.; Deng, C.; Wen, Y.; Chen, H.; Chang, Y.; and Wang, J. 2024. DS-Agent: Automated Data Science by Empowering Large Language Models with Case-Based Reasoning. In Proceedings of the 41st International Conference on Machine Learning.

Hong, S.; Lin, Y.; Liu, B.; Liu, B.; Wu, B.; Zhang, C.; Li, D.; Chen, J.; Zhang, J.; Wang, J.; Zhang, L.; Zhang, L.; Yang, M.; Zhuge, M.; Guo, T.; Zhou, T.; Tao, W.; Tang, R.; Lu, X.; Zheng, X.; Liang, X.; Fei, Y.; Cheng, Y.; Ni, Y.; Gou, Z.; Xu, Z.; Luo, Y.; and Wu, C. 2025. Data Interpreter: An LLM Agent for Data Science. In Findings of the Association for Computational Linguistics: ACL 2025.

Huang, Y.; Luo, J.; Yu, Y.; Zhang, Y.; Lei, F.; Wei, Y.; He, S.; Huang, L.; Liu, X.; Zhao, J.; and Liu, K. 2024. DA-Code: Agent Data Science Code Generation Benchmark for Large Language Models. In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing.

Jing, L.; Huang, Z.; Wang, X.; Yao, W.; Yu, W.; Ma, K.; Zhang, H.; Du, X.; and Yu, D. 2025. DSBench: How Far Are Data Science Agents from Becoming Data Science Experts? InTheThirteenthInternationalConferenceonLearningRepresentations.

Jumper, J.; Evans, R.; Pritzel, A.; Green, T.; Figurnov, M.; Ronneberger, O.; Tunyasuvunakool, K.; Bates, R.; Žídek, A.; Potapenko, A.; et al. 2021. Highly accurate protein structure prediction with AlphaFold. Nature.

KimiTeam;Bai,T.;Bai,Y.;Bao,Y.;Cai,S.;Cao,Y.;Charles, Y.; Che, H.; Chen, C.; Chen, G.; et al. 2026. Kimi K2. 5: Visual Agentic Intelligence. arXiv preprint arXiv:2602.02276. Kumbhar, S.; Mishra, V.; Coutinho, K.; Handa, D.; Iquebal, A.; and Baral, C. 2025. Hypothesis Generation for Materials Discovery and Design Using Goal-Driven and ConstraintGuided LLM Agents. In Findings of the Association for Computational Linguistics: NAACL 2025.

Lai, E.; Vitagliano, G.; Zhang, Z.; Chabra, O.; Sudhir, S.; Zeng, A.; Zabreyko, A. A.; Li, C.; Kossmann, F.; Ding, J.; Chen, J.; Markakis, M.; Russo, M.; Wang, W.; Wu, Z.; Cafarella, M.; Cao, L.; Madden, S.; and Kraska, T. 2026. KRAMABENCH: A Benchmark for AI Systems on Datato-Insight Pipelines over Data Lakes. In The Fourteenth International Conference on Learning Representations.

Lai, Y.; Li, C.; Wang, Y.; Zhang, T.; Zhong, R.; Zettlemoyer, L.; Yih, W.-T.; Fried, D.; Wang, S.; and Yu, T. 2023. DS1000: A Natural and Reliable Benchmark for Data Science Code Generation. In Proceedings of the 40th International Conference on Machine Learning.

Leek, J.; and Peng, R. 2015. What is the question? Mistaking the type of question being considered is the most common error in data analysis. Science, 347: 1314–1315.

Li, C.; Deng, W.; Lu, M.; and Yuan, B. 2025a. AtmosSciBench: Evaluating the Recent Advance of Large Language Model for Atmospheric Science. In The Thirty-ninth Annual Conference on Neural Information Processing Systems Datasets and Benchmarks Track.

Li, H.; Su, J.; Chen, Y.; Li, Q.; and Zhang, Z.-X. 2023. SheetCopilot: Bringing Software Productivity to the Next Level through Large Language Models. In Advances in Neural Information Processing Systems.

Li, X. L.; Kaiyom, F.; Liu, E. Z.; Mai, Y.; Liang, P.; and Hashimoto, T. 2025b. AutoBencher: Towards Declarative Benchmark Construction. In The Thirteenth International Conference on Learning Representations.

Liu, A.; Mei, A.; Lin, B.; Xue, B.; Wang, B.; Xu, B.; Wu, B.; Zhang, B.; Lin, C.; Dong, C.; et al. 2025. Deepseek-V3.2: Pushing the Frontier of Open Large Language Models. arXiv preprint arXiv:2512.02556.

Liu, X.; Wu, Z.; Wu, X.; Lu, P.; Chang, K.-W.; and Feng, Y. 2024. Are LLMs Capable of Data-based Statistical and Causal Reasoning? Benchmarking Advanced Quantitative Reasoning with Data. In Findings of the Association for Computational Linguistics: ACL 2024.

Ma, P.; Ding, R.; Wang, S.; Han, S.; and Zhang, D. 2023. InsightPilot: An LLM-Empowered Automated Data Exploration System. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing: System Demonstrations.

Majumder, B. P.; Surana, H.; Agarwal, D.; Hazra, S.; Sabharwal,A.;andClark,P.2024a. Position:Data-drivenDiscovery

with Large Generative Models. In Forty-first International Conference on Machine Learning.

Majumder, B. P.; Surana, H.; Agarwal, D.; Mishra, B. D.; Meena, A.; Prakhar, A.; Vora, T.; Khot, T.; Sabharwal, A.; and Clark, P. 2024b. DiscoveryBench: Towards Data-Driven Discovery with Large Language Models. arXiv.

Nam, J.; Yoon, J.; Chen, J.; and Pfister, T. 2026. DS-STAR: Data Science Agent via Iterative Planning and Verification.

- OpenAI. 2026a. Introducing GPT-5.4. https://openai.com/ index/introducing-gpt-5-4/.
- OpenAI. 2026b. Introducing GPT-5.4 mini and nano. https: //openai.com/index/introducing-gpt-5-4-mini-and-nano/.


Ormaniec, W.; Sussex, S.; Lorch, L.; Schölkopf, B.; and Krause, A. 2025. Standardizing Structural Causal Models. InTheThirteenthInternationalConferenceonLearningRepresentations.

Ouyang, S.; Huang, D.; Guo, J.; Sun, Z.; Zhu, Q.; and Zhang, J. M. 2026. DSCodeBench: A Realistic Benchmark for Data Science Code Generation. Proceedings of the AAAI Conference on Artificial Intelligence.

Qwen Team. 2026. Qwen3.5: Towards Native Multimodal Agents.

Shi, C.; Ren, X.; Wang, Y.; Li, J.; Sun, Y.; Luo, Y.; and Sheng, R. 2026. A Survey of Human-AI Collaboration for Scientific Discovery.

Shojaee, P.; Nguyen, N.-H.; Meidani, K.; Farimani, A. B.; Doan, K. D.; and Reddy, C. K. 2025. LLM-SRBench: A New Benchmark for Scientific Equation Discovery with Large Language Models. In Forty-second International Conference on Machine Learning.

Tang, J.; Xia, L.; Li, Z.; and Huang, C. 2025. AI-Researcher: Autonomous Scientific Innovation. In The Thirty-ninth Annual Conference on Neural Information Processing Systems.

Wang, S.; Long, Z.; Fan, Z.; Huang, X.; and Wei, Z. 2025. Benchmark Self-Evolving: A Multi-Agent Framework for Dynamic LLM Evaluation. In COLING, 3310–3328.

Wu, W.; Zhang, Z.; Liu, L.; Xu, X.; Liu, J.; Fan, K.; Lv, Q.; Zhuang, J.; Zhang, C.; Yuan, Z.; Hou, S.; Lin, T.; Chen, K.; Zhou, B.; and Zhang, C. 2025. SciTS: Scientific Time Series Understanding and Generation with LLMs. CoRR.

Yang, A.; Li, A.; Yang, B.; Zhang, B.; Hui, B.; Zheng, B.; Yu,

- B.; Gao, C.; Huang, C.; Lv, C.; et al. 2025. Qwen3 Technical Report. arXiv preprint arXiv:2505.09388.


Zeng, A.; Lv, X.; Hou, Z.; Du, Z.; Zheng, Q.; Chen, B.; Yin, D.; Ge, C.; Huang, C.; Xie, C.; et al. 2026. GLM-5: From Vibe Coding to Agentic Engineering. arXiv preprint arXiv:2602.15763.

Zhang, D.; Zhoubian, S.; Cai, M.; Li, F.; Yang, L.; Wang, W.; Dong, T.; Hu, Z.; Tang, J.; and Yue, Y. 2024a. DataSciBench: An LLM Agent Benchmark for Data Science.

Zhang, S.; Fan, J.; Fan, M.; Li, G.; and Du, X. 2025. DeepAnalyze: Agentic Large Language Models for Autonomous Data Science. arXiv preprint arXiv:2510.16872.

Zhang, W.; Shen, Y.; Lu, W.; and Zhuang, Y. 2024b. DataCopilot: Bridging Billions of Data and Humans with Autonomous Workflow. In ICLR 2024 Workshop on Large Language Model (LLM) Agents.

Zhuang, Y.; Yu, Y.; Wang, K.; Sun, H.; and Zhang, C. 2023. ToolQA: a dataset for LLM question answering with external tools. In Proceedings of the 37th International Conference on Neural Information Processing Systems.
