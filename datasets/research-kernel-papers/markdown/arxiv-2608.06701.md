# Online Monitoring and Corrective Steering of Programming Agents

## arXiv:2608.06701v1 [cs.SE] 7 Aug 2026

Shuyang Liu†, Saman Dehghan†, Ji Young Kim†, Jatin Ganhotra∗, Martin Hirzel∗, and Reyhaneh Jabbarvand† †University of Illinois Urbana-Champaign, USA, {sl225, samand2, jyk14, reyhaneh}@illinois.edu

∗IBM, USA, {jatinganhotra, hirzel}@us.ibm.com

Abstract—Fixing GitHub issues in large-scale projects is a long-horizon task, especially when a fix requires changes across multiple locations or the issue description lacks the information needed to localize and repair it. As a result, agents traverse long trajectories that are prone to inefficiency and error: they drift away from their intended plan, repeat failed actions, or terminate without a working patch. This paper proposes LIVEPLAN to monitor, detect, and correct such behavioral inefficiencies and drifts in real time. LIVEPLAN decouples judging from advising: a deterministic, rule-based monitor examines general signals over the trajectory to detect issues without invoking an LLM, and only when an issue is detected does it consult an advisor LLM for a high-level, next-step correction. This design avoids the misleading re-planning and costly interventions of prior approaches. We implement LIVEPLAN on top of SWE-agent and evaluate it using five LLMs (three as executor agents and two as advisors) across SWE-bench Verified and SWE-bench Pro. Compared to vanilla SWE-agent, LIVEPLAN notably improves issue resolution rates, achieving consistent gains of up to 15.2% (average: 9.9%), while incurring only an additional cost of $0.08 per instance. The additional solutions concentrate on medium and hard instances. LIVEPLAN consistently outperforms alternative approaches in resolution rate, with minimal regression on already successful runs and new successes on problems that no baseline solves.

SAGE, ansible-185d41031 in SWE-bench Pro run with Gemini-2.5-Flash

###### New Plan

Thought: The user wants to implement the `host_label` static method in `CallbackBase`

1

###### Customized High-Level Plan

Action: view lib/ansible/plugins/callback/__init__.py

- 1. Identify all locations in the default stdout callback (and related callback methods) where host labels are constructed, especially for delegated tasks.
- 2. Implement a robust `CallbackBase.host_label(result)` in `lib/ansible/plugins/callback/__init_ _.py` that mirrors existing formatting and handles missing `_result` or delegation metadata safely.

- 3. Replace each duplicated host-label construction with calls to `CallbackBase.host_label(result)` while preserving any surrounding formatting (coloring, prefixes).

- 4. Run targeted checks or minimal validation to ensure delegated and non-delegated outputs are consistent with previous behavior.


Observation: The path lib/ansible/plugins/callback/__init__.py is not an absolute path...

Thought: I made a mistake in the path; it should be absolute. I will correct it and retry viewing the file.

2

view /app/lib/ansible/plugins/callback/__init__.py

--view_range -100 -1

Observation: Invalid `view_range`: [-100,

-1]. Its first element `-100`

… (Repeat Failed view)

Thought: I'm still not finding `CallbackBase`. I will try to be more strategic and use `rg` to find the exact line numbers of `class CallbackBase`

10

… (Change strategy)

Submit

43

Fig. 1: An example of SAGE [11] incorrect advice (a new global plan), causing SWE-agent to fail on a SWE-bench Pro [7] issue it had originally resolved in a vanilla run.

with Gemini-2.5-Flash. SAGE uses GPT-5.2-Codex as an advisor to analyze an existing trajectory—blind to the resolution status—and generates a new plan for re-execution to resolve possible trajectory problems. The advisor’s plan incorrectly directs the agent to implement CallbackBase in lib/ansible/plugins/callback/__init__.py, which does not exist in the repository. This causes the agent to struggle through its first 10 steps, trying to locate a file that does not exist, ultimately terminating without patching.

I. INTRODUCTION

LLM-based agents solve complex software-engineering tasks by following a plan: the sequence of issue-resolution phases prescribed in their system prompt, e.g., localize, reproduce, patch, validate [37]. Yet an agent may drift away from this plan during execution [18], e.g., skipping validation, or exhibit inefficiencies [8, 19] such as repeated actions and tool call failures, which cause failures or inflate costs even when the agent succeeds [17]. Existing attempts to correct such drift suffer from three main limitations:

(2) Using an LLM-as-a-judge requires determining how often to trigger it for analysis. Some techniques wait until the end of the trajectory to perform a post-hoc analysis and rerun the agent with advice (new plan) based on the analysis [8, 11, 27]. However, although the advisor can provide a global plan to guide the agent from the beginning, the benefit comes with caveats: if the plan is incorrect, similar to Fig. 1, the agent may not be able to understand and recover, given it is instructed to follow the plan. This is also costly, as it feeds the entire trajectory to the advisor LLM and reruns the agent. Other techniques periodically ask the advisor to evaluate a sliding window of the trajectory [9, 10, 25]. However, if the frequency is too high [9, 25], the approach remains costly; if it is too low [10], the steering feedback arrives too late, making it hard for the agent to recover from the failure mode. Overcoming this limitation entails triggering trajectory analysis only when necessary.

(1) They fold judging (is the trajectory in trouble) and advising (what should the agent do to fix the trouble) into a single mechanism: an advisor LLM serves as the judge to evaluate the trajectory and, based on that evaluation, recommends corrective actions for the remainder of the trajectory [31]. Judging and advising are inherently conflicting tasks: an advisor prompted to diagnose and provide corrective advice is incentivized to find a problem, a tendency related to the documented sycophantic bias of LLMs toward framing their prompts [30]. The advisor may surface a problem that does not exist and impose misleading advice that derails a run that was, in fact, on track. Overcoming this limitation requires separating judging and advising.

Figure 2 shows the execution of SWE-agent with DeepSeekV3 on Openlibrary-ba3abfb6a from SWE-bench Pro [7].

Figure 1 shows an example where SAGE [11] re-plans a trajectory for an issue originally resolved by SWE-agent [37]

openlibrary-ba3abfb6a, SWE-bench Pro, Deepseek-V3

| |
|---|


Locate the actual validate_record implementation... then inspect the validation checks

|Steps 1 - 5 Navigate the directory structure, read relevant files<br><br>|
|---|


- 1
- 2


Step 5th

|Steps 6 - 9 Continue exploring, search for and read functions<br><br>|
|---|


10

Found it! The ‘load’ function is defined in ‘__init__.py”. Let’s inspect this file and implement the changes. view __init__.py

Open the relevant

portion, and load … to inspect the validation checks

Step 10th

|11|Understood! Let's inspect the related functions to understand their current logic view __init__.py --view_range 760 950<br><br>|
|---|---|
| | |
| |Steps 12 - 15 broader context an initial submission (no edit)<br><br>| |Read Make|
|---|---|
| | |
|


| |Read Make|
|---|---|
| | |


3

Update the core import validation logic to accept override validation

Step 15th

16 submit

Fig. 2: An advisor periodically checking the trajectory fails to resolve an issue due to late feedback.

A periodic advisor, similar to SWE-PRM [10], evaluates the trajectory every five steps. During the first intervention after step 5, the executor is advised to continue exploring the repository to locate the buggy file. At step 10, it views the exact bug location. However, before taking any repair action in the next step, the advisor incorrectly concludes that the buggy location has not been found and that the agent should keep exploring, causing the agent to continue exploring without patching for the next five steps. After step 15, the advisor offers a patching suggestion, but the guidance arrives too late: the executor has already decided to terminate the run and resubmits, leaving the issue unresolved.

(3) While LLM-as-a-judge offers generalizability, i.e., the LLM draws on its internal knowledge to flag problems that are not necessarily encoded, it comes at the cost of reliability: LLMs are known to be unreliable evaluators that both miss real problems and flag spurious ones [8]. Overcoming this limitation entails a deterministic judge whose approach can flag a broad class of behavioral drifts.

We propose LIVEPLAN for online monitoring of agent trajectories to detect behavioral drifts and intervene with corrective steering. LIVEPLAN separates judgment from advising: it relies on a deterministic, rule-based monitor that examines a set of general signals over the trajectory to determine behavioral drifts (§II-A). These signals are general rather than tied to a specific benchmark or repository, so they flag a broad class of behavioral drift. Upon detection of a behavioral drift, LIVEPLAN generates predefined or custom high-level, corrective, next-step advice to steer the trajectory (§II-B). By separating judgment from advising and planning, judging with a deterministic monitor that does not hallucinate a nonexistent problem, and advising only when that monitor fires, LIVEPLAN addresses the limitations of prior work.

We implement LIVEPLAN on top of SWE-agent [37] and compare its performance against four baselines and ablated versions on the SWE-bench Verified [12] and SWE-bench

Think

Intervention Processor Executor Agent

Observation /Advice

Drop action, keep advice

yes

Propose action

vanilla

|Execute action|
|---|


Keep action, keep advice

no

Block action?

|Incrementally update| |
|---|---|
| | |


