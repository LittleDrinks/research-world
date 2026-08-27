# arXiv:2604.12147v3 [cs.SE] 7 Aug 2026

## From Plan to Action: How Well Do Agents Follow the Plan?

Shuyang Liu∗

University of Illinois Urbana-Champaign Urbana, USA sl225@illinois.edu

Saman Dehghan∗

University of Illinois Urbana-Champaign Urbana, USA samand2@illinois.edu

Jatin Ganhotra

IBM New York, USA jatinganhotra@us.ibm.com

Martin Hirzel

IBM New York, USA hirzel@us.ibm.com

### Abstract

Agents are commonly instructed to follow a task-specific plan for guidance. However, it is unknown to what extent agents actually follow instructed plans. Without such an analysis—determining the extent agents comply with a given plan—it is impossible to assess whether a solution was reached through correct strategic reasoning or through other means, e.g., data contamination or overfitting to a benchmark. This paper presents the first extensive, systematic analysis of plan compliance in programming agents, examining 21,120 trajectories from SWE-agent across four LLMs on SWE-bench Verified and SWE-bench Pro under eight plan variations. Without an explicit plan, agents fall back on internalized workflows during training, which are often incomplete, overfit, or inconsistently applied. Providing the standard plan improves issue resolution, and we observe that periodic plan reminders can mitigate plan violations and improve task success. A subpar plan hurts performance even more than no plan at all. Surprisingly, inserting additional task-relevant phases in the early stage can degrade performance, particularly when these phases do not align with the model’s internal problem-solving strategy. These findings call for fine-tuning paradigms that teach models to follow instructed plans, rather than encoding task-specific plans in them, so that they reason and act adaptively, rather than memorizing workflows.

### CCS Concepts

- Software and its engineering → Software maintenance tools;
- Computing methodologies → Machine learning approaches.


### Keywords

Programming Agents, Process-Centric Analysis, Agent Planning

ACM Reference Format:

Shuyang Liu, Saman Dehghan, Jatin Ganhotra, Martin Hirzel, and Reyhaneh Jabbarvand. 2026. From Plan to Action: How Well Do Agents Follow the

∗Both authors contributed equally to this work.

This work is licensed under a Creative Commons Attribution 4.0 International License. ASE ’26, Munich, Germany

© 2026 Copyright held by the owner/author(s). ACM ISBN 979-8-4007-2882-2/2026/10 https://doi.org/10.1145/3832783.3834400

Reyhaneh Jabbarvand✉

University of Illinois Urbana-Champaign Urbana, USA reyhaneh@illinois.edu

Plan?. In Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering (ASE ’26), October 12–16, 2026, Munich, Germany. ACM, New York, NY, USA,12pages.https://doi.org/10.1145/3832783.3834400

### 1 Introduction

Agents have emerged as a promising paradigm for automating software engineering tasks, from code synthesis and translation to end-to-end issue resolution [14, 36, 38]. Central to these systems is the use of structured instructions, a.k.a. a plan, which decomposes a high-level objective of a given task into an ordered sequence of steps that the agent can follow to accomplish the task successfully. In theory, a plan can help reduce cognitive load for reasoning about future steps in the local reason-act-observe loop [39]. As a result, planning is commonly used in agentic frameworks, usually encoded as step-by-step instructions in the system prompt [1, 4, 28, 34]. For example, a plan for fixing GitHub issues will instruct the agent to navigate to a potential bug location (based on the issue description), reproduce the bug to ensure correct localization, patch the bug, and validate the patch’s correctness.

In practice, the plan is only advisory and without enforcement. At each trajectory step, the model performs local reasoning over its current context, and its actions may or may not align with the plan. As the trajectory grows and the context fills with error messages, file contents, and prior reasoning, the plan’s influence may diminish, consistent with the known limitations of LLMs in attending to earlier context [20]. Therefore, whether agents truly follow the instructed plan remains an open question. Evaluating plan compliance can reveal whether the agent accomplishes a task through correct strategic reasoning or through overfitting to benchmark trajectories or data contamination.

This paper presents a large-scale evaluation of plan compliance in programming agents. The analysis leverages a novel plan compliance metric, measured across three dimensions: Plan Phase Compliance, Plan Order Compliance, and Plan Phase Fidelity (§2). We evaluate 21,120 SWE-agent trajectories, generated to resolve instances of two popular benchmarks (SWE-bench Verified [6] and SWE-bench Pro [8]), using four backbone LLMs (GPT-5 mini, DeepSeek-V3, DeepSeek-R1, and Devstral-small), under eight plan settings: the standard navigate-reproduce-patch-validation plan, no specified plan, and six variations of the standard plan, obtained by removing, adding, and re-ordering plan phases. Our study answers the following research questions:

- RQ1: Standard Plan Compliance (§4.1). To what extent do agents follow the instructed plan? What factors impact plan compliance and violations? Does plan compliance help agents resolve issues? Findings. Agents follow the standard plan, although with varying compliance rates. Some strictly follow the plan in the specified order, while others adaptively override the plan based on the trajectory, depending on the problem’s difficulty. Following the plan positively helps all agents resolve more GitHub issues. The fine-tuning paradigm, context window pressure, data contamination, overfitting, and optimization for short-term reward are the most prevalent factors impacting plan compliance.
- RQ2: Behavior of Agents in the Absence of Plan (§4.2). How do agents operate in the absence of a plan? To what extent does removing the plan impact overall performance? Findings. Without a plan, agents follow their internalized problem-solving strategy, which overlaps with the standard plan to a varying degree. The success rate, however, drops in the absence of the standard plan.
- RQ3–RQ5: Impact of Plan Variations (§5.1–5.3). Do agents heed removal, addition, and reordering of plan phases? To what extent does frequent reminding of the plan phases help compliance in the long-horizon task of program repair? Findings. Removing a standard plan phase, even if the agent usually ignores it under the standard plan setting, negatively impacts the agents’ performance, confirming the overall impact of a global plan on local reasoning steps. The negative impact of a bad plan is greater than no plan at all. Surprisingly, augmenting plans with task-relevant phases inspired by best practices also negatively affects agents’ performance when they are not aligned with the model’s internal strategy. Periodic plan reminders reduce plan violations and improve performance.
- RQ6: Generalization to Other Benchmarks (§6.1). How much can the observations and conclusions about plan compliance generalize to another benchmark, i.e., SWE-bench Pro [8]? Findings. The plan compliance rate of the agents across all settings on SWEbench Pro drops by 13%, on average, compared to SWE-bench Verified. The agents exhibit different phase flow patterns, e.g., they give up on generating reproduction tests early and validate patches using existing regression tests rather than generating tests. This is likely because SWE-bench Pro instances are more challenging and less contaminated, and the high-level standard plan is no longer effective at guiding the agents.
- RQ7: Impact of Nondeterminism (§6.2). To what extent is plan compliance of agents under different plan settings attributed to nondeterminism? Findings. Nondeterminism exists but does not impact our findings. We account for nondeterminism by repeating experiments and comparing persistent behaviors across plan settings. We are the first to (1) conduct a large-scale analysis of plan


compliance by agents, (2) introduce novel plan compliance metrics, (3) speculate the root causes of plan violations, and (4) study how plan compliance relates to task success. Our findings suggest that the effectiveness of the plan is tightly coupled to its alignment with the model’s internalized workflow and the task’s complexity. Therefore, future research should focus on fine-tuning paradigms that teach models to follow plans more effectively, rather than encoding task-specific plans into them.

### 2 Experimental Design

We aim to analyze whether and to what extent programming agents follow the specified, task-appropriate software engineering workflows. Given the popularity of programming agents for fixing realworld GitHub issues, this study will focus on program repair. The default practical workflow for this task involves localizing the bug, patching the code, and then validating whether the patch resolved the bug. Many existing scaffolds, e.g., SWE-agent/mini-SWE-agent, Trae agent, and OpenHands, explicitly instruct the agent to follow a similar plan in their system prompt1 [1, 28, 34]:

