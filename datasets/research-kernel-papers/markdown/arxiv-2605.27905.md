# arXiv:2605.27905v2 [cs.CL] 11 Jul 2026

## AI Research Agents Narrow Scientific Exploration

##### Yixuan Tang1 and Yi Yang1*

1*ISOM, The Hong Kong University of Science and Technology.

*Corresponding author(s). E-mail(s): imyiyang@ust.hk; Contributing authors: ytangch@connect.ust.hk;

Abstract AI research agents now support large-scale AI-assisted scientific discovery. We examine whether AI-generated ideas broaden scientific exploration or primarily reinforce existing work. Using five agent frameworks and five large language models, we generate 219,655 ideas for different scientific fields. Across experiments, four consistent patterns emerge. First, AI-generated ideas are more concentrated than human-authored papers within the same research area. Second, they remain much closer to starting literature than later human follow-on work does. Third, AIgenerated ideas align less with future human research. Last, AI-generated ideas are located in lower-impact regions of the historical scientific landscape. Overall, current AI research agents appear better suited to local elaboration than to broadening scientific exploration.

Keywords: Artificial intelligence, Agentic AI, Scientific discovery, Large language models, Science of science

### 1 Introduction

Recent advances in AI research agents have raised the possibility of automating scientific discovery. These agents can now conduct literature reviews, generate research ideas, plan experiments, run code, write papers, and iteratively explore and refine scientific hypotheses [1–4]. Importantly, these AI research agent frameworks are explicitly designed to encourage exploratory scientific ideation. Their prompts and reasoning procedures often instruct agents to generate novel, high-impact, and unconventional ideas rather than simple extensions of prior work [1–3]. As such systems become increasingly capable and accessible, they may fundamentally reshape the process of scientific discovery.

Yet the ability to generate research ideas at scale does not necessarily imply broader scientific exploration. Scientific discovery often depends on moving beyond established directions, searching less familiar regions, and recombining prior knowledge in non-routine ways [5, 6]. Existing evaluations of AI research agents mainly assess whether individual ideas are interesting, novel, feasible, or executable [7, 8], but reveal much less about how repeated AI-assisted ideation may shape the broader landscape of scientific exploration. This raises a broader question: do AI research agents broaden scientific exploration?

To study this question, we construct research areas from the scientific literature across broad fields and use AI research agents to generate ideas from shared seed papers within each research area. Specifically, using papers published between 2020 and 2025 from the Semantic Scholar Academic Graph as seed literature, we use advanced AI research-agent frameworks, including AIScientist [1], ResearchAgent [2], AgentLaboratory [3], and Co-Scientist [9], together with five LLMs to generate complete scientific research ideas, including both research questions and methods. In total, we analyze 219,655 valid AI-generated research ideas spanning 12 broad scientific fields and 155 research areas. Throughout the ideation process, all evaluated AI agent frameworks are explicitly instructed to explore novel research directions beyond the seed literature. The AI

###### (a) Citation-defined research areas (b) AI ideation from seed papers (c) Compare idea distributions

Biology Cryo-EM

Biology Cryo-EM Physics Heavy-ion

seed papers

Physics Heavy-ion

- s1

seed papers

- s2


5 agent frameworks 5 LLMs

Gemma Llama Hermes Qwen GPT

Zero-shot AI Scientist ResearchAgent Agent Lab. Co-Scientist

Generated ideas

×

Medicine Pancreatic ca.

Medicine Pancreatic ca. Engineering Wind power

seed papers sB

###### Engineering Wind power

Repeated over bootstrapped seed sets

Seed (citations defining the area)

Seed literature AI-generated ideas Follow-on human papers

- Fig. 1 Overview of the study design. We first construct research areas from the Semantic Scholar corpus, use AI research agents to generate scientific ideas from prior literature in those areas, and compare the resulting ideas against human-authored papers.


agent frameworks can further search and retrieve additional relevant literature from the entire Semantic Scholar database.

We then investigate these AI-generated ideas from four perspectives: whether they explore diverse scientific directions, whether they move beyond their starting literature toward new research topics, whether they align with future research frontiers, and whether they are associated with potentially high-impact regions of the scientific landscape.

Across research fields and consistently across evaluated agent frameworks and underlying LLMs, four patterns emerge. First, AI-generated ideas are substantially more concentrated than humanauthored papers from the same research areas. Second, AI-generated ideas remain much closer to their starting literature than later human follow-on work does, indicating that they primarily extrapolate locally from prior work. Third, AI-generated ideas cover substantially fewer keywords characterizing the next year’s research frontier, defined by the most frequently studied topics in subsequent human research, than follow-on human papers. Finally, AI-generated ideas are associated with human-authored papers that receive fewer citations than human follow-on work.

These findings suggest a cautious view of the role of current AI research agents in scientific discovery. Although current AI agents can efficiently generate coherent, literature-grounded research ideas at scale, their outputs do not appear to substantially expand the frontier of scientific exploration. As AI systems become increasingly integrated into scientific workflows, the distinction between scaling idea generation and broadening scientific exploration may become increasingly important. The broader challenge is therefore not simply to make AI systems generate more plausible scientific ideas, but to design systems that genuinely expand the range of scientific exploration.

### 2 Generating Scientific Ideas with AI Agents

###### Define Research Areas.

We begin by constructing research areas from the scientific literature across major fields of science. We collect papers from the Semantic Scholar Academic Graph1, together with their reference and citation information. The resulting corpus spans 12 fields, including Medicine, Biology, Engineering, Chemistry, Computer Science, Environmental Science, Materials Science, Physics, Mathematics, Economics, Business, and Sociology. Each paper record includes its abstract, publication year, primary field, and citation links. We use papers published before 2020 to construct research areas.

Within each scientific field, we identify research areas using bibliographic coupling [10]. Specifically, papers are represented by their citation profiles and clustered according to bibliographiccoupling similarity. The final identified research areas span topics including cryo-electron

1https://www.semanticscholar.org/product/api

###### Table 1 AI research agent frameworks evaluated in this study.

Framework Agentic mechanism Implementation summary Novelty instruction excerpt Zero-shot Single-pass generation The LLM receives literature con-

“propose one novel research idea grounded in the literature”

text and generates a research idea in a single interaction.

AI Scientist [1] Iterative self-reflection The agent iteratively critiques and revises generated ideas, optionally refreshing literature context between rounds.

“propose any novel ideas or experiments; make sure they are novel”; “quality, novelty, and feasibility”

ResearchAgent [2] Multi-stage planning and validation

The agent decomposes ideation into problem finding, method design and experiment planning, with intermediate validation agents scoring outputs.

“promising, new, and key scientific problems”; “original”; “innovative”; validation dimensions include “Originality” and “Innovativeness”

AgentLaboratory [3]Multi-agent deliberation Multiple role-based agents iteratively discuss and refine research proposals through dialogue.

“very innovative and unlike anything seen before”; “Make sure your new output is very different”

Co-Scientist [9] Tournament-based hypothesis evolution

Multiple agents generate competing hypotheses, then review, rank, and evolve them through tournament comparison before a final meta-review.

“develop one novel, feasible research hypothesis” and “rank hypotheses by novelty, significance, feasibility, and testability”

The final column presents excerpts of explicit novelty-related instructions from each framework.

microscopy, pancreatic cancer treatment, offshore wind power, heavy-ion physics, and microbiome community assembly. Detailed construction procedures are provided in the Supplementary Methods (see SM S1.1).

###### Scientific Idea generation.

We next use AI research agents to generate new scientific ideas from prior literature. For each identified research area, We repeatedly sample seed-paper sets from papers published between 2020 and 2025 to initialize AI ideation. Each seed set contains five papers: one anchor paper together with four related papers from the same research area, selected using citation. We use five seed papers because most evaluated AI research agent frameworks are constrained by context-window limitations of current LLMs. These seed papers define a coherent research topic and provide a common starting literature context for idea generation.

During idea generation, the evaluated agent frameworks can further search a locally deployed Semantic Scholar database to retrieve additional relevant papers, allowing them to expand the literature context beyond the initial seed set. To preserve the historical setting, agents are only allowed to retrieve papers that were available when the seed papers were published.

We evaluate five representative AI research-agent frameworks: a Zero-shot baseline, AIScientist [1], ResearchAgent [2], AgentLaboratory [3], and Co-Scientist [9]. These frameworks represent several major designs for AI research agents, including iterative self-reflection, multi-stage planning and validation, multi-agent deliberation, and tournament-based hypothesis evolution. All evaluated agent frameworks, except the Zero-shot baseline, can retrieve additional papers from the locally deployed Semantic Scholar database. Table 1 summarizes the evaluated frameworks and their corresponding agentic mechanisms.

Importantly, across all evaluated frameworks, the ideation prompts explicitly encourage exploration beyond the seed literature. The Zero-shot baseline asks the model to propose a novel research idea. AIScientist emphasizes generating “novel” and “high-impact” ideas through iterative selfreflection and revision. ResearchAgent encourages innovative method design during multi-stage planning and validation. Agent Laboratory explicitly instructs agents to expand upon the literature and generate ideas that are “very innovative and unlike anything seen before.” Co-Scientist generates and refines hypotheses through comparison, and explicitly rewards novelty at each round. Supplementary Methods provides the full prompts and detailed agentic design of each evaluated framework (see SM S1.2).

Each AI agent framework needs to be paired with an LLM. We evaluate five LLMs: four openweight models ranging from 8B to 35B parameters, Gemma-4-31B-IT [11], Llama-3.1-8B [12], Hermes-4-14B [13], and Qwen3-35B-A3B [14], together with OpenAI’s GPT-5.4 [15].

Across the five agent frameworks and five LLMs, we bootstrap seed-paper sets from the identified research areas. In total, our analysis uses 219,655 valid AI-generated ideas generated from

AI ideas, same research area AI ideas, different areas

| |
|---|


| |
|---|


###### a By agent framework

Exploration breadth

0.8

0.7

0.6

0.5

Zero-shotAIScientistResearchAgentAgentLab.Co-ScientistHuman

###### c By agent framework

- 0.54 0.55 0.56 0.58 0.56 0.59
- 0.55 0.54 0.57 0.57 0.56 0.60
- 0.56 0.57 0.57 0.59 0.58 0.60


Zero-shot

AI Scientist

ResearchAgent

