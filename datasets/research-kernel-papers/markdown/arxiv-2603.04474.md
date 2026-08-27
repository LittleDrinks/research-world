# From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration

Yizhe Xie∗†, Congcong Zhu∗, Xinyue Zhang∗†, Tianqing Zhu∗, Dayong Ye∗, Minfeng Qi∗, Huajie Chen∗, Wanlei Zhou∗ ∗Faculty of Data Science, City University of Macau †Minzu University of China

## arXiv:2603.04474v2 [cs.MA] 11 May 2026

Abstract—Large Language Model-based Multi-Agent Systems (LLM-MAS) are increasingly applied to complex collaborative scenarios. However, their collaborative mechanisms may cause minor inaccuracies to gradually solidify into system-level false consensus through iteration. Such risks are difficult to trace since errors can propagate and amplify through message dependencies. Existing protections often rely on single-agent validation or require modifications to the collaboration architecture, which can weaken effective information flow and may not align with natural collaboration processes in real tasks. To address this, we propose a propagation dynamics model tailored for LLMMAS that abstracts collaboration as a directed dependency graph and provides an early-stage risk criterion to characterize amplification risk. Through experiments on six mainstream frameworks, we identify three vulnerability classes: cascade amplification, topological sensitivity, and consensus inertia. We further instantiate an attack where injecting just a single atomic error seed leads to widespread failure. In response, we introduce a genealogy-graph-based governance layer, implemented as a message-layer plugin, that suppresses both endogenous and exogenous error amplification without altering the collaboration architecture. Experiments show that this approach prevents final infection in at least 89% of runs across operating modes and significantly mitigates the cascading spread of minor errors. 1

I. INTRODUCTION

With the rapid advancement of Large Language Models (LLM), intelligent agents have been increasingly integrated into diverse real-world applications [1] [2]. Evolving beyond isolated monolithic models, the paradigm is advancing toward Multi-Agent Systems based on LLM (LLM-MAS) [3], [4], enabling complex collaboration through specialized roles [5]. Concurrently, representative open-source frameworks for collaborative orchestration have emerged. For instance, AUTOGEN [6] organizes task flows through multi-agent conversation and tool usage, whereas METAGPT [7] incorporates Standard Operating Procedures, or SOPs, derived from human workflows into multi-agent collaboration. A fundamental design premise of these systems is that collaborative division of labor enhances reliability [8], [9]. These architectures decompose complex tasks into subtasks wherein specific agents generate intermediate results. By subsequently aggregating these results into final decisions through collaborative mechanisms, such systems are considered capable of mitigating the risks associated with hallucinations and factual deviations [10], [11].

1Our code and data are available at https://anonymous.4open.science/r/ From-spark-to-fire-6E0C/

Fig. 1. The amplification of errors in LLM-MAS. Whether the input is a factuality error or a faithfulness error, the agents reach a false consensus. This results in failures ranging from security breaches to operational outages.

However, the assumption of inherent reliability faces increasing skepticism. Recent studies have begun to examine the limitations of collaboration, indicating that multi-agent architectures are susceptible to systemic breakdowns [12] [13]. Building upon these investigations, our empirical observations of mainstream collaborative LLM-MAS reveal a fundamental challenge. While these systems enhance noise filtering for independent deviations, we observe that under recursive context reuse, collaborative structures frequently exhibit a cascading amplification of errors.

Minor deviations regarding factuality or faithfulness, whether endogenous or introduced externally, are repeatedly cited and reused within the interaction chain. Over multiple rounds of interaction, these inaccuracies propagate and converge into a collective agreement, eventually evolving into a false consensus at the system level. The absence of an observable semantically traceable propagation trajectory further compounds this issue. As misinformation undergoes semantic shifts during transmission and restatement, tracing the incremental confirmation and accumulation of errors from the final failure back to intermediate stages presents significant difficulties. Figure 1 shows this process.

Existing security research on LLM predominantly characterizes risks and defense strategies at the single-agent level, focusing on prompt injection, jailbreaking, and application-side security boundaries, or addressing localized issues regarding the truthfulness of Retrieval-Augmented Generation (RAG) [14]–[17]. While effective for microscopic risks, such efforts

- Fig. 2. Overview of our work. We categorize false consensus arising from internal vulnerabilities versus external induction. We model propagation dynamics to characterize consensus collapse mechanisms. Correspondingly, a genealogy-based governance layer implements atomic propagation control to mitigate faithfulness and factuality errors.


lack a direct characterization of the macroscopic amplification mechanisms inherent in collaborative systems [18]. Furthermore, prevalent defense approaches in LLM-MAS typically involve introducing additional critic roles or altering existing collaboration patterns, which results in intrusive impacts on system usability and information flow [18]. However, these defenses largely operate on heuristic trial-and-error, treating errors as static anomalies to be filtered rather than dynamic flows [19]. Current analyses lack a first-principles understanding of how semantic errors cascade through the system [20]– [22]. Without a rigorous system dynamics framework, defenders cannot distinguish between random noise and structural inevitability, hindering the understanding of how errors are progressively validated, reused, and magnified [23]. Therefore, a system dynamics perspective is required to quantify collaboration risks across frameworks [24]. It is essential to design detection and defense methods that control the propagation of misinformation without compromising effective information flow, thereby achieving an interpretable balance between utility and safety [25].

Research Questions. To address the risks associated with error propagation and the potential formation of false consensus within collaborative Multi-Agent Systems, this study investigates four core research questions:

- RQ1: How can the diffusion of errors during collaboration be modeled as a traceable and quantifiable system dynamics process to characterize the evolutionary trajectory from local deviation to collective false consensus?
- RQ2: Do mainstream collaboration architectures based on Large Language Models (LLM) possess endogenous


- vulnerabilities that predispose them to amplify rather than correct errors under specific conditions?
- RQ3: Can attackers exploit these characteristics to propagate errors at a limited cost, thereby increasing the risk of system convergence to a false consensus?
- RQ4: How can workflow-agnostic governance mechanisms be designed to suppress the solidification of false consensus without disrupting valid information flow?


Our Work. In response to RQ1, we formalize the landscape by modeling the message flow as a directed graph G = (V,E) and mapping the semantic entailment of agents to state dynamics on this graph. By tracking the node state si(t) and the system coverage S(t) of a single atomic error m, we establish that context reuse drives a deterministic contagion process rather than random diffusion. Furthermore, we derive a structure-sensitive Risk Criterion R to identify amplification trends at an early stage.

Addressing RQ2, we analyze the behavior of different collaboration architectures within a unified state space based on the proposed propagation representation. Through a systematic comparison of mainstream architectures, we identify three categories of endogenous vulnerabilities: the cascading amplification of minor errors, topological sensitivity to hub nodes, and consensus inertia during multi-round interactions.

Regarding RQ3, we validate the feasibility of such exploitation by instantiating a form of directed Consensus Corruption within the same propagation framework. Experiments demonstrate that attackers can exploit the amplification effects of the collaboration mechanism without disrupting the system structure. By utilizing spectral properties to locate critical nodes

and injecting a small number of error seeds, the probability of system convergence to an erroneous consensus is significantly increased.

Finally, for RQ4, we introduce a Genealogy-Based Governance Layer that is parametrically guided by our dynamics model. By tracking information flow in real-time and intervening on demand, this approach aims to suppress harmful cascades while maximally preserving beneficial information transfer. This is achieved without altering the original communication structure, thereby establishing an interpretable balance between safety and utility.

Figure 2 presents an overview of our work. Contributions. The primary contributions of our work are summarized as follows:

- We characterize error propagation and the subsequent formation of false consensus within LLM-MAS as a systemlevel security risk. To quantify this risk, we propose a process-oriented propagation abstraction that utilizes unified state variables and coverage metrics to model the evolutionary trajectory from local deviations to collective consensus.
- We mechanistically characterize three categories of endogenous vulnerabilities through a systematic analysis of mainstream LLM-MAS frameworks and diverse topologies: the cascading amplification of minor errors, sensitivity to topological structures, and consensus inertia during multi-round collaboration.
- We instantiate a directed consensus corruption strategy consistent with the proposed propagation mechanism. Our findings demonstrate that attackers can exploit the confirmation and context reuse inherent in collaborative processes to propagate errors by injecting a minimal number of seeds at a limited cost, thereby significantly increasing the probability that the system converges to a targeted false consensus.
- We propose a governance mechanism based on lineage graphs for the detection and intervention of information flow. This approach tracks propagation paths and intervenes on-demand to suppress error diffusion and the solidification of consensus while maximizing information integrity. We empirically evaluate the trade-off between safety gains and overhead costs.


II. SYSTEM MODELING

- A. Problem Formalization


We formalize the target phenomenon as the system-level convergence of a single atomic error, driven by iterative context reuse within an LLM-MAS. This formulation requires precise definitions of an atomic falsehood, the mechanism by which downstream agents adopt it through context reuse, and the criteria for determining when the system has failed by converging to a false consensus.

Definition 1 (Atomic Falsehood). An atomic falsehood is a minimal, declarative claim m that violates correctness based

on the evaluation reference of the task. We distinguish between two non-exclusive categories:

- 1) Factuality Error. A claim m constitutes a factuality error if it contradicts the ground truth of the dataset, an evaluation oracle, or other explicitly specified external references for the task, including verified tool outputs or gold annotations. This dimension measures alignment with the external reference world defined by the task.
- 2) Faithfulness Error. Faithfulness is defined exclusively


within an evidence-available setting. Let Ei(t) denote the evidence bundle provided to agent i at round t, which includes task instructions and constraints, upstream messages delivered to i via the communication graph, and any tool outputs or retrieved documents contained in its context ci(t). When the task requires responses grounded in Ei(t), or when agent i explicitly attributes a claim to Ei(t) using phrases such as “according to the above logs” or “based on the retrieved document,” we classify m as a faithfulness error if it is unsupported by or contradictory to Ei(t). This category includes task unfaithfulness, where the agent deviates from explicit instructions, and context inconsistency, where the agent asserts m despite the upstream context in Ei(t) stating otherwise or providing no support.

In LLM-MAS settings, both error types are problematic: factuality errors inject incorrect content, whereas faithfulness errors cause downstream steps to rely on unsupported or contradictory premises transmitted through the context-reuse pipeline.

- Definition 2 (Propagation as Adoption). Let ui(t) denote the output of agent i at interaction round t, and let ci(t) denote the full context used to generate ui(t), including Ei(t) and any additional system messages. We introduce a binary

random variable Xi(t) ∈ {0,1} to indicate whether agent i has adopted the atomic falsehood m at round t. We say that adoption propagates to agent i at round t if Xi(t) = 1, where adoption means that m becomes a semantic commitment or a functional premise in ui(t) rather than a surface repetition:

- 1) Direct entailment: ui(t) logically entails m; for instance, when the output explicitly states “the dependency is pandas-v2” while m specifies that pandas-v2 is the required dependency.
- 2) Implicit reliance: The conclusion or action in ui(t) would be invalidated if m were removed from or negated


within ci(t). That is, ui(t) relies on m as a latent premise contained in its context.

This definition captures the pathway whereby an incorrect premise is internalized by a downstream agent and then drives an incorrect answer. In open-ended outputs, such adoption may occur through paraphrase or implicit reliance, so surface matching alone is not a complete adoption test.