- Navigation (N). The agent searches for, opens, and reads files relevant to the issue description, building an understanding of the codebase and localizing the relevant components.
- Reproduction (R). The agent generates new tests to reproduce the bug, i.e., tests that fail on the buggy code.
- Patch (P). The agent edits the application code to fix the bug.
- Validation (V). The agent runs reproduction tests and generates new tests to validate patch correctness.


Assessing whether an agent follows the instructed plan for a task requires process-centric analysis of trajectories. We build our process-centric analysis on top of Graphectory and Langutory [21]. Graphectory represents linear raw trajectories as enriched graph structures, where nodes are the agent’s distinct actions and edges denote the chronological execution order. Langutory is an abstract representation of the trajectory in the form of language. That is, by mapping the agent’s actions across the sequence of 𝑛 trajectory steps 𝑇 = (𝑠1, . . .,𝑠𝑛) to an alphabet Φ = {𝑝1, . . .,𝑝𝑚} of 𝑚 letters2, Langutory L(𝑇, Φ) explains the agent’s problem-solving strategy as a sequence of letters.

When the alphabet denotes plan phases, constructing Langutory requires mapping each raw trajectory action to the phase it attempts to perform. We map file and directory inspection to Navigation, newly generated test creation and execution before any application-code edit to Reproduction, application-code edits to Patch, and newly generated test creation or execution after patching to Validation. Agent-generated tests are distinguished from existing repository tests: running existing tests is treated as regression testing, which is outside the default NRPV plan unless explicitly included in a plan variant. Actions that do not correspond to a plan phase, such as environment probing or dependency checks, are labeled as General. For dynamically executed Python code, such as heredocs, we parse the code to identify environment setup, file modifications, and test logic using signals such as assertions and test-specific imports (e.g., pytest, unittest, and mock). The mapping implementation is available in our artifact [22].

Given a plan phase alphabet Φ and expected phase sequence L★(Φ), we say a Langutory complies with the instructed plan if it includes all and only specified plan phases in the specified order. We propose a novel process-centric metric, plan compliance (𝑃𝐶), measured across three dimensions: plan phase compliance (𝑃𝑃𝐶), plan order compliance (𝑃𝑂𝐶), and plan phase fidelity (𝑃𝑃𝐹).

1The specified plan for some agents could be more verbose. Regardless, all existing agents follow similar high-level plans. 2𝑚 ≪ 𝑛 to show an overall strategy rather than detailed actions.

Navigation (N) Reproduction (R) Patch (P) Validation (V) General

||1|
|---|
<br><br>|view nanops.py<br><br>|
|---|
<br><br>| |
|---|
<br><br>create test_min_count.py<br><br>|2|
|---|
<br><br>|str_replace nanops.py str_1 str_2 observation: edit succeeds|
|---|
<br><br>|4|
|---|
<br><br>|8|
|---|
<br><br>|10|
|---|
<br><br>|submit|
|---|
<br><br>| |
|---|
<br><br>python test_min_count.py<br><br>|3|
|---|
<br><br>| |
|---|
<br><br>python test_min_count.py<br><br>|5|
|---|
<br><br>| |
|---|
<br><br>create test_min_count_comprehensive.py<br><br>|6|
|---|
<br><br>|python test_min_count_comprehensive.py<br><br>|
|---|
<br><br>|7|
|---|
<br><br>|str_replace nanops.py str_3 str_4 observation: edit succeeds|
|---|
<br><br>|python test_min_count_comprehensive.py<br><br>|
|---|
<br><br>|9|
|---|
<br><br>view nanops.py<br><br>create test_min_count.py<br><br>nanops.py &lt;old_str1, new_str2&gt;<br><br>submit<br><br>1<br><br>3<br><br>str_replace 5<br><br>✔<br><br>python<br><br>2<br><br>4<br><br>test_min_count.py<br><br>create test_min_count_comprehensive.py<br><br>python<br><br>6<br><br>nanops.py &lt;old_str3, new_str4&gt;<br><br>str_replace<br><br>✔<br><br>7 8<br><br>9<br><br>Langutory: NRRPVVVPV (NR2PV3PV)<br><br>test_min_count_comprehensive.py||5|
|---|
<br><br>| |
|---|
<br><br>view dates.py<br><br>|create reproduce_bug.py|
|---|
<br><br>|1|
|---|
<br><br>|str_replace dates.py str_3 str_4 observation: edit fails|
|---|
<br><br>10 create test_fix.py<br><br>| |
|---|
<br><br>python test_fix.py<br><br>|python reproduce_bug.py|
|---|
<br><br>|2|
|---|
<br><br>|str_replace reproduce_bug.py str_1 str_2 observation: edit succeeds|
|---|
<br><br>|3|
|---|
<br><br>| |
|---|
<br><br>python reproduce_bug.py<br><br>|4|
|---|
<br><br>|6|
|---|
<br><br>|view dates.py --view_range 607 638<br><br>|
|---|
<br><br>|7|
|---|
<br><br>|view dates.py --view_range 594 602<br><br>|
|---|
<br><br>|8|
|---|
<br><br>|str_replace dates.py str_5 str_6 observation: edit succeeds|
|---|
<br><br>|9|
|---|
<br><br>|11|
|---|
<br><br>|12|
|---|
<br><br>|submit|
|---|
<br><br>create<br><br>1<br><br>python reproduce_bug.py<br><br>reproduce_bug.py &lt;old_str1, new_str2&gt;<br><br>str_replace<br><br>✔<br><br>2<br><br>3 view dates.py<br><br>4<br><br>dates.py<br><br>view [607, 638]<br><br>dates.py<br><br>view [594, 602]<br><br>dates.py<br><br>str_replace &lt;old_str3,new_str4 ❌&gt;<br><br>dates.py &lt;old_str5, new_str6&gt;<br><br>str_replace ✔<br><br>5<br><br>create test_ﬁx.py<br><br>python test_ﬁx.py<br><br>6<br><br>7<br><br>8<br><br>9<br><br>10<br><br>11<br><br><br>submit<br><br>Langutory: RRRRNNNPPVV(R4N3P2V2)<br><br>reproduce_bug.py||1|
|---|
<br><br>|view /testbed<br><br>|
|---|
<br><br>|2|
|---|
<br><br>|view /testbed/django/contrib/auth<br><br>|
|---|
<br><br>|3|
|---|
<br><br>|view /testbed/django/contrib/auth/token.py<br><br>|
|---|
<br><br>|str_replace token.py str_1 str_2 observation: Edit succeeds|
|---|
<br><br>4<br><br>|submit|
|---|
<br><br>|5|
|---|
<br><br>view /testbed<br><br>/testbed/django/ view contrib/auth<br><br>/testbed/django/co view ntrib/auth/token.py<br><br>1<br><br>2<br><br><br>token.py<br><br>str_replace &lt;old_str1,new_str2 ✔&gt;<br><br>3<br><br>submit<br><br>4<br><br>Langutory: NNNP(N3P)|
|---|---|---|


PPC=0.5, POC=0.5, PPF=1 PC=0.63

PPC=1, POC=1, PPF=1 PC=1

PPC=1, POC=0.75, PPF=1 PC=0.91

(a) (DSK-R1 · xarray-4356 · Resolved)

(b) (DSK-R1 · matplotlib-21568 · Unresolved) (c) (DSK-V3 · django-13551 · Unresolved)

Figure 1: Illustrative examples of agent trajectories and their corresponding Graphectory and Langutory representations. Plan: L★(Φ) = N R P V .

To illustrate the concept, Figure 1 shows three trajectories generated by SWE-agent along with their corresponding Graphectory and Langutory. Figure 1a shows a compliant and successful execution. SWE-agent DSK-R1 starts by navigating to the buggy file nanops.py (step 1), creates and executes a reproducing test (steps 2–3), edits the buggy file (step 4), validates the patch by creating and executing a more comprehensive test (steps 5–7), edits the file again to handle corner cases (step 8), and re-executes the test (step 9) before submitting the patch. This yields a Langutory of 𝑁𝑅2𝑃𝑉3𝑃𝑉, which is compliant with the instructed plan L★(Φ) = N R P V . The execution in Figure 1b covers all plan phases in its trajectory, but violates the intended order, with excessive reproduction (steps 1–4) preceding navigation (steps 5–7) and leading to an unresolved patch. The execution in Figure 1c skips key phases, transitioning directly from navigation (steps 1–3) to patching (step 4) before submission, violating the plan. The consequence of plan violation is a low-quality patch that does not resolve the issue.