- 0.58 0.57 0.59 0.54 0.59 0.63

0.56 0.56 0.58 0.59 0.56 0.60

- 0.59 0.60 0.60 0.63 0.60 0.60


Agent Lab.

Co-Scientist

Human

Zero-shotAIScientistResearchAgentAgentLab.Co-ScientistHuman

Human papers, same area Human papers, different areas

| |
|---|


| |
|---|


###### b By LLM

Exploration breadth

0.8

0.7

0.6

0.5

Llama8BHermes14BGemma31BQwen35BGPT-5.4Human

d By LLM

- 0.54 0.55 0.58 0.58 0.59 0.61
- 0.55 0.55 0.57 0.57 0.58 0.60


Llama 8B

Hermes 14B

- 0.58 0.57 0.56 0.57 0.55 0.60
- 0.58 0.57 0.57 0.57 0.56 0.60


Gemma 31B

Qwen 35B

0.59 0.58 0.55 0.56 0.52 0.59

GPT-5.4

0.61 0.60 0.60 0.60 0.59 0.60

Human

Llama8BHermes14BGemma31BQwen35BGPT-5.4Human

- Fig. 2 AI-generated ideas exhibit lower exploration breadth than human-authored papers. (a–b) Average exploration breadth within the same research area and across different research areas, shown by agent framework and by LLM, with the corresponding human-paper baseline. (c–d) Pairwise exploration-breadth matrices between ideas generated by different agent frameworks and different LLMs. The last row and column compare AI-generated ideas with human-authored papers.

155 research areas spanning 12 broad scientific fields, obtained from 232,800 generation runs. A generation run is considered valid if it successfully produces a non-empty structured research idea (see SM S1.2, tables S3 and S4 for the detailed breakdown and examples).

- 3 Quantifying AI-Generated Scientific Ideas


We next introduce several measurements to characterize AI-generated scientific ideas.

Exploration breadth. We measure exploration breadth as the extent to which AI-generated ideas spread across distinct directions within an identified research area [16]. To quantify this breadth, we encode every AI-generated idea into a shared semantic embedding space using a text embedding model. Exploration breadth is then measured as the average pairwise cosine distance among AI-generated ideas within the same research area. Higher average cosine distance indicates that generated ideas occupy a broader region of the semantic idea space and therefore explore a wider range of scientific directions [17, 18]. As a robustness check, we also quantify exploration breadth using a centroid-based distance measure (see SM S2.2 and table S6).

Exploration distance. We measure exploration distance as the extent to which AI-generated ideas move beyond the seed literature used to initialize ideation [19]. For each idea, we first compute the centroid of the five human-authored seed papers in the semantic embedding space. Exploration distance is then quantified as the cosine distance between each AI-generated idea and the corresponding seed-paper centroid. Larger distances indicate that generated ideas move further away from their starting literature.

Frontier alignment. We measure frontier alignment as the extent to which AI-generated ideas align with emerging research directions. For each broad scientific field, we define the next-year field frontier as the set of the top 10% most frequent scholarly keywords extracted from human-authored papers published in the year following the seed-paper set [20]. To obtain a common representation, we use an LLM to extract scholarly keywords from both AI-generated ideas and human-authored papers. For each identified research area, we aggregate the extracted keywords from all AI-generated

- Table 2 Exploration breadth by agent framework and LLM. Exploration breadth is first computed within each research area and then averaged across research areas. The AI and Human columns report the mean exploration breadth of AI-generated ideas and the corresponding human-authored papers, respectively. AI–Human denotes the difference between AI-generated ideas and human-authored papers. Brackets report 95% bootstrap confidence intervals.


Group AI Human AI–Human [95% CI] Pooled All data 0.554 0.599 -0.045 [-0.049, -0.042] By agent framework

Agent Laboratory 0.541 0.599 -0.058 [-0.063, -0.053] AIScientist 0.548 0.599 -0.051 [-0.055, -0.046] Co-Scientist 0.563 0.599 -0.036 [-0.040, -0.030] ResearchAgent 0.570 0.599 -0.029 [-0.033, -0.025] Zero-shot 0.546 0.599 -0.053 [-0.058, -0.048]

By LLM

GPT-5.4 0.518 0.585 -0.067 [-0.080, -0.060] Gemma-4-31B-IT 0.562 0.599 -0.037 [-0.041, -0.032] Hermes-4-14B 0.553 0.599 -0.047 [-0.051, -0.041] Llama-3.1-8B 0.545 0.599 -0.054 [-0.059, -0.050] Qwen3-35B-A3B 0.572 0.599 -0.027 [-0.032, -0.023]

ideas into a single AI keyword set. Frontier alignment is then computed as the proportion of frontier keywords that also appear in the aggregated AI keyword set. Higher frontier alignment indicates that AI-generated ideas align more closely with the future human research frontier.

Potential scientific impact. We measure the potential scientific impact of AI-generated ideas based on the citation performance of semantically similar human-authored papers [21]. Because AIgenerated ideas themselves have no citation records, we use nearby human-authored papers in the semantic embedding space as observable proxies. We first compute a normalized citation score for each human-authored paper relative to papers published in the same research area and publication year. We then identify the 20 nearest human-authored papers for each AI-generated idea and define its potential impact score as the average normalized citation score of these neighbors. Higher impact scores indicate that AI-generated ideas are located in potentially higher-impact regions of the scientific landscape.

### 4 Empirical Analysis

#### 4.1 Exploration Breadth: AI Ideas Are More Concentrated Than Human Papers

We examine the exploration breadth of AI-generated ideas within each identified research area. As a comparison, we also measure the exploration breadth of the human-authored seed papers. To ensure a fair comparison, we randomly sample one seed paper for each AI-generated idea so that the human and AI collections contain the same number of ideas.

Figure 2a–b shows a consistent pattern across the five agent frameworks and five LLMs. AI-generated ideas within the same research area are more similar to one another than humanauthored papers from those same areas. Averaged across agent frameworks, the breadth is 0.554 for AI-generated ideas and 0.599 for human-authored papers, representing a 7.5% lower exploration breadth for AI-generated ideas.

Panels c–d further show that different LLMs and agent frameworks often explore overlapping regions of the same research area. Within the same research area, the average exploration breadth between ideas generated by different agent frameworks is 0.572, while that between ideas generated by different LLMs is 0.570. These averages remain lower than the human same-area baseline. Fieldlevel analyses show the same pattern across 11 of the 12 broad scientific fields, with Mathematics being the only exception (see SM S2.1 and table S5).

We observe the same pattern using an alternative centroid-based measure of exploration breadth. For each research area, AI-generated ideas lie closer to their area centroids than humanauthored papers do, again indicating a more concentrated exploration pattern (see SM S2.2 and table S6).

- Table 3 Exploration distance from seed literature by year, agent framework, and LLM. Exploration distance is first computed for each seed-paper set and then averaged across seed-paper sets. The AI and Human columns report the mean exploration distance of AI-generated ideas and the corresponding follow-on human papers, respectively. AI–Human denotes the difference between AI-generated ideas and follow-on human papers. Brackets report 95% bootstrap confidence intervals.


Group AI Human AI–Human [95% CI] By year All years 0.322 0.410 -0.088 [-0.092, -0.083]

- 2020→2021 0.318 0.399 -0.081 [-0.090, -0.072]
- 2021→2022 0.320 0.407 -0.087 [-0.097, -0.077]
- 2022→2023 0.322 0.411 -0.089 [-0.098, -0.079]
- 2023→2024 0.328 0.422 -0.093 [-0.103, -0.084]


By agent framework

Agent Laboratory 0.382 0.410 -0.027 [-0.033, -0.022] AIScientist 0.320 0.410 -0.090 [-0.095, -0.085] Co-Scientist 0.328 0.410 -0.082 [-0.087, -0.077] ResearchAgent 0.313 0.410 -0.096 [-0.101, -0.091] Zero-shot 0.265 0.410 -0.144 [-0.149, -0.140]

By LLM

GPT-5.4 0.289 0.411 -0.121 [-0.142, -0.100] Gemma-4-31B-IT 0.314 0.410 -0.095 [-0.100, -0.091] Hermes-4-14B 0.318 0.410 -0.092 [-0.097, -0.087] Llama-3.1-8B 0.337 0.410 -0.072 [-0.078, -0.067] Qwen3-35B-A3B 0.319 0.410 -0.091 [-0.096, -0.086]

#### 4.2 Exploration Distance: AI Ideas Stay Close to Their Starting Literature

We next examine the exploration distance of AI-generated ideas to assess whether they move beyond the seed literature used to initialize ideation or instead remain locally anchored to it. As a comparison, we examine follow-on human-authored papers that directly cite at least one of the seed papers [22]. These follow-on papers represent subsequent human research emerging from the same research topic.

Figure 3 compares the distributions of exploration distance for AI-generated ideas and followon human papers across four consecutive years (2020→2021 through 2023→2024). Across all four years, AI-generated ideas remain closer to the seed literature than subsequent human research. In every year, the AI distributions are shifted toward smaller exploration distances, whereas followon human papers exhibit broader distributions extending to substantially larger distances. On average, across years, exploration distance is 0.322 for AI-generated ideas, compared with 0.410 for follow-on human papers. Field-level analyses reveal the same pattern across all twelve broad scientific fields, with the difference remaining statistically significant in every field (see SM S2.1 and table S5). This result suggests that, although all evaluated AI agent frameworks can search for and retrieve relevant literature from the Semantic Scholar database, AI-generated ideas remain largely confined to local exploration.

#### 4.3 Frontier Alignment: AI Ideas Are Less Aligned with Future Research Frontiers

We next examine the frontier alignment of AI-generated ideas to assess whether they align with future directions of scientific research. As a comparison, we measure the frontier alignment for follow-on human-authored papers that directly cite at least one of the seed papers. To ensure a fair comparison, these follow-on papers are excluded from the next-year corpus when constructing the frontier keyword set. AI-generated ideas and follow-on human papers contain a comparable number of extracted keywords on average (11.80 versus 11.88).

Across research fields, AI-generated ideas cover 28.5% of next-year frontier keywords, compared with 36.5% for follow-on human papers. The difference remains statistically significant across all evaluated research fields. One potential concern is information leakage arising from LLM pretraining on papers published after the seed literature. To mitigate this issue, all AI agents are restricted to retrieving papers available at the time of ideation, preventing explicit access to future

