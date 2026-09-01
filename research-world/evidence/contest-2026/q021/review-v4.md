# q021 V4 独立评审

- Reviewer：q021 V4 独立 reviewer
- 评审对象：`research-world/evidence/contest-2026/q021/v4.md`；canonical：`research-world/projects/q021/project.json`；rubric：六维评分（readme.md §评分）
- 独立性：未读取 Trajectory、v1/v2/v3 正文或其他案例；仅对照 review-v3.md 的三项最小必改逐条核验；全部来源经 anysearch 独立检索与全文提取核验。

## BACKBRIEF

复述任务：以全新独立 reviewer 身份核验 V4 的科学（Vineeth 均值术语、终点定义、BCID2 覆盖）、统计（n=30 pilot、~329/arm NI 算术、10% NI 界值）、伦理（BSL/IRB/来源标识符）与 ITT 原则（污染/panel 外保留 ITT 主要分析）；核验 review-v3 五项 finding 是否真正修复；独立验证全部 8 个引用来源的 URL/DOI/PMID 与声称数值。交付门槛：总分 ≥10/12、无 0 分、关键引用通过、无伪造执行。唯一输出：本文件 `q021/review-v4.md`。

## Verdict

**deliverable**。总分 11/12（≥10）、无 0 分、无虚构来源、无伪造执行结果。V3 全部五项 finding（C1 ITT 违反、C2 panel 外 ITT 不明确、M1 均值/中位术语、M2 终点同质过度声称、M3 ~320 样本量偏差）均已在 V4 中正确修复。独立核验发现一项新的 minor 级别引用标识符错误（Banerjee PMID 指向错误论文）。终态 `pending_review` 适当。

## 六维 rubric

| 维度 | 分数 | 依据 |
|---|---|---|
| 问题理解 | 2 | "克服"重定义为演化约束下的可测量指标；对象/范围/争议/缺口准确；沿 V3 无回退 |
| 文献证据 | 1 | 8 个来源全部真实存在且内容核验通过；Davies & Davies 期刊已修正为 MMBR；但 Banerjee PMID 26209620 实际指向无关论文（正确 PMID 为 26197846），DOI 10.1093/cid/civ478 与 PMC4560903 正确（见 Finding M4） |
| Direction 质量 | 2 | 三方向机制层面可区分（减压/阻断传播 vs RDT 精准化 vs 演化约束联合），各带核心陈述、正反证据、替代解释、可区分预测与不确定性 |
| 科学推理 | 2 | Vineeth 术语已修正为"均值"；终点精确定义为下界+待测延迟参数；~329/arm 算术独立验证正确；10% NI 界值明确标注临时性；pilot 定位不声称功效 |
| 研究计划 | 2 | ITT 主要分析包含所有随机化患者（污染/panel 外保留）；PP 与敏感性分析作为次要分析；污染与 panel 外路径均有明确操作定义；n=30 可行性定位适当 |
| 表达与追溯 | 2 | 主线单一；Planned/Executed/未解决项分离；V3→V4 变化总结清晰完整；终态 `pending_review` 适当 |

**总分：11/12，无 0 分。**

## 来源核验（正文引用去重后 8 个，全部经 anysearch 独立检索）