order of first occurrences. In Figure 1b, the first occurrence indices of N R P V are [5, 1, 8, 10]. The longest increasing subsequence is [1, 8, 10] with length 3, yielding 𝑃𝑂𝐶 = 34. Failing to follow the expected order can cause inefficient trajectories or task failure. In Figure 1b, the agent begins with reproduction before properly navigating the codebase, leading to repeated modifications to the reproduction script (steps 3–4), and a failed edit at step 8.

Agents operate through iterative reasoning–action–observation cycles [39], in which decisions are locally conditioned on the current context rather than the initial instructed plan. Moreover, training strategies can overfit the LLMs to certain actions outside of the instructed plans for specific tasks. Hence, some actions may not map to plan phases in the Langutory. For example, an agent may decide to open a pull request after patch validation, which is not part of the instructed plan in existing programming agents [1, 28, 34]. In such a case, Langutory may contain unknown letters that are considered gibberish with respect to the specified plan phases. Including additional actions beyond those in the recommended plan is not necessarily negative, but can be distracting. Therefore, 𝑃𝑃𝐹 penalizes the appearance of phases outside the plan alphabet:

We will explain our novel process-centric plan compliance metrics using this illustrative example. 𝑃𝑃𝐶 measures whether Langutory L(𝑇, Φ) covers the phases specified in the plan:

𝑃𝑃𝐶 = |Φ ∩ {L(𝑇, Φ)𝑡 | 1 ≤ 𝑡 ≤ 𝑛}|

𝑃𝑃𝐹 = |Φ|

(3)

(1)

|Φ ∪ {L(𝑇, Φ)𝑡 | 1 ≤ 𝑡 ≤ 𝑛}|

|Φ|

𝑃𝑃𝐹 ∈ (0, 1], and 𝑃𝑃𝐹 = 1 if every phase appearing in the Langutory belongs to Φ. The overall compliance score is the geometric mean of its three component metrics:

Here, L(𝑇, Φ)𝑡 denotes the phase label assigned to the t-th action in trajectory 𝑇 under the phase vocabulary Φ. 𝑃𝑃𝐶 = 1 if every phase in Φ appears at least once in the Langutory. In practice, an agent may skip some plan phases, e.g., directly jumping into patching after navigation without reproduction test generation. Therefore, 𝑃𝑃𝐶 ∈ [0, 1]. In Figure 1c, the agent skips reproduction and validation, resulting in 𝑃𝑃𝐶 = 0.5. The executions in Figure 1a and 1b cover all plan phases in Φ and achieve 𝑃𝑃𝐶 = 1.

𝑃𝐶 = (𝑃𝑃𝐶 . 𝑃𝑂𝐶 . 𝑃𝑃𝐹)1/3 (4) 𝑃𝐶 ∈ [0, 1], where score 𝑃𝐶 = 1 indicates perfect plan compliance. Geometric mean aggregates sub-metrics multiplicatively, ensuring equal weighting and preventing compensation across dimensions. Low compliance in any dimension proportionally reduces the overall score. Lower 𝑃𝐶 scores reflect deviations in missing phases, spurious phases, or violations of the logical phase ordering.

Not only is covering all phases important, but so is following the proper order through trajectory execution. 𝑃𝑂𝐶 measures the fraction of phases in L★(Φ) that appear in the correct relative order:

### 3 Empirical Setup

LIS(𝑖1, . . .,𝑖𝑚) 𝑚

(2)

𝑃𝑂𝐶 =

Models and Scaffold. To capture a multi-dimensional analysis of plan compliance, we evaluate the SWE-agent scaffold [38] across four diverse LLMs: GPT-5 mini [26] (closed-source frontier reasoning model), DeepSeek-R1 [7] (open-source reasoning

where LIS(·) denotes the length of the longest increasing subsequence and 𝑖𝑘 denotes the first occurrence index of phase 𝑝𝑘 in L(𝑇, Φ) (if present). Phase revisits are allowed; 𝑃𝑂𝐶 evaluates the

#### Table 1: Summary of studied plan settings, their corresponding formulation, and type of plan variation.

Plan Setting Plan Formulation Plan Variation Plan Description Standard (Default) Plan ⟨𝑁, 𝑅, 𝑃, 𝑉 ⟩ Baseline Standard Navigation-Reproduction-Patch-Validation plan No Plan — Reduction Plan removed entirely from the system prompt Default Plan - Reproduction ⟨𝑁, ¬R, 𝑃, 𝑉 ⟩ Reduction Reproduction phase removed Default Plan - Validation ⟨𝑁, 𝑅, 𝑃, ¬V⟩ Reduction Validation (after patching) phase removed Default Plan + Regression Test Execution ⟨𝑅𝐺, 𝑁, 𝑅 𝑃, 𝑉, 𝑉𝐺 ⟩ Augmentation Regression test execution phases added Default Plan + Summary of Changes ⟨𝑁, 𝑅, 𝑃, 𝑉, 𝑆⟩ Augmentation Summarizing changes before submission added Reordered Default Plan ⟨𝑁, 𝑃, 𝑅, 𝑉 ⟩ Reordering Patching moved before Reproduction Periodic Plan Reminder ⟨𝑁, 𝑅, 𝑃, 𝑉 ⟩ Repeating Default plan re-injected every five trajectory steps

model), DeepSeek-V3 [19] (open-source general-purpose model), and Devstral-small [24B] [25] (distilled model specialized in coding). We use the default settings of the models and agent (see our artifact for details [22]). SWE-agent provides a standardized execution environment, supports multiple LLMs, and embeds a default plan in its system prompt. These properties make it a natural testbed for studying the role of planning in programming agents.

the four studied models, we randomly sampled 20 trajectories and selected the first occurrence of each default-plan phase, yielding a total of 320 actions. The annotators labeled these actions without access to the automatically assigned labels. Agreement among the two manual annotations and the automated labels achieved a Fleiss’ 𝜅 [11] of 0.99, indicating near-perfect agreement and supporting the reliability of the automated mapping.

Plan Settings. We evaluate performance of agents on a given dataset problem under eight plan settings: (1) default plan (RQ1), (2) no-plan, i.e., removing the entire plan from the system prompt (RQ2), (3) removing the reproduction phase (RQ3), (4) removing the validation phase (RQ3), (5) adding a regression test execution phase before navigation, 𝑅𝐺, and after validation, 𝑉𝐺 (RQ4),

### 4 Standard Plan Compliance and Violation

This section first investigates to what extent SWE-agent with different choices of LLMs follows the standard program repair workflow, i.e., Navigation , Reproduction , Patch , and Validation (§4.1). As an extreme alternative, we remove the entire plan and evaluate how the trajectories change (§4.2).

- (6) adding a change summarization phase𝑆 before submission (RQ4),
- (7) step reordering, i.e., reproduction test generation after patching (RQ4), and (8) plan reminder, i.e., periodically re-injecting the default plan into the agent’s prompt (RQ5). Table 1 lists plan settings and their corresponding plan-compliant phase sequence, which our pipeline checks trajectories against. We will explain the rationale for these plan mutations in the corresponding RQs.


### 4.1 RQ1. Standard (Default) Plan Setting

The standard program repair plan that has been used for years by software developers is localizing the bug (navigating through files, classes, methods, and lines to pinpoint the bug location) and attempting to reproduce it, patch it, and validate the patch through test execution. Existing scaffolds instruct agents to follow a similar plan with the given order in their default system prompt (Φ = {𝑁,𝑅,𝑃,𝑉 } and L★(Φ) = N R P V ). Figure 2a presents the average 𝑃𝑃𝐶, 𝑃𝑂𝐶, 𝑃𝑃𝐹, and 𝑃𝐶 values (Equations 1–4) calculated for 2,000 trajectories under this plan. Figures 2b–2d show breakdowns by problem difficulty levels (Easy, Medium, and Hard). Beyond quantitative metrics, Figure 3 shows the plan phase flow of the agents for all the trajectories.