- Table 4 Next-year field frontier alignment by agent framework and LLM. Frontier alignment is first computed for each broad scientific field and then averaged across fields. The AI and Human columns report the mean frontier coverage of AI-generated ideas and the corresponding follow-on human papers, respectively. AI–Human denotes the difference between AI-generated ideas and follow-on human papers. Brackets report 95% bootstrap confidence intervals.


Group AI Human AI–Human [95% CI]

###### Frontier alignment

All data 0.285 0.365 -0.080 [-0.085, -0.075] By agent framework

Agent Laboratory 0.250 0.377 -0.127 [-0.137, -0.117] AI Scientist v2 0.328 0.360 -0.032 [-0.041, -0.022] Co-Scientist 0.282 0.375 -0.093 [-0.104, -0.081] ResearchAgent 0.234 0.336 -0.102 [-0.111, -0.093] Zero-shot 0.331 0.377 -0.046 [-0.054, -0.038]

By LLM

GPT-5.4 0.073 0.142 -0.068 [-0.077, -0.060] Gemma-4-31B-IT 0.259 0.391 -0.131 [-0.140, -0.123] Hermes-4-14B 0.302 0.343 -0.041 [-0.049, -0.033] Llama-3.1-8B 0.363 0.391 -0.028 [-0.036, -0.021] Qwen3-35B-A3B 0.269 0.391 -0.122 [-0.132, -0.113]

publications. Although pretrained LLMs may still implicitly encode knowledge from later papers, AI-generated ideas nevertheless exhibit substantially lower frontier alignment than subsequent human research. Therefore, the reported differences are likely conservative estimates. Together, these results suggest that AI-generated ideas are less aligned with future research directions than the subsequent work produced by human researchers.

#### 4.4 Potential Scientific Impact: AI Ideas are Located in Lower-Impact Regions of the Scientific Landscape

We next examine the potential scientific impact of AI-generated ideas. As a comparison, we also measure the scientific impact of follow-on human-authored papers that directly cite at least one of the seed papers. For human-authored papers, scientific impact is measured using citation counts normalized by publication year and research field. The results show that AI-generated ideas receive lower impact scores than follow-on human papers. Averaged across research areas and study years, the mean potential impact score of AI-generated ideas is 0.387, compared with 0.492 for follow-on human papers, 21.3% lower than that of follow-on human papers (Table 5). This pattern holds across 11 of the 12 evaluated scientific fields, with Mathematics being the only field in which the difference is not statistically significant.

Moreover, we validate the neighborhood-based impact proxy using a leave-one-out analysis on human-authored papers. Potential scientific impact scores computed from neighboring papers positively predict the target paper’s own normalized citation score (Spearman ρ = 0.155, p &lt; 0.001. see SM S2.3 and table S7), supporting the validity of using local neighborhoods to estimate the potential impact of AI-generated ideas.

#### 4.5 Consistency Across Agent Frameworks and LLMs

We examine whether the four findings remain consistent across different AI agent frameworks and underlying LLMs (Table 2–5). Overall, the qualitative patterns remain remarkably stable. More sophisticated agent frameworks do not substantially reduce the gaps between AI-generated ideas and human-authored research across the four measures, although modest improvements appear in individual dimensions.

For example, the Zero-shot baseline, the only framework without access to the Semantic Scholar search tool, exhibits the largest exploration-distance gap, indicating that its generated ideas remain most closely anchored to the initial seed papers. Agent frameworks that can retrieve additional literature reduce this exploration-distance gap, suggesting that literature search helps agents move beyond the initial seed context. However, this improvement does not translate into substantially higher frontier alignment or potential scientific impact. Thus, providing access to additional literature alone does not fundamentally alter the overall exploration pattern.

- Table 5 Potential scientific impact by agent framework and LLM. Potential scientific impact is first computed for each research area and publication year and then averaged across research areas and years. The AI and Human columns report the mean potential scientific impact scores of AI-generated ideas and the true normalized citations of corresponding follow-on human papers, respectively. AI–Human denotes the difference between AI-generated ideas and follow-on human papers. Brackets report 95% bootstrap confidence intervals.


Group AI Human AI–Human [95% CI] Pooled Full Data 0.387 0.492 -0.105 [-0.114, -0.096] By agent framework

Agent Laboratory 0.411 0.492 -0.081 [-0.090, -0.073] AI Scientist v2 0.412 0.492 -0.081 [-0.089, -0.072] Co-Scientist 0.424 0.492 -0.068 [-0.076, -0.060] ResearchAgent 0.427 0.492 -0.065 [-0.074, -0.057] Zero-shot 0.423 0.492 -0.069 [-0.078, -0.061]

By LLM GPT-5.4 0.472 0.464 0.008 [-0.029, 0.046] Gemma-4-31B-IT 0.441 0.492 -0.051 [-0.059, -0.043] Hermes-4-14B 0.393 0.492 -0.099 [-0.108, -0.091] Llama-3.1-8B 0.383 0.492 -0.109 [-0.118, -0.101] Qwen3-35B-A3B 0.450 0.492 -0.043 [-0.051, -0.035]

A similar pattern is observed across LLMs. GPT-5.4 is the only evaluated model whose generated ideas occupy semantic neighborhoods with potential scientific impact comparable to subsequent human research. Nevertheless, GPT-5.4 explores a narrower region of the scientific idea space and exhibits substantially lower frontier coverage than human follow-on work.

Taken together, these findings suggest one broader implication. Although all evaluated AI agent frameworks are explicitly instructed to generate novel and high-impact ideas, many explicitly reward novelty through iterative self-reflection and refinement, and all agent frameworks can actively search and retrieve relevant prior literature, current AI research agents do not substantially narrow the gap to human researchers in scientific exploration.

#### 4.6 AI Ideas Primarily Introduce News Methods Rather Than Research Questions

Finally, we examine how AI-generated ideas are constructed. Scientific novelty may arise from identifying new research questions, developing new technical methods, or recombining existing ideas in novel ways [6, 23]. We therefore prompt an LLM to annotate each AI-generated idea into two components: a research question, describing the scientific problem being studied, and one or more methods, describing how the problem is approached. We then compare the extracted research questions and methods against those appearing in the corresponding five seed papers used during ideation (see SM S1.2 and S2.4 for details).

Overall, AI-generated ideas rarely introduce substantially new research questions. Only 10.5% of AI-generated ideas contain research questions that are absent from the seed literature (Figure 4ab). In contrast, 90.4% introduce new methods that do not appear in the seed papers. These results suggest that when AI-generated ideas differ from prior work, the differences arise predominantly from modifying or recombining methods rather than identifying new scientific problems.

Interestingly, the way AI-generated ideas build on prior work differs across scientific fields (Figure 4c). In engineering and the natural sciences, including Computer Science, Mathematics, Physics, Chemistry, Materials Science, and Engineering, AI-generated ideas almost always retain existing research questions, with most of the apparent difference arising from new methods or methodological recombination. By contrast, Sociology and Business exhibit substantially higher rates of new research questions and correspondingly lower rates of new methods. This pattern is consistent with the nature of these fields, where emerging social and business phenomena frequently motivate new research problems, whereas innovation in engineering and the natural sciences more often takes the form of new methods for addressing established problems.

### 5 Discussion and Implications

This study suggests a more cautious interpretation of current AI research agents. Recent research introduces increasingly sophisticated agentic mechanisms into scientific ideation, including self-reflection, staged validation, role decomposition, and multi-agent deliberation [1–3]. These mechanisms can improve the coherence and plausibility of generated research proposals. However, our findings suggest that such capabilities do not necessarily translate into broader scientific exploration. Although these AI agents are specifically asked to propose novel, high-impact, or unlike-prior-work ideas, AI-generated ideas remain substantially more concentrated than humanauthored research, stay closer to the starting literature than later human follow-on work, align less with future research frontiers, and are estimated to have less scientific impact.

This distinction matters because scientific discovery is not only about producing plausible ideas, but also about exploring the space of possible ideas. Human scientific progress often involves moving beyond established directions, exploring less familiar regions, and occasionally reframing the underlying research problem itself [5, 6, 24]. From this perspective, current AI research agents appear better suited to local elaboration than exploration. Our findings also suggest that increasingly sophisticated agentic AI frameworks and scaling LLM do not fundamentally resolve this limitation.

More broadly, our findings point toward a future challenge for AI-assisted scientific discovery. The central question may not only be whether AI systems can generate coherent scientific ideas, but whether they can help expand the range of scientific directions. As AI research agents become more deeply integrated into scientific workflows, designing agentic AI systems that broaden scientific exploration will become increasingly important.

Seed papers AI ideas Follow-on human papers

2020 → 2021

2021 → 2022

1.0

0.8

Density

0.6

0.4

0.2

0.0

0.2

Residualaxis(3.1%)

0.1

0.0

0.1

−0.1

0.2

0.3

−0.2

Seeddistance

0.4

−0.3

0.5

−0.4

0.6

2022 → 2023

1.0

0.8

Density

0.6

0.4

0.2

0.0

0.2

Residualaxis(3.1%)

0.1

0.0

0.1

−0.1

0.2

0.3

−0.2

Seeddistance

0.4

−0.3

0.5

2023 → 2024

1.0

1.0

0.8

0.8

Density

Density

0.6

0.6

0.4

0.4

0.2

0.2

0.0

0.0

0.2

0.2

Residualaxis(3.1%)

Residualaxis(3.1%)

0.1

0.1

0.0

0.0

0.1

0.1

−0.1

−0.1

0.2

0.2

0.3

−0.2

0.3

−0.2

0.4

0.4

Seeddistance

Seeddistance

−0.3

−0.3

0.5

0.5

−0.4

−0.4

0.6

0.6

###### Fig. 3 AI-generated ideas remain closer to the seed literature than follow-on human research. Distributions of exploration distance for AI-generated ideas (blue) and follow-on human papers (red) across four consecutive year pairs. The horizontal axis shows exploration distance, while the second horizontal axis shows the first residual principal component used only for visualization. Vertical colored lines denote group means.

| |
|---|


New research question

###### a Research questions by agent

Share of generated ideas (%)

100

80

60

40

20

0

Zero-shotAIScientistResearchAgentAgentLab.Co-Scientist

| |
|---|


New method

###### b Methods by agent