| # | 来源 | 判定 | 独立核验详情 |
|---|---|---|---|
| 1 | WHO《Antimicrobial resistance》事实简报 (2026) | pass | URL https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance 存活；页面日期 Jul 16, 2026；V4 引用的 AWaRe 数据（Access ~53%、Watch ~45%）与 V3 已核验结果一致 |
| 2 | Davies & Davies, MMBR 2010 | pass | anysearch 确认 DOI 10.1128/mmbr.00016-10 → Microbiol Mol Biol Rev 74(3):417-433；PMID 20805405 正确；V4 期刊标注"Microbiol Mol Biol Rev"正确（非 Nature Reviews Genetics） |
| 3 | Vineeth et al., Indian J Crit Care Med 2024 | pass | anysearch 提取全文确认：PMC11080102 真实；mean run-out time BCID2 = 2:49（2.82h）、常规 = 40:21（40.35h）；29.5% 死亡率；V4 术语"均值"正确（原文用 mean/frequency/percentage） |
| 4 | Huo & Liu, PLoS ONE 2024 | pass | anysearch 提取全文确认：19(4):e0301944；"at least ten arms and last for four years"原文可查；"Neither strategy possesses benefits in reducing mortality rates"与 V4 将死亡率仅作安全终点的定位一致 |
| 5 | Pong et al., BMJ Open 2021 | pass | anysearch 确认 PMID 33879485、DOI 10.1136/bmjopen-2020-044480；绝对 NI 界值中位数 9%（IQR 4.2%-10%）；V4 引用 10% 处于 IQR 上界，合理 |
| 6 | CDC《2013 抗生素耐药性威胁报告》 | pass | URL https://stacks.cdc.gov/view/cdc/20705 真实 |
| 7 | Nyhoegen et al., Evol Appl 2024 | pass | anysearch 确认 PMID 39100751、DOI 10.1111/eva.13764；标题"The many dimensions of combination therapy: How to combine antibiotics to limit resistance evolution"；V4 描述为"进化障碍"合理概括 |
| 8 | Banerjee et al., Clin Infect Dis 2015 | pass（带 PMID 错误） | DOI 10.1093/cid/civ478 正确；PMC4560903 真实且全文提取确认 rmPCR/AS 降阶梯中位时间 21h vs 对照 34h vs rmPCR-only 38h（P<.001）；**但 PMID 26209620 实际指向 "A Metalloproteinase Mirolysin of Tannerella forsythia"（Jusko et al. 2015），正确 Banerjee PMID 为 26197846** |

**有效率：8/8 来源真实可核验（100%），无虚构引用。关键引用核验：通过（Vineeth 数值属实、Banerjee 降阶梯时间属实）。标识符：7/8 完整正确，1/8 存在 PMID 错误（DOI/PMC 正确）。**

## 独立算术验证

### 非劣效性样本量（未来正式 RCT）

V4 声称：p_control = 0.30，δ = 0.10（绝对），单侧 α = 0.025，power = 0.80，每组约 329 例，总计 658 例。

独立计算：
```
n = (z_α + z_β)² × 2p(1-p) / δ²
  = (1.96 + 0.8416)² × 2 × 0.30 × 0.70 / 0.10²
  = 7.844 × 0.42 / 0.01
  = 329.4 per arm
  → 659 total
```

**裁决**：V4 声称 ~329/arm、658 total 与独立计算一致（四舍五入差异 <1）。通过。

## review-v3 五项 finding 修复核验

| # | V3 Finding | V4 修复 | 独立判定 |
|---|---|---|---|
| C1 | 污染处置违反 ITT（从主要分析剔除） | V4 明确"所有随机化患者保留在 ITT 主要分析中"；污染病例仅在 PP 分析中排除 | **已修复** |
| C2 | Panel 外病原 ITT 归属不明确 | V4 明确"所有随机化患者保留在 ITT 主要分析中；panel 外病原体病例在 PP 分析中排除" | **已修复** |
| M1 | Vineeth "Mean" 误写为"中位时间" | V4 全文使用"均值"（"均值时间为 2 小时 49 分钟（2.82 小时）"） | **已修复** |
| M2 | 主要终点"同质且有来源"过度声称 | V4 改为"Vineeth et al. (2024) 仅提供了报告可用时间的下界数据"，明确决策延迟为需测量参数 | **已修复** |
| M3 | ~320 例数值偏差（正确值 ~660） | V4 修正为 ~329/arm、658 total，独立算术验证正确 | **已修复** |

**五项：5/5 全部正确修复。**