Dataset. We evaluate the mentioned LLMs and plan settings for resolving real-world GitHub issues from SWE-bench Verified [6, 16] and SWE-bench Pro [8]. Specifically, our primary evaluation (RQ1– RQ6) uses 497 instances3 of SWE-bench Verified, covering three difficulty levels (Easy, Medium, and Hard), providing a realistic setting for agent behavior. To study the generalizability of findings, we repeat RQ1–RQ5 for Python instances of SWE-bench Pro.

Analysis and Metrics. Along with the plan compliance metrics (Equations 1–4), we report the success rate [16] and Graphectory metrics (the number of nodes 𝑁𝐶, temporal edges 𝑇𝐸𝐶, and loops 𝐿𝐶 in the Graphectory) [21]. Success rate determines the overall impact of plans on the agent’s ability to resolve the issue, and Graphectory metrics provide insights into how plans affect the overall trajectory toward resolution. In addition to metrics, we leverage process-centric Phase Flow Analysis by Liu et al. [21] to provide an in-depth analysis of plan-phase changes in trajectories exhibiting plan violations. Phase Flow Analysis can reveal consistent trends in agent trajectories across different problems. The outcome of this analysis is a Sankey diagram illustrating the evolution of trajectories from one plan phase to the next.

- Finding 1. Standard plan compliance varies across models. Devstral-small consistently follows the plan phases in the given order, demonstrated by high 𝑃𝑃𝐶 and 𝑃𝑂𝐶 values. However, it exhibits out-of-plan phases to a notable degree in its trajectories (gray flows in Figure 3), with low overall 𝑃𝐶. GPT-5 mini, on the other hand, may adapt its strategy depending on the difficulty of the problem. Its trajectories show out-of-plan phases (lower 𝑃𝑃𝐹), and it usually skips Reproduction (lower𝑃𝑃𝐶 and𝑃𝑂𝐶). DeepSeek-V3 exhibits a near-perfect 𝑃𝑃𝐹 = 0.99 but substantially lower 𝑃𝑃𝐶 and 𝑃𝑂𝐶, i.e., restricts itself to plan phases but frequently omits some or executes them out of order. DeepSeek-R1 consistently demonstrates lower plan compliance than others, both in following the instructed plan phases and in doing so in the correct order.

- Finding 2. Standard plan compliance is overall higher on resolved instances. Intuitively, following the instructed standard plan that reflects decades of best practices should lead to successful bug repair. The Mann–Whitney U test [23] confirms the significance of this observation for Devstral-small and DeepSeek-R1, where


Mapping Validation. To assess the reliability of our automated action-to-phase mapping, two authors independently annotated a stratified sample from the Default Plan trajectories. For each of

3We exclude the 3 Very Hard instances, none of which is resolved by any studied model under any plan setting and thus provides limited evidence for comparative analysis.

Success Rate (%)

|56.3|
|---|
|38.4|
|39.4|
|64.8|


Resolved Unresolved Resolved Unresolved Resolved Unresolved Resolved Unresolved

GPT5-mini

DeepSeek-V3

DeepSeek-R1

Devstral-small

(a) All (b) Easy (c) Medium (d) Hard

#### Figure 2: Standard plan compliance metrics and success rate for studied trajectories across all models.

| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


All

| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


Easy

| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


Medium

Hard

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

- Figure 3: Phase flow analysis under Standard plan (L★(Φ) = N R P V ). Flow thickness notes the proportion of trajectories going from one phase to another. The black bar indicates trajectory termination, and gray flows represent out-of-plan phases.


resolved instances consistently exhibit higher plan compliance (𝑝 = 1𝑒 − 5 and 𝑝 = 0.032, respectively).

The correlation is positive for DeepSeek-V3, but with less statistical significance (𝑝 = 0.60). The exception is GPT-5 mini, where unresolved trajectories are usually more compliant with the plan, demonstrating negative correlation but with low statistical significance (𝑝 = 0.285). Phase flow analysis (Figure 3) demystifies this observation: GPT-5 mini adapts its strategy based on problem difficulty. For easier problems, where the issue description also likely contains all the information to localize the bug, it often skips

Reproduction and transitions from navigation to patch. For harder problems, it follows the instructed plan more closely, with thicker

Navigation -to- Reproduction flows in earlier phase changes.

- Finding 3. Necessity for process-centric plan compliance metrics. Graphectory metrics &lt;node count, edge count, loop count&gt; are in general higher for Devstral-small (&lt;86,179,64&gt;) and GPT-5 mini (&lt;38,49,18&gt;) compared to DeepSeek-V3 (&lt;15,27,4&gt;) and DeepSeek-R1 (&lt;14,21,4&gt;). Pearson correlation [29] shows a very weak positive correlation (0 &lt; 𝑟 ≤ 0.2) between plan compliance 𝑃𝐶 and Graphectory metrics. This confirms the need for a new process-centric metric to specifically target plan compliance, as an orthogonal factor to trajectory complexity.
- Finding 4. The standard plan, in its current form, is incomplete. We observe that GPT-5 mini and Devstral-small, in addition


to creating and executing new tests as instructed by the plan, frequently run existing tests in the repository (lower 𝑃𝑃𝐹 compared to other models). The practice is, in fact, useful for better reproduction test generation and patch validation [5]. This finding motivates augmenting existing plans with additional, relevant phases, and assessing the impact of this plan on trajectories (§5.2).

4.1.1 Contributing Factors to Plan Compliance/Violation. Finetuning paradigm. Depending on the LLM, agents may skip specific plan phases, perform them in a different order, or exhibit out-of-plan actions. Except for Devstral-small, SWE-agent with other LLMs tends to skip Reproduction (less presence in Figure 3). SWE-agent with DeepSeek models often performs Reproduction

before Navigation . RQ2 (§4.2) investigates this under a controlled setting. This also motivates modifying the plan by removing some steps (§5.1) to further investigate plan compliance across models.

Context window pressure. As trajectories grow, the initial plan must compete with an increasingly long history of thoughts, tool calls, file contents, and error messages, which can make the plan less salient later in execution. Deviation is further encouraged by the agent’s locally-conditioned decision process, in which each action is chosen primarily based on the current context and recent tool feedback rather than explicit adherence to the original global workflow. We further investigate this speculation in RQ5 by frequent plan reminders (§5.3.2).

Data contamination and overfitting. Backbone LLMs may overfit to the workflow defined by the standard plan. There is also a risk of data contamination when a successful trajectory for solving individual problems in SWE-bench Verified is used to fine-tune them [27, 32]. Therefore, plan compliance may not be rooted in their ability to follow plan instructions [30] or the plan positively impacting their reasoning to accomplish the task [18]. We will evaluate the impact of this factor by repeating the experiments on a less contaminated SWE-bench Pro dataset (§6.1).

### 4.2 RQ2. No Plan Setting

The previous research question shows a notable variance in compliance with the Standard plan across agents. Given that the scaffold is identical in all agents, two important factors influencing the observations are (1) the ability of specific LLMs to follow the instructed plan, or (2) a conflict between following plan-prescribed phases and training-prescribed workflows. We investigate the magnitude of the former in §5. For the latter, we repeated the experiments under a No Plan setting to observe how agents perform without any specific plan. We completely remove the default plan from the system prompt of SWE-agent. Thereby, the agent only receives a high-level guideline to fix the issue: given the issue description, make changes to satisfy the issue description requirements4.

Figure 5 compares issue resolution on SWE-bench Verified with and without the Standard Plan. The left bars show the total number of instances resolved under each setting, while the top bars show the number of instances in each intersection. The dot matrix indicates the corresponding resolution set: black dots mark settings under which the instances are resolved, and gray dots mark settings under which they are unresolved. Thus, from left to right, the top bars represent instances unresolved under both settings, resolved only under the Standard Plan, resolved only under No Plan, and resolved under both settings. Although the agent receives no plan instruction under this setting, we further investigate if it exhibits any trace of Standard plan in its trajectory. The rationale here is that the backbone LLM of the agent may already have seen instructions related to this task during training/fine-tuning. Figure 4 shows phase flow analysis of trajectories under the No Plan setting.