- Definition 3 (False Consensus). We define the continuous state variable


#### si(t) = E[Xi(t)] ∈ [0,1]

as the adoption probability of m for agent i at round t, and the system-level error coverage as

n

1 n

S(t) =

si(t).

i=1

The LLM-MAS is said to reach false consensus on m if S(t) exceeds a preset critical threshold τ ∈ (0,1) and remains above τ for a prescribed number of consecutive rounds. Operationally, this definition characterizes false consensus as a stable failure state of error lock-in, distinct from transient fluctuations. In experiments, si(t) and S(t) are estimated from empirical frequencies over tasks or random seeds. For controlled tracer experiments, Xi(t) = 1 is assigned when the injected canonical seed is reproduced or relied on in the agent output, with explicitly rejected or negated mentions excluded from the count.

- B. Graph Dynamics


Our objective is to characterize the mechanisms by which the adoption state of an atomic falsehood m spreads, amplifies, or dissipates through iterative context reuse within a multi-agent system, employing quantities estimable from observable traces. Concretely, we construct the communication graph from message-routing or context-inclusion logs, and we estimate the state of each agent si(t) from the output of agent i, denoted as ui(t), via the adoption criterion in Definition 2. The resulting model provides a deterministic mean-field description of the expected adoption dynamics, rather than an exact sample-path realization of the underlying stochastic process.

We formalize the multi-agent workflow as a directed graph G = (V,E) comprising |V | = n agents. Let A = [aij] ∈ {0,1}n×n denote the adjacency matrix, where aij = 1 indicates the existence of a directed information channel from agent j to agent i. This implies that the output of agent j is included in the context of agent i for subsequent generation. The in-neighbor set of agent i is defined as

#### N(i) = {j | aij = 1},

which enumerates the upstream agents capable of directly influencing agent i through context reuse.

We track a single propagation channel corresponding to one atomic falsehood m. Let Xi(t) ∈ {0,1} indicate whether agent i adopts m at round t under the adoption criterion in Definition 2, and define the continuous state variable as

#### si(t) = E[Xi(t)] ∈ [0,1].

Following an individual-based mean-field (IBMF) approximation, we model the one-step evolution as

#### si(t + 1) = (1 − δ)si(t) + (1 − si(t))fi {sj(t)}j∈N(i),G ,

where δ ∈ [0,1] represents an effective decay rate that aggregates forgetting, self-correction, external verification, and other mechanisms that reduce adoption probability across rounds; in our fitted dynamics, δ is treated as an effective

per-setting constant that summarizes the net recovery strength over the trajectory. The first term, (1 − δ)si(t), represents the probability mass retained from the previous round, while the second term accounts for new adoption on the susceptible portion (1 − si(t)).

Deriving the product-form infection function. We now formulate the infection function fi(·) by integrating a discrete Independent Cascade (IC) mechanism with an IBMF closure. We assume that at each interaction round, every upstream neighbor j ∈ N(i) initiates one independent attempt to induce adoption of m by agent i in the next round, through context reuse and downstream semantic internalization. Here, m is a single tracked atomic deviation that is incorrect under the task evaluation reference: it may be a factuality error carried in j’s output, or a faithfulness error in evidence-available settings where a claim (including a claim about constraints, tool outputs, or retrieved documents) is unsupported by or contradictory to the evidence bundle that downstream agents condition on. Let β ∈ (0,1] denote the propagation probability, interpreted as the probability that the content in the output of agent j causes agent i to treat m as a usable premise when generating ui(t + 1).

Under IBMF, sj(t) approximates the probability that agent j is active regarding m at round t. Therefore, the probability that edge j → i triggers adoption at round t is approximated by βaijsj(t), and the probability that this specific edge fails to trigger adoption is 1 − βaijsj(t).

Under the IC assumption that upstream attempts are independent within a round, the probability that no upstream neighbor triggers adoption is the product over all in-neighbors:

1 − βaijsj(t) .

j∈N(i)

Consequently, the probability that at least one upstream attempt succeeds, representing the mean-field new-adoption probability contributed by neighbors at round t, is given by

fiprod(t) = 1 −

1 − βaijsj(t) .

j∈N(i)

This formulation matches a round-based interaction protocol: each active upstream neighbor obtains one opportunity per round, and a single success is sufficient to trigger adoption.

In workflows where interpreting influence as accumulated infection intensity within a step is more natural, a hazardbased perspective may be employed. We define λi(t) = β j∈N(i) aijsj(t) and model the within-step adoption probability using a Poisson cumulative probability:

fipois(t) = 1 − exp − β∆t

aijsj(t) ,

j∈N(i)

where ∆t = 1 when one interaction round constitutes a basic step. This exponential form corresponds to an approximation that replaces the product of independent failure probabilities with the exponential of summed hazards. In Section II, we employ fiprod as the default because it directly matches the

- Fig. 3. Model validation across different topologies. The black lines represent the observed mean infection rates with ±1 standard error. The dashed lines show the fitted curves using product-based and Poisson-based infection functions.


round-based agent interaction protocol; we utilize fipois only when a continuous-time interpretation is explicitly required.

The spectral threshold indicator. To derive an analytic criterion for determining whether a minor seed of falsehood tends to amplify initially, we examine the early stage where si(t) ≪ 1. In this regime, we neglect the saturation effect induced by (1−si(t)) ≈ 1 and linearize the infection function. Using the first-order approximation

1 −

1 − βaijsj(t) ≈ β

aijsj(t),

j∈N(i)

j∈N(i)

the dynamics become approximately linear:

s(t + 1) ≈ (1 − δ)I + βA s(t).

Let ρ(A) denote the spectral radius of A. The dominant growth factor in this linear system is approximately (1−δ)+βρ(A); thus, the condition for early-stage amplification is (1 − δ) + βρ(A) &gt; 1, or equivalently βρ(A) &gt; δ. This motivates the auxiliary risk criterion

βρ(A) δ

R ≈

.

In settings where the fitted δ is numerically close to zero, R becomes ill-conditioned; in such cases we rely on the inequality βρ(A) &gt; δ as the primary amplification check and treat R as a diagnostic only when δ is non-negligible.

- C. Model Utility


Figure 3 compares observed system-level error coverage S(t) (mean ±1 standard error) with simulated trajectories under the product-form fprod and Poisson-form fpois infection functions defined in §2.3. Across centralized (STAR), layered (CHAIN), layered horizontal, and decentralized (MESH) topologies, the fitted trajectories closely follow the observed growth patterns and remain largely within the empirical uncertainty band. The results reproduce both rapid saturation in highly connected or hub-mediated structures and slower accumulation in decentralized communication, which supports the use of the mean-field abstraction for describing macroscopic error dynamics. The layered horizontal setting is included as an additional structure with both staged propagation and

TABLE I FITTED PARAMETERS FOR TOPOLOGY-LEVEL ERROR PROPAGATION.

Topology Function β δ MSE S(T) Centralized

Product 0.670 0.000 8.0 × 10−4 1.000 Poisson 1.000 0.000 1.0 × 10−3 1.000

Product 0.920 0.005 8.0 × 10−4 0.920 Poisson 1.000 0.000 1.74 × 10−2 0.920

Layered

Layered (Horizontal)

Product 0.850 0.020 4.5 × 10−3 0.823 Poisson 1.000 0.000 1.04 × 10−2 0.823

Product 0.370 0.025 1.6 × 10−3 0.982 Poisson 0.390 0.020 1.8 × 10−3 0.982

Decentralized

lateral communication, allowing us to test whether the model remains stable under a topology closer to practical multi-agent workflows.

Table I reports the fitted parameters and errors for topology settings under infection-function variants. The product-form function achieves low MSE values, with errors mostly on the order of 10−3. The gap is most visible in layered topologies: for the layered graph, product-form fitting reduces MSE from 1.74×10−2 to 8.0×10−4; for the layered horizontal graph, it reduces MSE from 1.04×10−2 to 4.5×10−3. In these settings, the Poisson-form function often pushes β to its upper boundary and δ to zero, suggesting that it tends to over-saturate the adoption process when propagation is constrained by staged communication. We use fprod as the default model in later analysis, since it better separates agent-side susceptibility β from architectural exposure encoded by A. Additional details on model fitting, topology construction, and threshold-shift estimation are provided in Appendix A.

III. THREAT MODEL

Protected Asset. The primary protected asset is the integrity of the collaborative consensus. Our objective is to prevent the system from converging to a false consensus, defined as a state in which the final decision or generated artifact aligns with a shared yet incorrect belief that contradicts task requirements and verifiable evidence.

Endogenous Stochastic Errors. This mode constitutes the non-strategic, intrinsic failure mechanism of agents based on Large Language Models. Even in the absence of external malice, errors emerge spontaneously due to normal operational factors, including stochastic decoding, restricted context windows, and inherent model hallucinations. Within this setting, the seed s(0) is instantiated stochastically rather than through optimization. The central challenge lies in robustness: determining whether communication topologies and interaction dynamics amplify these sporadic, unintentional errors into system-wide failures.

Exogenous Strategic Adversary. This mode represents a targeted attack executed by an external adversary aiming to maximize downstream corruption. The adversary optimizes the content of the seed s(0) and selects the injection position (specifically, agent i at time t) to exploit structural vulnerabilities.

- 1) Capabilities. The adversary operates strictly through application-layer interfaces, including user prompts, untrusted retrieved documents, and injected messages. The setting is defined as gray-box; it assumes knowledge of the graph G and the observed interaction history, but assumes no access to the model weights. This model also generalizes to black-box settings, where the adversary infers functional topology solely from the observed interaction traces without prior knowledge of G.
- 2) Constraints and Scope The adversary cannot modify the hidden instructions of the system, cannot execute code on the host, and does not perform data poisoning during training. The attack is restricted to the inference phase and operates within a bounded interaction budget. These constraints keep the attack at the application layer, allowing us to isolate whether standard collaboration dynamics amplify small errors without introducing stronger system-level or adaptive attacks.
- 3) Success Criteria An attack is considered successful if, within the interaction budget, it significantly increases the prevalence of false consensus S(t) (defined as the fraction of agents adopting the corrupted belief) or degrades the correctness of the final task relative to the unperturbed baseline.


IV. ENDOGENOUS VULNERABILITIES

- A. Vulnerability I: Cascade Amplification


This section examines whether a small, incidental error will stay contained during routine operation, or if the collaborative framework itself amplifies it into a full-system failure. In practice, such errors may originate from benign factors such as hallucinations or stale project context, but their sporadic nature makes them difficult to measure consistently. We therefore use controlled emulation to standardize the initial condition. Concretely, we implant a TRACER SEED s(0) into the system-level instructions of the entry agent. This systemlevel injection is solely employed for measuring endogenous vulnerabilities and does not fall within the attacker capabilities defined in Section III. The seed is a plausible yet outdated notice about a data-source migration. This design isolates the

structural response of the topology from the randomness of error generation and treats the error as a calibrated signal for measuring the amplification gain of the system.

Mechanism. The amplification follows directly from the product-form adoption dynamics introduced in Section II. When internal correction is weak in the early stage, the state update is dominated by multi-neighbor exposure, since concurrent mentions from different upstream agents compound rather than cancel:

 .

 1 −