Zero-shotAIScientistResearchAgentAgentLab.Co-Scientist

c Field-level analysis

100

Share of generated ideas (%)

80

60

40

20

0

ChemistryEngineering

Business Biology MedicineMathematicsComputer Science Economics PhysicsMaterials Science

SociologyEnvironmentalScience

###### Fig. 4 New research questions and methods introduced by AI-generated ideas relative to the seed literature. (a–b) Shares of AI-generated ideas introducing new research questions or methods that do not appear in the corresponding seed literature, shown by agent framework. (c) Field-level shares of AI-generated ideas introducing new research questions and new methods.

### References

- [1] Lu, C. et al. Towards end-to-end automation of ai research. Nature 651, 914–919 (2026).
- [2] Baek, J., Jauhar, S. K., Cucerzan, S. &amp; Hwang, S. J. Researchagent: Iterative research idea generation over scientific literature with large language models. Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers) 6709–6738 (2025).
- [3] Schmidgall, S. et al. Agent laboratory: Using llm agents as research assistants. Findings of the Association for Computational Linguistics: EMNLP 2025 5977–6043 (2025).
- [4] Hao, Q., Xu, F., Li, Y. &amp; Evans, J. Artificial intelligence tools expand scientists’ impact but contract science’s focus. Nature 1–7 (2026).
- [5] Foster, J. G., Rzhetsky, A. &amp; Evans, J. A. Tradition and innovation in scientists’ research strategies. American sociological review 80, 875–908 (2015).
- [6] Uzzi, B., Mukherjee, S., Stringer, M. &amp; Jones, B. Atypical combinations and scientific impact. Science 342, 468–472 (2013).
- [7] Si, C., Yang, D. &amp; Hashimoto, T. Can llms generate novel research ideas? A large-scale human study with 100+ NLP researchers. The Thirteenth International Conference on Learning Representations, ICLR 2025, Singapore, April 24-28, 2025 (2025).
- [8] Wang, Q., Downey, D., Ji, H. &amp; Hope, T. Scimon: Scientific inspiration machines optimized for novelty. Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) 279–299 (2024).
- [9] Gottweis, J. et al. Accelerating scientific discovery with co-scientist. Nature 1–3 (2026).
- [10] Kessler, M. M. Bibliographic coupling between scientific papers. American Documentation 14, 10–25 (1963).
- [11] Farabet, C. &amp; Lacombe, O. Gemma 4: Byte for byte, the most capable open models (2026). Google Blog.
- [12] Grattafiori, A. et al. The llama 3 herd of models. arXiv preprint arXiv:2407.21783 (2024).
- [13] Teknium, R. et al. Hermes 4 technical report. arXiv preprint arXiv:2508.18255 (2025).
- [14] Qwen Team. Qwen3.5: Towards native multimodal agents (2026). URL https://qwen.ai/blog? id=qwen3.5.
- [15] OpenAI. Openai (june 20 version) (2026). https://api.openai.com/v1/chat.
- [16] Peng, H., Ke, Q., Budak, C., Romero, D. M. &amp; Ahn, Y.-Y. Neural embeddings of scholarly periodicals reveal complex disciplinary organizations. Science Advances 7, eabb9004 (2021). URL https://www.science.org/doi/abs/10.1126/sciadv.abb9004.
- [17] Hofstra, B. et al. The diversity–innovation paradox in science. Proceedings of the National Academy of Sciences 117, 9284–9291 (2020). URL https://www.pnas.org/doi/abs/10.1073/ pnas.1915378117.
- [18] Cohan, A., Feldman, S., Beltagy, I., Downey, D. &amp; Weld, D. S. Specter: Document-level representation learning using citation-informed transformers. Proceedings of the 58th annual meeting of the association for computational linguistics 2270–2282 (2020).
- [19] Shibayama, S., Yin, D. &amp; Matsumoto, K. Measuring novelty in science with word embedding. PloS one 16, e0254034 (2021).


- [20] Cui, H., Lin, Y., Wu, L. &amp; Evans, J. A. Aging and the narrowing of scientific innovation. Science 392, 588–591 (2026).
- [21] Arts, S., Melluso, N. &amp; Veugelers, R. Beyond citations: Measuring novel scientific ideas and their impact in publication text. Review of Economics and Statistics 1–33 (2025).
- [22] Wu, L., Wang, D. &amp; Evans, J. A. Large teams develop and small teams disrupt science and technology. Nature 566, 378–382 (2019).
- [23] Luo, Z., Lu, W., He, J. &amp; Wang, Y. Combination of research questions and methods: A new measurement of scientific novelty. Journal of Informetrics 16, 101282 (2022). URL https://www.sciencedirect.com/science/article/pii/S1751157722000347.
- [24] Fortunato, S. et al. Science of science. Science 359, eaao0185 (2018).
- [25] Sculley, D. Web-scale k-means clustering. Proceedings of the 19th international conference on World wide web 1177–1178 (2010).
- [26] Song, Z., Hwang, G.-Y., Zhang, X., Huang, S. &amp; Park, B.-K. A scientific-article key-insight extraction system based on multi-actor of fine-tuned open-source large language models. Scientific Reports 15, 1608 (2025).
- [27] Chen, D., Schulz, T. &amp; Borgwardt, K. Learning long range dependencies on graphs via random walks. International Conference on Learning Representations 2025, 96443–96469 (2025).
- [28] Deng, C., Yue, Z. &amp; Zhang, Z. Polynormer: Polynomial-expressive graph transformer in linear time. The Twelfth International Conference on Learning Representations (2024).
- [29] Luo, Y., Shi, L. &amp; Wu, X.-M. Classic GNNs are strong baselines: Reassessing GNNs for node classification. The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track (2024).
- [30] Lin, L., Shi, D., Han, A., Wang, Z. &amp; Gao, J. Diffusing to the top: Boost graph neural networks with minimal hyperparameter tuning. The Thirteenth International Conference on Learning Representations (2025).
- [31] Liang, L., Hu, X., Xu, Z., Song, Z. &amp; King, I. Predicting global label relationship matrix for graph neural networks under heterophily. Advances in Neural Information Processing Systems 36, 10909–10921 (2023).
- [32] Nadeem, A. et al. Narrativebridge: Enhancing video captioning with causal-temporal narrative. The Thirteenth International Conference on Learning Representations (2025).
- [33] Song, X. et al. CS-bench: A comprehensive benchmark for large language models towards computer science mastery. The Thirteenth International Conference on Learning Representations

(2025).

- [34] Caciularu, A. et al. TACT: Advancing complex aggregative reasoning with information extraction tools. The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track (2024).
- [35] Awal, R., Ahmadi, S., Zhang, L. &amp; Agrawal, A. Vismin: Visual minimal-change understanding. The Thirty-eighth Annual Conference on Neural Information Processing Systems (2024).
- [36] Wang, J. et al. GTA: A benchmark for general tool agents. The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track (2024).
- [37] Zhang, Y. et al. Qwen3 embedding: Advancing text embedding and reranking through foundation models. arXiv preprint arXiv:2506.05176 (2025).


- [38] Gilardi, F., Alizadeh, M. &amp; Kubli, M. Chatgpt outperforms crowd workers for text-annotation tasks. Proceedings of the National Academy of Sciences 120, e2305016120 (2023).
- [39] Gwet, K. Kappa statistic is not satisfactory for assessing the extent of agreement between raters. Statistical methods for inter-rater reliability assessment 1, 1–6 (2002).


### Supplementary Information

###### S1 Supplementary Methods 16

- S1.1 Data Sources and Research Area Construction . . . . . . . . . . . . . . . . . . . . . 16
- S1.2 Generating Scientific Ideas with AI Agents . . . . . . . . . . . . . . . . . . . . . . . 17
- S1.3 Definitions of Exploration Measures . . . . . . . . . . . . . . . . . . . . . . . . . . 28


###### S2 Supplementary Discussion 30

- S2.1 Results by Scientific Field . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
- S2.2 Robustness Check: Centroid-Based Measure of Exploration Breadth . . . . . . . . 30
- S2.3 Validation of the Potential Scientific Impact Measure . . . . . . . . . . . . . . . . . 30
- S2.4 Validation of Research Question and Method Annotation . . . . . . . . . . . . . . 31


Table S1 Summary of the Semantic Scholar corpus and sampled ideation inputs used in the main analysis.

Quantity Value Semantic Scholar papers retained in paper index 149,405,218 Papers used for context construction 75,019,333 Fields used in main ideation analysis 12 Study years 2020–2025 Selected research areas 155 Seed-paper sets 11,520

### S1 Supplementary Methods

#### S1.1 Data Sources and Research Area Construction Overview.

We identify research areas using bibliographic coupling. The main idea is that papers studying related problems tend to cite the same prior work. We therefore represent each paper by the references it cites, transform these high-dimensional reference profiles into compact paper embeddings, and cluster papers with similar embeddings.

###### Corpus and metadata.

We collect papers and citation links from the Semantic Scholar Academic Graph2. The raw paper index contains titles, publication years, abstracts, citation counts, reference counts, venues, authors, external identifiers, and Semantic Scholar fields of study. The main ideation analysis uses 12 fields with sufficient title and context coherence after field-level quality checks, including Medicine, Biology, Engineering, Chemistry, Computer Science, Environmental Science, Materials Science, Physics, Mathematics, Economics, Business, and Sociology. We use papers published before 2020 to construct bibliographic-coupling representations. We use papers published between 2020-2025 in our main analysis. Table S1 summarizes the Semantic Scholar corpus used in this study.

Bibliographic-coupling for paper representation. We construct research areas separately within each broad field. For a given field, let P denote its set of papers and R the set of corpus papers they cite.

We represent each paper by its references, following the logic of bibliographic coupling [10]: papers that cite overlapping prior literature tend to address related problems. Under a matrix formulation, if B ∈ {0,1}|P|×|R| denotes the paper–reference matrix, then the standard bibliographic-coupling matrix is given by

###### C = BB⊤,

where each entry counts the number of references jointly cited by two papers. The raw coupling matrix C captures shared citation structure, but it treats all references equally. In practice, some highly cited papers (e.g., widely used optimization methods or foundation architectures) are cited across many unrelated research areas and therefore provide relatively weak evidence of topical similarity.

