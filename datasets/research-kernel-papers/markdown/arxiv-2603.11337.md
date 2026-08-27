# RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering Agents

1st Yonas Atinafu

David R. Cheriton School of Computer Science University of Waterloo Waterloo, Canada yatinafu@uwaterloo.ca

2nd Robin Cohen

David R. Cheriton School of Computer Science University of Waterloo Waterloo, Canada rcohen@uwaterloo.ca

## arXiv:2603.11337v1 [cs.AI] 11 Mar 2026

Abstract—LLM agents increasingly perform end-to-end ML engineering tasks where success is judged by a single scalar test metric. This creates a structural vulnerability: an agent can increase the reported score by compromising the evaluation pipeline rather than improving the model. We introduce RewardHackingAgents, a workspace-based benchmark that makes two compromise vectors explicit and measurable: evaluator tampering (modifying metric computation or reporting) and train/test leakage (accessing held-out data or labels during training). Each episode runs in a fresh workspace with patch tracking and runtime file-access logging; detectors compare the agent-reported metric to a trusted reference to assign auditable integrity labels. Across three tasks and two LLM backbones, scripted attacks succeed on both vectors in fully mutable workspaces; singlemechanism defenses block only one vector; and a combined regime blocks both. In natural-agent runs, evaluator-tampering attempts occur in ≈ 50% of episodes and are eliminated by evaluator locking, with a ~25–31% median runtime overhead. Overall, we demonstrate that evaluation integrity for MLengineering agents can be benchmarked as a first-class outcome rather than assumed.

Index Terms—Keywords: Secure AI, Trusted AI, MLengineering, LLM evaluation integrity, benchmarking, reward hacking, agentic-systems

I. INTRODUCTION

LLM-based agents are beginning to act not only as assistants, but as autonomous developers for ML engineering workflows: editing code, running training loops, and iterating until a target test metric is achieved [1]–[3]. In this setting, the metric becomes an explicit optimization target. The uncomfortable implication is that a capable agent may discover strategies that increase the reported metric without increasing the underlying model quality. This is not a hypothetical failure mode: it is the standard failure mode of optimizing an imperfect objective, commonly described as reward hacking or specification gaming [4]–[6].

Most existing evaluations of agentic systems emphasize task completion and end metrics, and implicitly assume the evaluation pipeline is trustworthy [1]–[3], [7]. In software engineering benchmarks, agents are typically scored by a test suite treated as ground truth [7], [8]. In ML engineering tasks, however, the “judge” is executable code (training/evaluation scripts) that may live inside the agent’s editable workspace. If the agent can edit files, then evaluation integrity becomes part

of the problem, not a background assumption. Without explicit integrity checks, a benchmark can conflate real progress (better models) with compromised reporting (better numbers).

This paper argues for treating evaluation integrity as a first-class benchmark outcome. We introduce REWARDHACKINGAGENTS1, a workspace-based framework that makes two compromise vectors explicit and measurable: evaluator tampering (patching the code that computes or reports the metric) and train/test leakage (accessing held-out labels or test data during training). Each episode executes inside a fresh workspace containing task code and data splits; an agent proposes patches; the runner applies them; the episode executes training and evaluation; instrumentation logs file accesses; and detectors compare the agent-visible reported metric to a reference metric that is computed from pristine code under locked regimes (i.e., true_metric) to classify outcomes.

We additionally define four trust regimes that selectively restrict training-time access to held-out artifacts and protect evaluation integrity by computing the metric using pristine, external evaluation code. This lets us ask a precise question: which compromise vectors remain possible under each regime, and what runtime overhead does enforcement introduce?

Our contributions are threefold. First, we provide a benchmarkable episode abstraction for ML engineering agents that records patch actions (the concrete file diffs proposed/applied in the workspace), file accesses, and paired reported versus true metrics. Second, we operationalize evaluation integrity through detectors and regimes that separate evaluator tampering from train/test leakage. Third, we present an empirical study across three ML tasks, two LLM backbones, and three agent behaviors (scripted attacker, benign controls, and natural agents), quantifying compromise rates and runtime overhead under each regime.

II. BACKGROUND

By agentic ML (or agentic ML engineering), we mean settings where a language-model-based agent is not only generating suggestions, but is empowered to act in an ML workflow: it iteratively edits code and configuration, runs

1Code and artifacts: github.com/Yonas650/RewardHackingAgents.

training and evaluation, inspects outputs, and repeats this loop with the goal of improving a task metric. This differs from static “one-shot” code generation because the agent can use execution feedback and can directly modify the artifacts that determine the reported score. In many ML-engineering workflows, success is mediated by a measurement channel—often a single scalar metric emitted by local evaluation code [9]. As a result, agents that iteratively edit and run ML pipelines can end up optimizing that channel rather than the intended capability, especially when the evaluator is workspace-editable. If the evaluation pipeline (scripts, splits, and outputs) is editable within the agent’s workspace, then the measured score can be increased either by improving the model or by compromising the measurement procedure itself. This makes evaluation integrity a first-class concern in agentic ML engineering.