Trajectory Representation

Any signal detected?

Configurable Signal Database

no

yes

no

Still cooling down?

Generate a custom advice

(based on: issue description, last guidance, recent trajectory,

yes

Use pre-defined pre-defined advice) advice

Advisor Monitor

|Rule-based|
|---|


Legend: Gate

Data LLM-based

Fig. 3: Overview of LIVEPLAN workflow.

Pro [7] datasets, using five diverse general and reasoning LLMs (three as executors and two as advisors). The comprehensive evaluation confirms the effectiveness of LIVEPLAN in consistently improving the resolution rate of SWE-agent across all models and benchmarks, with consistent gains of up to 15.2% (average: 9.9%). LIVEPLAN not only consistently resolves more GitHub issues than the baselines but also guides the agent more effectively toward solving medium and hard issues. Besides improving the overall resolution rate, LIVEPLAN yields trajectories that are more compliant with the predefined instruction plan in SWE-agent [18], i.e., explore, localize, repair, and validate [33]. Our contributions are:

- Technique. We propose LIVEPLAN, an online monitoring and intervention technique that decouples judging from advising for agent trajectory steering. LIVEPLAN pairs a deterministic, rule-based monitor to detect whether and where a trajectory is in trouble without invoking an LLM, and thus without the risk of hallucinating a non-existent problem (§II-A). The LLM advisor is consulted only when the monitor fires and only for a high-level, next-step correction (§II-B).
- Empirical Evaluation. We perform a large-scale evaluation to assess the effectiveness of LIVEPLAN and other techniques on two widely used GitHub issue datasets. The study results in 7752 trajectories, 4668 of which were generated by intervention approaches, providing a valuable dataset for future research. We conducted a manual analysis of successful and unsuccessful interventions by LIVEPLAN and other baselines, discussing major root causes for intervention failures and guidelines for future research.


II. LIVEPLAN APPROACH

LIVEPLAN consists of three components (Figure 3): (1) Monitor incrementally constructs process-centric representations of the trajectory, evaluates them against a configurable set of general signals to determine behavioral drifts, and invokes the Advisor upon drift detection (§II-A); (2) Advisor

TABLE I. Blocking and non-blocking behavioral drifts detected by LIVEPLAN.

Type Category Signal Behavioral Drift Description

Premature Patching Patch before Localization. Skip Patching Finalize without producing a patch. Skip Validation Submit before validating the patch.

Plan Violation Skipping phase(s) in LANGUTORY.

Blocking

Thought Oscillation Repeated reasoning pattern without meaningful progress. Action Oscillation Repeated execution loops, such as selfloops or cyclic action sequences.

Oscillation Repeated back-edges in GRAPHECTORY

Prolonged Navigation Spends many steps in navigation. Prolonged Reproduction Prolonged bug reproduction. Prolonged Patching Performs many consecutive edits. Prolonged Validation Spends excessive effort validating.

Long same-phase sequence in LANGUTORY

Long Stagnation

Non-blocking

Repeated Action A back edge in GRAPHECTORY

Action Revisit Repeatedly performs the same action, such as revisiting previously viewed locations.

returns a predefined advice corresponding to the drift, or prompts an LLM to generate a custom advice based on issue description, trajectory context, Monitor status, and latest advice, if available (§II-B); depending on the latest action and Monitor observation, (3) Intervention Processor interacts with the executor agent for corrective steering (§II-C).

A. Monitor

Algorithm 1 shows the workflow of Monitor along with other components. At each step, after the executor reasons about the next action but before executing it (Line 7), Monitor tentatively updates the trajectory representations and checks them for behavioral drift (Lines 8–9). If none is observed, execution proceeds (Lines 10–13). Otherwise, Monitor consults the Advisor for corrective steering advice (Lines 14–22).

- A common strategy is to feed an LLM the entire trajectory,


or a slice of it, to review and surface issues. Using an LLM as a judge is prone to hallucination and error [8, 30]. More critically, when a single LLM performs both judging and advising, its steering suggestion is subject to its own biased assessment [6, 14, 20, 30]. To mitigate this, recent work proposes rubric-based judging, directing the LLM to score trajectories against predefined signals [29]. While this constrains the judge and reduces hallucination and bias, it does not eliminate the deeper problem: evaluation still depends on the LLM applying the rubric correctly and, crucially, deterministically. Layering a non-deterministic judge onto an already non-deterministic agent thus compounds rather than contains this instability. Also, a single-prompt rubric is often insufficient: reliable judging may require a tool-equipped sub-agent to actively inspect the environment, substantially increasing cost [3].

Monitor uses two process-centric trajectory representations, GRAPHECTORY and LANGUTORY [17], to generically encode behavioral drifts and detect them via deterministic algorithms. GRAPHECTORY converts the trajectory into an enriched graph, with nodes as distinct agent actions and edges as chronological execution order; LANGUTORY abstracts low-level actions into a sequence of problem-solving phases. The original GRAPHECTORY treats only actions as nodes, with thought included as a node property. LIVEPLAN augments GRAPHEC-

Algorithm 1 LIVEPLAN Runtime Monitoring and Intervention Require: Issue description I, advisor cooldown threshold θc, max consecu-

tive blocking interventions θi, long stagnation threshold θp

- 1: T ← ∅ ▷ committed trajectory
- 2: H ← BUILDINITIALHISTORY(I) ▷ executor-visible history
- 3: G ← ∅; L ← ∅ ▷ GRAPHECTORY and LANGUTORY monitor states
- 4: lastTrigger ← 0; lastAdvisor ← 0; latestAdvice ← ∅
- 5: blockCount ← 0 ▷ consecutive blocking interventions
- 6: while task not finished do
- 7: step ← PROPOSESTEP(H)
- 8: (G′, L′) ← EXTENDMONITORSTATE(G, L, step)
- 9: rules ← CHECKRULES(G′, L′, θp)
- 10: if rules = ∅ then
- 11: (T, H) ← EXECUTEANDRECORD(step, T, H)
- 12: (G, L) ← (G′, L′)
- 13: blockCount ← 0
- 14: else
- 15: preDefinedAdvice ← MONITORADVICE(rules)
- 16: advice ← preDefinedAdvice
- 17: if |T| − lastAdvisor ≥ θc then ▷ advisor cooldown elapsed
- 18: recentSteps ← STEPSSINCE(T, lastTrigger)
- 19: customAdvice ← CALLADVISOR
- 20: advice ← customAdvice
- 21: lastAdvisor ← |T|
- 22: end if
- 23: if CONTAINBLOCKINGRULE(rules) and blockCount &lt; θi then
- 24: H ← APPENDADVICE(H, advice) ▷ do not execute action
- 25: blockCount ← blockCount + 1 ▷ rollback: discard G′, L′
- 26: else
- 27: (T, H) ← EXECUTEANDRECORD(step, T, H)
- 28: (G, L) ← (G′, L′)
- 29: H ← APPENDADVICE(H, advice)
- 30: blockCount ← 0
- 31: end if
- 32: latestAdvice ← advice
- 33: lastTrigger ← |T|
- 34: end if
- 35: end while
- 36: function CALLADVISOR
- 37: Input: I, recentSteps, latestAdvice, preDefinedAdvice
- 38: Return: one LLM-generated next-step advice
- 39: end function


TORY with thought nodes and edges to also monitor ineffective thinking that manifests as behavioral drift. It also splits the GRAPHECTORY’s localization phase into navigation (locating the potential bug) and reproduction (confirming it), extending both GRAPHECTORY nodes and LANGUTORY alphabets with these new phases. This lets Monitor and Advisor detect behavioral drifts and issue corrective steering more specifically.

|python<br><br>…<br><br>18<br><br>str_replace parser.py ×<br><br>&lt;str3, str4&gt;<br><br>17<br><br>test_parser.py<br><br>24<br><br>view /testbed<br><br>view /testbed/html.py<br><br>grep<br><br>str_replace<br><br>/testbed/html.py ×<br><br>&lt;str1, str2&gt;<br><br>1<br>2 format<br>3<br><br><br>4<br><br>python /testbed/test_html.py<br><br>5<br><br>22 20 19 21<br><br>23<br><br>submit|view /testbed<br><br>1<br><br>view /testbed/io<br><br>2<br><br><br>view /testbed/ascii ×<br><br>grep input<br><br>view<br><br>5<br><br>3<br>4<br><br><br>/testbed/io/ascii/core.py<br><br>–-view_range [128,300]<br><br>view<br><br>6<br><br>/testbed/io/ascii/core.py<br><br>…|view /testbed/manager.py<br><br>1<br><br>create reproduce.py<br><br>2<br><br>python reproduce.py<br><br>3<br><br>str_replace<br><br>/testbed/manager.py ×<br><br>&lt;str5, str6&gt;<br><br>4<br><br><br>submit|
|---|---|---|


Navigation (N)

Reproduction (R)

Patch (P)

Validation (V)

General

Langutory: NNNNNN Langutory: NRRP

(a) Repeated Action (b) Oscillation (c) Long Stagnation (d) Plan Violation