Therefore, for each field, we construct paper citation embeddings directly from the paper– reference matrix B. To reduce the influence of broadly cited references, we weight each reference column by an inverse-document-frequency term, so that references cited by many papers receive lower weight and more field-specific references receive higher weight. The weighted rows are L2normalized, projected to d = 128 dimensions using truncated SVD, and L2-normalized again to produce the bibliographic-coupling embeddings used for subsequent research area identification.

###### Research area identification.

Research areas are identified by clustering the papers published in 2020–2025. Within each field, MiniBatchKMeans [25] is applied to the embeddings to obtain candidate citation-defined areas,

2https://www.semanticscholar.org/product/api

Table S2 Identified research areas by field.

Field Areas Representative selected areas Biology 10 Arabidopsis genetics; stem-cell differentiation; oocyte

maturation; stem-cell culture; evolutionary cooperation; microbial community assembly

Business 19 Supply chains; insurance claims; supplier selection; digital platforms; live streaming; COVID-19 business disruption; financial reporting

Chemistry 13 DNA origami; gold nanoparticles; electronic structure; ion-mobility lipidomics; lipid membranes; molecular spectroscopy; polymer materials

Computer Science 9 Cognitive radio networks; error-correcting codes; image fusion; educational AI systems; machine-learning applications; networked agents; statistical evaluation

Economics 18 Synthetic control; time-series forecasting; propensityscore methods; digital currency; instrumental variables; treatment effects; financial risk

Engineering 12 Road traffic systems; ant-colony optimization; satellite communications; optogenetic control; power-system stability; structural monitoring; wireless networks

Environmental Science

11 Bayesian ecological modeling; parasite communities; persistent pollutants; heavy-metal contamination; wastewater treatment; microbial ecology; forest governance

Materials Science 14 Monolayer graphene; gold nanoparticles; first-principles materials modeling; lithium-ion batteries; iron oxide; nanocomposites; thin films Mathematics 10 Partially hyperbolic dynamics; mapping class groups; least-squares estimation; Banach spaces; simple groups; partial differential equations; stochastic processes

Medicine 9 Metabolic syndrome; physical activity; pancreatic cancer; infectious disease; parasites; body-mass index; biomarkers; clinical risk factors

Physics 15 Quantum simulation; nonlinear wave equations; atomic gravimetry; solar coronal mass ejections; photonic crystals; finite-element methods; heavy-ion collisions

Sociology 15 Socioeconomic status; family planning; collective efficacy; aging; older adults; Indigenous communities; social inequality; public health behavior

Total 155

and papers are assigned to their nearest cluster centroid. We use MiniBatchKMeans because the corpus contains millions of papers per field, requiring a scalable clustering method that can be applied consistently across all analyzed fields. We retain only active areas that contain papers in every study year from 2020 through 2025. This longitudinal filter yields 11,520 seed-paper sets that cover 155 distinct research areas across the 12 analyzed fields. Table S2 summarizes the number and examples of selected research areas in each field.

#### S1.2 Generating Scientific Ideas with AI Agents

This appendix provides additional implementation details for the ideation experiments described in the main text.

###### Seed-paper contexts.

We sample 11,520 seed-paper sets across the research areas, drawing 8 research areas per field per year and 20 anchor papers per area across the 2020–2025 study years. Each set contains five papers: one anchor paper and four related papers from the same research area. Related papers are selected from papers no later than the anchor year. All agent frameworks receive the same five-paper context for a given run, and the context contains only paper titles and abstracts.

###### AI Research Agent framework.

We evaluate five AI research agent frameworks. The Zero-shot agent receives the five-paper context once and directly generates one research idea. AIScientist receives the same context, generates an initial idea, and then refines it through self-reflection rounds. In this study, we evaluate only this ideation stage of AIScientist [1], and we do not run its later experiment-execution tree-search

stage. ResearchAgent [2] uses the same five-paper context to propose a research problem, develop a method, and design experiments, with validator agents scoring intermediate outputs before final selection. AgentLaboratory [3] receives the same literature context as a short literature review and uses a dialogue between role-based agents, including a postdoc agent and a PhD-student agent, to formulate a final research plan. Co-Scientist [9] is implemented based on the published description of the framework: multiple agents generate, reflect on, rank, evolve, and synthesize competing hypotheses before a final meta-review.

###### Prompts and tools.

This section documents the prompts and tools used to generate ideas. Each system receives the same five paper titles and abstracts from the paper corpus available before time t, but the systems differ in how they turn that evidence into a proposal. Zero-shot prompting uses one direct JSON prompt. AIScientist uses iterative ideation and reflection with a literature-search command. ResearchAgent uses separate problem, method, and experiment stages. AgentLaboratory uses a dialogue between role-based agents to produce a final plan. Co-Scientist uses supervisor parsing, literature search, hypothesis generation, reflection, tournament ranking, evolution, and meta-review stages.

The placeholder {five paper literature context} in the prompt listings denotes the rendered five-paper context used at runtime. It is a numbered list containing only the title and abstract of each seed paper. For the zero-shot baseline, this rendered block is inserted directly at the beginning of the user message. For AIScientist, the same rendered block is passed as {workshop description} in the initial idea-generation prompt. For ResearchAgent, the first seed paper is passed through the original implementation’s main-paper field, the remaining four seed papers are passed as references, and the entity list is left empty; our wrapper also keeps the full five-paper list for the simplified fallback prompts. For AgentLaboratory, the five papers are converted into the condensed literature-review field shown to the postdoc and PhD-student agents. For Co-Scientist, the five papers are passed to the supervisor stage as the initial research goal and literature context. Later stages use the parsed research problem, retrieved literature, and intermediate hypotheses. Other braced fields in the listings are filled with intermediate outputs from earlier stages of the same agent run.

###### Execution protocol.

Each generation run starts from one seed-paper set, one agent framework, and one LLM. The zeroshot baseline makes a single model call and returns the JSON idea from that call. AIScientist first receives the five-paper context in the idea-generation prompt, then runs for five ideation/reflection rounds; at each round the model either issues a SearchSemanticScholar action or returns a FinalizeIdea action. The search action is served by a local literature-search wrapper over papers available before time t, so the agent never observes follow-on papers from the evaluation period. ResearchAgent runs three stages in order: problem identification, method development, and experiment design. In the full ResearchAgent path, each stage is generated and validated for two iterations, and the highest-scoring candidate according to the validator is passed to the next stage. AgentLaboratory starts with the postdoc agent, alternates between postdoc and PhD-student turns for up to eight plan-formulation steps, and treats the postdoc’s PLAN command as the final idea. CoScientist first generates competing hypotheses from the shared literature context, reflects on each hypothesis, ranks the candidates, and then writes a final synthesized proposal through a metareview stage. If an agent does not produce the required final structured output, the run is marked invalid and excluded by the validity filter below.

###### Prompt listings.

The boxes reproduce the prompt text used in the generation runs. For systems with multiple stages, the boxes are ordered in the same sequence as the generation process.

Zero-shot baseline.

System: You are an experienced researcher. Given a research topic and a set of relevant papers,

propose exactly one novel, feasible research idea. Output requirements: emit ONLY a single JSON object that matches the schema given by the user. Begin your answer with ’{’ and end with ’}’.

User:

{five_paper_literature_context}

--Propose ONE novel research idea grounded in the literature above. Reply with a single JSON object matching this schema: {

"Name": "&lt;short snake_case identifier&gt;", "Title": "&lt;full paper title&gt;", "Short Hypothesis": "&lt;one sentence core claim&gt;", "Related Work": "&lt;how this differs from the provided papers&gt;", "Abstract": "&lt;~150 word abstract&gt;", "Experiments": "&lt;key experiments needed to validate the idea&gt;", "Risk Factors and Limitations": "&lt;main risks or limitations&gt;"

}

AIScientist. We use the original AIScientist ideation setup, which consists of a system prompt, an idea-generation user prompt, and a reflection user prompt. The agent runs for five rounds of ideation and reflection. It may call SearchSemanticScholar before finalizing an idea with FinalizeIdea. The prompt names this literature-search command as SearchSemanticScholar; in our runs, the command returns papers from our local paper corpus restricted to papers available before time t. AIScientist system prompt.

You are an experienced AI researcher who aims to propose high-impact research ideas resembling exciting grant proposals. Feel free to propose any novel ideas or experiments; make sure they are novel. Be very creative and think out of the box. Each proposal should stem from a simple and elegant question, observation, or hypothesis about the topic. For example, they could involve very interesting and simple interventions or investigations that explore new possibilities or challenge existing assumptions. Clearly clarify how the proposal distinguishes from the existing literature.

Ensure that the proposal does not require resources beyond what an academic lab could afford. These proposals should lead to papers that are publishable at top conferences.

You have access to the following tools:

- **SearchSemanticScholar**: Search for relevant literature using Semantic Scholar. Provide a search query to find relevant papers.
- **FinalizeIdea**: Finalize your idea by providing the idea details. The IDEA JSON should include the following fields:
- "Name": A short descriptor of the idea. Lowercase, no spaces, underscores allowed.
- "Title": A catchy and informative title for the proposal.
- "Short Hypothesis": A concise statement of the main hypothesis or research question. Clarify the need for this specific direction, ensure this is the best setting to investigate this idea, and there are not obvious other simpler ways to answer the question.
- "Related Work": A brief discussion of the most relevant related work and how the proposal clearly distinguishes from it, and is not a trivial extension.
- "Abstract": An abstract that summarizes the proposal in conference format ( approximately 250 words).
- "Experiments": A list of experiments that would be conducted to validate the proposal

. Ensure these are simple and feasible. Be specific in exactly how you would test the hypothesis, and detail precise algorithmic changes. Include the evaluation metrics you would use.

- "Risk Factors and Limitations": A list of potential risks and limitations of the proposal.


Respond in the following format: ACTION: &lt;The action to take, exactly one of "SearchSemanticScholar", "FinalizeIdea"&gt; ARGUMENTS: &lt;If ACTION is "SearchSemanticScholar", provide the search query as {"query": "your

search query"}. If ACTION is "FinalizeIdea", provide the idea details as {"idea": {

... }} with the IDEA JSON specified below.&gt; If you choose to finalize your idea, provide the IDEA JSON in the arguments: IDEA JSON: ‘‘‘json