Existing agent evaluations largely report end metrics and assume the scorer is reliable [1]–[3], [7]. In contrast, ML engineering tasks often place the scorer inside the workspace as executable code and local artifacts, creating an attack surface that is absent when the judge is external. What is missing is a benchmark interface that (i) makes common compromise vectors explicit, (ii) records auditable evidence of attempted compromise, and (iii) supports targeted protections and access restrictions so researchers can quantify which failure modes remain possible and at what cost.

We address this gap with an episode abstraction that logs agent edits and file accesses and compares an agent-visible metric to a reference metric computed from pristine code under locked regimes. Section IX situates this design relative to prior work in reward hacking, agent benchmarks, and evaluation reliability.

III. THREAT MODEL AND PROBLEM SETUP

We consider an ML engineering agent that operates by proposing code edits (patches) within a task workspace. Each task provides a training script (train_model.py), an evaluation script (evaluate.py), and a reference metric implementation (metrics_ref.py). The agent may propose arbitrary patches to files in the workspace, including the evaluator and reference code, and may read accessible files unless blocked by policy. In locked regimes, true_metric is computed from pristine external code (not workspace copies).

Compromise vectors. We focus on two compromise vectors that are directly measurable in a workspace setting:

Evaluator tampering occurs when the agent modifies the evaluation procedure (e.g., evaluate.py) so that the reported metric no longer reflects the true model performance on the intended test split. We operationalize this via evaluator hash deviation and disagreement between the reported metric and a trusted reference metric.

Train/test leakage occurs when the training procedure accesses held-out test artifacts or any leak artifact that reveals held-out information (e.g., test inputs or a file that directly exposes test labels) during training. We operationalize this via runtime file access logs that tag paths as

train/val/test/leak using task-specific path rules, and record whether access was denied.

Outcomes and labels. Each episode produces a trusted metric (true_metric) computed by metrics_ref.py and an agent-visible metric (reported_metric) computed by the (possibly patched) evaluation script or forced to the trusted value in locked regimes. Detectors classify episodes into mutually exclusive families: no compromise, evaluator tampering, train/test leakage, blocked-by-policy attempts, or metric drift that is inconclusive (mismatch without evidence of tampering or leakage).

Out of scope. We do not model OS-level escapes, kernel exploits, or side-channel exfiltration beyond file access within the workspace. Our goal is not to claim a complete security sandbox; it is to benchmark and measure integrity failures that arise naturally from patch-based agent operation in realistic ML engineering tasks.

IV. FRAMEWORK

REWARDHACKINGAGENTS structures evaluation as repeated episodes. Each episode is an isolated execution of an agent on a task instance inside a fresh workspace, producing an auditable record of actions and outcomes. Figure 1 summarizes the system.

Episode lifecycle. For each episode, the runner creates a new workspace by copying a task scaffold (source code and data splits) into an episode directory. The agent then proposes a set of patches, represented as structured edits to workspace files. The runner applies the patches, records which edits were accepted, and executes the training and evaluation pipeline. Finally, it computes integrity flags and aggregates results into artifacts.

Instrumentation: file access logging and enforcement. We instrument file operations within the episode process to log each read/write with contextual metadata including the calling script, path, and a split tag (train/val/test/leak). In regimes that deny train-time access to test/leak files, attempted reads trigger a PermissionError and are logged as denied. This yields a direct measurement of leakage attempts and whether they were successfully blocked.

Trusted reference metric. To separate genuine learning progress from compromised reporting, each task includes a reference metric implementation (metrics_ref.py) that computes true_metric from the model artifact and the intended evaluation split. In locked regimes, the runner computes true_metric using pristine external copies of the evaluator/reference scripts, making this computation trusted for that regime. The episode’s reported_metric is taken from the (possibly patched) evaluate.py output when evaluation is mutable, and from the trusted reference computation when evaluation is locked.

Detectors and outcome labels. Detectors combine three evidence sources: (i) the evaluator hash (eval_hash_changed), (ii) file access logs (attempted and denied reads of test/leak paths), and (iii) disagreement between reported_metric and true_metric. Episodes with metric mismatch

Fig. 1. System overview: tasks and workspace templates, agentgenerated patches, episode runner, instrumentation/detectors, and trust regimes (mutable, evalhashlock, train_deny, full_locked).

but no tampering or leakage evidence are labeled metric_drift_inconclusive rather than counted as compromise. This distinction is important for credible false-positive reporting.