Fig. 4: Examples of behavioral drifts captured by GRAPHECTORY and LANGUTORY.

We define behavioral drift as a condition in a trajectory that deviates from common expectations. Under this definition, deviation from the specified plan, repetitive thoughts or actions that fail to advance the agent, and stagnation in any problemsolving phase are behavioral drifts. While signals defined this way are general, they may be incomplete. To account for that, LIVEPLAN maintains a configurable signal database that users can augment. Furthermore, as we discuss in §II-B, the LLM Advisor can still use its general knowledge to guide corrective steering.

Some behavioral drifts are alarming, e.g., skipping critical problem-solving phases, such as patch validation before submission, which may result in an incorrect patch. Therefore, the execution of actions that manifest such drifts should be blocked. Others represent inefficiencies that can be improved but are not necessarily harmful. For example, prolonged navigation through the repository to localize a bug could be due to ineffective reasoning/tooling, or a legitimate need to gather sufficient context to repair a multi-hunk bug. Therefore, execution of the corresponding actions can be allowed, accompanied by corrective steering advice.

Table I lists ten blocking and non-blocking behavioral drifts that Monitor can detect. They can be detected in GRAPHECTORY and LANGUTORY through generic signals: a back-edge in GRAPHECTORY, regardless of the nature of the action, indicates Repeated Action (Figure 4a); repeated self-loops or multi-node cycles in GRAPHECTORY indicate Thought or Action Oscillation (Figure 4b); a sequence of the same phase in LANGUTORY, whose length exceeds the stagnation threshold θp, indicates Long Stagnation (Figure 4c); and a missing phase symbol in LANGUTORY indicates skipping a plan phase, hence Plan Violation (Figure 4d).

- B. Advisor


LIVEPLAN either provides predefined advice or invokes the LLM-based Advisor to generate custom advice (Lines 14– 22). Predefined advice offers only high-level, problem-agnostic guidance; Figure 5 shows the predefined messages for Prolonged Navigation and Action Oscillation drifts. Although relevant to the detected drift, it may be too general to help the executor recover, so Advisor is also equipped with an LLM to generate advice specific to the problem.

Long Stagnation. Phase-specific messages are used for Navigation, Reproduction, Patching, and Validation.

• Prolonged Navigation. You have the following options to explore next, which increase your chance to solve the problem: (1) keep exploring the code base as you do, but focus on the relevant code only; (2) create and run a reproduction test to better localize the bug; (3) if you already have enough information, edit the source code to implement the fix.

Oscillation. You are repeating action {action} in the last {X} trajectory steps. The observation has likely not changed. Concretely reason if this action can help you resolve the issue. If not, think about a better action in the next step so that you can resolve the problem.

Fig. 5: Examples of predefined advice in LIVEPLAN.

When invoked, the LLM-based Advisor receives four inputs: the issue description, the committed trajectory slice since the last advice (to minimize context), the latest advice if available, and the predefined advice for the detected drift. The predefined advice serves as a high-level hint to help it focus, while the recent trajectory remains the primary evidence for grounding the recommendation. Advisor outputs a next-step recommendation, rather than a long-horizon plan, keeping the intervention focused, avoiding over-constraining the executor, and preventing context clutter and degradation [16, 34, 35]. Since even minimal context can increase cost and latency, LIVEPLAN implements a cooling mechanism: Advisor invokes the LLM only if at least θc trajectory steps have elapsed since the last LLM-generated advice (Line 17).

C. Intervention Processor

The Intervention Processor component takes the advice from Advisor and, depending on the drift type, performs one of two actions: (1) for a blocking drift, it rejects the culprit action before execution, discards the tentative GRAPHECTORY and LANGUTORY updates, and appends the advice to the executor history for corrective steering, up to θi consecutive times to avoid stalling execution (Lines 23–25); (2) for a non-blocking drift, or once the blocking-intervention limit is reached, it lets the executor proceed and appends the advice to steer subsequent decisions (Lines 26–31).

TABLE II. Effectiveness on SWE-bench Pro-Python.

Average Advisor Executor Cost

Success Rate (%)

Model

Method

Vanilla 21.76 0.05 GPT-5.2 SAGE 18.79 (-2.97) 0.23

-

DeepSeek (V3)

- Predefined Advice 25.00 (+3.24) 0.11 GPT-5.2 Periodic Advisor 28.79 (+7.03) 0.12 GPT-5.2 LIVEPLAN 34.09 (+12.33) 0.15

Vanilla 13.17 0.78 GPT-5.2 SAGE 18.18 (+5.01) 1.16

-

Gemini (2.5-flash)

- Predefined Advice 18.94 (+5.77) 0.98 GPT-5.2 Periodic Advisor 26.14 (+12.97) 0.84 GPT-5.2 LIVEPLAN 28.41 (+15.24) 1.04

Vanilla 52.5 0.24 MiniMax-M3 SAGE 50.38 (-2.12) 0.34

-

MiniMax (M2.5)

- Predefined Advice 54.17 (+1.67) 0.23 MiniMax-M3 Periodic Advisor 54.54 (+2.04) 0.32 MiniMax-M3 LIVEPLAN 57.95 (+5.45) 0.24

III. EXPERIMENTAL EVALUATION

LIVEPLAN is pluggable to any open-source ReActbased [38] agent. We build LIVEPLAN on top of SWE-agent as it offers a stable, well-tested implementation.

Benchmarks. We evaluate on two repository-level issue resolution benchmarks: SWE-bench Verified [12] and SWE-bench Pro1 [7], a more challenging benchmark designed to be resistant to contamination.

Baselines. We compare LIVEPLAN against (1) SWE-agent using its original, predefined plan with the executor LLM, and

- (2) SAGE [11], which replaces this original plan with one generated by the advisor LLM given a previous trajectory. We also evaluate two ablated variants of LIVEPLAN: (3) Periodic Advisor, which removes Monitor so Advisor periodically evaluates and intervenes on the trajectory, similar to SWEPRM [10] and Wink [25]2, and (4) Predefined Advice, which removes Advisor and monitors the trajectory using only predefined message interventions, similar to [17]3.


LLMs. We use three representative LLMs as executors: DeepSeek-V3 [15], an open-source general-purpose model; Gemini-2.5-Flash [5], a lightweight reasoning model; and MiniMax-M2.5 [23], a model optimized for coding and agentic workflows. Each executor is paired with a stronger but affordable advisor: GPT-5.2-Codex [26] (medium reasoning effort) pairs with the general-purpose executors DeepSeekV3 and Gemini-2.5-Flash, while MiniMax-M3 [24] pairs with the coding-specialized MiniMax-M2.5. A stronger advisor is a prerequisite for meaningful intervention: an advisor no more capable than the executor offers no guidance beyond what the executor could already reach through its own reasoning. We apply the same executor-advisor pairing across all intervention approaches, so that differences in resolution rate reflect the intervention mechanism rather than advisor capability.

Hyperparameters. Following the default configurations of SWE-agent and SWE-bench Pro [7, 33], we use a perinstance cost limit of $2 and a model temperature of 0

1 To account for the cost, we use SWE-bench Pro-Python. 2 These techniques have no runnable artifacts available, so this ablation serves as the closest reproducible analog. 3 Artifacts for [17] exist but do not implement all LIVEPLAN monitoring rules and signals; we use our ablated version instead to isolate the impact of the intervention technique.

TABLE III. Effectiveness on SWE-bench Verified.

Average Advisor Executor Cost

Success Rate (%)

Model

Method

- DeepSeek (V3)

Vanilla 38.20 0.04 GPT-5.2 LIVEPLAN 49.40 (+11.20) 0.08

- Gemini (2.5-flash)

Vanilla 37.80 0.46 GPT-5.2 LIVEPLAN 48.40 (+10.60) 0.58

- MiniMax (M2.5)

Vanilla 74.20 0.30

MiniMax-M3 LIVEPLAN 79.20 (+5.00) 0.25 for all experiments. In the ablated Periodic Advisor variant, Advisor is triggered every five steps, consistent with the SWE-PRM setting for fair comparison. Similarly, we set the cooling period θc to five steps. For long stagnation detection, we set the threshold θp to seven consecutive steps in the same phase, computed from Vanilla SWE-agent runs prior to any intervention, yielding average maximum consecutive phase lengths of 5.64 for resolved instances and 7.61 for unresolved instances across all models. This threshold thus separates normal progress from likely stagnation without being tuned to any intervention method. For blocking behavioral drifts, LIVEPLAN allows at most five consecutive interventions (θi = 5); beyond this, the agent prevents repeated blocking from stalling execution indefinitely. We run SAGE using their provided prompts and pipeline without modification. A. RQ1: Effectiveness in Improving Resolution Rate

We run Vanilla SWE-agent and LIVEPLAN with all advisor and executor LLMs on both benchmarks. To manage experimental costs, we run the ablated versions and SAGE on SWEbench Pro only across all three executor models. We prioritize SWE-bench Pro as it has emerged as the dominant benchmark for long-horizon, agentic software engineering, with SWEbench Verified increasingly retired as a primary measure of progress. Tables II-III summarize the results.