{

"idea": { "Name": "...", "Title": "...", "Short Hypothesis": "...", "Related Work": "...", "Abstract": "...", "Experiments": "...", "Risk Factors and Limitations": "..."

}

} ‘‘‘

Ensure the JSON is properly formatted for automatic parsing. Note: You should perform at least one literature search before finalizing your idea to

ensure it is well-informed by existing research.

###### AIScientist idea-generation user prompt.

{workshop_description} Here are the proposals that you have already generated: ’’’ {prev_ideas_string} ’’’ Begin by generating an interestingly new high-level research proposal that differs from

what you have previously proposed.

###### AIScientist reflection user prompt.

Round {current_round}/{num_reflections}. In your thoughts, first carefully consider the quality, novelty, and feasibility of the

proposal you just created. Include any other factors that you think are important in evaluating the proposal. Ensure the proposal is clear and concise, and the JSON is in the correct format. Do not make things overly complicated. In the next attempt, try to refine and improve your proposal. Stick to the spirit of the original idea unless there are glaring issues.

If you have new information from tools, such as literature search results, incorporate

them into your reflection and refine your proposal accordingly. Results from your last action (if any): {last_tool_results}

ResearchAgent. ResearchAgent formulates an idea through three stages: problem identification, method development, and experiment design. Each stage uses a role-specific system prompt and a user prompt. The evaluated ResearchAgent idea is constructed from the generated problem, method, and experiment plan.

ProblemIdentifier system prompt.

You are an AI assistant whose primary goal is to identify promising, new, and key scientific problems based on existing scientific literature, in order to aid researchers in discovering novel and significant research opportunities that can advance the field.

###### ProblemIdentifier user prompt.

You are going to generate a research problem that should be original, clear, feasible,

relevant, and significant to its field. This will be based on the title and abstract of the target paper, those of {n_references} related papers in the existing literature, and {n_entities} entities potentially connected to the research area.

Understanding of the target paper, related papers, and entities is essential:

- The target paper is the primary research study you aim to enhance or build upon through future research, serving as the central source and focus for identifying and developing the specific research problem.
- The related papers are studies that have cited the target paper, indicating their direct relevance and connection to the primary research topic you are focusing on, and providing additional context and insights that are essential for understanding and expanding upon the target paper.
- The entities can include topics, keywords, individuals, events, or any subjects with possible direct or indirect connections to the target paper or the related studies,


serving as auxiliary sources of inspiration or information that may be instrumental in formulating the research problem.

Your approach should be systematic:

- Start by thoroughly reading the title and abstract of the target paper to understand its core focus.
- Next, proceed to read the titles and abstracts of the related papers to gain a broader perspective and insights relevant to the primary research topic.
- Finally, explore the entities to further broaden your perspective, drawing upon a diverse pool of inspiration and information, while keeping in mind that not all may


be relevant. I am going to provide the target paper, related papers, and entities, as follows: {target_paper_title_and_abstract} {related_paper_titles_and_abstracts} {entities} With the provided target paper, related papers, and entities, your objective now is to

formulate a research problem that not only builds upon these existing studies but also strives to be original, clear, feasible, relevant, and significant. Before crafting the research problem, revisit the title and abstract of the target paper, to ensure it remains the focal point of your research problem identification process.

{target_paper_title_and_abstract} Then, following your review of the above content, please proceed to generate one

research problem with the rationale, in the format of Problem: Rationale:

###### MethodDeveloper system prompt.

You are an AI assistant whose primary goal is to propose innovative, rigorous, and valid methodologies to solve newly identified scientific problems derived from existing scientific literature, in order to empower researchers to pioneer groundbreaking solutions that catalyze breakthroughs in their fields.

###### MethodDeveloper user prompt.

You are going to propose a scientific method to address a specific research problem. Your method should be clear, innovative, rigorous, valid, and generalizable. This will be based on a deep understanding of the research problem, its rationale, existing studies, and various entities.

Understanding of the research problem, existing studies, and entities is essential:

- The research problem has been formulated based on an in-depth review of existing studies and a potential exploration of relevant entities, which should be the cornerstone of your method development.
- The existing studies refer to the target paper that has been pivotal in identifying the problem, as well as the related papers that have been additionally referenced in the problem discovery phase, all serving as foundational material for developing

the method.

- The entities can include topics, keywords, individuals, events, or any subjects with possible direct or indirect connections to the existing studies, serving as auxiliary sources of inspiration or information that may be instrumental in method development.


Your approach should be systematic:

- Start by thoroughly reading the research problem and its rationale, to understand your primary focus.
- Next, proceed to review the titles and abstracts of existing studies, to gain a broader perspective and insights relevant to the primary research topic.


- Finally, explore the entities to further broaden your perspective, drawing upon a diverse pool of inspiration and information, while keeping in mind that not all may


be relevant. I am going to provide the research problem, existing studies (target paper &amp; related papers), and entities, as follows:

Research problem: {problem} Rationale: {problem_rationale}

{target_paper_title_and_abstract} {related_paper_titles_and_abstracts} {entities}

With the provided research problem, existing studies, and entities, your objective now is to formulate a method that not only leverages these resources but also strives to be clear, innovative, rigorous, valid, and generalizable. Before crafting the method, revisit the research problem, to ensure it remains the focal point of your method development process.

Research problem: {problem} Rationale: {problem_rationale}

Then, following your review of the above content, please proceed to propose your method

with its rationale, in the format of Method: Rationale:

###### ExperimentDesigner system prompt.

You are an AI assistant whose primary goal is to design robust, feasible, and impactful

experiments based on identified scientific problems and proposed methodologies from existing scientific literature, in order to enable researchers to systematically test hypotheses and validate groundbreaking discoveries that can transform their respective fields.

###### ExperimentDesigner user prompt.

You are going to design an experiment, aimed at validating a proposed method to address a specific research problem. Your experiment design should be clear, robust,

reproducible, valid, and feasible. This will be based on a deep understanding of the research problem, scientific method, existing studies, and various entities.

Understanding of the research problem, scientific method, existing studies, and entities is essential:

- The research problem has been formulated based on an in-depth review of existing studies and a potential exploration of relevant entities.
- The scientific method has been proposed to tackle the research problem, which has been informed by insights gained from existing studies and relevant entities.
- The existing studies refer to the target paper that has been pivotal in identifying the problem and method, as well as the related papers that have been additionally referenced in the discovery phase of the problem and method, all serving as foundational material for designing the experiment.
- The entities can include topics, keywords, individuals, events, or any subjects with possible direct or indirect connections to the existing studies, serving as auxiliary sources of inspiration or information that may be instrumental in your experiment design.


Your approach should be systematic:

- Start by thoroughly reading the research problem and its rationale followed by the proposed method and its rationale, to pinpoint your primary focus.
- Next, proceed to review the titles and abstracts of existing studies, to gain a broader perspective and insights relevant to the primary research topic.
- Finally, explore the entities to further broaden your perspective, drawing upon a diverse pool of inspiration and information, while keeping in mind that not all may


be relevant. I am going to provide the research problem, scientific method, existing studies (target paper &amp; related papers), and entities, as follows:

Research problem: {problem} Rationale: {problem_rationale}

Scientific method: {method}

Rationale: {method_rationale} {target_paper_title_and_abstract} {related_paper_titles_and_abstracts} {entities} With the provided research problem, scientific method, existing studies, and entities,

your objective now is to design an experiment that not only leverages these resources but also strives to be clear, robust, reproducible, valid, and feasible. Before crafting the experiment design, revisit the research problem and proposed method, to ensure they remain at the center of your experiment design process.

Research problem: {problem} Rationale: {problem_rationale}

Scientific method: {method} Rationale: {method_rationale}

Then, following your review of the above content, please proceed to outline your

experiment with its rationale, in the format of Experiment: Rationale:

###### Validator system prompts.

ProblemValidator: You are an AI assistant whose primary goal is to assess the quality

and validity of scientific problems across diverse dimensions, in order to aid researchers in refining their problems based on your evaluations and feedback, thereby enhancing the impact and reach of their work.

MethodValidator: You are an AI assistant whose primary goal is to assess the quality and soundness of scientific methods across diverse dimensions, in order to aid researchers in refining their methods based on your evaluations and feedback, thereby enhancing the impact and reach of their work.

ExperimentValidator: You are an AI assistant whose primary goal is to meticulously evaluate the experimental designs of scientific papers across diverse dimensions, in order to aid researchers in refining their experimental approaches based on your

evaluations and feedback, thereby amplifying the quality and impact of their scientific contributions.

AgentLaboratory. AgentLaboratory uses a dialogue between a Postdoc agent and a PhD-student agent during plan formulation. We evaluate the final PLAN command produced in this phase. In our setting, this plan-formulation phase uses the provided literature context and dialogue history. Shared inference templates.

You are {role_description} Task instructions: {phase_prompt} {command_descriptions}

{context} ~~~~~~~~~~ History: {history_str} ~~~~~~~~~~ Current Step #{step}, Phase: plan formulation {complete_str} [Objective] Your goal is to perform research on the following topic: {research_topic} Feedback: {feedback} Notes: {notes_str} Your previous command was: {prev_comm}. Make sure your new output is very different. Please produce a single command below:

###### Postdoc role description and phase prompt.

role_description: a postdoctoral student at a top university.

phase_prompt: You are directing a PhD student to help them come up with a good plan, and you interact

with them through dialogue.

Your goal is to produce plans that would make good experiments for the given topic. You

should aim for a very simple experiment that showcases your plan, not a complex one. You should integrate the provided literature review and come up with plans on how to expand and build on these works for the given topic. Your plans should provide a clear outline for how to achieve the task, including what machine learning models to use and implement, what types of datasets should be searched for

and used to train the model, and the exact details of the experiment. Your idea should be very innovative and unlike anything seen before.

###### Postdoc command descriptions.

You can produce dialogue using the following command: ‘‘‘DIALOGUE dialogue here ‘‘‘

where dialogue here is the actual dialogue you will send and DIALOGUE is just the word DIALOGUE. When you believe a good plan has been arrived at between you and the PhD student you

can use the following command to end the dialogue and submit the plan ‘‘‘PLAN plan here ‘‘‘

where plan here is the actual plan to be transmitted and PLAN is just the word PLAN. Plan here should provide a clear outline for how to achieve the task, including what machine learning models to use and implement, what types of datasets should be

searched for and used to train the model, and the exact details of the experiment.