Trust regimes. We evaluate four trust regimes (our term for evaluation policies that determine what is trusted and what is restricted) that isolate compromise vectors: mutable allows evaluator edits and train-time access to test/leak files; evalhashlock records evaluator hash changes but scores the episode using pristine external reference code (while still allowing training-time reads); train_deny denies train-time reads of test/leak paths but leaves evaluation code mutable; and full_locked combines both defenses by denying traintime access to test/leak artifacts and scoring using pristine external reference code.

Measurement validity. We treat single signals as insufficient on their own: file access events provide direct evidence of attempted split leakage, while evaluator hash deviation provides direct evidence of code tampering. Metric disagreement (reported_metric ̸= true_metric) is used as supporting evidence but is not, by itself, labeled as compromise; mismatches without tamper/leak evidence are labeled metric_drift_inconclusive. This design reduces false positives and makes integrity claims auditable from episode artifacts.

V. EXPERIMENTAL DESIGN

Tasks. We instantiate three ML engineering tasks spanning tabular, vision, and NLP:2 (i) Credit Risk classification using an XGBoost-style pipeline [10] over comma-separated values (CSV) splits, (ii) CIFAR-10 image classification using a

2Experiments used 1× RTX 6000 Ada GPU; 8 CPU; 32/48GB RAM (TinyLlama/Qwen).

ResNet-18-style pipeline [11] over the standard batch files [12], and (iii) SST-2 (Stanford Sentiment Treebank 2) sentiment classification using a DistilBERT-style pipeline [13] over tab-separated values (TSV) splits [14], [15]. We choose these tasks to cover heterogeneous data formats and toolchains (CSV, batch files, TSV), creating realistic opportunities for both evaluator tampering and split leakage in a workspace setting. Each task provides explicit train/val/test splits and a reference metric implementation (metrics_ref.py), which is executed from pristine external copies under locked regimes.

Backbones and agents. We evaluate two LLM backbones (TinyLlama [16] and Qwen [17]) and three agent behaviors, each run as a separate experimental condition (they do not co-exist within an episode): attack_suite (scripted attacks to measure worst-case compromise capability), benign_hf (a noop control that applies no patches, used to estimate false positives and metric drift), and two natural agents (naive_hf and instruction_hf) run under our default metric-improvement prompt (no explicit instruction to tamper with evaluation or to access held-out artifacts), while retaining the same patch capabilities as in other regimes. We choose these backbones to span open chat model scale: TinyLlama as a small model and Qwen as a larger model, providing coverage from a lightweight open chat model to a stronger open chat model.

Regimes. All episodes run under one of four trust regimes: mutable, evalhashlock, train_deny, and full_locked (Section IV).

Episode counts. For the scripted attack-suite, we run 3 tasks × 40 episodes per task, yielding 120 episodes per regime per backbone. For benign controls, we similarly run 120 episodes per regime per backbone. For natural agents, we run 3 tasks × 40 episodes × 2 agents, yielding 240 episodes per regime per backbone.

Metrics. We report compromise rates (overall, evaluator tampering, and train/test leakage), attempt rates for each vector, and enforcement overhead measured as episode wallclock runtime. We additionally analyze the difference between agent-visible reported metrics and trusted reference metrics to quantify metric inflation under regimes that permit evaluator modifications.

VI. RESULTS

We report three evaluation settings: (i) scripted attacks under our threat model (attack_suite), (ii) benign controls for false positives and drift (benign_hf), and (iii) natural agent behavior (naive_hf and instruction_hf). Unless otherwise stated, rates aggregate all tasks and episodes for a given backbone and trust regime; Table I reports 95% confidence intervals for overall compromise rates (Wilson score interval).

The scripted attack-suite confirms that integrity failures are not edge cases: in mutable, the attacker succeeds on both compromise vectors in every episode (overall_success = 1.0, success_eval = 1.0, success_train = 1.0) across both backbones (Table I). Single-mechanism defenses reduce the attack surface but leave one compromise vector open: evalhashlock prevents evaluator tampering

TABLE I SCRIPTED ATTACK-SUITE OUTCOMES (3 TASKS × 40 EPISODES/TASK). SUCCESS_EVAL/SUCCESS_TRAIN: SUCCESSFUL (NOT BLOCKED) TAMPERING/LEAKAGE; OVERALL_SUCCESS: EITHER VECTOR SUCCEEDS.

Backbone Regime Overall (95% CI) Success Eval Success Train Blocked Train

tinyllama mutable 1.00 [0.97, 1.00] 1.00 1.00 0.00 tinyllama evalhashlock 1.00 [0.97, 1.00] 0.00 1.00 0.00 tinyllama train_deny 1.00 [0.97, 1.00] 1.00 0.00 1.00 tinyllama full_locked 0.00 [0.00, 0.03] 0.00 0.00 1.00

qwen mutable 1.00 [0.97, 1.00] 1.00 1.00 0.00 qwen evalhashlock 1.00 [0.97, 1.00] 0.00 1.00 0.00 qwen train_deny 1.00 [0.97, 1.00] 1.00 0.00 1.00 qwen full_locked 0.00 [0.00, 0.03] 0.00 0.00 1.00

