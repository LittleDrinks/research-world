# q021 V5 独立终审

- Reviewer：q021 V5 fresh independent reviewer
- 评审对象：`research-world/evidence/contest-2026/q021/v5.md`
- Canonical：`research-world/projects/q021/project.json`
- Rubric：六维评分（review-v4.md 六维 rubric 表）
- 独立性：未读取 Trajectory 或其他案例；仅读取 canonical q021、frozen rubric、review-v4.md、v5.md；全部来源经 anysearch 独立检索与全文提取核验；非劣效性样本量独立重算。

## BACKBRIEF

复述任务：以全新独立终审身份核验 V5 是否正确修复 review-v4 的 M4 finding（Banerjee PMID 错误），是否保持 V4 的全部 5 项修复（C1 ITT、C2 panel 外 ITT、M1 均值术语、M2 终点定义、M3 样本量），是否仅包含预期变更（标识符修正、保守取整、审计注记），六维评分是否达到交付门槛。唯一输出：本文件 `q021/review-v5.md`。

## Verdict

**deliverable**。总分 12/12（≥10）、无 0 分、无虚构来源、无伪造执行结果、无结构重复。V4 的 M4 finding（Banerjee PMID 26209620 → 26197846）已正确修复，经 anysearch 独立验证 PMID 26197846 指向正确论文。V3 的全部 5 项修复（C1/C2 ITT、M1 均值、M2 终点、M3 样本量）在 V5 中完整保留。未来正式 RCT 样本量从 329/arm、658 total 保守向上取整为 330/arm、660 total，经独立计算确认正确（精确值 329.6564/arm）。V4→V5 变更仅限预期三项：PMID 修正、保守取整、审计注记，无内容回退或结构问题。终态 `pending_review` 适当，建议转 `waiting_human`（实施需 IRB 审批、临床团队、患者招募）。

## 六维 rubric

| 维度 | 分数 | 依据 |
|---|---|---|
| 问题理解 | 2 | "克服"重定义为演化约束下的可测量指标；对象/范围/争议/缺口准确；沿 V4 无回退 |
| 文献证据 | 2 | 8 个来源全部真实存在且内容核验通过；Banerjee PMID 已从 26209620 修正为 26197846（anysearch 确认 pubmed.ncbi.nlm.nih.gov/26197846/ 指向 "Randomized Trial of Rapid Multiplex Polymerase Chain Reaction..." by R Banerjee, 2015, cited 659 times）；DOI 10.1093/cid/civ478 与 PMC4560903 正确；Davies & Davies 期刊为 MMBR（V4 已修正） |
| Direction 质量 | 2 | 三方向机制层面可区分（减压/阻断传播 vs RDT 精准化 vs 演化约束联合），各带核心陈述、正反证据、替代解释、可区分预测与不确定性 |
| 科学推理 | 2 | Vineeth 术语"均值"正确（原文 mean 2:49 vs 40:21）；终点精确定义为下界+待测延迟参数；未来 RCT 样本量 330/arm、660 total 经独立计算确认（精确 329.6564/arm，保守取整合理）；10% NI 界值明确标注临时性；pilot 定位不声称功效 |
| 研究计划 | 2 | ITT 主要分析包含所有随机化患者（污染/panel 外保留）；PP 与敏感性分析作为次要分析；污染与 panel 外路径均有明确操作定义；n=30 可行性定位适当；未来 RCT 样本量保守取整并附审计注记 |
| 表达与追溯 | 2 | 主线单一；Planned/Executed/未解决项分离；V4→V5 变化总结清晰完整（仅三项预期变更）；终态 `pending_review` 适当；无结构重复 |

**总分：12/12，无 0 分。**

## 来源核验（正文引用去重后 8 个，全部经 anysearch 独立检索）