- Finding 5. Even when not explicitly instructed, agents follow the Standard plan to a notable degree. The phase flow analysis in Figure 4 shows that Devstral-small starts with Navigation , and most trajectories still follow the Standard workflow N R P V , with some phases out of the Standard plan in between. Similarly, GPT-5 mini trajectories also follow a subset of Standard plan, often without Reproduction . In contrast, DeepSeek-V3 and DeepSeekR1 largely reduce their trajectories to N P patterns, skipping

Reproduction or Validation . This suggests that different models internalize problem-solving processes differently, depending on their training. In the absence of global plans, the encoded strategy takes over the reasoning to solve the problem.

- Finding 6. The success rate drops in the absence of the standard plan, although to different degrees across models and


4The system prompt for this experiment is available on the artifact website under artifacts/plan-settings/no_plan/default.yaml

difficulty levels. Figure 5 shows that removing the plan consistently reduces performance across all models. The majority of the instances that SWE-agent resolved only under the Standard plan setting are of Medium difficulty. Devstral-small and GPT-5 mini, which exhibit problem-solving strategies similar to the Standard plan, show only minor drops when the plan is removed. In contrast, DeepSeek models, particularly DeepSeek-R1, experience a substantial performance drop, despite showing lower compliance when the plan is present. This indicates that the plan, even if not properly followed, can positively impact the local reasoning of the agents, guiding them toward their goal. Without it, reasoning becomes less focused, often resulting in premature convergence: these models demonstrate smaller Graphectory metric values under the No Plan setting, compared to the Standard plan.

Finding 7. Agents can fix previously unresolved issues under no-plan setting. DeepSeek-V3, DeepSeek-R1, Devstral-small, and GPT-5 mini each resolve additional instances that are not solved under the default plan: 23, 11, 28, and 34, respectively. As we will show later (§6.2), this is largely affected by the inherent nondeterminism of LLM-based agents, with 4, 7, 16, and 4 instances deterministically only resolved under the no-plan setting. Manual inspection of these instances reveals a consistent trend across all models: The Standard plan instructs the model to reproduce the bug before the patch. However, reproduction test generation is non-trivial [2, 3]. In the instances studied, the models generated incorrect reproduction tests, leading to repeated patch-test failure cycles without success. Under the No Plan setting, the same model skipped the reproduction phase and generated the correct patch. This is alarming but interesting: the solution under No Plan can be due to data contamination [27].

### 5 Plan Variations

RQ2 shows that agents, even if not explicitly instructed to follow the standard plan, still incorporate it in their problem-solving strategy. As discussed, this is likely due to the training objectives of backbone LLMs. For a more controlled plan compliance analysis, we create variations of the Standard plan with small changes (removing one plan phase in §5.1 or adding one phase outside of the Standard plan in §5.2). We then investigate compliance with the mutated plan and the impact of isolated plan changes on success rate.

### 5.1 RQ3. Reduced Plan Settings

We study two reduced plan variations by removing either the

Reproduction or the Validation phase. Removing Navigation and Patching is unlikely to reveal notable observations, as these two phases are essential and consistently appear in agent trajectories from observations in the No Plan setting.

5.1.1 RQ3.1. No Reproduction Setting. Figures 6–8 illustrate the results under L★(Φ) = N P V . Devstral-small and GPT-5 mini achieve lower scores on 𝑃𝑃𝐹, since Reproduction is encoded in their internal problem-solving strategy. They also achieve nearperfect compliance for 𝑃𝑃𝐶 and 𝑃𝑂𝐶, i.e., follow all other plan phases in proper order. Phase flow analysis (Figure 6) shows an interesting observation about the impact of the plan on their trajectory: in the absence of plan, these two models include Reproduction

more consistently in their trajectories compared to when the plan excludes only that phase (compare Figure 6 with Figure 4). This,

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

#### Figure 4: Phase flow analysis under No Plan setting. Agents still exhibit traces of Standard plan phases (Φ = { N , R , P , V }).

- Finding 8. The negative impact of a bad, incomplete plan is greater on trajectories than the impact of no plan at all. Overall, removing a specific plan phase can strongly affect models that (1) do not have it in their internal workflow to compensate or

(2) are trained to incorporate the plan in their reasoning, as in its absence, their reasoning is incomplete.

- Finding 9. Agents can fix previously unresolved issues under reduced plan settings. Similar to Finding 7, the primary reason for exclusive resolution under the No Reproduction setting is the agents’ inability to generate a good reproduction test when instructed by the Standard plan. In contrast, under the No Validation setting, specifically when we eliminate the impact of nondeterminism (§6.2), agents can rarely resolve previously unsolved issues: GPT-5 mini (7), Devstral-small (19), DeepSeek-V3 (5), and DeepSeek-R1 (1). Analysis of those instances shows that agents still incorporated the validation phase, suggesting remaining impact of nondeterminism.


#### Figure 5: Impact of No Plan setting on the success rate.

consequently, impacts the ability of these models to accomplish the task. As shown in Figure 7a, their success rate decreases notably.

In contrast, DeepSeek models achieve nearly-perfect 𝑃𝑃𝐹 values, indicating that their trajectories do not observe Reproduction . However, they suffer the most from lower 𝑃𝑃𝐶 and 𝑃𝑂𝐶, confirmed by phase flow analysis. Similarly, these two models suffer from an incomplete plan, reflected in the drop in success rate. DeepSeekR1’s performance drop is more substantial. A deeper analysis of its trajectories reveals that, in many cases (349 instances), the model produces malformed tool calls, emitting function calls as plain text rather than in the expected format. This leads to repeated execution errors and eventual termination5. The observation suggests that removing Reproduction destabilizes DeepSeek-R1 interaction with the scaffold itself, beyond its effect on problem-solving.

### 5.2 RQ4. Augmented Plan Settings

We investigate compliance with plans that include new phases to further demonstrate overfitting to known plans. Arbitrary, taskirrelevant phases may bias the findings; it will be unclear whether an agent struggles with plan compliance or reacts negatively to incoherent instructions. To account for this threat, we only introduce phases relevant to the issue repair task, namely, (1) executing regression tests at the beginning and end (§5.2.1) and (2) summarizing changes in a PR-style format before submission (§5.2.2).

- 5.1.2 RQ3.2. No Validation Setting. Figures 6, 7b, and 9 illustrate the results under L★(Φ) = N R P . GPT-5 mini suffers greatly


5.2.1 RQ4.1. Plan with Regression Test Execution. Figures 10–12 summarize the results. Devstral-small and GPT-5 mini already perform regression testing, even when not explicitly instructed to do so (Finding 4). The small drop in success rate is likely due to nondeterminism (§6.2). Devstral-small has a high 𝑃𝑃𝐶, including all phases, while GPT-5 mini adaptively skips or reorders some phases as discussed (lower 𝑃𝑃𝐶). Concerning regression testing, Devstral-small and GPT-5 mini show a notable difference: as shown through phase flow analysis (Figure 10), Devstral-small performs regression testing after Navigation and after Validation , while GPT-5 mini consistently runs regression tests as the first step and after Validation using new tests.

without Validation , indicating a strong dependence on this phase, as it enables the model to identify incorrect patches and iteratively refine them, rather than prematurely submitting them.

In contrast, DeepSeek-V3 shows only slight performance degradation and high 𝑃𝑃𝐹, consistent with its tendency to skip

Validation in the No Plan setting. This further reinforces the importance of either alignment of the model’s internalized strategy with the instructed plan or enabling true reasoning and adaptive planning in models. Devstral-small is less affected than in the No Reproduction setting, suggesting that early-stage grounding through reproduction (e.g., for better bug localization) is more critical to its performance, while validation plays a less central role in shaping its trajectory. We believe this is yet another signal about the data contamination in this model, as it can generate correct patches without validation. DeepSeek-R1 again exhibits the lowest success rate and significantly lower 𝑃𝑃𝐶 and 𝑃𝑂𝐶, with the majority of trajectories terminating early with repeated tool-calling failures (§5.1.1).