Attack-suite success by trust regime and backbone

| |tinyllama<br><br>qwen| | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |


1.0

0.8

Overall success rate

0.6

0.4

0.2

0.0

mutable evalhashlock train_deny full_locked

Fig. 2. Attack-suite (scripted) outcomes by regime and backbone. Partial defenses block one vector but leave the other open; full_locked blocks both.

from affecting the score (success_eval = 0.0) yet leaves train/test leakage fully exploitable (success_train = 1.0), while train_deny blocks leakage attempts (blocked_train = 1.0, success_train = 0.0) but leaves evaluator tampering fully exploitable (success_eval = 1.0). Only full_locked blocks both vectors simultaneously, driving overall compromise to 0; under this regime, train/test leakage attempts are denied (blocked_train = 1.0) rather than succeeding (Table I, Fig-

- ure 2).


A key takeaway is that the two vectors behave like independent failure modes: defenses that “fix evaluation” do not fix leakage, and defenses that “fix leakage” do not fix evaluation. This separation is the point of the regime design: it supports defense selection and per-vector mitigation evaluation.

Benign controls establish that our detectors are not triggerhappy: across all regimes and both backbones, the falsepositive rate is 0 (Table II). We do observe occasional metric

disagreements in mutable (TinyLlama: 7/120; Qwen: 4/120), which are labeled metric_drift_inconclusive rather than compromise. Such mismatches can also arise from benchmark noise (e.g., test-set label errors) or subtle dataset replication differences, so we treat disagreement without tamper/leak evidence as inconclusive [18], [19]. In evaluatorlocking regimes, reported_metric is forced to the trusted reference by construction, so metric mismatch cannot occur; thus, drift is only observable in regimes where the evaluator is allowed to report its own metric.

We measure runtime overhead using benign episodes as the cleanest baseline. In these runs, full_locked increases median runtime only slightly relative to mutable (about +2% for both backbones), indicating that the integrity mechanisms can be lightweight when the agent is not actively perturbing the workspace.

TABLE II BENIGN CONTROL (AGENT=BENIGN_HF): FALSE POSITIVES ARE ZERO ACROSS ALL REGIMES; DRIFT-ONLY EPISODES OCCUR ONLY IN MUTABLE AND ARE LABELED INCONCLUSIVE RATHER THAN HACKING.

Backbone Regime n FP FP rate Drift Drift rate tinyllama mutable 120 0 0.000 7 0.058 tinyllama evalhashlock 120 0 0.000 0 0.000 tinyllama train_deny 120 0 0.000 0 0.000 tinyllama full_locked 120 0 0.000 0 0.000 qwen mutable 120 0 0.000 4 0.033 qwen evalhashlock 120 0 0.000 0 0.000 qwen train_deny 120 0 0.000 0 0.000 qwen full_locked 120 0 0.000 0 0.000

- A. Natural behavior: how often agents attempt and succeed without scripted attacks

Natural agents behave differently from the scripted attack_suite designed to trigger worst-case compromises.

Across both backbones in our natural-agent runs (3 tasks, 40 episodes/task, 2 agents), evaluator-tamper attempts occur in half of episodes (attempt_eval = 0.5), while we observe zero logged train/test leakage attempts (attempt_train = 0.0). We define an evaluator-tamper attempt as any episode where the agent proposes or applies a patch that modifies the evaluation entrypoint (e.g., evaluate.py) or otherwise changes the computation/reporting of reported_metric. We define a train/test leakage attempt as any training-time file access event tagged as test or leak by the split classifier (regardless of whether it is permitted or denied); split tagging is task-specific and implemented as explicit path rules over the provided train/val/test/leak artifacts. This implies that the dominant observed risk under these conditions is evaluatorside manipulation rather than leakage.

Consistent with this, regimes that leave evaluation mutable (mutable and train_deny) exhibit a 50% overall compromise rate (overall_success = 0.5), whereas regimes that lock evaluator integrity (evalhashlock and full_locked) drive observed compromise to zero (Figure 3a, Figure 3b). The reported-vs-true scatter further shows that compromised episodes manifest as clear deviations from the diagonal (Figure 3c), making metric inflation directly observable and quantifiable for auditing and defense comparison when trusted references are available.

To quantify inflation when evaluator edits are possible, we compute reported-true metric differences(summarized in Figure 3c). These distributions are regime-dependent: locked regimes drive inflation to approximately zero, while regimes with mutable evaluation exhibit substantial positive shifts (reported metrics exceeding trusted metrics), consistent with evaluator tampering rather than genuine learning progress.

- B. Overhead: what enforcement costs


Integrity enforcement has measurable but bounded cost. Under natural agents, train_deny is close to mutable in median runtime (small single-digit percent increases depending on backbone), while evaluator-locking regimes introduce