1) Comparison Against Vanilla Runs: LIVEPLAN consistently achieves a higher resolution rate than Vanilla SWE-agent across both benchmarks, demonstrating the effectiveness of real-time monitoring and corrective steering. Gains are greater on SWE-bench Pro, with improvements of +12.33 and +15.24 percentage points for DeepSeekV3 and Gemini-2.5-Flash, respectively, versus +11.20 and +10.60 points on SWE-bench Verified. Even for MiniMaxM2.5, which is a strong model, LIVEPLAN still improves the success rates by +5.45 points on SWE-bench Pro and +5.00 points on SWE-bench Verified. These gains come with only modest cost increases for DeepSeek-V3 and Gemini-2.5-Flash, while simultaneously reducing costs for MiniMax-M2.5. Figure 6 compares the overlap of resolved instances between LIVEPLAN and Vanilla, grouped by difficulty. Black dots indicate the method(s) that resolve the corresponding instances to a bar, and gray dots mark those that do not. Colors indicate instance difficulty. For SWE-bench Verified, we use the difficulty labels provided by the benchmark based on the estimated developer effort to resolve the issue. For SWE-bench Pro, following prior work [3], we estimate difficulty using the number of files modified in the reference patch: easy (1 file),

##### MiniMax-M2.5 Gemini-2.5-Flash DeepSeek-V3

SWE-bench Pro

|Easy|
|---|


|Medium|
|---|


|Hard|
|---|


|Very Hard|
|---|


SWE-bench Verified

Fig. 6: Resolution overlap between LIVEPLAN and Vanilla.

- TABLE IV. Comparison of trigger frequency of the Advisor by different techniques.


Average Intervention

Trigger Rate (%)

Model

Method

Advisor Executor

DeepSeek (V3)

Periodic Advisor 3.25 99.6 LIVEPLAN 2.33 93.9

GPT-5.2

Gemini (2.5-flash)

Periodic Advisor 7.37 97.7 LIVEPLAN 2.99 93.9

MiniMax (M3)

MiniMax (M2.5)

Periodic Advisor 7.38 99.6 LIVEPLAN 1.47 83.3

medium (2–3 files), hard (4–10 files), and very hard (&gt; 10 files). Across all model-benchmark pairs, LIVEPLAN consistently resolves a substantial number of instances beyond those already solved by the vanilla. More importantly, these gains are concentrated on harder tasks: on SWE-bench Verified, more than half of the instances uniquely resolved by LIVEPLAN belong to the hard category; on SWE-bench Pro, nearly all additional resolutions fall into the medium and hard categories. These results suggest that online monitoring and steering are particularly beneficial for more challenging and less contamination-prone software engineering tasks.

- 2) Comparison Against SAGE: LIVEPLAN consistently

outperforms SAGE at even lower cost. SAGE’s notable cost overhead comes from running Vanilla SWE-agent once, feeding its entire trajectory to Advisor for re-planning, and reexecuting the agent with the new plan. SAGE even underperforms the Vanilla run under DeepSeek-V3 and MiniMax-M2.5. Although SAGE produces highly specific guidance, such as exact line numbers or concrete code snippets to insert, this detail is often factually incorrect (Figure 1). Executor LLMs, being generally less capable, often cannot critically evaluate or recover from such erroneous instructions and instead follow the hallucinated guidance faithfully, causing task failures.

- 3) Comparison Against Ablated Versions and Similar Ap-


proaches: Removing Monitor or Advisor degrades the performance of LIVEPLAN, demonstrating the effectiveness of

SWE-bench Pro

SWE-bench Verified

Deepseek-V3 Gemini-2.5-Flash MiniMax-M2.5

Fig. 7: Overlapping resolved instances among techniques.

both and the superiority of LIVEPLAN over similar alternatives: SWE-PRM (every five steps) and Wink (every step) periodically analyze the trajectory and intervene, similar to the Periodic Advisor variant. Such techniques are guaranteed to trigger the Advisor, whereas LIVEPLAN does so when needed.

- Table IV shows that the Periodic Advisor triggers Advisor in almost all trajectories4, while LIVEPLAN triggers it as needed. The average number of interventions in Periodic Advisor is also notably higher than LIVEPLAN. As we confirm through manual analysis, the lower performance despite the higher and denser triggering rate is due to the Advisor providing misleading advice. Using DeepSeek-V3 and Gemini-2.5-Flash, the average cost of LIVEPLAN per instance is higher than that of Periodic Advisor, despite triggering Advisor less often. The additional cost reflects longer successful trajectories rather than more expensive interventions (details in §III-B).

Compared to the Predefined Advice variant, which is similar to the proposed technique in [17], LIVEPLAN consistently outperforms it with a considerable margin. This is because this variant only provides predefined, high-level messages, which may be insufficient to help the agent recover from behavioral drifts. Since Predefined Advice variant detects a broader set of issues than [17], it is an upper bound on that technique’s performance, i.e., LIVEPLAN’s margin over that technique would be even larger.

Figure 7 illustrates the overlap of resolved instances by all approaches. Across most model-benchmark pairs, LIVEPLAN contributes the largest set of uniquely resolved instances, e.g., 73 for Gemini-2.5-Flash and 32 for MiniMax-M2.5 on SWEbench Verified. The distribution of resolved instances suggests that different intervention strategies exhibit complementary strengths across task subsets. Overall, LIVEPLAN offers the strongest balance between effectiveness and cost.

B. RQ2: Detailed Cost Analysis of LIVEPLAN LIVEPLAN’s gains come at minimal cost and overhead.

- Table V reports that across all settings, the advisor costs only $0.01–$0.06 per instance on average. Rule-based monitoring incurs nearly zero runtime overhead, i.e., a few milliseconds. The Advisor latency is modest relative to the


4 The trajectories in which the Advisor is not triggered are shorter than the five-step threshold due to unsuccessful early termination.

- TABLE V. Cost and latency analysis. Exec: Executor; Adv: Advisor; Mon: Monitor. “—” indicates not applicable.


Cost ($) Latency (s) Dataset Advisor Executor Exec. Adv. Mon. Adv.

Setting

Method Steps

- DeepSeek (V3)

Vanilla 16 0.04 — — GPT-5.2 LIVEPLAN 30 0.12 0.04 0.0 10.9

- Gemini (2.5-flash)

Pro

Vanilla 75 0.78 — — GPT-5.2 LIVEPLAN 47 0.98 0.06 0.0 9.6

- MiniMax (M2.5)

Vanilla 47 0.24 — — MiniMax-M3 LIVEPLAN 47 0.24 0.01 0.0 29.1

- DeepSeek (V3)

Vanilla 21 0.04 — — GPT-5.2 LIVEPLAN 24 0.06 0.02 0.0 5.8

Verified

- Gemini (2.5-flash)

Vanilla 52 0.46 — — GPT-5.2 LIVEPLAN 38 0.55 0.04 0.0 8.1

- MiniMax (M2.5)

Vanilla 70 0.30 — — MiniMax-M3 LIVEPLAN 58 0.23 0.02 0.0 39.5

100

DeepSeek-V3 Gemini-2.5-Flash MiniMax-M2.5

86.7 59.5 35.7 32.7 0.4 0.0 86.7 17.4 62.0 13.5 7.6 0.8 21.6 25.8 27.1 33.1 51.1 48.9

[B] Plan Violation [B] Oscillation Navigation Reproduction Patching Validation [N] Repeated Action [B] Plan Violation [B] Oscillation Navigation Reproduction Patching Validation [N] Repeated Action

80

ProVerified

- 0.8 1.5 8.6 5.6 6.1 5.3 4.5 11.7 21.1 20.7 0.4 1.1
- 1.9 11.4 10.9 20.7 18.2 21.2


[N] Long Stagnation

60

15.9 26.1 53.4 60.5 42.4 43.9 25.4 14.6 6.2 4.6 6.2 1.4 50.4 2.0 54.2 21.0 5.0 0.8 15.8 22.8 35.2 31.8 45.6 42.4

40

7.8 7.6 13.6 12.8 24.2 21.6 1.6 0.6 8.6 7.8 0.2 0.6 7.2 14.6 13.0 14.6 51.6 48.0

[N] Long Stagnation

20

10.2 12.8 34.8 33.0 58.8 46.8

0

Vanilla LivePlan Vanilla LivePlan Vanilla LivePlan

Fig. 8: Behavioral drifts in final trajectories.

runtime of long-horizon repository-level repair tasks. Beyond cost, LIVEPLAN often reduces execution effort by decreasing inefficient exploration. For Gemini-2.5-Flash and MiniMaxM2.5, interventions generally shorten trajectories and, in some cases, even reduce the overall cost. In contrast, trajectories become longer for DeepSeek-V3 because LIVEPLAN discourages common shortcuts such as skipping validation [18], encouraging a more complete and reliable repair process. Regardless, the resulting cost overhead remains small.

- C. RQ3: Process-Centric Analysis of Trajectories