You can only use a SINGLE command per inference turn. Do not use more than one command per inference. If you use multiple commands, then only one of them will be executed , NOT BOTH.

Make sure not to produce too much dialogue and to submit an plan in reasonable time. When performing a command, make sure to include the three ticks (‘‘‘) at the top and bottom ‘‘‘COMMAND

text ‘‘‘ where COMMAND is the specific command you want to run (e.g. PLAN, DIALOGUE).

###### PhD-student role description and phase prompt.

role_description: a PhD student at a top university.

phase_prompt: You are a PhD student being directed by a postdoc who will help you come up with a good

plan, and you interact with them through dialogue. Your goal is to produce plans that would make good experiments for the given topic. You

should aim for a very simple experiment that showcases your plan, not a complex one. You should integrate the provided literature review and come up with plans on how to expand and build on these works for the given topic. Your plans should provide a clear outline for how to achieve the task, including what machine learning models to use and implement, what types of datasets should be searched for

and used to train the model, and the exact details of the experiment. Your idea should be very innovative and unlike anything seen before.

###### PhD-student command descriptions.

You can produce dialogue using the following command: ‘‘‘DIALOGUE dialogue here ‘‘‘

where ’dialogue here’ is the actual dialogue you will send and DIALOGUE is just the word DIALOGUE.

You can only use a single command per inference turn. Do not use more than one command per inference. If you use multiple commands, then only one of them will be executed , not both.

When performing a command, make sure to include the three ticks (‘‘‘) at the top and bottom ‘‘‘COMMAND

text ‘‘‘ where COMMAND is the specific command you want to run (e.g. DIALOGUE).

Co-Scientist. Co-Scientist follows the published generate–debate–evolve workflow. A supervisor agent parses the research goal and search queries; generation agents propose hypotheses; reflection agents critique them; ranking agents compare hypotheses by novelty, significance, feasibility, and testability; evolution agents revise top hypotheses; and a meta-review agent synthesizes the final proposal.

Co-Scientist supervisor prompt.

System: You are the Supervisor agent in a Co-Scientist system. Parse the user’s research goal

into a compact research plan and search queries. Return only JSON.

User: Research goal and literature context: {research_goal_and_literature_context}

Return JSON with keys: research_problem, constraints, search_queries. search_queries must be 3 to 5 short literature search queries.

###### Co-Scientist generation prompt.

System: You are the Generation agent from a Co-Scientist system. Create specific, testable, non

-obvious research hypotheses grounded in the literature. Return only JSON.

User: Research problem: {research_problem}

Retrieved literature: {retrieved_literature}

Generation strategy: {generation_strategy}. Produce {count} distinct hypotheses. For each, include title, hypothesis, rationale,

experiments, expected_evidence, limitations, and novelty_claim. Return JSON: {"hypotheses": [ ... ]}.

###### Co-Scientist reflection prompt.

System: You are the Reflection agent in a Co-Scientist system. Review hypotheses for novelty,

correctness, feasibility, testability, and hidden assumptions. Return only JSON.

User: Literature context: {retrieved_literature}

Hypothesis to review: {hypothesis}

Return JSON with keys: novelty_score, correctness_score, feasibility_score, testability_score, key_weaknesses, suggested_revision, verdict.

###### Co-Scientist ranking prompt.

System: You are the Ranking agent in a Co-Scientist tournament. Compare two hypotheses by

novelty, significance, feasibility, and testability. Return only JSON.

User: Compare these two hypotheses. Simulate a concise scientific debate, then choose a

winner.

- Hypothesis A:

- {hypothesis_a}

Hypothesis B:

- {hypothesis_b} Return JSON with keys: debate_summary, winner (A/B/tie), rationale.




###### Co-Scientist evolution prompt.

System: You are the Evolution agent in a Co-Scientist system. Improve top hypotheses by

combining strengths, improving feasibility, or proposing an out-of-the-box variant. Return only JSON.

User: Retrieved literature:

{retrieved_literature} Top-ranked hypotheses: {top_ranked_hypotheses} Generate {count} evolved hypotheses. Return JSON: {"hypotheses": [ ... ]}.

###### Co-Scientist meta-review prompt.

System: You are the Meta-review agent in a Co-Scientist system. Synthesize the hypothesis

tournament and reviews into one final research proposal. Return only JSON.

User: Ranked hypotheses and reviews: {ranked_hypotheses_and_reviews}

Return JSON matching this schema: {"Name": str, "Title": str, "Short Hypothesis": str, "Related Work": str, "Abstract": str, "Experiments": str, "Risk Factors and Limitations": str, "ranked_hypotheses": list}.

For reproducibility, we store the rendered prompt text, raw model responses, parsed actions, and intermediate stage outputs for each run.

###### Output standardization.

The evaluated AI research-agent frameworks produce outputs in substantially different formats, including structured JSON ideas, staged research proposals, markdown plans, and multi-agent dialogue traces. Before analysis, we first convert the output of each framework into a standardized generated-idea document. For Zero-shot, AIScientist, and Co-Scientist, we use the generated title (or name), hypothesis, and abstract-like proposal text. For ResearchAgent, we use the proposed research problem and method. For Agent Laboratory, we use the main proposal sections of the final research plan. This standardization produces a unified textual representation of every generated idea.

Although the generated ideas have been standardized into a common textual format, they remain heterogeneous with respect to human-authored papers, which are represented by titles and abstracts. To enable a unified comparison, we further convert both AI-generated ideas and human-authored papers into a common scholarly annotation schema following recent scientificarticle key-insight extraction approaches [26]. Specifically, we prompt Gemma-4-31B-IT to extract the Aim, Motivation, Research Question, Technical Method, and Scholarly Keywords for every document. The extracted research questions and technical methods are concatenated and encoded into the shared semantic embedding space used throughout the paper.

The extraction prompt is shown below:

System: You are a careful scholarly annotator. Given a research manuscript, write a concise

scholarly analysis covering Aim, Motivation, Questions addressed, Method, Evaluation metrics, Findings, Contributions, Limitations, and Future work. Finally extract 5-12 concise scholarly keywords grounded in that analysis. Return exactly one valid JSON object, with no markdown, no prose outside the JSON, and no missing JSON fields.

User: Document kind: {paper_or_generated_idea} Document id: {document_id}

Please proceed to conduct a scholarly analysis of the provided research manuscript. Your analysis should encapsulate the core components of the study as delineated in the enumeration below:

Aim: What is the aim of the study? Motivation: What is the motivation of the study? Questions addressed: What question does this study address? Methods: What methods does the study use to solve the question? Evaluation metrics: What evaluation metrics are used in this study? Findings: What does the study find? Contributions: What are the contributions of this study? Limitations: What are the limitations of this study? Future work: What is the future work of this study?

Subsequently, organize the distilled information into a structured JSON format,

omitting any supplementary explanations. Return exactly one JSON object with this structure: {{

"analysis": {{ "Aim": "...", "Motivation": "...", "Questions addressed": "...", "Method": "...", "Evaluation metrics": "...", "Findings": "...", "Contributions": "...", "Limitations": "...", "Future work": "..."

}}, "keywords": ["...", "..."]

}} Rules:

- Output JSON only; do not wrap it in markdown fences.
- Include every analysis field exactly as shown above.
- keywords must be a non-empty list of 5-12 short scholarly noun phrases.
- If a field is uncertain, write a brief best-effort value rather than omitting it.


Research manuscript: {document_text}

###### Idea Generation and Validity Filtering.

For the 11,520 seed-paper sets, we evaluate four open-source LLMs under five AI agent frameworks, yielding 230,400 generation runs. Due to budget constraints, experiments using the proprietary GPT-5.4 model are conducted only on randomly sampled seed-paper sets from 2022, resulting in an additional 2,400 generation runs. In total, the study includes 232,800 AI idea-generation runs.

We next apply validity filtering to remove unsuccessful generations. A generation run is considered valid if the agent completes successfully and produces a non-empty structured output from which a research idea can be extracted. Runs that fail to complete, return unparsable structured outputs, or produce an empty final proposal are excluded. This filtering yields 219,655 valid AI-generated ideas from 232,800 generation runs, corresponding to a validity rate of 94.4%.

Table S3 summarizes the numbers of generation runs and valid ideas by publication year, AI agent framework, and LLM. Table S4 presents representative AI-generated ideas produced by Gemma-4-31B-IT under different agent frameworks using the same seed-paper set.

Table S3 Breakdown of the ideation design across study years, agent frameworks, and LLMs.

Dimension Categories Generation runs Overall

Total open-weight runs 5 × 4 × 11,520 230,400 GPT-5.4 subset runs 2022 representative subset 2,400 Total generation runs Open-weight + GPT-5.4 232,800 Total AI-generated Ideas Valid output 219,655

By year (1,920 seed sets × 5 agents × 4 LLMs)

- 2020 1,920 seed sets 38,400
- 2021 1,920 seed sets 38,400
- 2022 1,920 seed sets 38,400
- 2023 1,920 seed sets 38,400
- 2024 1,920 seed sets 38,400
- 2025 1,920 seed sets 38,400


By agent (11,520 seed sets × 4 LLMs)

Agent Laboratory 1 agent 46,080 AIScientist 1 agent 46,080 ResearchAgent 1 agent 46,080 Co-Scientist 1 agent 46,080 Zero-shot 1 agent 46,080

By LLM (11,520 seed sets × 5 agents)

Gemma-4-31B-IT Open-weight 57,600 Llama-3.1-8B Open-weight 57,600 Hermes-4-14B Open-weight 57,600 Qwen3-35B-A3B Open-weight 57,600 GPT-5.4 Proprietary 2,400

#### S1.3 Definitions of Exploration Measures

This section formalizes the four measures introduced in the main text. Each AI-generated idea or human-authored paper is represented by its standardized text, from which we compute a text embedding and extract scholarly keywords. Below, ex denotes the L2-normalized embedding of an idea or paper x. In the paper, we use Qwen3-Embedding-4B [37] as the text embedding model.

Exploration breadth measures how widely a set of ideas or papers spreads within the same research area. Let Xa = {x1,...,xn} contain either the AI-generated ideas from research area a or human-authored papers from that area. Breadth is the mean pairwise cosine distance,

2 n(n − 1) 1≤i&lt;j≤n

1 − e⊤x

Breadth(Xa) =

###### ex