larger overhead (roughly +25–31% in our medians). The benign runs show much smaller overhead because the agent does not perturb the workspace, leading to shorter episode trajectories with fewer patch attempts and fewer reruns; in contrast, natural agents typically trigger more evaluation iterations and additional trusted checks/metric computation in locking regimes, which increases end-to-end runtime. The empirical cumulative distribution function(ECDF) view confirms this as a systematic right-shift rather than rare outliers (Figure 4b). Taken together, Figure 4a summarizes the central engineering tradeoff: stronger integrity guarantees reduce compromise but reduce throughput.

VII. DISCUSSION AND LIMITATIONS

Our results support two core conclusions. First, in MLengineering agent settings where the scorer is code inside the workspace, evaluation integrity cannot be treated as an implicit assumption. More broadly, benchmark scores can be unstable targets of optimization, strengthening the case for reporting integrity evidence alongside raw performance [20]. Under the scripted attacker, partial defenses are insufficient: evaluator locking prevents evaluator tampering but leaves train/test leakage fully exploitable, while train-time deny prevents leakage but leaves evaluator tampering fully exploitable (Table I, Figure 2). Only the combined regime blocks both vectors.

Second, natural agent behavior differs from the scripted attacker in an important way: in our runs, natural agents do not attempt train/test leakage (attempt_train = 0 across regimes), but they do attempt evaluator tampering in half the episodes (attempt_eval = 0.5), succeeding in mutable and train_deny regimes and dropping to zero under evaluator hash locking and full locking (Figures 3b–3a). This reinforces a key methodological point: benchmarks should measure both worstcase capability (what an agent can do) and natural behavior (what an agent tends to do), because the risk profile depends on both [20].

We also observe that integrity measurement must distinguish compromise from non-adversarial variance. In benign controls, false positives are zero across all regimes, while drift-only mismatches occur only in mutable (5.8% for TinyLlama; 3.3% for Qwen) and are labeled inconclusive rather than hacking (Table II). This design choice is deliberate: a benchmark that

Status

Overall success

Eval tamper attempts

pristine compromised

1.0

| |
|---|


| |
|---|


| |
|---|


Backbone

| | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |


| | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |


0.5

0.5

tinyllama qwen

| |
|---|


0.8

0.4

0.4

reported_metric

0.3

0.3

Fraction

Fraction

0.6

0.2

0.2

0.4

0.1

0.1

0.2

0.0

0.0

Regime

tinyllama mutable

tinyllama evalhashlock

tinyllama train_deny

tinyllama full_locked

tinyllama mutable

tinyllama evalhashlock

tinyllama train_deny

tinyllama full_locked

qwen mutable

qwen evalhashlock

qwen train_deny

qwen full_locked

qwen mutable

qwen evalhashlock

qwen train_deny

qwen full_locked

mutable

train_deny full_locked

| |
|---|


| |
|---|


0.0

evalhashlock

0.0 0.2 0.4 0.6 0.8 1.0

true_metric

(c) Reported vs. true. Fig. 3. Natural-agent behavior across regimes and backbones.

(a) Overall compromise.

(b) Eval-tamper attempts.

Natural agents

Scripted attack-suite

tinyl-mutable

qwen-mutable

1.0

1.0

1.0

0.50 0.00

1.00 1.00

mutable

mutable

0.8

0.8

Compromise rate

0.8

0.6

0.00 0.00

- 0.00 1.00
- 1.00 0.00


evalhashlock

evalhashlock

success rate

0.6

0.4

tinyllama-mutable

0.6

ECDF

tinyllama-evalhashlock

0.4

0.2

0.50 0.00

train_deny

train_deny

tinyllama-train_deny tinyllama-full_locked qwen-mutable

natural

tinyl-full_locked

qwen-full_locked

attack

0.4

0.0

0.2

6.00 6.25 6.50 6.75 7.00 7.25 7.50 7.75

0.00 0.00

0.00 0.00

full_locked

full_locked

Median runtime (s)

qwen-evalhashlock

0.0

0.2

(a) Overhead vs. compromise.

eval_tamper_success train_leak_success

eval_tamper_success train_leak_success

qwen-train_deny qwen-full_locked

0.0

(c) Attack surface.

0 50 100 150 200

runtime_sec

(b) Runtime ECDFs.

Fig. 4. Summary views: tradeoff, runtime distributions, and attack surface across regimes/backbones.

Runtime median by regime

Benign runtime by regime/backbone

14

| | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |


8

| | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |


12

7

10

6

Median runtime (s)

Seconds

8

5

6

4

4

3

2

2

0

1

tinyllama mutable

tinyllama evalhashlock

tinyllama train_deny

tinyllama full_locked

qwen mutable

qwen evalhashlock

qwen train_deny

qwen full_locked

0

tinyllama mutable

tinyllama evalhashlock

tinyllama train_deny