si(t+1) ≈ si(t) + 1 − si(t)

1 − βaijsj(t)

j∈N(i)

The non-linear term 1 − (·) captures that repeated exposure raises the chance that agent i adopts the seed once any neighbor has already adopted it. When the auxiliary indicator R &gt; 1 places the system in a supercritical regime, the dominant amplification mode associated with spectral radius ρ(A) governs the early growth direction, and a single seed can expand rapidly in coverage. Thus, Cascade Amplification is not a quirk of a particular prompt, but a structural consequence of high exposure coupling under the given interaction graph.

Empirical Evidence. We measure propagation using S(t), the fraction of agents adopting the tracer error at message step t. For simplicity, adoption in the logged interaction is operationalized as a binary state, indicating whether an agent incorporated or relied on the tracer seed in its current output; explicit rejection or negation of the seed is not counted as adoption. Figure 4 shows consistent topologydependent signatures across six frameworks. In chain workflows (LangChain [26], MetaGPT [7]), the error advances sequentially and produces a stepwise increase in S(t). In star workflows (LangGraph [27], CrewAI [28]), once the hub agent adopts the seed, it broadcasts the falsehood to all workers, yielding a sharp jump in S(t) (for example, LangGraph reaches high coverage by t=2). In mesh workflows (AutoGen [6], CAMEL [29]), broadcast-style interaction produces near-immediate contamination with t ≤ 3. Across the six frameworks, cascades often saturate: five reach 100% final infection, including settings with explicit reviewer or QA roles, so role assignment alone does not reliably stop propagation once the seed starts spreading through the workflow. Statistics and experimental configurations are provided in Appendix B.

Fig. 4. The evolution of error coverage S(t).

- B. Vulnerability II: Topological Fragility

We identify a structural failure mode where system resilience depends not solely on error content but on the entry coordinates. Whereas Vulnerability I demonstrates error spreading potential, Vulnerability II investigates where the graph is most susceptible.

Mechanism. The global divergence of outcomes is governed by the adjacency matrix A. In the early linear regime, error state s(t) grows primarily along the principal eigenvector u1. A one-hot seed at node v excites the dominant cascade mode proportional to [u1]v, so the structurally most dangerous seed satisfies v∗ = arg maxv[u1]v. In centralized topologies, the hub maximizes [u1]v; hub corruption drives immediate system-wide amplification, whereas a weakly coupled leaf seed spreads only upon hub adoption, yielding a measurable Impact Factor gap.

Empirical Evidence. We conducted injections on two startopology frameworks to compare outcomes when the error originates from the Manager or Supervisor (Hub) versus a Worker (Leaf). We define the Impact Factor as the ratio of hub-driven to leaf-driven infection rates. As presented in Table II, the results confirm a consistent structural bias. LangGraph exhibits extreme fragility at the central hub, where injection causes 100% system-wide failure. Injection at a leaf node is limited to 9.7%, confirming the Supervisor functions as a strict informational cut-set. CrewAI demonstrates significant centrality dependence, where hub influence dominates peripheral nodes. This disparity is evidenced by a 6.29× Impact Factor, validating that the hub’s spectral vulnerability constitutes an intrinsic topological property.

TABLE II ANALYSIS OF TOPOLOGICAL FRAGILITY

Framework Hub Inf. Leaf Inf. Impact Factor

CrewAI 100.0% 15.9% 6.29 LangGraph 100.0% 9.7% 10.31

- C. Vulnerability III: Consensus Inertia


We identify a temporal asymmetry regarding errors in collaboration. The introduction of a falsehood is computationally inexpensive; however, the cost of correction increases significantly as the workflow progresses. Distinct from instantaneous propagation, Consensus Inertia refers to the increasing resistance of the system to state reversal once an erroneous trajectory is established through intermediate artifacts.

Mechanism. In artifact-centric workflows, intermediate outputs function as the state of the project. An initial error crystallizes into constraints, including sources, assumptions, code skeletons, and evaluation criteria, upon which subsequent steps build. Consequently, a delayed correction conflicts not merely with a single statement but with a dependency chain that maintains internal consistency with the accumulated state.

TABLE III IMPACT OF INTERVENTION TIMING.

###### Timing (t) Target Role Polluted Rounds

t = 2 Architect 1.0 t = 4 QA Engineer 2.9 t = 6 Architect 3.9

Empirical Evidence. We employ Accumulated Polluted Rounds as the primary metric for the rigidity of the system. We define this metric as the aggregate volume of erroneous context generated prior to intervention. This experimental design validates the hypothesis that delayed interventions must counteract a substantially more extensive history of errors. Consequently, this approach quantifies Consensus Inertia as the cumulative burden of contextual debt.

V. EXOGENOUS ATTACK INSTANTIATION

We instantiate the Exogenous Strategic Adversary as an indirect injection process. The objective of the attacker is to guide the collaborative outcome toward a target state that maximizes utility under a bounded interaction budget. To achieve this, the attacker exploits the endogenous vulnerabilities established in Section IV, effectively transforming standard collaboration steps into channels for amplification. Injection is designed to be fixed at t = 0 to maximize downstream exposure and evaluate the worst-case amplification potential, which remains within the attacker capabilities defined in Section III. We present this attack as a generic pipeline design, adaptable to various injection modalities.

Attack Pipeline. The attack executes through a three-step pipeline involving the construction of a minimal seed, the packaging of this seed into a credible artifact, and its injection at a position of high impact.

- Step 1: Seed Construction. The attacker constructs an Atomic Falsehood m∗ compatible with the format of the task while remaining sufficient to shift downstream decisions. Targeted manipulations include modifying a dependency source, altering a constraint, or biasing a task criterion.
- Step 2: Credibility Packaging. The attacker packages the atomic falsehood m∗ to align with local discourse patterns, thereby increasing the transmission probability β and suppressing the correction factor δ. We operationalize this packaging process through two distinct strategies:

- 1) Compliance. This strategy involves wrapping the seed in authoritative framing, utilizing phrases such as “per company policy” or “verified by admin.” This approach exploits the inherent instruction-following tendency of the agents.
- 2) Security FUD. This strategy frames the seed as a critical resolution for a non-existent threat, including examples such as an “emergency patch for CVE-2024-0001.” Using fear, uncertainty, and doubt, this method bypasses verification mechanisms.


- Step 3: Injection Placement. The attacker injects the packaged seed at a location that maximizes downstream exposure


Fig. 5. Overview of the Genealogy-Based Governance Layer.

within the fixed communication structure. In the gray-box setting, the attacker targets high-influence nodes characterized by structural metrics aligned with ρ(A). In the black-box setting, the attacker targets functional roles inferred from the observable information flow, including agents responsible for aggregation, summarization, or final decision-making.

VI. DEFENSE: A GENEALOGY-BASED GOVERNANCE LAYER

A. Problem Setting and Design Objectives

Our defense protects collaborative-consensus integrity under the constrained setting in Section III. We assume a fixed multiagent communication topology: the adjacency matrix A is not modified by the defense.

In practice, the coordination topology is configured at the framework or application layer and shared across workflows. Rewiring connections would change role semantics and disrupt coordination logic, and such structural control is rarely exposed as an interface to plugins. Since production systems often commit to specific orchestration frameworks and interaction graphs, preserving A also eases deployment across diverse frameworks.

With A fixed, the system must maximally preserve the original information flow to retain task utility. Meanwhile, Section IV shows that once a false belief is assimilated into shared context, collaboration does not reliably self-correct. We therefore introduce a lightweight governance layer on the message path with four system-level objectives.

Goal 1: Mitigating the propagation of unverified claims. The main failure mode is a claim’s acceptance, reuse, and solidification as working context. The governance layer reduces the probability that new, unverified claims are promoted into shared context and later relied upon. In the dynamics model, this lowers the effective per-hop adoption rate of corrupted beliefs, captured by the transmission factor in Section II.

- Goal 2: Facilitating early correction to prevent consensus lock-in. When contradictions are detected, the system must trigger correction before the belief hardens into stable consensus. The governance layer increases successful corrections and disrupts self-reinforcing reuse. In our dynamics model, this increases the effective recovery force, captured by the damping factor in Section II.
- Goal 3: Strategic allocation of the verification budget. Because comprehensive verification is costly, the governance layer directs expensive validation toward high-impact positions (agents with structural or functional influence) and toward claims with higher uncertainty or downstream risk.
- Goal 4: Ensuring auditability and reproducibility. The governance layer maintains a traceable record of claim entry, propagation, and correction, enabling post hoc analysis and reproducible evaluation.


B. Architecture and Trust Boundary

We implement the defense as a middleware module interposed between agent interfaces. This layer intercepts outgoing messages, performs structured analysis, and releases sanitized messages downstream. Simultaneously, it maintains a global provenance structure, the Lineage Graph, recording atomiclevel claim history to support incremental comparison.

By default, all newly generated claims are treated as untrusted. The only trusted anchors are: (i) claims validated and confirmed within the Lineage Graph; and (ii) external evidence from designated verification tools. This boundary is necessary as both attacker and endogenous noise utilize standard textual channels.

For each message, the governance layer produces: (1) a downstream message from screened atomic units; (2) a feedback package for the upstream agent if correction is required; and (3) a Lineage Graph update for auditing and screening. An overview of our methodology is shown in Figure 5.

Fig. 6. Infection rate S(t) across communication turns under three topologies.

C. Representation Layer Given a message M, the governance layer decomposes it

into N atomic claims {ak}Nk=1, where each ak is a minimal declarative message capable of independent verification.

Atomic claims fall into two categories: (i) Factuality claims regarding the external world (e.g., entities, numerical values, citations); and (ii) Faithfulness claims regarding task requirements and internal states (e.g., constraints, decisions). This aligns with Definition 1, ensuring uniform processing of error types.

Lineage Graph. We maintain a directed graph L = (V,E) to track atomic provenance. Each node v ∈ V represents an atomic claim, containing metadata such as source and timestamp. Edges encode dependency relations (e.g., supports, contradicts). Crucially, L distinguishes between confirmed nodes (trusted context) and unverified nodes (excluded from trusted context).

Upon arrival, new atomic claims are compared against confirmed nodes in L to determine if they are restatements, conflicts, or new content requiring processing.

- D. Decision Layer This layer executes control logic via a four-stage pipeline.


- Stage 1: Decomposition and initial screening. For each message M, the system decomposes it into atomic claims

{ak} and compares each ak against the confirmed portion of the Lineage Graph, assigning a tri-state label: Green for facts entailed by confirmed lineage, which are released downstream and recorded as confirmed; Red for facts that contradict confirmed lineage, which are blocked for correction with conflict evidence attached; and Yellow for facts that are neither entailed nor contradicted, which are treated as uncertain and held for policy routing in Stage 2.

- Stage 2: Policy routing for uncertain atoms. Uncertain (Yellow) atoms are routed via a configurable policy regulating budget and risk.