In addition to outcome-centric analysis, we conduct three types of automated process-centric analyses to better understand the notable improvement of LIVEPLAN over Vanilla.

1) Prevalence of Triggering Signals: We measure the prevalence of behavioral drifts in completed trajectories of Vanilla and LIVEPLAN (Figure 8), and the percentage of instances in which LIVEPLAN observes each drift during execution (Table VI). Drifts observed by LIVEPLAN may not remain in the final trajectory, since LIVEPLAN steers the agent away from them. On average, 86.16% and 78.33% of Vanilla trajectories in SWE-bench Pro and SWE-bench Verified show behavioral drifts. They are more prevalent in SWEbench Pro, whose more complex problems require longer, drift-prone trajectories.

The exact behavioral drifts in Vanilla runs may not be observed in LIVEPLAN. However, Table VI shows that LIVEPLAN observes many similar behavioral drifts during execution and attempts to steer the agent away. Specifically,

DeepSeek-V3 Gemini-2.5-Flash MiniMax-M2.5

R U R U R U

|PPC POC PPF|0.55|0.54|0.74|0.63|0.85|0.81| |
|---|---|---|---|---|---|---|---|
| |0.55|0.54|0.74|0.63|0.85|0.81| |
| |1.00|0.99|0.95|0.97|0.80|0.81| |
|PC|0.67|0.66|0.80|0.72|0.83|0.81| |
|PPC POC PPF|0.63|0.61|0.71|0.65|0.83|0.80| |
| |0.63|0.61|0.71|0.65|0.83|0.80| |
| |0.98|0.97|0.97|0.97|0.80|0.80| |
|PC|0.73|0.71|0.78|0.73|0.82|0.80| |
|PPC POC PPF|0.79|0.78|0.89|0.83|0.97|0.94| |
| |0.75|0.73|0.89|0.83|0.95|0.93| |
| |0.99|0.98|0.98|0.96|0.80|0.82| |
|PC|0.83|0.81|0.92|0.86|0.90|0.89| |
|PPC POC PPF|0.81|0.84|0.89|0.88|0.97|0.97| |
| |0.77|0.79|0.89|0.88|0.97|0.96| |
| |0.95|0.96|0.97|0.96|0.80|0.80| |
|PC|0.84|0.85|0.91|0.90|0.91|0.90| |


P P P

VanillaLivePlanVanillaLivePlan

###### SWE-bench ProSWE-bench Verified

1.0

0.9

P P P

0.8

Score

P P P

0.7

0.6

P P P

0.5

Fig. 9: Average plan compliance score for Resolved (R) and Unresolved (U) instances of Vanilla and LIVEPLAN.

LIVEPLAN significantly reduces blocking signals. Many of the high-risk behavioral drifts, namely Plan Violation and Action/Thought Oscillation, that are prevalent in the final Vanilla trajectories and are notably observed during LIVEPLAN runs do not appear in final LIVEPLAN trajectories. 55.63% and 40.27% of blocking behavioral drifts in Vanilla trajectories under SWE-bench Pro and SWE-bench Verified drops to 34.37% and 13.67% in LIVEPLAN, respectively.

As our manual analysis confirms (§III-D), the remaining blocking drifts are due to the executor either being unable to follow the advice or choosing not to, repeating the drift after exceeding the consecutive-intervention threshold θi. Nonblocking signals may remain in completed LIVEPLAN trajectories. This is because they can signal either an inefficiency or a legitimate, prolonged attempt necessary to solve hard problems. These results show that LIVEPLAN improves execution quality by minimizing high-risk behavioral drifts while preserving the flexibility needed for long-horizon tasks.

2) Plan Compliance Analysis: LIVEPLAN’s final trajectories, specifically resolved SWE-bench Pro instances by DeepSeek-V3 and Gemini-2.5-Flash, exhibited Plan Violation, albeit to a lesser extent than Vanilla, motivating deeper plancompliance analysis. Following prior work [18], we measure trajectory adherence to SWE-agent’s repair plan, i.e., Navigate, Reproduce, Patch, and Validate, via four metrics: Plan Phase Compliance (PPC) penalizes skipped phases; Plan Order Compliance (POC) penalizes out-of-order execution; and Plan Phase Fidelity (PPF) penalizes behaviors outside the plan. The overall Plan Compliance (PC) is the geometric mean of PPC, POC, and PPF. PC=1 only when a trajectory executes all and only the specified phases in the correct order.

Figure 9 reports average compliance scores for resolved and unresolved instances of Vanilla and LIVEPLAN. Consistent with prior work [18], resolved trajectories achieve higher PC than unresolved ones, indicating that successful repairs mostly followed the intended workflow. LIVEPLAN improves PC mainly through higher PPC and POC, suggesting online intervention helps agents complete the required phases in the intended order. PPF is occasionally lower under LIVE-

TABLE VI. Observed behavioral drifts by LIVEPLAN. Setting Plan

Repeated Dataset Advisor Executor Navigation Reproduction Patching Validation Action SWE-bench Pro

Long Stagnation

Oscillation

Violation

DeepSeek-V3 80.7 26.1 1.5 11.4 11.0 95.5 28.8 Gemini-2.5-Flash 43.9 31.8 5.3 20.5 20.8 73.5 59.5

GPT-5.2

MiniMax-M3 MiniMax-M2.5 1.9 48.7 5.3 1.1 21.3 10.3 44.1

DeepSeek-V3 28.2 22.8 7.4 0.6 14.6 37.0 12.8 Gemini-2.5-Flash 7.7 34.9 13.8 8.4 15.7 78.3 37.8

SWE-bench Verified

GPT-5.2

MiniMax-M3 MiniMax-M2.5 6.2 42.4 21.2 0.6 47.8 6.8 47.0

#### SWE-bench Pro

1.0

LCS Similarity

0.5

0.0

SWE-bench Verified

1.0

LCS Similarity

0.5

0.0

DeepSeek-V3 Gemini-2.5-Flash MiniMax-M2.5

|Prefix Phase<br><br>| |
|---|
<br><br>Full Phase|
|---|


- Fig. 10: Trajectory similarity between Vanilla and LIVEPLAN before the first intervention and over complete trajectories.


PLAN, which we attribute to Advisor suggesting beneficial outof-plan actions, e.g., additional regression testing to validate the patch. Since these trajectories succeed, the out-of-plan behavior appears productive rather than aimless.

3) Strategy Divergence Analysis: The plan-compliance analysis showed that Advisor interventions affect how closely the executor follows its prescribed plan. Independent of that plan, we next perform an apples-to-apples comparison between Vanilla and LIVEPLAN trajectories to understand whether they are similar before the intervention and how they change after it. We compute normalized longest common subsequence (LCS) similarity between LANGUTORY of Vanilla (X) and

LIVEPLAN (Y ) for each instance as 2×||LCS(X|+|X,YY | )|. Larger values indicate more similar execution behavior. We evaluate

similarity on (1) the LANGUTORY prefixes before the first intervention and (2) the LANGUTORY of complete trajectories. The former captures divergence from execution nondeterminism, since both runs evolve independently before any intervention. The latter captures the combined effect of nondeterminism and online intervention.

Figure 10 reports the results. Prefix similarity is high, often 0.8–0.9, indicating agents initially follow similar strategies despite execution non-determinism. After intervention, similarity consistently decreases, showing that LIVEPLAN redirects the subsequent problem-solving strategy. A paired one-sided Wilcoxon signed-rank test [36] comparing prefix and full-trajectory similarity per instance confirms the significance: in every model-benchmark pair, prefix similarity is significantly higher (median paired difference &gt; 0, p &lt; 1e−10). Since prefix and full-trajectory similarities are paired by instance, and difficulty is held fixed across the two measure-

TABLE VII. Resolution transition matrix relative to Vanilla. R: Resolved, U: Unresolved, DS: DeepSeek-V3, GF: Gemini2.5-Flash, and MM: MiniMax-M2.5.

R→U ↓ U→R ↑ DS GF MM DS GF MM

Dataset Method

SAGE 26 12 22 19 28 16 Predefined Advice 16 13 15 25 28 15 Periodic Advisor 16 11 17 35 42 22 LIVEPLAN 2 2 7 33 38 21

SWE-bench Pro

SWE-bench Verified LIVEPLAN 12 7 7 56 68 28

ments, the post-intervention drop reflects the intervention itself rather than task variation. While we discuss the impact of nondeterminism in detail later (§III-E), these results indicate that LIVEPLAN’s performance gains stem from targeted behavioral corrections rather than run-to-run variation.

D. RQ4: Analysis of Improvements and Regressions

Table VII reports resolution transitions relative to Vanilla, computed over instances where each method is triggered. LIVEPLAN consistently achieves the fewest R→U regressions while producing many U→R improvements5, particularly on SWE-bench Pro. These results show that LIVEPLAN not only resolves notable previously unsuccessful instances but also preserves the Vanilla successes. We manually analyzed improvement (U→R) and regression R→U cases to understand root causes. Two authors independently inspected the trajectory, intervention(s), resulting patch, and golden patch to inductively identify root causes, with categories emerging from and refined during analysis rather than defined in advance. The authors then discussed findings to reach consensus on final root-cause labels6.