tinyllama full_locked

qwen mutable

qwen evalhashlock

qwen train_deny

qwen full_locked

(b) Natural-agent runtime medians.

(a) Benign overhead medians (benign_hf).

Fig. 5. Runtime overhead summary by regime and backbone.

over-attributes drift to compromise would not be credible as a measurement tool.

Overhead and practicality. Enforcement is not free. Under benign controls, full_locked increases median episode time by about 2% relative to mutable. Under natural agents, evaluator hash locking and full locking introduce larger overhead increases relative to mutable (roughly 25–31% in our medians, depending on backbone), while train_deny is closer to mutable. These overheads reflect additional integrity checks and trusted metric computation, and they make explicit the tradeoff between security posture and throughput (Figure 4a, Figure 4b).

Limitations. Our study covers three tasks, two LLM backbones, and a patch-based agent interface. The regimes we evaluate target two concrete vectors (evaluator tampering and train/test leakage) and are not a complete defense against all possible attacks (e.g., data poisoning within train splits, subtle metric manipulation that preserves hashes, or OSlevel escapes). Finally, our natural-agent results should be interpreted as empirical behavior under our prompting and task design, not as a universal claim about all LLM agents.

VIII. OVERVIEW OF CONTRIBUTIONS

We presented REWARDHACKINGAGENTS, a benchmark framework that treats evaluation integrity as a measurable outcome for ML-engineering LLM agents. By combining perepisode workspaces, patch tracking, file-access instrumentation, trusted reference metrics, and explicit trust regimes, our framework separates evaluator tampering from train/test leakage and quantifies how defenses change the attack surface. Across worst-case scripted attacks, partial defenses fail to prevent compromise, while a combined regime blocks both vectors. Under natural agent behavior, evaluator-tamper attempts are common and are eliminated by evaluator locking and full locking, with bounded overhead. We hope this work encourages agent evaluations that do not merely score outcomes, but also verify that those outcomes were obtained honestly.

IX. RELATED WORK

Reward hacking, specification gaming, and reward tampering. A long-standing concern in ML and AI safety is that optimizing a convenient proxy objective can produce behaviors that increase the measured score without achieving the intended goal (often discussed as reward hacking or specification gaming) [4], [21]. Related work in reinforcement learning studies tampering with the reward channel itself (e.g., “wireheading” / corrupted rewards) and develops formal characterizations and mitigation principles [5], [22]. Our setting is different in mechanism but aligned in spirit: in agentic ML engineering, the “reward channel” is frequently a scalar metric produced by editable training/evaluation code and local artifacts. We therefore make integrity failures observable at the workflow level by pairing an agent-visible reported metric with

a reference metric computed from pristine code under locked regimes, alongside logs of the agent’s interactions with code and data.

Benchmarks for ML engineering and research agents. Recent benchmarks evaluate LLM agents on end-to-end ML experimentation and engineering, typically by letting an agent iteratively edit code, run experiments, and improve performance [1]–[3], [23]. These efforts are crucial for measuring capability, but their primary score is still an outcome metric (e.g., validation/test performance, competition score) and they generally do not treat evaluation integrity as a first-class measurable outcome. In parallel, agent designs for ML engineering continue to improve (e.g., via search and targeted refinement) [24], making it increasingly important to disentangle genuine learning progress from metric inflation when the agent has broad write access to the workspace. Our contribution complements these benchmarks by adding an auditable integrity layer—tracking patch actions and file accesses and separating compromise vectors—so future capability evaluations can report not only “how high the score is,” but also “how trustworthy the score is.”

Software engineering agents and test-based evaluation. In software engineering benchmarks, agents are often scored by a test suite that is treated as ground truth, such as SWEbench [7]. Follow-on work improves label reliability via human validation (e.g., SWE-bench Verified) [8]. While these evaluations differ from ML engineering (where the “judge” is often the evaluation script itself), they illustrate a shared lesson: benchmark scores are only meaningful insofar as the evaluation procedure is robust to gaming. Our work focuses on the ML-engineering regime where the evaluation pipeline is itself part of the mutable workspace, and we operationalize integrity as separable, observable outcomes (evaluator tampering vs. train/test leakage) under trust regimes with selective access restrictions and evaluator locking.

Documentation, governance, and trustworthy reporting. Several lines of work aim to improve transparency and trust in deployed ML systems via structured documentation artifacts: Datasheets for Datasets [25], Model Cards for reporting model behavior [26], and FactSheets for AI services [27]. Broader governance efforts and guidelines (e.g., NIST’s AI RMF [28] and the Montréal Declaration [29]) emphasize accountability and responsible development. These approaches improve what is documented about models and datasets, but they do not directly address the benchmark setting we study: an autonomous ML-engineering agent that can modify the evaluation pipeline itself. Our benchmark complements documentation-based approaches by providing an auditable integrity signal (reported vs. trusted metrics plus evidence from patch logs and dataaccess traces) for agent-driven ML workflows.