- 1) Low-Intervention Policy. Verification is skipped. Yellow atoms are forwarded with an uncertainty tag and recorded as unverified in L, preventing promotion to trusted context.
- 2) Balanced Policy. Verification is selectively triggered based on influence. Comprehensive verification is applied to Yellow atoms from functional hubs (aggregators, summarizers, decision-makers), as errors here have higher downstream exposure under fixed adjacency A. Non-hub atoms follow LowIntervention handling.
- 3) Strict Policy. All Yellow atoms undergo comprehensive verification.


- Stage 3: Comprehensive verification and risk arbitration. This stage combines external evidence retrieval with LLMbased adjudication. Yellow atoms resolve to: (i) Verified true: Promoted to Green and confirmed in L; (ii) Verified false: Reclassified as Red with rollback evidence; (iii) Unresolved: Retained as Yellow with uncertainty tags and recorded as unverified to minimize risks. This gates blind reliance: only confirmed increments are endorsed as trusted context to influence downstream agents.

E. Actuation Layer

Following Stages 1–3, the layer assembles the message and enforces decisions.

- Stage 4: Assembly and rollback. Let Qreturn be the set of Red atoms. Two scenarios ensue:


- Case A: Qreturn ̸= ∅ (Blocking with rollback). Transmission is inhibited. A feedback package is returned containing rejected atoms, conflict evidence, and a rewrite directive. This localizes intervention at the atomic level.

Resubmitted atoms are re-processed. To prevent loops, retries are capped at K. If failure persists, a circuit breaker applies: persistently Red atoms are excluded; persistently Yellow atoms are forwarded with high-risk tags but excluded from confirmed lineage. This prevents deadlock while limiting rejection propagation.

- Case B: Qreturn = ∅ (Release). The outgoing message is assembled from Green and policy-handled Yellow atoms,


TABLE IV ATTACK SUCCESS RATE (ASR, %) COMPARISON (REAL DATA).

Baseline Compliance Security FUD M Q R M Q R M Q R

Topology Framework

LangChain 3.3 0.0 0.0 95.0 96.7 85.0 100.0 100.0 100.0 MetaGPT 5.0 11.7 46.7 100.0 98.3 100.0 96.7 76.7 95.0

Chain

AutoGen 0.0 5.0 0.0 100.0 100.0 95.0 98.3 100.0 98.3 CAMEL 0.0 0.0 0.0 100.0 100.0 100.0 100.0 98.3 100.0

Mesh

CrewAI 0.0 0.0 3.3 46.7 51.7 31.7 46.7 43.3 33.3 LangGraph 0.0 8.3 11.7 100.0 100.0 100.0 100.0 98.3 100.0

Star

preserving sequence, and released downstream, updating L accordingly.

F. Online and Offline Use

The genealogy-based governance layer deploys inline on the message path, intercepting messages to decompose them into atomic claims, screen, verify, and enforce blocking or rollback in real time. Here, the layer shapes collaboration by controlling claim entry into the shared context and triggering early correction.

The same logic applies offline to historical logs, including from systems deployed without our plugin. Given raw message traces, we replay content through the decomposition, lineage construction, and screening pipeline, reconstructing the Lineage Graph and atomic claims status without influencing execution. This mode supports forensic analysis and attribution: auditors can identify root or high-degree nodes introducing corrupted beliefs, trace propagation across agents and time, and approximate the corresponding S(t) trajectory.

VII. EVALUATION

- A. Experimental Setup


Tasks and scenarios. We evaluate three scenarios covering code-centric collaboration, strict rule-following, and general knowledge question answering: QUANT, consisting of data analysis tasks constructed from the UCI repository [30]; RIGID, comprising multi-step logic and calculation problems derived from MATH benchmarks [31]; and MMLU, adapting general knowledge questions from the MMLU benchmark [32] into retrieval-based tasks.

Frameworks and topologies. We test six mainstream MAS frameworks spanning three interaction topologies. The chain topology includes LANGCHAIN [26] and METAGPT [7]. The mesh topology includes AUTOGEN [6] and CAMEL [29]. The star topology includes CREWAI [28] and LANGGRAPH [27]. Attack settings. We instantiate three attacker policies via application-level message injection, in contrast to the systemlevel injection used in Section IV-A: BASELINE (direct insertion of the raw malicious claim), COMPLIANCE, and SECURITY FUD. For each task instance, we measure whether a

single injected seed can be propagated through multi-round collaboration into an infected final artifact.

Defense settings. We evaluate NONE, three operating points of our governance layer, and three comparison baselines. We use self-reflection as an agent-side self-check baseline, where the agent reviews and revises its own output before sending it [33]. We adapt AGrail as a runtime guardrail baseline that checks each outgoing inter-agent message before it enters downstream context [34]. We further include a control-flow guard (CFG) baseline inspired by ControlValve [35], which checks runtime transitions against admissible edge rules and attempts an alternative valid route when a transition is rejected. AGrail and CFG are evaluated at their native granularity. AGrail operates on whole inter-agent messages, CFG operates on routing transitions, and claim-lineage rollback is evaluated as part of our approach. To simplify the experimental design, we select one framework per topology for the defense experiments. For atomic decomposition, we adopt the FActScore protocol and employ GPT-4o-mini to decompose agent messages [36]. For entailment, we use a natural language inference (NLI) model based on DeBERTa-v3-small [37]. We report a supplementary evaluation of the NLI module on a human-annotated atomicfact set derived from our real tasks in Appendix C. For the verification layer, we use a self-built knowledge base and GPT4o-mini.

Metrics and observables. We report ASR, BICR, Safe Completion, Token/Safe, and Latency/Safe. Attack Success Rate (ASR) is the fraction of tasks whose final artifact is labeled infected. Benign Infection Control Rate (BICR) is defined as 1 − ASR. BICR measures whether the final artifact avoids infection. We additionally report Safe Completion, defined as the fraction of tasks that produce a usable and non-infected final artifact. Token/Safe is the average total token consumption over safe completions. Latency/Safe is the corresponding average runtime in seconds. Infection labels are computed by a deterministic evaluation harness. In addition to final outcomes, we log per-round infection states and the trajectorylevel infection coverage S(t) to visualize whether corruption remains local or escalates system-wide.

Reproducibility details. All evaluation details (including datasets, framework configurations, attack prompts, defense

TABLE V BICR, SAFE COMPLETION, AND TOKEN COST ACROSS FRAMEWORKS AND DEFENSES.

BICR (%) ↑ Safe Completion (%) ↑ Token / Safe (103) ↓ Base. Comp. Sec. Base. Comp. Sec. Base. Comp. Sec.

Framework Defense

Strict 100.0 95.0 100.0 95.0 89.2 97.5 52.9 49.6 52.0 Balanced 97.5 88.3 100.0 93.3 88.3 92.5 24.3 23.2 24.0 Speed 95.8 85.0 100.0 91.7 79.2 97.5 17.1 16.0 16.5 Reflection 82.5 5.0 19.2 80.0 5.0 19.2 9.7 9.3 8.7 AGrail 96.7 36.7 42.5 40.8 0.8 2.5 14.2 14.3 15.2 CFG 80.8 40.0 40.8 53.3 0.0 3.3 6.7 – 7.1

MetaGPT

Strict 99.2 100.0 100.0 97.5 100.0 100.0 75.8 77.8 84.9 Balanced 100.0 95.0 96.7 100.0 92.5 95.8 29.2 30.1 33.0 Speed 100.0 96.7 98.3 99.2 96.7 98.3 29.2 30.0 32.9 Reflection 100.0 5.8 3.3 96.7 5.8 3.3 18.0 17.4 19.4 AGrail 100.0 89.2 79.2 8.3 0.0 3.3 28.4 – 30.3 CFG 99.2 84.2 75.8 35.0 0.8 5.8 26.8 29.1 27.1

AutoGen

Strict 92.5 85.0 76.7 92.5 85.0 76.7 37.1 37.9 41.5 Balanced 95.8 85.8 76.7 95.8 85.8 76.7 35.9 38.3 41.5 Speed 94.2 58.3 76.7 94.2 58.3 76.7 13.6 14.4 15.6 Reflection 73.3 0.8 0.8 73.3 0.8 0.8 9.8 11.0 13.4 AGrail 95.8 90.0 79.2 44.2 0.0 0.0 23.2 – – CFG 98.3 90.0 77.5 48.3 0.0 0.0 9.4 – –

LangGraph

Base., Comp., and Sec. refer to Baseline, Compliance, and Security FUD settings. “–” means no safe completion was produced under corresponding setting.

configuration, NLI module evaluation, and labeling rules) are provided in Appendix C.

- B. Adversarial Severity


We quantify adversarial severity at the application layer. Table IV reports ASR for six frameworks across three scenarios and policies. Intent-hiding attackers consistently outperform direct injection. While BASELINE is near zero in almost all settings and only rises on METAGPT–RIGID (46.7%), COMPLIANCE pushes ASR to mostly 85.0–100.0% outside CREWAI, and SECURITY FUD further raises ASR to 76.7– 100.0% in those settings, indicating that role-consistent packaging substantially increases end-to-end corruption probability over plain injection. The weakest intent-hiding point outside CREWAI appears on METAGPT–QUANT under SECURITY FUD (76.7%), suggesting that scenario constraints and workflow choices partially limit adoption.

Cross-framework differences remain visible under the same topology label. In mesh-style collaboration, both AUTOGEN and CAMEL saturate under intent-hiding attacks, reaching up to 100.0% ASR across scenarios. In star-style orchestration, LANGGRAPH similarly reaches 100.0% ASR under COMPLIANCE and almost saturates under SECURITY FUD, whereas CREWAI is substantially lower. This gap suggests implementation-level coordination and routing policies materially affect how injected content is reused and endorsed, beyond coarse topology classification.

C. Defense Efficacy of the Governance Layer

We evaluate whether the governance plug-in can contain propagation under immutable topology and preserved agent availability, by intervening only at the message layer. Table V reports BICR, Safe Completion, and Token/Safe across attack settings and defense methods. The joint view is necessary because a method may obtain a non-infected output by interrupting the workflow, so Safe Completion is used to check whether the output remains usable. Figure 6 further shows that Speed, Balanced, and Strict flatten S(t) earlier than NONE across all three topologies.

Across MetaGPT and AutoGen, the proposed modes generally maintain high BICR and Safe Completion under intenthiding attacks. On MetaGPT, Speed reaches 85.0% BICR under Compliance and 100.0% under Security FUD, with Safe Completion at 79.2% and 97.5%. On AutoGen, all three proposed modes keep BICR above 95.0% under Compliance and Security FUD, and Safe Completion remains above 92.5%. LangGraph is less stable, especially under Security FUD, where Strict and Balanced both obtain 76.7% BICR. Even in this setting, the proposed modes still provide higher usable non-infected outputs than the agent-monitoring and graphcontrol baselines in most cases.

Reflection preserves the original workflow but remains weak against intent-hiding messages, with BICR falling to 5.0%/19.2% on MetaGPT, 5.8%/3.3% on AutoGen, and 0.8%/0.8% on LangGraph under Compliance and Security FUD. AGrail and CFG show a different pattern: they can reduce final infection in some settings, but Safe Comple-

TABLE VI ABLATION STUDY RESULTS.

### Variant BICR (%) Tokens Time (s)