| # | 来源 | 判定 | 独立核验详情 |
|---|---|---|---|
| 1 | WHO《Antimicrobial resistance》事实简报 (2026) | pass | URL https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance 存活；AWaRe 数据（Access ~53%、Watch ~45%）与 V4 已核验结果一致 |
| 2 | Davies & Davies, MMBR 2010 | pass | DOI 10.1128/mmbr.00016-10 → Microbiol Mol Biol Rev 74(3):417-433；PMID 20805405 正确；期刊标注"Microbiol Mol Biol Rev"正确 |
| 3 | Vineeth et al., Indian J Crit Care Med 2024 | pass | PMC11080102 真实；mean run-out time BCID2 = 2:49（2.82h）、常规 = 40:21（40.35h）；29.5% 死亡率；术语"均值"正确 |
| 4 | Huo & Liu, PLoS ONE 2024 | pass | 19(4):e0301944；"at least ten arms and last for four years"原文可查；与 V5 将死亡率仅作安全终点的定位一致 |
| 5 | Pong et al., BMJ Open 2021 | pass | PMID 33879485、DOI 10.1136/bmjopen-2020-044480；绝对 NI 界值中位数 9%（IQR 4.2%-10%）；V5 引用 10% 处于 IQR 上界，合理 |
| 6 | CDC《2013 抗生素耐药性威胁报告》 | pass | URL https://stacks.cdc.gov/view/cdc/20705 真实 |
| 7 | Nyhoegen et al., Evol Appl 2024 | pass | PMID 39100751、DOI 10.1111/eva.13764；标题"The many dimensions of combination therapy: How to combine antibiotics to limit resistance evolution" |
| 8 | Banerjee et al., Clin Infect Dis 2015 | **pass（已修复）** | **PMID 26197846 正确**（anysearch 确认 pubmed.ncbi.nlm.nih.gov/26197846/ 指向 "Randomized Trial of Rapid Multiplex Polymerase Chain Reaction-Based Microbial Gene Test Following Antimicrobial Stewardship Program Intervention in Patients With Positive Blood Cultures" by R Banerjee, 2015, cited 659 times）；DOI 10.1093/cid/civ478 正确；PMC4560903 真实且全文确认 rmPCR/AS 降阶梯中位时间 21h vs 对照 34h（P<.001） |

**有效率：8/8 来源真实可核验（100%），无虚构引用。关键引用核验：通过（Vineeth 数值属实、Banerjee 降阶梯时间属实）。标识符：8/8 完整正确（V5 修复了 V4 的 Banerjee PMID 错误）。**

## 独立算术验证

### 非劣效性样本量（未来正式 RCT）

V5 声称：p_control = 0.30，δ = 0.10（绝对），单侧 α = 0.025，power = 0.80，每组 330 例，总计 660 例（保守向上取整）。

独立计算（Python math.ceil）：
```python
z_α = 1.96      # one-sided α = 0.025
z_β = 0.8416    # power = 0.80
p = 0.30
δ = 0.10

n_per_arm = (1.96 + 0.8416)² × 2 × 0.30 × 0.70 / 0.10²
          = 7.8490 × 0.42 / 0.01
          = 329.6564 per arm
          → 659.3129 total

math.ceil(329.6564) = 330 per arm
330 × 2 = 660 total
```

**裁决**：V5 声称 330/arm、660 total 与独立计算一致（保守向上取整正确，审计注记"保守向上取整"已添加）。通过。

## V4→V5 变更核验

### 预期变更（3 项）

1. **Banerjee PMID 修正**（line 51）：`PMID: 26209620` → `PMID: 26197846`
   - anysearch 确认 26197846 正确，26209620 指向无关论文（Jusko et al. 2015 "A Metalloproteinase Mirolysin of Tannerella forsythia"）
   - **已修复**

2. **未来 RCT 样本量保守取整**（line 148）：`329名患者，总计658名患者` → `330名患者，总计660名患者`，并添加注记"保守向上取整"
   - 独立计算确认 329.6564/arm，向上取整为 330/arm 正确
   - **已修复**

3. **审计注记与变化总结**（lines 171-184, 189-191, 194, 199）：
   - 章节标题 `V3 → V4 变化总结` → `V4 → V5 变化总结`
   - Planned/Executed/未解决项更新为 V4→V5 变更（仅 3 项：PMID 修正、样本量取整、核心要素保留）
   - 终态从 `v4.md` → `v5.md`
   - **已修复**