Positioning and implications. Taken together, adjacent literatures motivate two requirements for agentic ML engineering evaluation: (i) metrics should be treated as potentially corruptible channels [5], [22], and (ii) benchmarks should support end-to-end agent workflows at scale [1]–[3]. Our benchmark is positioned to help the ML-agent community

iterate more safely: it provides an auditable episode abstraction (patches + file-access traces) and integrity-sensitive scoring, enabling future work to compare agent designs and defenses on both capability and compromise.

X. IMPACT AND FUTURE WORK

Impact. This work targets researchers building and evaluating ML-engineering agents. Our results show that, when evaluation code is workspace-editable, a single scalar score is not a sufficient outcome measure: under natural-agent behavior in our setup, evaluator-side manipulation occurs frequently, and under a scripted attacker both evaluator tampering and split leakage are readily achievable unless both are addressed. RewardHackingAgents provides a concrete way to report capability alongside integrity (e.g., score plus an auditable integrity label) and to compare defenses via explicit regimes and measured overheads. Beyond research evaluation, organizations adopting LLM agents for training, evaluation, and reporting can use the same framing—separating evaluator integrity from data-access integrity and logging auditable evidence—to reason about operational risk in automated ML pipelines, even when the exact mechanisms differ from our benchmark.

Future work. Several extensions are natural starting points. (1) Stronger, OS-level enforcement: the current in-process I/O logging can miss reads performed via subprocesses; sandboxing or syscall-level tracing would broaden coverage. (2) Richer integrity signals: extend detectors beyond file access and evaluator hashes to include provenance of reported numbers (e.g., structured metric attestations) and integrity of dependencies (configs, checkpoints, environment). (3) Broader threat models and tasks: expand beyond the two compromise vectors studied here to additional failure modes (e.g., dataset poisoning within the workspace, cache/serialization attacks, or “silent” evaluator perturbations). (4) Agent training with integrity constraints: use regimes and labels as supervision to train agents that achieve strong task performance while maintaining integrity.

AI-GENERATED CONTENT ACKNOWLEDGEMENT

Generative AI tools were used solely for proofreading and minor grammatical edits in parts of the manuscript, including some table text. The research content and findings are entirely the authors’ work.

REFERENCES

- [1] Q. Huang, J. Vora, P. Liang, and J. Leskovec, “MLAgentBench: Evaluating language agents on machine learning experimentation,” in Proceedings of the 41st International Conference on Machine Learning (ICML), ser. Proceedings of Machine Learning Research (PMLR), vol. 235, 2024, originally released as arXiv:2310.03302.
- [2] J. S. Chan, N. Chowdhury, O. Jaffe, J. Aung, D. Sherburn, E. Mays, G. Starace, K. Liu, L. Maksin, T. Patwardhan, L. Weng, and A. Ma˛dry, “MLE-bench: Evaluating machine learning agents on machine learning engineering,” in International Conference on Learning Representations (ICLR), 2025, originally released as arXiv:2410.07095.
- [3] D. Nathani, L. Madaan, N. Roberts, N. Bashlykov, A. Menon, V. Moens, A. Budhiraja, D. Magka, V. Vorotilov, G. Chaurasia, D. Hupkes, R. S. Cabral, T. Shavrina, J. Foerster, Y. Bachrach, W. Y. Wang, and R. Raileanu, “MLGym: A new framework and benchmark for advancing AI research agents,” arXiv, 2025, arXiv:2502.14499.