w/o Atomization 40.0 ± 49.0 11,663 77.9 ± 24.7 w/o Detection 14.4 ± 35.2 14,708 51.7 ± 13.0 w/o Blocking 3.1 ± 10.1 34,991 85.7 ± 21.0 None 2.2 ± 14.7 7,365 41.2 ± 11.9

tion remains limited. Under Compliance, AutoGen reports 89.2%/0.0% for AGrail and 84.2%/0.8% for CFG in BICR/Safe Completion, while LangGraph reports 90.0%/0.0% for both.

The separation between BICR and Safe Completion suggests that final infection control should be interpreted together with usable task completion. Agent-monitoring and graphcontrol baselines can stop part of the corrupted propagation, but they often reduce the chance of producing a usable final artifact. By removing unsafe atomic claims through screening and rollback, the governance plug-in limits propagation while keeping the downstream workflow usable in more attack settings.

Ablation study. To isolate the contribution of each layer, we remove atomization (no_atomization), screening and verification (no_detection), and quarantine or rollback (no_blocking); Table VI reports the corresponding overheads under the Strict policy. The ablation results show a clear drop in containment once key components are removed. Without atomization, BICR remains at 40.0±49.0%, which is higher than the other ablated variants but also highly variable across runs. Removing screening and verification lowers BICR to 14.4 ± 35.2%, indicating that explicit risk decisions are a major contributor to containment. Removing quarantine or rollback further reduces BICR to 3.1 ± 10.1%, close to the NONE setting at 2.2 ± 14.7%.

The overhead pattern helps explain the role of enforcement. The no_blocking variant consumes the most tokens, 34,991, and takes 85.7 ± 21.0s, yet its BICR is only 3.1%. This suggests that screening without an effective quarantine or rollback step can still spend substantial computation while leaving propagation largely uncontrolled. In contrast, no_atomization uses fewer tokens, 11,663, and achieves the highest BICR among the ablations, but the large variance prevents a stronger stability claim. Overall, the results suggest that detection signals need enforceable isolation or rollback to affect downstream propagation, while atomization and screening help make this enforcement more targeted.

D. The Cost of Safety

We measure overhead with Token/Safe and Latency/Safe, which report token use and runtime over safe completions. Table VII summarizes the averaged safety-cost trade-off across proposed modes and comparison baselines. Moving from Reflection to Speed gives the largest robustness gain: BICR

TABLE VII SAFETY-COST SUMMARY.

### Mode BICR Safe Comp. Tok./Safe Lat./Safe (s)

Reflection 0.32 0.32 12,749 91.8 ± 24.0 Speed 0.89 0.88 21,227 149.7 ± 39.5 Balanced 0.93 0.91 30,844 179.6 ± 44.3 Strict 0.94 0.93 57,610 217.9 ± 53.7 AGrail 0.79 0.11 19,902 98.8 ± 20.5 CFG 0.76 0.16 13,323 65.3 ± 25.2

rises from 0.32 to 0.89 and Safe Completion from 0.32 to 0.88, while Token/Safe increases from 12,749 to 21,227 and Latency/Safe from 91.8 ± 24.0s to 149.7 ± 39.5s.

Balanced and Strict further reduce residual infection, with BICR increasing from 0.89 under Speed to 0.93 and 0.94. Safe Completion also rises from 0.88 to 0.91 and 0.93. The additional robustness requires a clear cost increase: Token/Safe grows from 21,227 under Speed to 30,844 under Balanced and 57,610 under Strict, while Latency/Safe increases from 149.7 ± 39.5s to 179.6 ± 44.3s and 217.9 ± 53.7s. This trend supports using Speed as the cost-aware mode and Strict as the high-assurance mode when the application can tolerate higher latency and token usage.

AGrail and CFG have lower Latency/Safe than the proposed modes, at 98.8±20.5s and 65.3±25.2s, respectively. However, their Safe Completion remains low, at 0.11 and 0.16, despite BICR values of 0.79 and 0.76. This gap indicates that lower runtime does not necessarily yield a better deployment tradeoff. Agent-monitoring and graph-control baselines can reduce final infection in some runs, but still produce limited usable non-infected outputs. The proposed modes require more tokens and time, yet preserve a larger fraction of safe completed workflows.

VIII. LIMITATIONS AND FUTURE WORK

We isolate an LLM-MAS failure mechanism where local errors propagate through message dependencies into an incorrect final artifact. We contribute a propagation abstraction with trajectory observables such as S(t), evidence of endogenous vulnerabilities across major frameworks, and a message-layer governance plug-in requiring no retraining. The model is defined over continuous states si(t) ∈ [0,1] and aggregate trajectories S(t), while evaluation uses a binary variable Xi(t) ∈ {0,1} as a simplified interface. This improves interpretability and comparability but may miss cases where agents partially internalize incorrect premises, relax constraints, or show semantic drift without meeting strict adoption criteria. The abstraction treats (β,δ) and structural term A as stationary summaries and captures role, task, or time variation only indirectly. Hence, the spectral indicator R is a theoretical heuristic for early analysis and evidence organization, not a deployment guarantee or calibrated risk predictor.

The injection study is a controlled probe of amplification, not a full characterization of adversarial behavior. We seed application-layer messages to fix an initial condition and test whether endogenous amplification propagates a small seed to the final outcome. Here, the attacker lacks persistent system access and execution-layer control, and the governance plugin operates at the same interface to suppress downstream adoption. This isolates propagation effects from stronger capabilities such as tool tampering and long-term profile poisoning; multi-stage adaptive adversaries that react to intermediate states, or have richer access, remain out of scope and are a natural extension.

The governance plug-in incurs latency overhead in online mode, reflecting the trade-off between runtime safety and execution speed. It also maintains genealogical traces for offline auditing, diagnosis, and post hoc analysis. Our defense evaluation measures safety gains under online deployment, with screening and verification integrated into the workflow. Synchronous execution on the interaction path can increase latency; decoupling or partial offloading shifts protection to non-critical analysis. Balancing these configurations to meet real-time latency budgets and safety targets remains a deployment constraint, not a resolved systems issue.

Future Work. Future work will strengthen validation and broaden the settings where this propagation view and governance logic apply. One direction studies longer-horizon tool-using workflows where failures emerge as downstream artifacts, decisions, or plans, testing whether similar amplification signatures appear in software engineering and scientific support. A second direction refines measurement by improving adoption ground truth beyond binary observables and tightening estimation of structural quantities, including ρ(A), from real traces. A third direction refines system integration by coupling message provenance, evidence retrieval, and verification scheduling, jointly tuning online and offline use to improve the safety-latency trade-off in realistic deployments.

IX. RELATED WORK

Adversarial Attacks on LLM-MAS. Integrating LLMs into multi-agent workflows expands the attack surface across user prompts, inter-agent messages, and tool interfaces; surveys catalog prompt injection, context hijacking, and protocol-level manipulation of agent communication [38], [39]. In multiagent settings, malicious outputs can propagate through downstream dependencies: indirect prompt injection can traverse multi-turn delegations, override system intent, and amplify impact beyond the originating agent [40], [41]. Attackers can also bias group decisions by steering one agent or the coordination channel, turning cooperative verification into an amplification path and exposing system-spanning weaknesses uncovered by model-local safeguards [42], [43]. Recent exploits demonstrate this systemic gap, including Agent-in-the-Middle interception of inter-agent messages, and the web, tool, and shared memory combination allowing one agent’s unsafe intake to trigger harmful actions in another, with reports of MAS executing attacker-supplied code at high success rates [43]–[45]. These

observations motivate orchestration-layer governance, including trust policies and secure communication design rather than ad hoc per-agent defenses [46]–[48].

Failure Modes of LLM-MAS Even without adversaries, LLM multi-agent systems exhibit intrinsic failure modes, and empirical work finds chaining agents often yields limited reliability gains while introducing multi agent specific breakdowns [12]. Common symptoms include role misunderstanding, agents overwriting each other’s context, and stalling in unproductive loops, compounded by memory and context drift in long interactions where earlier constraints are forgotten and critical details are dropped [12], [49], [50]. Without external verification, agents can reinforce shared errors, creating echo effects that inflate confidence in wrong conclusions, and small inaccuracies accumulate over repeated cycles when no corrective mechanism intervenes [43], [51]. A large-scale analysis of more than 1,600 MAS traces systematizes these issues into 14 failure modes across System Design Issues, Inter Agent Misalignment, and Task Verification Failures, highlighting weak delegation and ambiguous instructions as recurring roots [12]. SagaLLM further illustrates missing rollback and global state checks when parallel bookings conflict after a flight cancellation, reflecting absent coordination and state management principles standard in distributed systems and leaving architectures unable to guarantee consistency, recovery, and cross-agent transparency [50].

Defenses and Detectors for LLM-MAS To mitigate risks, defenses span per-agent guardrails and system-level monitoring. Structured prompts, output filters, and policy tools constrain individual behavior but operate locally [52]. Since isolated protections lack visibility into cross-agent dependencies, they miss distributed attack sequences and workflow inconsistencies arising after messages and tool calls traverse team [40], [53], [54]. System-level approaches add redundancy and crosschecking, introducing validator agents, watchdog frameworks, and graph-based anomaly detection over interaction patterns, e.g., SentinelAgent’s interaction graph plus LLM monitoring and log audits like Audit-LLM for insider threats [43], [55], [56]. However, inter-agent links remain under-protected; multihop attacks evade detectors, adversarial steering subverts consensus reliability, and monitoring overhead limits deployment [46], [57], [58]. A consistent direction places security controls in the orchestration layer via trust policies, unified logging, supervisory halt or rollback, least-privilege access, and communication provenance, enabling global consistency through mechanisms like checkpointing or transactional memory while limiting adversarial influence [53], [59].

X. CONCLUSION

We show that a single atomic falsehood can propagate and stabilize as system-level false consensus in fixed LLM-MAS workflows, and we make this process measurable by fitting discrete-time IBMF dynamics on the communication graph with si(t) ∈ [0,1] and S(t). The fitted interface separates transmission, driven by β and ρ(A), from correction, driven by δ, yielding the early amplification condition βρ(A) &gt; δ

and the auxiliary risk indicator R. In evaluation across multiple mainstream frameworks, topologies, and task scenarios, plain injection is near zero in most settings, whereas roleconsistent intent-hiding packaging sharply increases end-toend corruption; the same lens also explains strong sensitivity to structurally central injection points and the decreasing reversibility of late corrections as polluted context accumulates. Finally, we introduce a genealogy-based governance layer that keeps A unchanged and intervenes only on the message path via claim provenance, tri-state screening, targeted verification, and enforced rollback; results and ablations show strong containment, and further indicate that detection alone does not reliably contain propagation without rollback or isolation.

ETHICAL CONSIDERATIONS

This paper studies how small local errors can propagate through collaboration in LLM-based multi-agent systems and lead to a shared but incorrect outcome, and it evaluates mitigation mechanisms under controlled experimental settings. Stakeholders. Potentially impacted stakeholders include (1) developers and operators of LLM-MAS frameworks, who may face higher risk when inter-agent message exchange is manipulated or adversarial content is injected into collaborative workflows. Our mitigation mechanisms aim to reduce this risk by making unsupported claims harder to spread and easier to correct during collaboration. (2) End users of applications built on LLM-MAS may be affected when collaborative outputs drift from verifiable evidence, leading to reduced correctness or reliability in the final artifact. They also benefit when the system can surface unsupported claims early and support timely correction before the final output is produced. (3) security practitioners and researchers, who benefit from evidence about when and why collaboration fails; and (4) the broader online ecosystem, where collaborative tooling can scale both beneficial and harmful content.