DeepSeek-V3 experiences a higher performance drop, accompanied by low 𝑃𝑃𝐶, suggesting difficulty in incorporating the regression testing phases. Running existing tests early in the trajectory and their lengthy feedback likely overrides the impact of other plan phases (lower 𝑃𝑂𝐶), shifting focus toward test environment setup and irrelevant execution results rather than effective bug localization and patching. DeepSeek-R1 continues to exhibit severe performance issues in this setting. The persistent tool-calling errors result in a very low success rate, preventing any conclusion

5Exit message: “Exit due to repeated format/blocklist/bash syntax errors”

No ReproduceNo Validation

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

#### Figure 6: Phase flow analysis under No Reproduction (L★(Φ) = N P V ) and No Validation plan setting (L★(Φ) = N R P ). Trajectories still show traces of removed phases from the Standard plan.

(a) (b)

Figure 7: Impact of No Reproduction plan (a) and No Validation plan (b) on the success rate.

phase typically occurs at the end of the trajectory and does not impact intermediate reasoning. DeepSeek-R1, however, exhibits a substantial performance drop, with pervasive tool-calling failures observed in 413 instances. This suggests that even orthogonal additions to the plan can destabilize this model’s reasoning.

Finding 10. Plan augmentation highlights plan overfitting, and is effective only when aligned with a model’s internal strategy. Introducing additional phases provides limited benefit and can degrade performance if the model does not naturally employ those steps. Adding early phases can introduce unnecessary overhead or distract the model if phases are not well internalized.

- Figure 8: No Reproduction plan compliance metrics.

- Figure 9: No Validation plan compliance metrics.


### 5.3 RQ5. Reordered and Reminded Plan Settings

5.3.1 RQ5.1. Reordered Plan Setting. Previous settings challenge agents to achieve high plan phase compliance (𝑃𝑃𝐶) and Plan Phase Fidelity (𝑃𝑃𝐹). Challenging plan order compliance (𝑃𝑂𝐶) involves reordering phases and investigating plan compliance. As in augmented plan settings, to avoid bias or noise, we reorder the phases so that the new plan remains relevant to the task. Specifically, we instruct the agent to patch the bug immediately after navigation and to postpone generating the reproduction test after patching, primarily for patch validation rather than bug localization.

The reordered plan (L★(Φ) = N P R V ) slightly impacts agents’ behavior. Phase flow analysis (Figure 14) shows that DeepSeek-V3 often proceeds directly from navigation to patching, consistent with the modified plan. As shown in Figure 15a, this slightly improves its success rate (from 191 resolved under the default plan to 196). In contrast, Devstral-small performs reproduction before patching despite the reordered instruction, resulting in a lower 𝑃𝑂𝐶 as reflected in Figure 16. For models that rely on reproduction, executing it before patching remains preferred, as it helps confirm the bug and improve the overall process. The reordering

regarding plan compliance. We speculate that this behavior is due to optimization for short-term reward [12], which is a known issue in DeepSeek-R1 and specifically in reinforcement learning [10, 31].

5.2.2 RQ4.2. Plan with Change Summary. Adding a summary phase, which is independent of the core repair process, yields minimal behavioral changes across most models. The overall plan compliance (𝑃𝐶) for Devstral-small, GPT-5 mini, and DeepSeek-V3 remains nearly unchanged from the Standard setting (Figure 13). The success rates are also largely unaffected (Figure 11b), as the summary

| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |
| | |
| | |


| | |
|---|---|
| | |
| | |
| | |


Regression

Summary

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

#### Figure 10: Phase flow analysis under Regression Testing (L★(Φ) = 𝑅𝐺 N R P V 𝑉𝐺 ) and Summary plan setting (L★(Φ) = N R P V S ).

(a) (b)

Figure 11: Impact of Regression Testing (a) and Summary plan (b) on the success rate.

Finding 12. Delaying weakly internalized phases can reduce interference, but it does not consistently improve performance. For models that do not naturally rely on a phase (e.g.,

Reproduction in DeepSeek-V3), postponing it can reduce interference with early steps. However, this benefit is not consistent: after accounting for nondeterminism (§6.2), the reordered plan yields only a negligible change in success rate (38.3% to 38%).

- 5.3.2 RQ5.2. Reminded Plan Setting. To mitigate the context window pressure (§4.1.1), where the initial plan becomes less influential as the trajectory length increases, we introduce a Reminded plan setting. In this variant, the Standard plan is periodically re-inserted into the context every five steps. Figure 17 shows that periodic plan reminders improve plan compliance for DeepSeek-V3 and maintain similar 𝑃𝐶 for the other models. This leads to consistent improvements in success rates across models, as shown in Figure 15b. The reminders prevent drifting into irrelevant sub-goals (e.g., exploring unrelated directories) and return focus to the repair task. 6 Factors Beyond the Scaffold and LLM
- 6.1 RQ6. Generalization to Other Benchmarks


Figure 12: Regression Testing plan compliance metrics.

In previous RQs, we observed that plan variants affect model performance and plan compliance differently, largely due to their internalized problem-solving strategies. One potential explanation is data contamination, where models may overfit to the SWE-bench Verified dataset. To assess generalization of the findings, we repeated RQ1–RQ5 on SWE-bench Pro [8], which aims to minimize overlap with LLM training corpora through licensing constraints. To minimize moving factors, we focused on 266 Python instances of SWE-bench Pro. This benchmark is more challenging and less contaminated, and the studied models achieve near-zero success

Figure 13: Summary plan compliance metrics.

leads to moderately reduced success rates for Devstral-small, which consistently relies on reproduction, and GPT-5 mini, which adaptively incorporates reproduction as problem difficulty increases.

Finding 11. Agents prioritize effective workflows over prescribed phase ordering. Agents do not rigidly follow suboptimal ordering constraints; instead, they override them in favor of execution orders that better support their problem-solving process.

ReorderedReminded

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

#### Figure 14: Phase flow analysis under Reordered (L★(Φ) = N P R V ) and Reminded setting (L★(Φ) = N R P V ).

(a) (b)

Figure 15: Impact of Reordered plan (a) and Reminded plan (b) on the success rate.

Patching , without reaching Validation . Similar to SWE-bench Verified, the majority of the agents still skip Reproduction , achieving relatively high 𝑃𝐶 scores on the No Reproduction setting.

### 6.2 RQ7. Impact of Nondeterminism

To mitigate any bias due to agents’ inherent nondeterminism, we repeated the experiments under the Standard plan three times. Pairwise McNemar tests [24] show statistically significant differences across runs, confirming the non-determinism. We then identify instances that are consistently resolved or unresolved across Standard plan runs and evaluate the remaining plan variants on this reproducible subset (GPT-5 mini: 401, Devstral-small: 308, DeepSeek-V3: 323, and DeepSeek-R1: 287). Figure 19a reports the plan compliance 𝑃𝐶, remaining nearly identical to that observed on the full benchmark. The results are consistent with our earlier findings: plan reduction, augmentation, and reordering affect models differently depending on their underlying problem-solving strategies, as reflected in the No Plan setting. Periodic plan reminders consistently improve performance by maintaining focus on the core task.

- Figure 16: Reordered plan compliance metrics.

- Figure 17: Reminded plan compliance metrics.


### 7 Related Work

rates in many instances. To obtain more meaningful comparisons, we selected instances that at least one of the LLMs could resolve under the Standard plan settings, leaving us with 31 instances.

Planning has become a central mechanism for improving the reliability of agents, especially for long-horizon and tool-using tasks. Several studies focus on constructing and refining plans in single- and multi-agent systems. Agent-Oriented Planning [17] and PMC [40] decompose complex tasks into structured subtasks and coordinate multiple agents to satisfy constraints, while EAGLET [33] and Plan-and-Act [9] separate planning and execution into distinct LLMs to improve long-horizon reasoning. ReWoo took an extreme stance, planning all actions up-front [37]. Liu et al. [21] introduce process-centric metrics, but as we saw in Finding 3 (§4.1), those alone are insufficient to understand plan compliance.