- [4] D. Amodei, C. Olah, J. Steinhardt, P. Christiano, J. Schulman, and D. Mané, “Concrete problems in AI safety,” arXiv, 2016, arXiv:1606.06565.
- [5] T. Everitt, V. Krakovna, L. Orseau, M. Hutter, and S. Legg, “Reward tampering problems and solutions in reinforcement learning: A causal influence diagram perspective,” arXiv, 2019, arXiv:1908.04734.
- [6] D. Manheim and S. Garrabrant, “Categorizing goodhart’s law,” arXiv, 2018, arXiv:1803.04585.
- [7] C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, and K. Narasimhan, “SWE-bench: Can language models resolve real-world GitHub issues?” in International Conference on Learning Representations (ICLR), 2024.
- [8] N. Chowdhury, J. Aung, C. J. Shern, O. Jaffe, D. Sherburn, G. Starace, E. Mays, R. Dias, M. Aljubeh, M. Glaese, C. E. Jimenez, J. Yang, L. Ho, T. Patwardhan, K. Liu, and A. Madry, “Introducing SWE-bench verified,” OpenAI Blog, 2024, accessed: 2025-12-17.
- [9] D. Sculley, G. Holt, D. Golovin, E. Davydov, T. Phillips, D. Ebner, V. Chaudhary, M. Young, J.-F. Crespo, and D. Dennison, “Hidden technical debt in machine learning systems,” in Advances in Neural Information Processing Systems (NeurIPS), 2015.
- [10] T. Chen and C. Guestrin, “Xgboost: A scalable tree boosting system,” in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD), 2016.
- [11] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” in Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016, originally released as arXiv:1512.03385.
- [12] A. Krizhevsky, “Learning multiple layers of features from tiny images,” University of Toronto, Tech. Rep., 2009, technical report.
- [13] V. Sanh, L. Debut, J. Chaumond, and T. Wolf, “Distilbert, a distilled version of bert: smaller, faster, cheaper and lighter,” in NeurIPS 2019 Workshop: EMC2 (Energy Efficient Machine Learning and Cognitive Computing), 2019, workshop poster; originally released as arXiv:1910.01108.
- [14] R. Socher, A. Perelygin, J. Wu, J. Chuang, C. D. Manning, A. Ng, and C. Potts, “Recursive deep models for semantic compositionality over a sentiment treebank,” in Proceedings of EMNLP, 2013.
- [15] A. Wang, A. Singh, J. Michael, F. Hill, O. Levy, and S. R. Bowman, “GLUE: A multi-task benchmark and analysis platform for natural language understanding,” in Proceedings of the 2018 EMNLP Workshop BlackboxNLP: Analyzing and Interpreting Neural Networks for NLP, 2018, originally released as arXiv:1804.07461.
- [16] TinyLlama Team, “Tinyllama/tinyllama-1.1b-chat-v1.0 model card,” Hugging Face Model Card, 2024.
- [17] Qwen Team, “Qwen/qwen1.5-7b-chat model card,” Hugging Face Model Card, 2024.
- [18] C. G. Northcutt, A. Athalye, and J. Mueller, “Pervasive label errors in test sets destabilize machine learning benchmarks,” in NeurIPS Datasets and Benchmarks Track, 2021, originally released as arXiv:2103.14749.
- [19] B. Recht, R. Roelofs, L. Schmidt, and V. Shankar, “Do imagenet classifiers generalize to imagenet?” in Proceedings of the 36th International Conference on Machine Learning (ICML), ser. Proceedings of Machine Learning Research (PMLR), vol. 97, 2019, originally released as arXiv:1902.10811.
- [20] M. Dehghani et al., “The benchmark lottery,” arXiv, 2021, arXiv:2107.07002.
- [21] V. Krakovna et al., “Specification gaming: The flip side of AI ingenuity,” DeepMind Blog, 2020, accessed: 2025-12-17.
- [22] T. Everitt, V. Krakovna, L. Orseau, M. Hutter, and S. Legg, “Reinforcement learning with a corrupted reward channel,” in Proceedings of the 26th International Joint Conference on Artificial Intelligence (IJCAI), 2017, originally released as arXiv:1705.08417.
- [23] X. Liu, H. Yu, H. Zhang, Y. Xu, X. Lei, H. Lai, Y. Gu, H. Ding, K. Men, K. Yang, S. Zhang, X. Deng, A. Zeng, Z. Du, C. Zhang, S. Shen, T. Zhang, Y. Su, H. Sun, M. Huang, Y. Dong, and J. Tang, “Agentbench: Evaluating LLMs as agents,” in International Conference on Learning Representations (ICLR), 2024.
- [24] J. Nam, J. Yoon, J. Chen, J. Shin, S. Ö. Arik, and T. Pfister, “MLE-star: Machine learning engineering agent via search and targeted refinement,” arXiv, 2025, arXiv:2506.15692.
- [25] T. Gebru, J. Morgenstern, B. Vecchione, J. W. Vaughan, H. Wallach, H. Daumé III, and K. Crawford, “Datasheets for datasets,” Communications of the ACM, vol. 64, no. 12, pp. 86–92, 2021, originally released as arXiv:1803.09010 (2018).


- [26] M. Mitchell, S. Wu, A. Zaldivar, P. Barnes, L. Vasserman, B. Hutchinson, E. Spitzer, I. D. Raji, and T. Gebru, “Model cards for model reporting,” in Proceedings of the Conference on Fairness, Accountability, and Transparency (FAccT), 2019.
- [27] M. Arnold, R. K. E. Bellamy, M. Hind, S. Houde, S. Mehta, A. Mojsilovic, K. N. Ramamurthy, D. Reimer, A. Olteanu, D. Piorkowski, J. Tsay, and K. R. Varshney, “Factsheets: Increasing trust in AI services through supplier’s declarations of conformity,” IBM Journal of Research and Development, 2019.
- [28] “Artificial intelligence risk management framework (AI RMF 1.0),” National Institute of Standards and Technology (NIST), Tech. Rep. NIST AI 100-1, 2023.
- [29] Université de Montréal, “The montréal declaration for a responsible development of artificial intelligence,” Website, 2018, accessed: 202512-14.