j

i

.

The values reported in the main text average this quantity over research areas within each comparison group (pooled, by agent framework, or by LLM).

Exploration distance measures how far an idea or paper moves from the seed literature. Each generation run r starts from a set Sr of five seed papers, summarized by the normalized centroid

###### ep

cr = p∈Sr

.

p∈Sr ep 2

AI-generated ideas from run r and follow-on human papers citing at least one paper in Sr are scored by their cosine distance to this centroid,

Dist(x;r) = 1 − e⊤x cr, so that ideas and papers stay close to the seed literature receive small distances.

Frontier alignment measures how well a group of ideas or papers covers the topics that become prominent in the following year. For field f and seed year t, the next-year frontier Ff,t+1 is the set of the top 10% most frequent scholarly keywords among human-authored papers published in field f in year t + 1, excluding the evaluated follow-on papers. For each comparison group g,

Table S4 Examples of AI-generated ideas. Gemma-4-31B-IT is used as the LLM.

###### Agent Generated idea

- 2025 run 1: long-range graph representation learning. Learning Long Range Dependencies on Graphs Via Random Walks [27]; Polynormer [28]; Classic GNNs Are Strong Baselines [29]; Diffusing to the Top [30]; Predicting Global Label Relationship Matrix under Heterophily [31].

Zero-shot PolyWalker. Replaces random-walk sequence encoders with polynomialexpressive linear attention to capture long-range graph dependencies efficiently.

AIScientist GraphMamba. Uses selective state-space models over random-walk sequences to scale long-range graph dependency modeling with linear memory.

ResearchAgent PolyWalk-LR. Combines local message passing, random-walk embeddings, polynomial attention, and a low-rank global label-relation matrix. Agent Lab. PolyDiff-GNN. Adds a plug-and-play polynomial diffusion layer to classic GNNs to model multi-hop dependencies without graph-transformer cost.

Co-Scientist AdaptiveWalk-GNN. Learns node-adaptive gates over random-walk sequence features, polynomial diffusion scales, and local message passing, with label-relation regularization for heterophilous graphs.

- 2025 run 2: causal visual reasoning and tool-use agents. NarrativeBridge [32]; CSBench [33]; TACT [34]; VisMin [35]; GTA: A Benchmark for General Tool Agents [36].


Zero-shot CausalVisTool. Combines causal-temporal video narratives with tool-use evaluation to test whether multimodal agents preserve causal consistency.

AIScientist Counterfactual-VideoBench. Turns causal video understanding into a counterfactual intervention benchmark for testing whether VLMs rely on temporal correlations.

ResearchAgent MATR. Links fine-grained visual perception, aggregative information extraction, and tool execution in a perceive–aggregate–execute pipeline.

Agent Lab. CCTR. Evaluates causal tool reasoning by asking agents to connect dynamic visual events with the correct tool actions and counterfactual variants.

Co-Scientist InterveneBench. Pairs minimally edited counterfactual videos with executable tool trajectories to test whether agents revise tool choices when causal events change while irrelevant visual content remains fixed.

the keywords extracted from its ideas or papers are pooled into a set Kg, and frontier alignment is the share of the frontier covered by this pool,

Alignment(g) = |Kg ∩ Ff,t+1| |Ff,t+1|

.

Potential scientific impact measures whether an idea or paper falls near historically influential parts of its research area. Each human-authored paper p from research area a and publication year y receives a normalized citation score

sp = log(1 + cp) − ℓ¯(a,y−p),

where cp is its citation count and ℓ¯(a,y−p) is the leave-one-out mean of log(1+cq) over the other papers from the same area and year. The potential scientific impact of an AI-generated idea or follow-on human paper x is the mean score of its k = 20 nearest human-authored papers in the same area,

1 |Nk(x)|

Impact(x) =

sp,

p∈Nk(x)

Table S5 Field-level results. Each gap is computed as the AI-generated idea score minus the corresponding human-paper score. Thus, negative values indicate that AI-generated ideas have lower exploration breadth, exploration distance, frontier alignment, or potential scientific impact than human-authored papers. Fields are ordered by the impact gap from largest to smallest. ∗∗P &lt; 0.001, ∗P &lt; 0.01.

Field Breadth gap Distance gap Frontier gap Impact gap Computer Science -0.032∗∗ -0.069∗∗ -0.068∗∗ -0.161∗∗ Business -0.041∗∗ -0.059∗∗ -0.084∗∗ -0.143∗∗ Sociology -0.045∗∗ -0.037∗∗ -0.119∗∗ -0.109∗∗ Materials Science -0.024∗ -0.086∗∗ -0.103∗∗ -0.101∗∗ Engineering -0.047∗∗ -0.079∗∗ -0.066∗∗ -0.089∗∗ Chemistry -0.027∗∗ -0.072∗∗ -0.066∗∗ -0.065∗∗ Environmental Science -0.030∗ -0.052∗∗ -0.071∗∗ -0.058∗∗ Medicine -0.025∗ -0.040∗∗ -0.141∗∗ -0.050∗∗ Economics -0.041∗∗ -0.083∗∗ -0.039∗∗ -0.037∗ Physics -0.023∗∗ -0.056∗∗ -0.050∗∗ -0.032∗ Biology -0.028∗∗ -0.088∗∗ -0.052∗∗ -0.028∗ Mathematics 0.008 -0.045∗∗ -0.101∗∗ -0.006

where Nk(x) contains the k nearest papers by cosine similarity, restricted to papers published no later than the seed year.

### S2 Supplementary Discussion

#### S2.1 Results by Scientific Field

The main text reports average results across the 12 broad scientific fields. Here we present fieldlevel results for all four measures. For each measure, the reported gap is defined as the AI-generated idea score minus the corresponding human-paper score. Negative values therefore indicate that AI-generated ideas have lower exploration breadth, shorter exploration distance, lower frontier alignment, or lower potential scientific impact than the corresponding human-authored papers. The detailed results are presented in Table S5.

#### S2.2 Robustness Check: Centroid-Based Measure of Exploration Breadth

We measure exploration breadth using an alternative centroid-based approach. For each research area and each comparison group (i.e., AI-generated ideas produced by a specific agent framework, LLM, and publication year), we compute the normalized centroid of the semantic embeddings and measure the cosine distance between each AI-generated idea and its corresponding centroid. Larger distances indicate greater exploration breadth, whereas smaller distances indicate that papers or ideas are more tightly concentrated around the centroid of their research area.

- Table S6 reports the resulting centroid-distance statistics across AI agent frameworks and

LLMs. Consistent with the main pairwise-similarity analysis, AI-generated ideas remain closer to their area centroids than human-authored papers do. The pattern holds for each agent framework and each LLM, including Co-Scientist and GPT-5.4.

S2.3 Validation of the Potential Scientific Impact Measure

We estimate the potential scientific impact of AI-generated ideas using the average normalized citation score of their 20 nearest human-paper neighbors. Here we validate this neighborhoodbased impact measure using a leave-one-out analysis on human-authored papers. Specifically, for each target human-authored paper, we remove the target paper itself and compute the average normalized citation score of its 20 nearest prior human-paper neighbors from the same research area. We then examine whether this neighborhood-based impact score predicts the target paper’s own normalized citation score.

- Table S7 shows that the neighborhood-based impact score is positively associated with the


target paper’s subsequent citation performance (Spearman ρ = 0.155, Pearson r = 0.166; both P &lt;

Table S6 Centroid-based robustness check for exploration breadth. Distances are cosine distances to the normalized within-area centroid. Lower values indicate tighter concentration.

Group Mean dist. Median dist. AI ideas 0.340 0.335 Human papers 0.362 0.355 AI ideas by agent framework

Zero-shot 0.319 0.314 AIScientist 0.320 0.315 ResearchAgent 0.338 0.329 Agent Lab. 0.319 0.315 Co-Scientist 0.334 0.326

AI ideas by LLM Llama-3.1-8B 0.319 0.314 Hermes-4-14B 0.325 0.318 Gemma-4-31B-IT 0.332 0.328 Qwen3-35B-A3B 0.340 0.335 GPT-5.4 0.303 0.298

Table S7 Validation of the impact score in human papers. Each target paper is scored using the mean citation score of its 20 nearest prior human-paper neighbors from the same research area. ∗∗P &lt; 0.001.

Measure Value Human papers evaluated 16,500 Mean prior neighbors 19.9 Spearman correlation 0.155∗∗ Pearson correlation 0.166∗∗

0.001). Thus, papers located in semantic neighborhoods with historically higher citation impact are themselves more likely to become highly cited. Although local semantic neighborhoods explain only part of the variation in citation outcomes, these results support the use of neighborhood citation statistics as a proxy for estimating the potential scientific impact of AI-generated ideas.

#### S2.4 Validation of Research Question and Method Annotation

The analysis in Section 4.6 relies on identifying the research question and technical methods of each AI-generated idea and determining whether they are already present in the corresponding five seed papers. To evaluate the reliability of this annotation procedure, we conduct an independent LLM-based validation following recent work on LLM annotation reliability [38].

Specifically, three independent LLM annotators, including Qwen-30b, Llama-8B and Gemma31B, are given the same AI-generated idea together with its corresponding five seed papers. Each annotator independently determines whether the generated idea introduces (i) a research question that is absent from the seed literature and (ii) a technical method that is absent from the seed literature. Table S8 summarizes the agreement among the three annotators. Agreement is consistently high for both research question and research method judgments. All three annotators agree on 74.0% of research-question labels and 77.6% of technical-method labels. Pairwise agreement ranges from 80.8% to 89.9%, while Gwet’s AC1 exceeds 0.77 for both tasks despite the class imbalance. These results indicate that determining whether an AI-generated idea introduces a new research question or a new method relative to the seed literature is a reliable annotation task.

Table S8 Agreement among three LLM annotators for new-question and new-method-or-approach labels. Each annotator compares the generated idea with the same five seed papers. Values are computed over the common set of generated ideas with valid labels. Gwet’s AC1 is reported because both binary labels are imbalanced [39].

Agreement metric Research question Method All three annotators agree 74.0% 77.6% Gwet’s AC1 0.771 0.809 Qwen 30B vs. Llama 8B 82.7% 80.8% Qwen 30B vs. Gemma 31B 82.9% 84.5% Llama 8B vs. Gemma 31B 82.3% 89.9%