Figure 19b shows the plan compliance (𝑃𝐶) values of studied agents under all plan settings. We observe that plan compliance drops by 13% on average across all agents. The phase flow analysis in Figure 18 demonstrates a different trend under the Standard plan setting in SWE-bench Pro compared to SWE-bench Verified (Figure 3), specifically for DeepSeek-V3 and DeepSeek-R1. This is likely because SWE-bench Pro instances are more challenging and most of the problem-solving effort goes into repetitive Navigation and

Devstral-small GPT5-mini DeepSeek-V3 DeepSeek-R1

Figure 18: Phase flow analysis under Standard plan for SWE-bench Pro (L★(Φ) = N R P V ).

- 9 Discussion

Generalization to Other Domains. Although this work focuses on programming agents, our process-centric analysis is not limited to software engineering. Applying it to another domain requires defining a domain-specific plan-phase vocabulary and mapping agent actions to these phases. The computation of plan compliance metrics remains unchanged. For example, a scientific discovery agent following an Observation-Research-Hypothesis-ExperimentAnalysis workflow [35] can be represented using the corresponding phase alphabet, with actions mapped through predefined rules or an LLM-based classifier. Controlled plan variations, such as phase removal and periodic reminders, can similarly be adapted to other domains, whereas plan augmentation requires domain knowledge to introduce task-relevant phases. Thus, our framework provides a general methodology for studying how instructed plans shape agent behavior and task success across domains.

Implications for Agent Design and Training. Our findings suggest that plan compliance should serve as a process-level signal rather than a maximized objective. Strict compliance is neither necessary nor always beneficial: agents may productively adapt an instructed plan to the task, whereas missing phases, harmful reordering, or loss of plan awareness can hinder successful execution. During execution, compliance signals can support online monitoring and trigger targeted reminders or adaptive plan refinement when harmful deviations emerge. During post-training, they can provide process-level supervision for teaching agents to follow task-appropriate plans while retaining the flexibility to adapt, rather than memorizing fixed workflows or optimizing solely for task success. This analysis can also support long-term monitoring as models, scaffolds, and task distributions evolve.

- 10 Conclusion

This paper analyzes 21,120 trajectories to assess plan compliance in programming agents. It introduces novel plan compliance metrics and runs agents under a variety of plans. It also evaluates the impact of different system-prompt plans on the agent’s success in the issueresolution task. We find that while plans clearly matter for task success, agents often struggle to comply with them. This highlights the potential to further boost agent performance in future work via better plans and/or improved plan compliance.

- 11 Data Availability Statement The artifacts of this paper are publicly available at [22].


Figure 19: Compliance metrics on SWE-bench Verified deterministic (a) and SWE-bench Pro (b)

SAGE [13] shows that plans distilled from prior executions can guide future behavior and improve performance on software engineering tasks. While these approaches demonstrate the benefits of planning, they primarily evaluate success at the task level and implicitly assume that agents will follow the generated or provided plans during execution. Jia et al. [15] assess whether a web agent’s actions align with its stated plan using LLM-based judges. However, this approach relies on costly and potentially unstable LLM scoring, limiting its scalability. In contrast, our work introduces mathematically defined plan compliance metrics that enable systematic analysis of agent behavior under controlled plan variations.

### 8 Threats to Validity

External Validity. We evaluate four models and conduct experiments on two different benchmarks, which consist of real-world GitHub issues and differ in task composition, providing complementary evaluation settings. We use a structured plan common among several programming agents (e.g., mini-SWE-agent, Trae agent, OpenHands) as the standard plan to avoid bias and to be representative of common practice.

Internal Validity. To minimize the impact of nondeterminism of agents, we use a consistent default configuration across all experiments and repeat each experiment three times, focusing on stable behavioral patterns rather than random artifacts.

Construct Validity. Our analysis relies on a phase-level abstraction of trajectories, which may omit fine-grained or project-specific actions. However, it captures the core problem-solving stages that determine plan compliance: navigation, reproduction, patching, and validation. Our pipeline is built on top of peer-reviewed artifacts and is validated with well-vetted tools. We distinguish between key variations, such as newly generated tests and regression tests. Remaining low-level differences are treated as general actions and do not affect the main conclusions.

Acknowledgments

This work is supported by NSF CCF-2238045 and IBM-Illinois Discovery Accelerator Institute (IIDAI) grants. We thank anonymous reviewers for their thoughtful comments and feedback.

### References

- [1] Trae Agent. 2026. Trae Agent System Prompt with Default Plan. https://github. com/bytedance/trae-agent/blob/main/trae_agent/prompt/agent_prompt.py.
- [2] Toufique Ahmed, Jatin Ganhotra, Avraham Shinnar, and Martin Hirzel. 2026. Investigating Test Overfitting on SWE-bench. In Conference on the Foundations of Software Engineering: Ideas, Visions, and Reflections track (FSE-IVR). 1292–1296. https://doi.org/10.1145/3803437.3805574
- [3] Toufique Ahmed, Martin Hirzel, Rangeet Pan, Avraham Shinnar, and Saurabh Sinha. 2024. TDD-Bench Verified: Can LLMs Generate Tests for Issues Before They Get Resolved? arXiv preprint arXiv:2412.02883 (2024). doi:10.48550/arXiv. 2412.02883
- [4] Yang Chen, Aliya Ahmad, Yiheng Zhou, and Reyhaneh Jabbarvand. 2026. Unlocking Model Potentials Through Adaptive Multi-Agent Scaffolding for Efficient Issue Resolution. arXiv preprint arXiv:2606.25514 (2026). doi:10.48550/arXiv.2606. 25514
- [5] Yang Chen, Toufique Ahmed, Reyhaneh Jabbarvand, and Martin Hirzel. 2026. Can Old Tests do New Tricks for Resolving SWE Issues?. In Symposium on the Foundations of Software Engineering (FSE). https://doi.org/10.1145/3808148
- [6] Neil Chowdhury, James Aung, Chan Jun Shern, Oliver Jaffe, Dane Sherburn, Giulio Starace, Evan Mays, Rachel Dias, Marwan Aljubeh, Mia Glaese, Carlos E. Jimenez, John Yang, Kevin Liu, and Aleksander Madry. 2024. Introducing SWEbench Verified. https://openai.com/index/introducing-swe-bench-verified/
- [7] DeepSeek-AI. 2025. DeepSeek-R1-0528. https://huggingface.co/deepseek-ai/ DeepSeek-R1-0528.
- [8] Xiang Deng, Jeff Da, Edwin Pan, Yannis Yiming He, Charles Ide, Kanak Garg, Niklas Lauffer, Andrew Park, Nitin Pasari, Chetan Rane, et al. 2025. SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? arXiv preprint arXiv:2509.16941 (2025). doi:10.48550/arXiv.2509.16941
- [9] Lutfi Eren Erdogan, Nicholas Lee, Sehoon Kim, Suhong Moon, Hiroki Furuta, Gopala Anumanchipalli, Kurt Keutzer, and Amir Gholami. 2025. PLAN-AND-ACT: improving planning of agents for long-horizon tasks. In Proceedings of the 42nd International Conference on Machine Learning (Vancouver, Canada) (ICML’25). JMLR.org, Article 594, 44 pages. doi:10.48550/arXiv.2503.09572
- [10] Sebastian Farquhar, Vikrant Varma, David Lindner, David Elson, Caleb Biddulph, Ian Goodfellow, and Rohin Shah. 2025. MONA: myopic optimization with non-myopic approval can mitigate multi-step reward hacking. In Proceedings of the 42nd International Conference on Machine Learning (Vancouver, Canada) (ICML’25). JMLR.org, Article 628, 36 pages.
- [11] J.L. Fleiss et al. 1971. Measuring nominal scale agreement among many raters. Psychological Bulletin 76, 5 (1971), 378–382. doi:10.1037/h0031619
- [12] Daya Guo, Dejian Yang, Haowei Zhang, Junxiao Song, Peiyi Wang, Qihao Zhu, Runxin Xu, Ruoyu Zhang, Shirong Ma, Xiao Bi, et al. 2025. DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement learning. Nature 645, 8081