## 重点裁决

### 1. ITT 原则是否正确实施？

**是。**

V4 在统计分析计划中明确："主要分析（ITT）：意向性治疗分析包含**所有随机化患者**，无论后续是否发现污染、BCID2-panel 阴性、panel 外病原体、交叉或其他方案偏离。"

在设计细节补充中进一步强化：
- 污染："所有随机化患者保留在 ITT 主要分析中；污染病例在 PP 分析中排除，并记录原因。"
- Panel 外病原："所有随机化患者保留在 ITT 主要分析中；panel 外病原体病例在 PP 分析中排除。"

ITT → PP → 敏感性分析的三层结构完整。

**裁决**：通过。C1/C2 均已修复。

### 2. 终点定义是否恰当？

**是。**

V4 主要终点："血培养报阳到可执行抗菌医嘱调整的时间（小时）"，操作性定义为"从血培养系统报警到临床医生完成抗菌药物医嘱修改的时间"。

关键改进：V4 明确区分了 Vineeth 测量的"报阳→报告可用"时间与本研究需测量的"报阳→医嘱调整"时间，指出"Vineeth et al. (2024) 仅提供了报告可用时间的**下界**数据，实际医嘱调整时间还需包含临床决策和医嘱下达的延迟参数，这是需要在本研究中明确测量的，而非预设的一小时固定值"。

这比 V3 的"同质且有来源"声称准确得多。

**裁决**：通过。M2 已修复。

### 3. Pilot 定位是否一致？

**是。**

V4 全文一致维持 pilot/可行性定位：
- "明确定位为 pilot/可行性研究"
- "旨在评估流程指标的可行性和初步效应量，为未来正式 RCT 提供参数估计，**而非证明临床或生态效应**"
- n=30 服务于可行性目标
- 30 天死亡率"仅作描述性安全信号，不做假设检验"
- KM 曲线已删除（"避免 Kaplan-Meier 曲线，因小样本事件数少，KM 估计精度极低"）
- 未来 RCT 的 NI 界值和样本量明确标注"临时性、待临床专家论证"

**裁决**：通过。

### 4. V4 文件是否存在格式问题？

V4 文件包含完整的两遍重复内容（相同文本出现两次）。这是文件创建时的格式问题，不影响实质内容。建议后续清理。

## Findings（按严重度）

### Critical
无。无虚构来源、无伪造执行结果、无致命科学错误。

### Major
无。V3 的两项 Major finding（C1/C2）均已在 V4 中正确修复。

### Minor
- **M4 Banerjee PMID 错误**：V4 列出 PMID 26209620，但 anysearch 独立检索确认该 PMID 实际指向 "A Metalloproteinase Mirolysin of Tannerella forsythia Inhibits All Pathways of the Complement System"（Jusko et al. 2015）。Banerjee et al. 2015 Clin Infect Dis 的正确 PMID 为 26197846。DOI 10.1093/cid/civ478 与 PMC4560903 均正确，论文内容（rmPCR/AS 降阶梯 21h vs 对照 34h）经全文提取验证属实。此错误为 V3 遗留，V3 reviewer 亦未检出。

## RESULT

- Verdict：**deliverable**
- 分数：11/12（问题理解 2、文献证据 1、Direction 质量 2、科学推理 2、研究计划 2、表达与追溯 2），无 0 分
- 引用有效率：8/8 来源真实（100%）；7/8 标识符完整正确，1/8 PMID 错误（DOI/PMC 正确）；关键引用核验通过；无伪造执行
- review-v3 五项修复：5/5 全部正确修复
- 最高严重度：Minor（M4 Banerjee PMID 错误）
- 文件：`research-world/evidence/contest-2026/q021/review-v4.md`（本次唯一输出，未改其他文件、未提交）

## V5 最小必改项

1. **修正 Banerjee PMID**：将 PMID 26209620 修正为 26197846。（对应 M4）