1) Improvements (U→R): Our analysis identifies the following reasons for LIVEPLAN’s success in converting previously unsuccessful Vanilla runs: (1) Correcting behavioral drift. Weaker executors, particularly DeepSeek-V3 and Gemini-2.5-Flash, frequently exhibit blocking behavioral drifts (Table VI); LIVEPLAN detects them promptly and redirects execution before they persist, eliminating Oscillations in 104/128 (81.3%) of affected trajectories and Plan Violation cases in 37/72 (51.4%). (2) Refocusing on the repair task. As trajectories lengthen, executors may drift from the main repair task due to accumulated context or intermediate failures (context poisoning [3]); by conditioning on the issue description and recent trajectory steps, Advisor redirects the executor away from 5 Although Periodic Advisor achieves slightly more U→R transitions in some settings, it also introduces substantially more R→U regressions, leading to a lower overall success rate than LIVEPLAN. 6 Identified root causes and corresponding instances are available in artifacts [21].

ansible-0fd88717, SWE-bench Pro, Deepseek-V3 Reproduction

General Navigation Patch Validation

|python<br><br>Exit<br><br>… (Repeat Failed Edit-Test Cycles)<br><br>|inspect|
|---|
<br><br>Pause ad-hoc tests. Manually i t password.py::run() … Adjust the control flow…<br><br>…<br><br>⚠Prolonged Validation<br><br>view password.py::run()<br><br>str_replace<br><br>Submit<br><br>23<br><br>32<br><br>password.py::run() √<br><br>&lt;str3, str4&gt;<br><br>Advisor 22 redirect<br><br>…<br><br>str_replace<br><br>cat<br><br>test_password _lookup.py<br><br>Steps 1 - 14 Initial incomplete patch<br><br>18 Thought: Let’s execute the test to verify the fix python /app/test_password_lookup.py Observation: ValueError 18<br><br>echo test_script.py<br><br>python<br><br>cat<br><br>Prolonged Validation<br><br>… …<br><br>str_replace password.py ×<br><br>&lt;str1, str2&gt;<br><br>15<br><br>16<br><br><br>16<br><br>17<br><br><br>…<br><br>…<br><br>55<br><br>22<br><br>21<br><br>create test_parse_format.py<br><br>24<br><br>test_script.py √<br><br>test_password _lookup.py<br><br>test_password _lookup.py ×<br><br>15 Thought: Let’s create a script to test the look up plugin<br><br>cat &lt;&lt; ‘EOF’ &gt; /app/test_password_lookup.py {TEST_SCRIPT_1} EOF<br><br>Thought: There was an issue. Let me rephrase and execute the test script properly to verify the fix<br><br>16<br><br>echo “{TEST_CONTENT}” &gt; test_script.py &amp;&amp; python test_script.py<br><br>Thought: Here's an updated test script that includes the required setup:<br><br>17<br><br>cat &lt;&lt; ‘EOF’ &gt; /app/test_password_lookup.py {TEST_SCRIPT_2} EOF<br><br>19- Repeat the same test execution<br><br>20 python /app/test_password_lookup.py Observation: ValueError<br><br><br>|23|Thought: fix parsing logic to separate salt and ident str_replace password.py::parser_content()<br><br>|
|---|---|
| | |
| |-salt=password[salt_sep+len(salt_slug):]<br><br>+remain=password[salt_sep+len(salt_slug):]<br><br>|
<br><br>|55|Exit (auto submitted)|
|---|---|
| | |
<br><br>|Initial incomplete patch Spends 7 consecutive steps editing and rerunning test_passwor_lookup.py (Similar to Vanilla run)<br><br>Action cycle: edit test_password_lookup.py python test_password_lookup.py<br><br>|
|---|
<br><br>Steps 1 - 22<br><br>-<br><br>|23|Thought: Let’s carefully review the ‘run’ method logic view /app/password.txt<br><br>|
|---|---|
| | |
| |Observation: salt=... ident=2b<br><br>|
<br><br>|24 Though<br><br>|t: Follow Guidance: edit run() control flow lace password.py::run()|
|---|---|
|str_rep<br><br>+ if None:<br><br>+ id<br><br>+ elif<br><br>+ ch| |
| |file_ident is not None and ident is<br><br>ent = file_ident ident is not None and (..): anged = True<br><br>|
|25 Though<br><br>|t: The changes looks correct. Now let's create r test script that doesn't require mocking the<br><br>sible environment. test_parse_format.py<br><br>|
|a simple entire An create| |
| | |
| |t: Let’s run the test: test_parse_format.py<br><br>|
|26 Though<br><br>| |
|Steps 27<br><br>Focused<br><br>python| |
| | |
| |- 33<br><br>validation + clean-up + submit|
<br><br>test_password _lookup.py<br><br>python<br><br>test_password _lookup.py ×<br><br>| |
|---|
<br><br>19<br><br>python test_parse_format.py √<br><br>25|
|---|


(a) Vanilla (Unresolved)

(b) LivePlan (Resolved)

- Fig. 11: Case study of a U→R transition. Intervention redirects the executor from ineffective validation to successful repair.


unproductive exploration and back toward the core problem.

- (3) Progressive online correction. 182/244 (74.6%) of U→R cases receive multiple interventions, averaging 3.70 across all 244 cases, letting LIVEPLAN continually correct newly emerging drifts rather than relying on a one-time redirection.


LIVEPLAN consistently intervenes before recovery becomes difficult. The first intervention occurs within the first third of the trajectory in all 244 U→R cases, leaving sufficient opportunity to steer the remaining execution. Figure 11 illustrates such a case (ansible-0fd88717 from SWE-bench Pro under DeepSeek-V3). Both Vanilla and LIVEPLAN runs initially generate an incomplete patch and then enter validation. As shown in Figure 11a, the Vanilla run gets stuck in ad-hoc test script creation and execution after several test setup failures, drifting away from the main repair task. The trajectory therefore exhibits Prolonged Validation (steps 15–21) and Action Oscillation (self-loop edges at step 18 and 19) before terminating unsuccessfully at step 55. In contrast, Figure 11b shows that LIVEPLAN detects the Prolonged Validation at step 227 and invokes Advisor, which recommends pausing the adhoc tests and instead inspecting and modifying the core logic directly. The executor follows this guidance, edits the correct control flow, performs focused validation, and successfully submits the final patch at step 33.

2) Regressions (R→U): Regressions across all techniques arise from several sources: (1) Misleading or low-quality guidance. Each method fails differently. SAGE may generate an incorrect global plan that redirects the executor toward a non-existent problem (Figure 1) Predefined Advice is often insufficient for task-specific repair. Periodic Advisor may misdiagnose the trajectory state and generate unhelpful guidance (Figure 2). (2) Execution non-determinism. The rerun may diverge from Vanilla execution before any intervention, causing failures absent in the original trajectory. (3) Brittle Vanilla successes. Some Vanilla runs succeed by chance despite limited or missing navigation and validation—likely

7 Note that trajectories are not identical and similar behavioral drifts may occur at different steps.

due to memorization/data contamination [1] rather than proper reasoning, making corrective intervention confusing. (4) Incomplete compliance. The executor may fail to faithfully follow or fully implement a correct advice. (5) Secondarytask distraction. Advice may intentionally redirect the executor toward secondary issues (e.g., environment configuration), distracting it from the primary repair task.

In nearly all LIVEPLAN R→Us, the root cause is not incorrect advice or a failure to intervene on time, but rather the executor’s inability to follow the correct guidance. We confirmed the advice’s accuracy by referring to the golden patch. Figure 12 shows such a case (ansible-8127abbc from SWE-bench Pro under MiniMax-M2.5). Monitor detects a prolonged navigation without generating a patch and triggers Advisor (step 14). The Advisor correctly identifies all five key repair elements (GP1–GP5), consistent with the gold patch, and directs the executor to begin editing. The executor follows part of the advice, e.g., modifying GP5 at step 14. Later, it (incorrectly) reasons that the GP3 edit was incorrect, reverting it at step 56, and ultimately submits a partial patch. In contrast, the Vanilla run remains in navigation until step 24, but collects all the context to generate a successful patch.

Guidelines for Future Research. Inference-time intervention should be complemented by intervention-aware post-training. While LIVEPLAN identifies when and how to steer execution, successful recovery depends on the executor faithfully carrying out the advice. Future work could train on interventionconditioned trajectories using process-level rewards that encourage executors to satisfy explicit guidance constraints across following steps, since optimizing only for final task success may encourage brittle, under-validated solutions. Posttraining complements this work: LIVEPLAN determines when and what advice to give, while the trained executor learns to reliably translate that advice into a correct solution. Given the execution non-determinism observed here, the evaluation should use repeated paired rollouts to estimate how an intervention changes the probability of resolution, rather than

ansible-8127abbc, SWE-bench Pro, MiniMax-M2.5 Reproduction