(2025), 633–638. doi:10.1038/s41586-025-09422-z

- [13] Hiroaki Hayashi, Bo Pang, Wenting Zhao, Ye Liu, Akash Gokul, Srijan Bansal, Caiming Xiong, Semih Yavuz, and Yingbo Zhou. 2025. Self-Abstraction from Grounded Experience for Plan-Guided Policy Refinement. arXiv preprint arXiv:2511.05931 (2025). doi:10.48550/arXiv.2511.05931
- [14] Ali Reza Ibrahimzada, Brandon Paulsen, Daniel Kroening, and Reyhaneh Jabbarvand. 2026. ReCodeAgent: A Multi-Agent Workflow for Language-agnostic Translation and Validation of Large-scale Repositories. arXiv preprint arXiv:2604.07341

(2026). doi:10.48550/arXiv.2604.07341

- [15] Allison Sihan Jia, Daniel Huang, Nikhil Vytla, Seung Won Wilson Yoo, Nirvika Choudhury, Shayak Sen, John C Mitchell, and Anupam Datta. 2025. What Is Your Agent’s GPA? A Framework for Evaluating Agent Goal-Plan-Action Alignment. arXiv preprint arXiv:2510.08847 (2025). doi:10.48550/arXiv.2510.08847
- [16] Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik Narasimhan. 2024. SWE-bench: Can Language Models Resolve RealWorld GitHub Issues?. In International Conference on Learning Representations (ICLR). doi:10.48550/arXiv.2310.06770
- [17] Ao LI, Yuexiang Xie, Songze Li, Fugee Tsung, Bolin Ding, and Yaliang Li. 2025. Agent-Oriented Planning in Multi-Agent Systems. In International Conference on Learning Representations, Y. Yue, A. Garg, N. Peng, F. Sha, and R. Yu (Eds.), Vol. 2025. 19495–19517. https://proceedings.iclr.cc/paper_files/paper/2025/file/ 31610e68fe41a62e460e044216a10766-Paper-Conference.pdf
- [18] Shanchao Liang, Spandan Garg, and Roshanak Zilouchian Moghaddam. 2026. The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason. In Proceedings of the IEEE/ACM 48th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP ’26). Association for Computing Machinery, New York, NY, USA, 395–405. doi:10.1145/3786583.3786882
- [19] Aixin Liu, Bei Feng, Bing Xue, Bingxuan Wang, Bochao Wu, Chengda Lu, Chenggang Zhao, Chengqi Deng, Chenyu Zhang, Chong Ruan, et al. 2025. DeepSeek-V3


Technical Report. arXiv:2412.19437 [cs.CL] doi:10.48550/arXiv.2412.19437

- [20] Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. 2024. Lost in the Middle: How Language Models Use Long Contexts. Transactions of the Association for Computational Linguistics 12 (02 2024), 157–173. doi:10.1162/tacl_a_00638
- [21] Shuyang Liu, Yang Chen, Rahul Krishna, Saurabh Sinha, Jatin Ganhotra, and Reyhaneh Jabbarvand. 2026. Process-Centric Analysis of Agentic Software Systems. In Conference on Object-Oriented Programming, Systems, Languages, and Applications (OOPSLA). https://doi.org/10.1145/3798271
- [22] Shuyang Liu, Saman Dehghan, Jatin Ganhotra, Martin Hirzel, and Reyhaneh Jabbarvand. 2026. "From Plan to Action: How Well Do Agents Follow the Plan?" artifact website. doi:10.5281/zenodo.19339901
- [23] H. B. Mann and D. R. Whitney. 1947. On a Test of Whether one of Two Random Variables is Stochastically Larger than the Other. The Annals of Mathematical Statistics 18, 1 (1947), 50 – 60. doi:10.1214/aoms/1177730491
- [24] Quinn McNemar. 1947. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. Psychometrika 12, 2 (1947), 153–157. doi:10.1007/BF02295996
- [25] Mistral AI. 2025. Devstral-Small-2512. https://openrouter.ai/mistralai/devstral2512.
- [26] OpenAI. 2025. GPT5-Mini. https://developers.openai.com/api/docs/models/gpt5-mini.
- [27] OpenAI. 2026. Why SWE-bench Verified no longer measures frontier coding capabilities. https://openai.com/index/why-we-no-longer-evaluate-swe-benchverified.
- [28] OpenHands. 2025. OpenHands System Prompt with Default Plan. https://github.com/OpenHands/OpenHands/blob/ 08118d742b564add3e970921ac8910c265ece975/evaluation/benchmarks/swe_ bench/prompts/swe_default.j2.
- [29] Karl Pearson. 1895. VII. Note on regression and inheritance in the case of two parents. Proceedings of the Royal Society of London 58, 347-352 (12 1895), 240–242. doi:10.1098/rspl.1895.0041
- [30] Thanosan Prathifkumar, Noble Saji Mathews, and Meiyappan Nagappan. 2025. Does SWE-Bench-Verified Test Agent Ability or Model Memory? arXiv preprint arXiv:2512.10218 (2025). doi:10.48550/arXiv.2512.10218
- [31] Cheng Qian, Emre Can Acikgoz, Qi He, Hongru Wang, Xiusi Chen, Dilek HakkaniTur, Gokhan Tur, and Heng Ji. 2026. Toolrl: Reward is all tool learning needs. Advances in Neural Information Processing Systems 38 (2026), 105523–105553. doi:10.48550/arXiv.2504.13958
- [32] IBM Research. 2026. From 73% to 11%: Revealing True SWE-Agent Capabilities with Discriminative Subsets. https://jatinganhotra.dev/blog/swe-agents/2025/06/ 05/swe-bench-verified-discriminative-subsets.html.
- [33] Shuzheng Si, Haozhe Zhao, Kangyang Luo, Gang Chen, Fanchao Qi, Minjia Zhang, Baobao Chang, and Maosong Sun. 2026. A Goal Without a Plan Is Just a Wish: Efficient and Effective Global Planner Training for Long-Horizon Agent Tasks. In Annual Meeting of the Association for Computational Linguistics (ACL). 13086–13113. https://doi.org/10.18653/v1/2026.acl-long.597
- [34] SWE-Agent. 2026. SWE-agent System Prompt with Default Plan. https://github. com/SWE-agent/SWE-agent/blob/main/config/default.yaml.
- [35] Wikipedia. 2026. Scientific Method. https://en.wikipedia.org/wiki/Scientific_ method.
- [36] Scott Wu. 2024. Introducing Devin, the first AI software engineer. Cognition Labs Blog (2024). https://cognition.com/blog/introducing-devin
- [37] Binfeng Xu, Zhiyuan Peng, Bowen Lei, Subhabrata Mukherjee, Yuchen Liu, and Dongkuan Xu. 2023. Rewoo: Decoupling reasoning from observations for efficient augmented language models. arXiv preprint arXiv:2305.18323 (2023). doi:10.48550/ arXiv.2305.18323
- [38] John Yang, Carlos E. Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik Narasimhan, and Ofir Press. 2024. SWE-agent: agent-computer interfaces enable automated software engineering. In Proceedings of the 38th International Conference on Neural Information Processing Systems (Vancouver, BC, Canada) (NIPS ’24). Curran Associates Inc., Red Hook, NY, USA, Article 1601, 125 pages. doi:10.48550/arXiv.2405.15793
- [39] Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik R Narasimhan, and Yuan Cao. 2023. ReAct: Synergizing Reasoning and Acting in Language Models. In International Conference on Learning Representations (ICLR). doi:10. 48550/arXiv.2210.03629
- [40] Cong Zhang, Xin Deik Goh, Dexun Li, Hao Zhang, and Yong Liu. 2025. Planning with Multi-Constraints via Collaborative Language Agents. In Proceedings of the 31st International Conference on Computational Linguistics, Owen Rambow, Leo Wanner, Marianna Apidianaki, Hend Al-Khalifa, Barbara Di Eugenio, and Steven Schockaert (Eds.). Association for Computational Linguistics, Abu Dhabi, UAE, 10054–10082. https://aclanthology.org/2025.coling-main.672/


Received 2026-03-26; accepted 2026-06-18