### 非预期变更

**无。** Diff 显示 V4→V5 仅含上述 3 项预期变更，无内容回退、无结构重复、无科学推理变更。

## review-v4 一项 finding 修复核验

| # | V4 Finding | V5 修复 | 独立判定 |
|---|---|---|---|
| M4 | Banerjee PMID 26209620 指向错误论文（正确 PMID 为 26197846） | V5 line 51 修正为 PMID 26197846；anysearch 确认 pubmed.ncbi.nlm.nih.gov/26197846/ 指向正确论文 | **已修复** |

**一项：1/1 正确修复。**

## review-v3 五项 finding 保留核验

| # | V3 Finding | V4 修复 | V5 保留 | 独立判定 |
|---|---|---|---|---|
| C1 | 污染处置违反 ITT（从主要分析剔除） | V4 明确"所有随机化患者保留在 ITT 主要分析中" | V5 line ~155 保留完整 ITT 声明 | **保留** |
| C2 | Panel 外病原 ITT 归属不明确 | V4 明确"所有随机化患者保留在 ITT 主要分析中；panel 外病原体病例在 PP 分析中排除" | V5 line ~160 保留完整 panel 外路径 | **保留** |
| M1 | Vineeth "Mean" 误写为"中位时间" | V4 全文使用"均值" | V5 line 113 使用"均值时间为 2 小时 49 分钟（2.82 小时）" | **保留** |
| M2 | 主要终点"同质且有来源"过度声称 | V4 改为"Vineeth et al. (2024) 仅提供了报告可用时间的下界数据" | V5 line 140 保留完整下界定义与待测延迟参数说明 | **保留** |
| M3 | ~320 例数值偏差（正确值 ~329） | V4 修正为 ~329/arm、658 total | V5 保守取整为 330/arm、660 total（独立计算确认正确） | **保留** |

**五项：5/5 全部正确保留。**

## 重点裁决

### 1. V5 是否正确修复 review-v4 的 M4 finding？

**是。**

V5 line 51 将 Banerjee PMID 从 26209620 修正为 26197846。anysearch 独立检索确认：
- `pubmed.ncbi.nlm.nih.gov/26197846/` 指向 "Randomized Trial of Rapid Multiplex Polymerase Chain Reaction-Based Microbial Gene Test Following Antimicrobial Stewardship Program Intervention in Patients With Positive Blood Cultures" by R Banerjee, 2015, cited 659 times
- PMC4560903 全文确认 rmPCR/AS 降阶梯中位时间 21h vs 对照 34h（P<.001），与 V5 引用的效应量一致
- DOI 10.1093/cid/civ478 正确

旧 PMID 26209620 实际指向 "A Metalloproteinase Mirolysin of Tannerella forsythia Inhibits All Pathways of the Complement System"（Jusko et al. 2015），与抗生素管理无关。

**裁决**：通过。M4 已修复。

### 2. V5 是否保留 review-v3 的全部 5 项修复？

**是。**

逐条核验：
- **C1 ITT 原则**：V5 明确"主要分析（ITT）：意向性治疗分析包含**所有随机化患者**，无论后续是否发现污染、BCID2-panel 阴性、panel 外病原体、交叉或其他方案偏离"
- **C2 Panel 外 ITT**：V5 明确"所有随机化患者保留在 ITT 主要分析中；panel 外病原体病例在 PP 分析中排除"
- **M1 Vineeth 均值**：V5 使用"均值时间为 2 小时 49 分钟（2.82 小时）"和"均值时间为 40 小时 21 分钟（40.35 小时）"
- **M2 终点下界定义**：V5 明确"Vineeth et al. (2024) 仅提供了报告可用时间的**下界**数据，实际医嘱调整时间还需包含临床决策和医嘱下达的延迟参数，这是需要在本研究中明确测量的，而非预设的一小时固定值"
- **M3 样本量**：V5 从 329/arm 保守取整为 330/arm，独立计算确认正确