General Navigation Patch Validation

|LivePlan (Unresolved)<br><br>str_replace<br><br>connection/ __init__.py<br><br>Partial compliance. Let me implement the changes.. (GP5 ✔)<br><br>…<br><br>str_replace worker.py<br><br>Drops plugin-loader setup keeps only CLI-context initialization. 🚨 (GP3 ✗)<br><br>Exit<br><br>🏅 Golden Patch Diff (relevant excerpt) worker.py<br><br>+display.set_queue(self._final_q) # GP1: queue+detach<br><br>+self._detach() # GP1: queue+detach<br><br>+context.CLIARGS = self._cliargs # GP2:restore CLI context<br><br>+paths = context.CLIARGS.get('collections_path') or []<br><br>+paths = paths if is_sequence(paths) else [paths]<br><br>+init_plugin_loader(paths) # GP3: initialize plugin loader connection/__init__.py<br><br>+class ConnectionKwargs(t.TypedDict): … # GP5: apply ConnectionKwargs<br><br>-new_stdin: io.TextIOWrapper | None = None # GP4: remove new_stdin +**kwargs: t.Unpack[ConnectionKwargs] # GP5: apply ConnectionKwargs<br><br>Prolonged navigation, no patch<br><br>Advisor correctly identifies GP1-GP5<br><br>…<br><br>view<br><br>connection/ __init__.py<br><br>Incorrect reasoning The new_stdin is optional and there is no need to change it (GP4 ✗)<br><br>…<br><br>Implements only part of the worker setup (GP1 ✔,GP2<br><br>✔, GP3 ✔, GP4 ✗)<br><br>Unresolved 🚨<br><br>(GP1 ✔, GP2 ✔, GP3 ✗, GP4 ✗, GP5 ✔)<br><br>14 16 56 …<br><br>(GP1 ✗, GP2 ✗, GP3 ✗, GP4 ✗, GP5 ✗)|
|---|


Fig. 12: Case study of a R→U transition under LIVEPLAN. TABLE VIII. Effectiveness in resolving instances of SWEbench Pro that deterministically pass or fail in Vanilla runs.

IV. RELATED WORK

Trajectory analysis and failure diagnosis. Liu et al. [17] propose process-centric trajectory representations via structured graphs and language abstractions. Chen et al. [4] and Liu et al. [19] conduct process-oriented error analysis on GitHub issue-resolution trajectories. TRAIL [8] and MAST [27] develop failure taxonomies, while FALAT [28] and AgentRx [2] offer step-wise failure localization frameworks. These provide post-hoc analysis but do not intervene during execution; LIVEPLAN instead monitors execution continuously and intervenes upon detecting drift, correcting behavior before it propagates. Online steering, planning, and self-correction. SelfRefine [22] and LATS [40] use iterative self-reflection but target stateless reasoning rather than long-horizon agent execution. Planning-based approaches, Plan-and-Act [9], EAGLET [32], and ReCAP [39], decouple planning from execution or learn stronger planners. For software engineering agents, SAGE [11] regenerates a plan from a completed trajectory and reruns the executor; SWE-PRM [10] and Wink [25] periodically invoke an LLM evaluator over recent windows; TrajEval [13] compares fine-grained trajectories against reference patches. LIVEPLAN instead avoids periodic LLM judgment and unnecessary interventions while providing targeted next-step advice, achieving the highest resolution rate across all settings, with substantially fewer Advisor interventions.

Success Advisor Executor Rate (%)

Model

#Instances Method

Vanilla 19.82 GPT-5.2 SAGE 16.67 (-3.15)

-

DeepSeek (V3)

- Predefined Advice 20.27 (+0.45) GPT-5.2 Periodic Advisor 23.87 (+4.05) GPT-5.2 LIVEPLAN 27.03 (+7.21)

222

Vanilla 8.92 GPT-5.2 SAGE 11.74 (+2.82)

-

Gemini (2.5-flash) 213

- Predefined Advice 12.68 (+3.76) GPT-5.2 Periodic Advisor 18.31 (+9.39) GPT-5.2 LIVEPLAN 18.78 (+9.86)

Vanilla 52.99 MiniMax-M3 SAGE 50.00 (-2.99)

-

MiniMax (M2.5) 234

- Predefined Advice 52.99 (+0.00) MiniMax-M3 Periodic Advisor 54.27 (+1.28) MiniMax-M3 LIVEPLAN 56.41 (+3.42)

drawing conclusions from a single trajectory. E. RQ5: Impact of Non-determinism

We re-evaluate all methods on the subset of SWE-bench Pro with deterministic outcomes across two repeated Vanilla runs. This reduces the number of instances but retains the majority of instances: 84%, 80%, and 88% of the study in §III-A for each model. The distribution of instances with consistent outcomes is similar to that of the complete set (20.3% easy, 41.0% medium, 36.8% hard, 1.9% very hard): DeepSeek-V3 (19.4% easy, 40.1% medium, 38.3% hard, 2.3% very hard); Gemini-2.5-Flash (21.1% easy, 39.4% medium, 37.6% hard, 1.9% very hard); and MiniMax-M2.5 (21.8% easy, 40.2% medium, 36.3% hard, 1.7% very hard). Because this subset is defined solely by Vanilla’s consistency, it cannot selectively favor or penalize any.

V. THREATS TO THE VALIDITY

External Validity. To ensure the generalizability of the results, we evaluate LIVEPLAN across three executors and two advisor LLMs on two widely used benchmarks of realworld GitHub issues. We compare LIVEPLAN with four baselines and ablated versions that resemble related work. To account for execution non-determinism, we further reevaluate LIVEPLAN on a subset of instances with consistent outcomes across two repeated Vanilla executions. Similar improvements are observed over the Vanilla baseline, suggesting that our approach is robust to run-to-run variation.

As shown in Table VIII, LIVEPLAN preserves the method ranking from Table II, achieving the highest success rate across all evaluated models, followed by Periodic Advisor, Predefined Advice, and Vanilla. It does so with an advantage comparable in magnitude to that of the full study, indicating that the gain is not an artifact of baseline volatility. We further repeat the SWE-bench Verified Vanilla runs for DeepSeek-V3 (limiting this validation to one model to contain experimental cost), where LIVEPLAN again substantially outperforms Vanilla, improving the success rate from 36.58% to 46.56%, a margin consistent with its full-set gain. These results confirm that the gains of LIVEPLAN are robust to execution nondeterminism rather than favorable run-to-run variation.

Internal Validity. We investigate the impact of the proposed technique not just on the outcome but also on the process.

Construct Validity. Our pipeline is built on peer-reviewed artifacts and validated with well-vetted tools. We analyze the results quantitatively and qualitatively, aligning the two analyses and avoid incorrect metric implementation or measurement.

VI. CONCLUDING REMARKS

We propose LIVEPLAN for lightweight monitoring and corrective steering of programming agents. LIVEPLAN relies on two abstract representations of raw trajectories, namely GRAPHECTORY and LANGUTORY, to monitor and determine behavioral drifts. It benefits from predefined advice relevant to the drift or custom LLM-generated advice when needed. In the next step, we pursue intervention-aware post-training.

VII. DATA AVAILABILITY The artifacts of this paper are publicly available at [21]. ACKNOWLEDGMENTS

This work is supported by NSF CCF-2238045 and IBMIllinois Discovery Accelerator Institute (IIDAI) grants.

REFERENCES

- [1] Anthropic, “Introducing claude opus 4.7,” https://www. anthropic.com/news/claude-opus-4-7, 2026.
- [2] S. Barke, A. Goyal, A. Khare, A. Singh, S. Nath, and C. Bansal, “Agentrx: Diagnosing ai agent failures from execution trajectories,” arXiv preprint arXiv:2602.02475, 2026.
- [3] Y. Chen, A. Ahmad, Y. Zhou, and R. Jabbarvand, “Unlocking model potentials through adaptive multi-agent scaffolding for efficient issue resolution,” arXiv preprint arXiv:2606.25514, 2026.
- [4] Z. Chen, W. Ma, and L. Jiang, “Beyond final code: A process-oriented error analysis of software development agents in real-world github scenarios,” arXiv preprint arXiv:2503.12374, 2025.
- [5] G. Comanici, E. Bieber, M. Schaekermann, I. Pasupat, N. Sachdeva, I. Dhillon, M. Blistein, O. Ram, D. Zhang, E. Rosen et al., “Gemini 2.5: Pushing the frontier with advanced reasoning, multimodality, long context, and next generation agentic capabilities,” arXiv preprint arXiv:2507.06261, 2025.
- [6] H. Deng, H. Zhang, J. Ou, and C. Feng, “Can llm be a good path planner based on prompt engineering? mitigating the hallucination for path planning,” in International Conference on Intelligent Computing. Springer, 2025, pp. 3–15.
- [7] X. Deng, J. Da, E. Pan, Y. Y. He, C. Ide, K. Garg, N. Lauffer, A. Park, N. Pasari, C. Rane, K. Sampath, M. Krishnan, S. Kundurthy, S. Hendryx, Z. Wang, C. B. C. Zhang, N. Jacobson, B. Liu, and B. Kenstler, “SWE-Bench Pro: Can AI agents solve long-horizon software engineering tasks?” Sep. 2025. [Online]. Available: https://arxiv.org/abs/2509.16941
- [8] D. Deshpande, V. Gangal, H. Mehta, J. Krishnan, A. Kannappan, and R. Qian, “Trail: Trace reasoning and agentic issue localization,” arXiv preprint arXiv:2505.08638, 2025.
- [9] L. E. Erdogan, N. Lee, S. Kim, S. Moon, H. Furuta, G. Anumanchipalli, K. Keutzer, and A. Gholami,