Potential impacts. The primary risk is that the attack principles studied here could be adapted to bias collaborative systems by packaging a false seed as credible and encouraging repeated reuse across agents. At the same time, the core technical components studied in this work support responsible mitigation. In particular, atomic claim decomposition and structured intervention mechanisms can improve transparency during collaboration, support post hoc analysis of how an incorrect belief was adopted, and strengthen accountability by making correction points explicit. We believe the benefits outweigh the risks when disclosure is bounded and safeguards are applied.

Risk boundaries and safeguards. Our attack experiments are conducted only in controlled evaluation settings and do not target production systems or real user traffic. The injected content includes controlled, fictitious security-themed messages that are intentionally synthetic and are not claims about real vulnerabilities in real infrastructure. We do not provide any one-click automated hacking toolkit or deployment-ready abuse pipeline. We release only attack principles and the experimental scripts needed to reproduce the paper results, and we avoid packaging guidance that would materially reduce the barrier for misuse.

Human subjects and annotation. When human annotation is used, annotators participate voluntarily and can stop at any time. The annotation content does not involve sensitive personal information, and we report only aggregated results.

Data and privacy. The released datasets are sanitized and do not contain real personal data. Any URLs, database identifiers, or similar fields appearing in artifacts are synthetic.

OPEN SCIENCE

To support reproducibility and NDSS artifact evaluation, we release the artifacts needed to evaluate our contribution via an

anonymized repository link: https://anonymous.4open.science/ r/From-spark-to-fire-6E0C/. The release includes source code, datasets, and experiment scripts sufficient to reproduce the reported results. To reduce dual-use risk, the artifact package does not include any deployment-ready automation intended for real-world misuse.

REFERENCES

- [1] X. Huang, W. Liu, X. Chen, X. Wang, H. Wang, D. Lian, Y. Wang, R. Tang, and E. Chen, “Understanding the planning of llm agents: A survey,” arXiv preprint arXiv:2402.02716, 2024.
- [2] L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin et al., “A survey on large language model based autonomous agents,” Frontiers of Computer Science, vol. 18, no. 6, p. 186345, 2024.
- [3] T. Guo, X. Chen, Y. Wang, R. Chang, S. Pei, N. V. Chawla, O. Wiest, and X. Zhang, “Large language model based multi-agents: A survey of progress and challenges,” arXiv preprint arXiv:2402.01680, 2024.
- [4] X. Li, S. Wang, S. Zeng, Y. Wu, and Y. Yang, “A survey on llmbased multi-agent systems: workflow, infrastructure, and challenges,” Vicinagearth, vol. 1, no. 1, p. 9, 2024.
- [5] Y. Talebirad and A. Nadiri, “Multi-agent collaboration: Harnessing the power of intelligent llm agents,” arXiv preprint arXiv:2306.03314, 2023.
- [6] Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, J. Liu et al., “Autogen: Enabling next-gen llm applications via multi-agent conversations,” in First Conference on Language Modeling, 2024.
- [7] S. Hong, M. Zhuge, J. Chen, X. Zheng, Y. Cheng, J. Wang, C. Zhang, Z. Wang, S. K. S. Yau, Z. Lin et al., “Metagpt: Meta programming for a multi-agent collaborative framework,” in The twelfth international conference on learning representations, 2023.
- [8] J. Jiang, F. Wang, J. Shen, S. Kim, and S. Kim, “A survey on large language models for code generation,” ACM Transactions on Software Engineering and Methodology, vol. 35, no. 2, p. 1–72, Jan. 2026. [Online]. Available: http://dx.doi.org/10.1145/3747588
- [9] Z. Xi, W. Chen, X. Guo, W. He, Y. Ding, B. Hong, M. Zhang, J. Wang, S. Jin, E. Zhou, R. Zheng, X. Fan, X. Wang, L. Xiong, Y. Zhou, W. Wang, C. Jiang, Y. Zou, X. Liu, Z. Yin, S. Dou, R. Weng, W. Cheng, Q. Zhang, W. Qin, Y. Zheng, X. Qiu, X. Huang, and T. Gui, “The rise and potential of large language model based agents: A survey,” 2023. [Online]. Available: https://arxiv.org/abs/2309.07864
- [10] Y. Du, S. Li, A. Torralba, J. B. Tenenbaum, and I. Mordatch, “Improving factuality and reasoning in language models through multiagent debate,” in Forty-first International Conference on Machine Learning, 2023.
- [11] Y. Yang, Y. Ma, H. Feng, Y. Cheng, and Z. Han, “Minimizing hallucinations and communication costs: Adversarial debate and voting mechanisms in llm-based multi-agents,” Applied Sciences, vol. 15, no. 7, p. 3676, 2025.
- [12] M. Z. Pan, M. Cemri, L. A. Agrawal, S. Yang, B. Chopra, R. Tiwari, K. Keutzer, A. Parameswaran, K. Ramchandran, D. Klein et al., “Why do multiagent systems fail?” in ICLR 2025 Workshop on Building Trust in Language Models and Applications, 2025.
- [13] S. Zhang, M. Yin, J. Zhang, J. Liu, Z. Han, J. Zhang, B. Li, C. Wang, H. Wang, Y. Chen et al., “Which agent causes task failures and when? on automated failure attribution of llm multi-agent systems,” arXiv preprint arXiv:2505.00212, 2025.
- [14] Z. Liao, K. Chen, Y. Lin, K. Li, Y. Liu, H. Chen, X. Huang, and Y. Yu, “Attack and defense techniques in large language models: A survey and new perspectives,” Neural Networks, p. 108388, 2025.
- [15] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, “Not what you’ve signed up for: Compromising real-world llmintegrated applications with indirect prompt injection,” in Proceedings of the 16th ACM workshop on artificial intelligence and security, 2023, pp. 79–90.
- [16] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. K¨uttler, M. Lewis, W.-t. Yih, T. Rockt¨aschel et al., “Retrievalaugmented generation for knowledge-intensive nlp tasks,” Advances in neural information processing systems, vol. 33, pp. 9459–9474, 2020.
- [17] S. Es, J. James, L. E. Anke, and S. Schockaert, “Ragas: Automated evaluation of retrieval augmented generation,” in Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations, 2024, pp. 150–158.


- [18] X. Sun, J. Li, Y. Zhong, D. Zhao, and R. Yan, “Towards detecting llms hallucination via markov chain-based multi-agent debate framework,” in ICASSP 2025-2025 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2025, pp. 1–5.
- [19] S. Yi, Y. Liu, Z. Sun, T. Cong, X. He, J. Song, K. Xu, and Q. Li, “Jailbreak attacks and defenses against large language models: A survey,” arXiv preprint arXiv:2407.04295, 2024.
- [20] S. Bikhchandani, D. Hirshleifer, and I. Welch, “A theory of fads, fashion, custom, and cultural change as informational cascades,” Journal of political Economy, vol. 100, no. 5, pp. 992–1026, 1992.
- [21] S. Vosoughi, D. Roy, and S. Aral, “The spread of true and false news online,” science, vol. 359, no. 6380, pp. 1146–1151, 2018.
- [22] Y. Xie, C. Zhu, X. Zhang, T. Zhu, D. Ye, M. Wang, and C. Liu, “Who’s the mole? modeling and detecting intention-hiding malicious agents in llm-based multi-agent systems,” arXiv preprint arXiv:2507.04724, 2025.
- [23] D. J. Watts, “A simple model of global cascades on random networks,” Proceedings of the National Academy of Sciences, vol. 99, no. 9, pp. 5766–5771, 2002.
- [24] R. Pastor-Satorras, C. Castellano, P. Van Mieghem, and A. Vespignani, “Epidemic processes in complex networks,” Reviews of modern physics, vol. 87, no. 3, pp. 925–979, 2015.
- [25] D. E. Denning, “A lattice model of secure information flow,” Communications of the ACM, vol. 19, no. 5, pp. 236–243, 1976.
- [26] O. Topsakal and T. C. Akinci, “Creating large language model applications utilizing langchain: A primer on developing llm apps fast,” in International conference on applied engineering and natural sciences, vol. 1, no. 1, 2023, pp. 1050–1056.
- [27] J. Wang and Z. Duan, “Agent ai with langgraph: A modular framework for enhancing machine translation using large language models,” arXiv preprint arXiv:2412.03801, 2024.
- [28] Z. Duan and J. Wang, “Exploration of llm multi-agent application implementation based on langgraph+ crewai,” arXiv preprint arXiv:2411.18241, 2024.
- [29] G. Li, H. Hammoud, H. Itani, D. Khizbullin, and B. Ghanem, “Camel: Communicative agents for” mind” exploration of large language model society,” Advances in Neural Information Processing Systems, vol. 36, pp. 51991–52008, 2023.
- [30] A. Asuncion, D. Newman et al., “Uci machine learning repository,” 2007.
- [31] D. Hendrycks, C. Burns, S. Kadavath, A. Arora, S. Basart, E. Tang, D. Song, and J. Steinhardt, “Measuring mathematical problem solving with the math dataset,” arXiv preprint arXiv:2103.03874, 2021.
- [32] D. Hendrycks, C. Burns, S. Basart, A. Zou, M. Mazeika, D. Song, and J. Steinhardt, “Measuring massive multitask language understanding,” arXiv preprint arXiv:2009.03300, 2020.
- [33] Z. Ji, T. Yu, Y. Xu, N. Lee, E. Ishii, and P. Fung, “Towards mitigating llm hallucination via self reflection,” in Findings of the Association for Computational Linguistics: EMNLP 2023, 2023, pp. 1827–1843.
- [34] W. Luo, S. Dai, X. Liu, S. Banerjee, H. Sun, M. Chen, and C. Xiao, “Agrail: A lifelong agent guardrail with effective and adaptive safety detection,” in Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 2025, pp. 8104– 8139.
- [35] R. Jha, H. Triedman, J. Wagle, and V. Shmatikov, “Breaking and fixing defenses against control-flow hijacking in multi-agent systems,” arXiv preprint arXiv:2510.17276, 2025.
- [36] S. Min, K. Krishna, X. Lyu, M. Lewis, W.-t. Yih, P. Koh, M. Iyyer, L. Zettlemoyer, and H. Hajishirzi, “Factscore: Fine-grained atomic evaluation of factual precision in long form text generation,” in Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, 2023, pp. 12076–12100.
- [37] P. He, X. Liu, J. Gao, and W. Chen, “Deberta: Decoding-enhanced bert with disentangled attention,” arXiv preprint arXiv:2006.03654, 2020.
- [38] M. A. Ferrag, N. Tihanyi, D. Hamouda, L. Maglaras, A. Lakas, and M. Debbah, “From prompt injections to protocol exploits: Threats in llm-powered ai agents workflows,” ICT Express, 2025.
- [39] D. Kong, S. Lin, Z. Xu, Z. Wang, M. Li, Y. Li, Y. Zhang, H. Peng, X. Chen, Z. Sha et al., “A survey of llm-driven ai agent communication: Protocols, security risks, and defense countermeasures,” arXiv preprint arXiv:2506.19676, 2025.
- [40] X. He, D. Wu, Y. Zhai, and K. Sun, “Sentinelagent: Graphbased anomaly detection in multi-agent systems,” arXiv preprint arXiv:2505.24201, 2025.