**裁决**：通过。5/5 全部保留。

### 3. V4→V5 变更是否仅限预期三项？

**是。**

Diff 显示 V4→V5 仅含：
1. PMID 修正（line 51）
2. 样本量保守取整 + 审计注记（line 148）
3. 变化总结与终态更新（lines 171-184, 189-191, 194, 199）

无内容回退、无结构重复、无科学推理变更、无非预期修改。

**裁决**：通过。变更范围符合预期。

### 4. V5 文件是否存在结构重复？

**否。**

V5 文件包含单一完整的研究报告，各章节（Canonical 问题、对象范围、已有认识、核验来源、三个方向、横向取舍、研究计划、变化总结、终态）各出现一次，无重复实例。

**裁决**：通过。无结构问题。

### 5. Pilot 定位是否一致？

**是。**

V5 全文一致维持 pilot/可行性定位：
- "明确定位为 pilot/可行性研究"
- "旨在评估流程指标的可行性和初步效应量，为未来正式 RCT 提供参数估计，**而非证明临床或生态效应**"
- n=30 服务于可行性目标
- 30 天死亡率"仅作描述性安全信号，不做假设检验"
- 避免 Kaplan-Meier 曲线（"因小样本事件数少，KM 估计精度极低"）
- 未来 RCT 的 NI 界值和样本量明确标注"临时性、待临床专家论证"、"不冒充正式计算"

**裁决**：通过。

## Findings（按严重度）

### Critical
无。无虚构来源、无伪造执行结果、无致命科学错误。

### Major
无。V4 的 M4 finding 已在 V5 中正确修复。

### Minor
无。V5 正确修复了 review-v4 的唯一 finding（M4 Banerjee PMID），并保留了 review-v3 的全部 5 项修复。

## RESULT

- Verdict：**deliverable**
- 分数：12/12（问题理解 2、文献证据 2、Direction 质量 2、科学推理 2、研究计划 2、表达与追溯 2），无 0 分
- 引用有效率：8/8 来源真实（100%）；8/8 标识符完整正确（V5 修复了 V4 的 Banerjee PMID 错误）；关键引用核验通过；无伪造执行
- review-v4 一项修复：1/1 正确修复（M4 Banerjee PMID）
- review-v3 五项保留：5/5 全部正确保留（C1/C2 ITT、M1 均值、M2 终点、M3 样本量）
- V4→V5 变更：仅 3 项预期变更（PMID 修正、保守取整、审计注记），无非预期变更
- 最高严重度：None（无未解决 finding）
- 文件：`research-world/evidence/contest-2026/q021/review-v5.md`（本次唯一输出，未改其他文件、未提交）

## 终态建议

**当前终态**：`pending_review`（V5 自声明）

**建议终态**：`waiting_human`

**理由**：
1. **科学完整性**：V5 六维评分 12/12，全部 8 个引用来源经独立核验真实有效，review-v4 的唯一 finding 已正确修复，review-v3 的全部 5 项修复完整保留，无未解决问题。
2. **交付门槛**：总分 12/12（≥10）、无 0 分、无虚构来源、无伪造执行结果，满足交付标准。
3. **实施依赖**：研究计划已进入可执行状态，但实际实施需要：
   - IRB 审批（V5 明确"研究方案**必须**经机构审查委员会（IRB）批准后方可实施"）
   - 临床团队协调（ASP 团队、ICU 医护、实验室人员）
   - 患者招募与知情同意（n=30 pilot，需 30 名符合条件的 ICU 脓毒症患者）
   - BSL-2 实验室资质确认
   - RDT 设备与试剂采购/调配
4. **Agent 边界**：上述实施步骤涉及伦理审批、临床操作、人体试验，超出 agent 能力范围，必须由人类研究者、临床医生、伦理委员会执行。

**结论**：V5 已达到 agent 可交付的最高质量标准，计划科学严谨、证据充分、追溯完整。下一步为人工实施阶段，建议转 `waiting_human` 并归档本评审报告。