- “Plan-and-act: Improving planning of agents for longhorizon tasks,” in International Conference on Machine Learning (ICML), Jul. 2025. [Online]. Available: https://openreview.net/forum?id=ybA4EcMmUZ
- [10] S. Gandhi, J. Tsay, J. Ganhotra, K. Kate, and Y. Rizk, “When agents go astray: Course-correcting SWE agents with PRMs,” in Workshop on Scaling Environments for Agents (SEA@NeurIPS), Dec. 2025. [Online]. Available: https://openreview.net/forum?id=wyrcoDNaGO
- [11] H. Hayashi, B. Pang, W. Zhao, Y. Liu, A. Gokul, S. Bansal, C. Xiong, S. Yavuz, and Y. Zhou, “Selfabstraction from grounded experience for plan-guided policy refinement,” arXiv preprint arXiv:2511.05931, 2025.
- [12] C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, and K. R. Narasimhan, “SWE-bench: Can language models resolve real-world github issues?” in The Twelfth International Conference on Learning Representations, 2024. [Online]. Available: https:// openreview.net/forum?id=VTF8yNQM66
- [13] M. Kim, D. Wang, S. Cui, F. Farmahinifarahani, S. Garg, B. Ray, T. Y. Zhuo, R. Mukherjee, and V. Kumar, “Trajeval: Decomposing code agent trajectories for fine-grained diagnosis,” arXiv preprint arXiv:2603.24631, 2026.
- [14] X. Lin, Y. Ning, J. Zhang, Y. Dong, Y. Liu, Y. Wu, X. Qi, N. Sun, Y. Shang, K. Wang et al., “Llm-based agents suffer from hallucinations: A survey of taxonomy, methods, and directions,” arXiv preprint arXiv:2509.18970, 2025.
- [15] A. Liu, B. Feng, B. Xue, B. Wang, B. Wu, C. Lu, C. Zhao, C. Deng, C. Zhang, C. Ruan et al., “Deepseekv3 technical report,” arXiv preprint arXiv:2412.19437, 2024.
- [16] N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, “Lost in the middle: How language models use long contexts,” Transactions of the Association for Computational Linguistics, vol. 12, pp. 157–173, 02 2024. [Online]. Available: https://doi.org/10.1162/tacl a 00638

- [17] S. Liu, Y. Chen, R. Krishna, S. Sinha, J. Ganhotra, and R. Jabbarvand, “Process-centric analysis of agentic software systems,” Proc. ACM Program. Lang., vol. 10, no. OOPSLA1, Apr. 2026. [Online]. Available: https: //doi.org/10.1145/3798271
- [18] S. Liu, S. Dehghan, J. Ganhotra, M. Hirzel, and R. Jabbarvand, “Evaluating plan compliance in autonomous programming agents,” arXiv preprint arXiv:2604.12147, 2026.
- [19] S. Liu, F. Liu, L. Li, X. Tan, Y. Zhu, X. Lian, and L. Zhang, “An empirical study on failures in automated issue solving,” arXiv preprint arXiv:2509.13941, 2025.
- [20] X. Liu, X. Yang, Z. Li, P. Li, and R. He, “Agenthallu: Benchmarking automated hallucination attribution of llm-based agents,” arXiv preprint arXiv:2601.06818, 2026.
- [21] Liu, Shuyang and Dehghan, Saman and Kim, Jiyoung and Ganhotra, Jatin and Hirzel, Martin and Jabbar-


- vand, Reyhaneh, “Artifact repository,” https://github.com/ Intelligent-CAT-Lab/Agent-Planner.git, 2026.
- [22] A. Madaan, N. Tandon, P. Gupta, S. Hallinan, L. Gao, S. Wiegreffe, U. Alon, N. Dziri, S. Prabhumoye, Y. Yang, S. Gupta, B. P. Majumder, K. Hermann, S. Welleck, A. Yazdanbakhsh, and P. Clark, “Self-refine: Iterative refinement with self-feedback,” in Conference on Neural Information Processing Systems (NeurIPS), Dec. 2023. [Online]. Available: https: //proceedings.neurips.cc/paper files/paper/2023/hash/ 91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference. html

- [23] MiniMax, “Minimax m2.5,” https://www.minimax.io/ models/text, 2025.
- [24] ——, “Minimax m3,” https://www.minimax.io/blog/ minimax-m3, 2026.
- [25] R. Nanda, C. Maddila, S. Jha, E. M. Khan, M. Paltenghi, and S. Chandra, “Wink: Recovering from misbehaviors in coding agents,” arXiv preprint arXiv:2602.17037, 2026.
- [26] OpenAI, “Introducing gpt-5.2-codex,” https://openai. com/index/introducing-gpt-5-2-codex/, 2025.
- [27] M. Z. Pan, M. Cemri, L. A. Agrawal, S. Yang, B. Chopra, R. Tiwari, K. Keutzer, A. Parameswaran, K. Ramchandran, D. Klein, J. E. Gonzalez, M. Zaharia, and I. Stoica, “Why do multiagent systems fail?” in ICLR 2025 Workshop on Building Trust in Language Models and Applications, 2025. [Online]. Available: https://openreview.net/forum?id=wM521FqPvI
- [28] M. N. Rafi, M. Ahasanuzzaman, D. J. Kim, Z. Wang, and T.-H. Chen, “Falat: Tracing failures in llm agent trajectories via dependency-guided search,” arXiv preprint arXiv:2606.00765, 2026.
- [29] D. Rao and C. Callison-Burch, “Autorubric: Unifying rubric-based llm evaluation,” arXiv preprint arXiv:2603.00077, 2026.
- [30] M. Sharma, M. Tong, T. Korbak, D. Duvenaud, A. Askell, S. Bowman, E. Durmus, Z. Hatfield-Dodds, S. Johnston, S. Kravec et al., “Towards understanding sycophancy in language models,” in International Conference on Learning Representations, vol. 2024, 2024, pp. 110–144.
- [31] N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao, “Reflexion: Language agents with verbal reinforcement learning,” Advances in neural information processing systems, vol. 36, pp. 8634–8652, 2023.
- [32] S. Si, H. Zhao, K. Luo, G. Chen, F. Qi, M. Zhang, B. Chang, and M. Sun, “A goal without a plan is just a wish: Efficient and effective global planner training for long-horizon agent tasks,” Oct. 2025. [Online]. Available: https://arxiv.org/abs/2510.05608
- [33] SWE-agent, “Swe-agent documentation,” https://swe-agent.com/latest/usage/batch mode/, 2025.

- [34] Teresa Torres, “Context rot: Why ai gets worse the longer you chat,” https://www.producttalk.org/ context-rot/, 2026.
- [35] X. J. Wang, H. Bai, Y. Sun, H. Wang, S. Zhang,


- W. Hu, M. Schroder, B. Mutlu, D. Song, and R. D. Nowak, “The long-horizon task mirage? diagnosing where and why agentic systems break,” arXiv preprint arXiv:2604.11978, 2026.
- [36] F. Wilcoxon, “Individual comparisons by ranking methods,” Biometrics Bulletin, vol. 1, no. 6, pp. 80–83,

1945. [Online]. Available: http://www.jstor.org/stable/ 3001968

- [37] J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, and O. Press, “Swe-agent: agentcomputer interfaces enable automated software engineering,” in Proceedings of the 38th International Conference on Neural Information Processing Systems, ser. NIPS ’24. Red Hook, NY, USA: Curran Associates Inc., 2024.
- [38] S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. R. Narasimhan, and Y. Cao, “ReAct: Synergizing reasoning and acting in language models,” in International Conference on Learning Representations (ICLR), May

2023. [Online]. Available: https://openreview.net/forum? id=WE vluYUL-X

- [39] Z. Zhang, T. Chen, W. Xu, A. Pentland, and J. Pei, “ReCAP: Recursive context-aware reasoning and planning for large language model agents,” in Conference on Neural Information Processing Systems (NeurIPS), Dec. 2025. [Online]. Available: https://openreview.net/forum?id=r2ykUnzuGt
- [40] A. Zhou, K. Yan, M. Shlapentokh-Rothman, H. Wang, and Y.-X. Wang, “Language agent tree search unifies reasoning, acting, and planning in language models,” in International Conference on Machine Learning (ICML), Jul. 2024, pp. 62138–62160. [Online]. Available: https://proceedings.mlr.press/v235/zhou24r.html