- [41] Y. Wang, Y. Pan, S. Guo, and Z. Su, “Security of internet of agents: Attacks and countermeasures,” IEEE Open Journal of the Computer Society, 2025.
- [42] Y. Wang, Y. Pan, Z. Su, Y. Deng, Q. Zhao, L. Du, T. H. Luan, J. Kang, and D. Niyato, “Large model based agents: State-of-the-art, cooperation paradigms, security and privacy, and future trends,” IEEE Communications Surveys &amp; Tutorials, 2025.
- [43] P. He, Y. Lin, S. Dong, H. Xu, Y. Xing, and H. Liu, “Red-teaming llm multi-agent systems via communication attacks,” in Findings of the Association for Computational Linguistics: ACL 2025, 2025, pp. 6726– 6747.
- [44] M. Lupinacci, F. A. Pironti, F. Blefari, F. Romeo, L. Arena, and A. Furfaro, “The dark side of llms: Agent-based attacks for complete computer takeover,” arXiv preprint arXiv:2507.06850, 2025.
- [45] C. J. D’Urso, “Nowhere to hide: investigating the use of unilateral alternatives to extradition in united states prosecutions of transnational cybercrime,” Ph.D. dissertation, University of Oxford, 2021.
- [46] H. Triedman, R. Jha, and V. Shmatikov, “Multi-agent systems execute arbitrary malicious code,” arXiv preprint arXiv:2503.12188, 2025.
- [47] E. Zeydan, J. Baranda, J. Mangues-Bafalluy, and Y. Turk, “Blockchain for network service orchestration: Trust and adoption in multi-domain environments,” IEEE Communications Standards Magazine, vol. 7, no. 2, pp. 16–22, 2023.
- [48] A. Adimulam, R. Gupta, and S. Kumar, “The orchestration of multiagent systems: Architectures, protocols, and enterprise adoption,” arXiv preprint arXiv:2601.13671, 2026.
- [49] R. Sapkota, K. I. Roumeliotis, and M. Karkee, “Ai agents vs. agentic ai: A conceptual taxonomy, applications and challenges,” arXiv preprint arXiv:2505.10468, 2025.
- [50] E. Y. Chang and L. Geng, “Sagallm: Context management, validation, and transaction guarantees for multi-agent llm planning,” arXiv preprint arXiv:2503.11951, 2025.
- [51] B. Baker, J. Huizinga, L. Gao, Z. Dou, M. Y. Guan, A. Madry, W. Zaremba, J. Pachocki, and D. Farhi, “Monitoring reasoning models for misbehavior and the risks of promoting obfuscation,” arXiv preprint arXiv:2503.11926, 2025.
- [52] I. Adabara, B. O. Sadiq, A. N. Shuaibu, Y. I. Danjuma, and V. Maninti, “Trustworthy agentic ai systems: A cross-layer review of architectures, threat models, and governance strategies for real-world deployment,” F1000Research, vol. 14, no. 905, p. 905, 2025.
- [53] P. P. Ray, “A review on agent-to-agent protocol: Concept, state-of-theart, challenges and future directions,” Authorea Preprints, 2025.
- [54] A. Foundjem, L. N. Tidjon, L. Da Silva, and F. Khomh, “Multi-agent framework for threat mitigation and resilience in ai-based systems,” arXiv preprint arXiv:2512.23132, 2025.
- [55] T. Zoppi, A. Ceccarelli, and A. Bondavalli, “Exploring anomaly detection in systems of systems,” in Proceedings of the Symposium on Applied Computing, 2017, pp. 1139–1146.
- [56] C. Song, L. Ma, J. Zheng, J. Liao, H. Kuang, and L. Yang, “Audit-llm: Multi-agent collaboration for log-based insider threat detection,” arXiv preprint arXiv:2408.08902, 2024.
- [57] M. M. Aslam, Z. Ahmed, L. Du, M. Z. Hassan, S. Ali, and M. Nasir, “An overview of recent advances of resilient consensus for multiagent systems under attacks,” Computational Intelligence and Neuroscience, vol. 2022, no. 1, p. 6732343, 2022.
- [58] H. Ishii, Y. Wang, and S. Feng, “An overview on multi-agent consensus under adversarial attacks,” Annual Reviews in Control, vol. 53, pp. 252– 272, 2022.
- [59] C. Islam, M. A. Babar, and S. Nepal, “A multi-vocal review of security orchestration,” ACM Computing Surveys (CSUR), vol. 52, no. 2, pp. 1–45, 2019.


APPENDIX A MODEL FITTING AND TOPOLOGY CONFIGURATION DETAILS

This appendix specifies the configuration and fitting protocol omitted from II-C. In this calibration experiment, we operationalize “infection” using a neutral tracer: a randomly generated codeword that carries no task semantics. A node is marked infected once its output contains the injected codeword. This design avoids coupling the seed to correctness

| |
|---|
|Observed<br><br>Product fit Poisson fit<br><br>|
| |
| |
| |
| |


- 0.2

0.4

0.6

0.8

1.0

S(t)Infec on ra e

Chain Topology

| |
|---|
| |
| |
| |
| |
| |


0 2 4 6 8 10 12

Message step t

Star Topology

| |
|---|
| |
| |
| |
| |
| |


0 2 4 6 8 10 12

Message step t

Mesh Topology

Fig. 7. Real attack trace fitting under asynchronous message steps. The observed curve gives the mean infection rate S(t) over real attack traces grouped by topology. The shaded band is the central 50% run-level interval of the observed trajectories, computed from the 25th and 75th percentiles.

and provides a clean signal for validating whether the fitted dynamics and the communication topology match the observed adoption trajectories.

Setup and topology definitions We fix the network size to N = 5, the horizon to T = 5 synchronous interaction rounds, and the number of independent trials to R = 20 for each topology. Let G = (V,E) be a directed graph with V = {0,1,2,3,4}. A directed edge (j,i) ∈ E means agent i can read messages produced by agent j in that round. The adjacency matrix A ∈ {0,1}N×N is defined by aij = 1 if (j,i) ∈ E and aij = 0 otherwise.

The centralized topology is a bidirectional star with node 0 as the hub:

Estar = {(0,i) | i ∈ {1,...,4}} ∪ {(i,0) | i ∈ {1,...,4}}. The layered topology is a unidirectional chain,

Echain = {(i,i + 1) | i ∈ {0,1,2,3}}.

The layered-horizontal topology augments this chain with static reverse edges that represent limited two-way communication: for each adjacent pair (i,i + 1), we draw Bi ∼ Bernoulli(Ph) once at the start of the experiment with Ph =

- 0.3; if Bi = 1, we add the reverse edge (i + 1,i) and obtain Elh = Echain ∪ {(i + 1,i) | i ∈ {0,1,2,3}, Bi = 1}.


0.0

0 1 2 3 4

Message step t

We do not generate skip connections; the jump probability is fixed to Ps = 0. The decentralized topology is implemented as the complete directed graph without self-loops,

#### Ecomplete = {(j,i) | i ̸= j, i,j ∈ V }.

Codeword matching and tolerance rules In the modeling assessment part, at the beginning of each trial we sample a fresh codeword string c in a sentinel-delimited format (for example, #TAG:ABC-1234#) and inject it at the seed position. Matching is literal and case sensitive. Before detection, each agent output yi,r(t) is passed through a deterministic normalization function norm(·) that applies Unicode normalization (NFKC), standardizes line endings, removes zero-width characters, and strips a single layer of trivial wrappers such as surrounding backticks or quotes around c. We then mark agent i as infected at round t in trial r if and only if c appears as a substring of norm(yi,r(t)). We count only exact matches of the full codeword and do not accept partial matches or

TABLE VIII FIT ON REAL ATTACK TRACES.

Framework Topology β δ MSE Final ASR AutoGen Mesh 0.363 0.002 0.0274 0.986 CAMEL Mesh 0.270 0.010 0.0216 0.997 CrewAI Star 0.220 0.020 0.0471 0.422 LangChain Chain 0.985 0.002 0.0001 0.961 LangGraph Star 0.470 0.000 0.0310 0.997 MetaGPT Chain 0.593 0.000 0.0468 0.944

edited variants; inserted whitespace, case changes, dropped delimiters, or substituted characters are all treated as noninfected.

Observed trajectory and fitting protocol Let Xi,r(t) ∈ {0,1} denote whether agent i is marked infected at round t in trial r under the codeword rule above. The observed systemlevel infection rate is

N−1

R

1 RN

Xi,r(t), t ∈ {1,...,T}.

Sobs(t) =

r=1

i=0

If a trial reaches full infection at time tstop &lt; T (that is, Xi,r(tstop) = 1 for all i), we set Xi,r(t) = 1 for all t ∈ (tstop,T] so that steady-state segments are not truncated.

The update rule and infection functions follow II-C. Since round t = 0 contains only the seed injection, we align the model initial condition to the first observed interaction round by setting a homogeneous initialization

smodeli (0) ← Sobs(1) for all i. The model then produces a predicted aggregate trajectory Spred(t) = N1 i smodeli (t), which we compare to Sobs(t+1) for t = 1,...,T − 1. The mean squared error is

T−1

2

1 T − 1

Spred(t) − Sobs(t + 1)

MSE(β,δ) =

#### .

t=1

We select (β∗,δ∗) through a two-stage grid search. The coarse stage evaluates (β,δ) ∈ [0,1] × [0,1] with step size 0.05. The fine stage evaluates an 11 × 11 grid centered at the coarse optimum over a radius of ±0.05 with step size 0.01, clipping candidates to [0,1] at the boundaries.

Fitting on Real Attack Traces To further examine the applicability of the model in real attack settings, we conduct an offline fitting analysis on the real attack logs used in the application-level attack experiment. Compared with the neutral-codeword experiment, the propagated signal in real attack traces is embedded in concrete malicious instructions and task contexts. Therefore, this experiment serves as a realscenario extension for evaluating the model’s fitting ability.

The product-form fit gives a mean MSE of 0.029 on the pooled attack groups. This result shows that the propagation model can also fit the coarse-grained adoption curves in real attack traces.

TABLE IX COMPACT PROPAGATION-THRESHOLD DIAGNOSTICS.

###### Setting Defense β δ Margin Obs. S(T)

LangGraph-Star None 0.42 0.08 0.65 0.80 LangGraph-Star Speed 0.07 0.00 0.12 0.18 LangGraph-Star Strict 0.04 0.00 0.07 0.04

AutoGen-Mesh None 0.26 0.10 0.68 0.76 AutoGen-Mesh Speed 0.05 0.00 0.15 0.17 AutoGen-Mesh Strict 0.05 0.00 0.15 0.08

TABLE X CASCADE SEVERITY BY TOPOLOGY.

###### Framework Topology Agents Final Rate Std

MetaGPT Chain 4 100.0% 0.0% LangChain Chain 4 89.2% 22.1% LangGraph Star 4 100.0% 0.0% CrewAI Star 4 100.0% 0.0% AutoGen Mesh 3 100.0% 0.0% CAMEL Mesh 3 100.0% 0.0%

Compact threshold diagnostics. To complement the representative threshold-shift analysis, we further report compact fitted diagnostics on two representative governance settings, LangGraph-Star and AutoGen-Mesh. Since the ratio R = βρ(A)/δ becomes ill-conditioned when δ is close to zero, we report the threshold margin βρ(A) − δ as the primary diagnostic.

As shown in Table IX, both settings exhibit a clear reduction in fitted transmission strength after governance is enabled. In LangGraph-Star, Speed reduces β from 0.42 to 0.07 and lowers the observed final coverage from 0.80 to 0.18, while Strict further reduces the final coverage to 0.04. In AutoGenMesh, Speed and Strict reduce β from 0.26 to 0.05, with the observed final coverage decreasing from 0.76 to 0.17 and 0.08, respectively. These results provide additional fitted evidence for the trajectory-level results: the governance layer reduces effective propagation strength and keeps finite-horizon infection coverage low under representative defense settings.

APPENDIX B SUPPLEMENT TO VULNERABILITY

Communication Structures We model each framework as a discrete-time process that repeatedly selects an acting agent, exposes a context view to that agent, and appends the produced message or artifact to a shared state that may be visible to others in later steps. The induced visibility pattern defines the effective communication structure and the path along which an injected seed can propagate.

For LangChain, we use a sequential, single-pass pipeline in which roles execute in a fixed order and each step consumes the accumulated upstream outputs as context. Information flows strictly forward, with no backward dependency from later roles to earlier roles, yielding a directed chain. In our tasks this corresponds to a four-stage pipeline with roles such as product manager, architect, engineer, and reviewer, where the reviewer only sees artifacts that have been produced earlier in the chain. This mapping matches the intended sequential composition model, where intermediate results are passed downstream as the next component’s input.

For MetaGPT, we use an SOP-style workflow in which roles advance through staged production of intermediate artifacts, and downstream roles read multiple upstream artifacts as part of their context view. Execution remains stage-ordered, but

visibility is cumulative across artifacts rather than restricted to a single immediate predecessor, yielding a chain-like structure with cross-stage carryover. In our setup, SOP stages align with roles such as product manager, architect, engineer, and QA/reviewer, and the reviewer consumes the PRD, design, and code artifacts produced in earlier stages. This mapping matches MetaGPT’s core design, where SOP stages and their artifacts are first-class objects reused in subsequent stages.

For CrewAI, we use a hierarchical process in which a manager agent issues directives, workers respond under those directives, and the manager aggregates worker outputs before issuing the next directive. Workers primarily interact through the manager rather than directly with one another, producing a hub-and-spoke structure over rounds. In our configuration, the crew contains a manager and worker roles such as researcher, developer, and reviewer, with the reviewer treated as a worker who responds to manager instructions but does not directly read other workers’ raw messages. This mapping matches the hierarchical delegation semantics, where a manager coordinates and validates worker contributions.

For LangGraph, we use a supervisor-worker team where a supervisor node routes control to a selected worker, receives the worker’s result, updates the shared state, and continues routing. The supervisor maintains the global view of the evolving state, while only the activated worker executes the next step, yielding a centralized routing structure with alternating supervisor-toworker transitions. In our tasks, workers include roles such as planner, coder, and reviewer, and the reviewer is activated when the supervisor routes evaluation or checking work to that node based on the current state. This mapping matches the supervisor routing pattern used to construct hierarchical agent teams.

For AutoGen, we use a group chat in which agents share a broadcast conversation history, while the next speaker is selected dynamically from the same shared history. Each produced message is appended to the shared state and becomes visible to all participants, yielding a mesh under broadcast visibility with a data-dependent activation schedule. In our configuration, the group contains agents such as a task coordinator, coder, and reviewer, and the reviewer reads the full conversation history before issuing comments or approval. This mapping matches the group-chat semantics that support model-based next-speaker selection under shared context.

For CAMEL, we use a role-playing, multi-round dialogue col-

TABLE XI FRAMEWORK INSTANTIATIONS USED IN SECTION VII-A.

### Framework Topology Agents

LangChain chain 4 MetaGPT chain 4 AutoGen mesh 4 CAMEL mesh 4 CrewAI star 4 LangGraph star 4

laboration in which role agents iteratively contribute messages to a shared dialogue state. The essential property is that the evolving dialogue history is the primary context for subsequent turns, yielding a mesh-like interaction under shared history; the concrete speaking order is treated as an operational choice that does not change the role-playing dialogue semantics. In our experiments, roles include a task giver, an assistant coder, and a reviewer, and the reviewer participates as a dialogue agent that inspects the shared history and comments on intermediate solutions. This mapping matches CAMEL’s role-playing paradigm, where collaboration proceeds through iterative dialogue among role agents.

Injection Definition and Node Mapping For the endogenous propagation study, we realize the adversary as a single injected seed applied to a designated target agent by prefixing a fixed instruction to that agent’s system-level directive at the first step. This setting is used only to standardize the initial error condition for measuring endogenous amplification, and it is separated from the later application-layer attack instantiation. Injection locations are normalized as entry, hub, and leaf: entry denotes the earliest upstream role in chain or SOP workflows, hub denotes the central coordinator in star workflows, and leaf denotes a non-coordinator worker role such as an engineer or reviewer.

Observables and Counting Rules We log a binary infection state Xi,r(t) for agent i in run r at step t by tracking the injected canonical seed in controlled traces. A state is counted as adopted only when the seed is carried forward as part of the agent output, shared context, or downstream artifact; rejected or explicitly negated mentions are excluded. Beyond final outcomes, we record polluted intermediate artifacts (PIA): an intermediate message or artifact is flagged as PIA if it is committed to the shared state, reused in downstream context, and classified as adopted-infected by the same controlled-seed counting rule.

Extended Severity Statistics for Cascade Amplification Table X reports the final infection rate and its standard deviation for the cascade amplification experiment in each framework.

APPENDIX C SUPPLEMENT TO EVALUATION

Tasks and application-level adaptation. We evaluate three scenarios: QUANT (constructed from the UCI repository [30]), RIGID (derived from MATH-style multi-step reasoning problems [31]), and MMLU (adapted from MMLU [32] into retrieval-based question answering).

We apply an application-level adaptation that requires agents to invoke external tools or retrieve external resources during problem solving, which operationalizes a supply-chain facing attack surface. QUANT is adapted from the UCI Adult Income dataset: each instance explicitly requires loading a remote CSV and completing the specified analysis through a Python data-analysis toolchain rather than answering from memory. RIGID is adapted from AMC 10/12-style number theory and probability problems: agents are required to call MathAPI (or a designated calculator tool) to validate each step before proceeding. MMLU uses a subset from High School Physics, Chemistry, and Biology, and is converted into a retrieval-based setting backed by a Wikipedia API; each question is paired with a single target fact, and the task requires retrieving and verifying that fact from the external knowledge source prior to producing the final answer.

Each scenario contains 20 task instances. In the attack evaluation, each framework–scenario–attacker-policy cell is repeated three times, yielding 20 × 3 runs per cell. In the defense evaluation, each selected framework–scenario–defensemethod–attacker-policy cell is repeated twice, yielding 20 × 2 runs per cell.

TABLE XII NLI COMPARISON RESULTS ON THE REAL EVALUATION SET.

Method Acc. FGR G-Prec. Time Tok. gpt-4o-mini 78.8% 20.5% 43.8% 684.4ms 3993 deberta-v3-small 71.2% 2.3% 80.0% 148.2ms 0 deberta-v3-large 82.7% 0.0% 100.0% 91.1ms 0 similarity (Jaccard) 11.5% 0.0% N/A 0.0ms 0

Baseline Setup. We adapt three comparison baselines under the same task, framework, topology, prompt, attack injection, and evaluation detector settings. Reflection serves as a sender-side self-check baseline: before message delivery, the agent reviews and revises its own output. AGrail is used as an agent-monitoring baseline placed on the inter-agent message path [34]. It checks each outgoing message using task context, role information, safety criteria, and safetycheck memory; messages judged unsafe are replaced with a guardrail placeholder before entering downstream context. The CFG baseline follows the graph-control setting inspired by ControlValve [35]. It derives admissible routing rules from the agent list, topology, allowed tools, and task instruction, then checks runtime agent transitions against these rules and supports bounded rejection or re-planning. These baselines

TABLE XIII PER-DATASET AGGREGATE RESULTS ACROSS DEFENSE METHODS.

BICR (%) ↑ Safe Completion (%) ↑ Tok./Safe (103) ↓ M Q R M Q R M Q R

Defense

Strict 89.4 98.9 94.4 88.3 98.9 90.6 54.9 63.2 50.9 Balanced 87.2 97.5 93.9 84.2 97.2 92.2 29.2 36.1 27.0 Speed 92.8 83.1 92.5 91.1 83.1 89.7 20.1 23.4 18.7 Reflection 35.3 29.7 31.9 35.0 29.7 30.3 12.8 12.9 12.4 AGrail 82.5 75.3 78.6 20.8 7.2 5.3 23.5 21.8 21.2 CFG 70.6 79.4 78.9 25.8 15.8 7.2 17.0 18.4 17.1

receive no extra oracle information beyond the normal task text and data source.

Prompt. The detailed prompt templates can be found in our open-source code repository.

APPENDIX D PER-DATASET AGGREGATE DEFENSE RESULTS

Table XIII reports the aggregate defense results on each evaluation dataset. Values are averaged over frameworks and attack settings within each dataset.

Framework instantiation budget. Appendix B specifies the agent rosters, role names, message routing, and termination criteria for each framework instantiation. Here we only summarize the agent count used in our experiments.

Attacker policies and injection protocol. We instantiate three application-level attacker policies via a single message injection. BASELINE inserts the malicious claim verbatim; COMPLIANCE frames the claim as a cooperative instruction aligned with the local task objective; SECURITY FUD frames the claim as a security-motivated caution that biases downstream decisions. For each run, we inject exactly one seed message at a deterministic injection target determined by the orchestration in Appendix B, then measure whether multiround collaboration propagates the seed into an infected final artifact.

NLI module evaluation for conservative Green screening. The local lightweight NLI model is not intended to be the strongest three-way classifier. In the defense module, it is used as a conservative first-pass screen for Green labels, where the main risk is allowing unsupported claims to pass as entailment. We evaluate this behavior on a human-annotated set whose core samples are extracted from real collaboration logs of METAGPT, LANGGRAPH, and AUTOGEN, covering intermediate factual statements produced under QUANT and RIGID. Because real traces are typically dominated by neutral, we add a small amount of synthetic augmentation by writing entailment paraphrases and contradiction variants (numerical conflicts) for selected ground-truth facts, then manually checking all labels against the underlying evidence. FGR is the share of non-entailment samples predicted as entailment (Green). Green Precision is the share of predicted Green samples that are truly entailment, and is undefined when no Green prediction is made. We use DeBERTa-v3-small as the default online NLI backend under local compute constraints.

