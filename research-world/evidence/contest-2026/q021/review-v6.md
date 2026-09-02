# q021 V6 独立终审

- Reviewer：q021 V6 fresh independent reviewer
- 评审对象：`research-world/evidence/contest-2026/q021/v6.md`
- Canonical：`research-world/projects/q021/project.json`
- Rubric：六维评分（readme.md 第 69–80 行 rubric 表）
- 终态规则：readme.md 第 81–88 行四种终态
- 独立性：未读取其他 V6 reviewer 结论；仅读取 canonical q021、frozen rubric、review-v5.md、v5.md、v6.md、run.md；Banerjee 条目经 anysearch 独立检索与交叉核验；非劣效性样本量已由 review-v5 独立重算（本轮不重复）。

## BACKBRIEF

以全新独立终审身份核验 V6 是否：(1) 只执行了必要的 DOI/标题修正、终态变更和审计说明更新，V5 的 ITT、pilot 定位、样本量和三方向科学内容无回退；(2) 六维总分 ≥10/12、无 0 分；(3) 关键引用 Banerjee 2015 的 PMID 26197846、PMCID PMC4560903、DOI 10.1093/cid/civ447 交叉一致，旧 DOI civ478 确认指向其他论文；(4) `waiting_human` 终态符合协议定义；(5) 无伪造临床 executed。唯一输出：本文件 `review-v6.md`。

## 独立来源核验：Banerjee 2015

使用 anysearch 独立检索，交叉验证四个标识符：

| 标识符 | 检索结果 | 判定 |
|---|---|---|
| PMID 26197846 | `pubmed.ncbi.nlm.nih.gov/26197846/` → Banerjee R et al. 2015 "Randomized Trial of Rapid Multiplex Polymerase Chain Reaction…" Clin Infect Dis 61(7):1071-1080, cited 659 | ✅ 正确 |
| PMCID PMC4560903 | `pmc.ncbi.nlm.nih.gov/articles/PMC4560903/` → 同一篇 Banerjee 2015 全文 | ✅ 正确 |
| DOI 10.1093/cid/civ447 | `academic.oup.com/cid/article/61/7/1071/289120` → 同一篇 Banerjee 2015, DOI 10.1093/cid/civ447 | ✅ 正确 |
| DOI 10.1093/cid/civ478（V5 旧值） | `academic.oup.com/cid/article/61/7/1043/289968` → **Hook EW III et al.** "Phase 2 Trial of Oral Solithromycin 1200 mg or 1000 mg as Single-Dose Therapy for Uncomplicated Gonorrhea" PMID 26089222 | ❌ 错误论文 |

**结论**：
- V6 的 DOI 10.1093/cid/civ447 经三个独立标识符交叉核验，确认指向正确论文。
- V5 的旧 DOI 10.1093/cid/civ478 确认指向 Hook et al. 2015（淋病 solithromycin 试验），与 Banerjee 完全无关。
- **review-v5 声称 "DOI 10.1093/cid/civ478 正确" 是 review-v5 的核验遗漏**。V6 发现并修正了此错误。

## V5→V6 差异审计（diff 精确）

`diff v5.md v6.md` 输出 5 处变更，逐条审计：

| # | 位置 | V5 | V6 | 判定 |
|---|---|---|---|---|
| 1 | Line 1 标题 | `（V5）` | `（V6）` | ✅ 预期 |
| 2 | Line 50 Banerjee 条目 | 中文缩略标题 `《多重PCR与抗菌药物管理对血流感染患者降阶梯治疗的影响》` | 添加英文完整标题 `（Randomized Trial of Rapid Multiplex Polymerase Chain Reaction–Based Blood Culture Identification and Susceptibility Testing）` | ✅ 更准确，与 DOI/PMID 交叉一致 |
| 3 | Line 52 Banerjee DOI | `10.1093/cid/civ478` | `10.1093/cid/civ447` | ✅ 修正正确（见上表核验） |
| 4 | Lines 171-181 变更总结 | V4→V5 的 3 条 Planned/Executed | V5→V6 的 3 条 Planned/Executed（DOI 修正、终态修正、变更说明） | ✅ 如实反映本轮变更 |
| 5 | Line 189 终态段落 | `pending_review` | `waiting_human` + 详细原因 | ✅ 符合协议终态定义 |

**非预期变更**：**无。** diff 仅包含上述 5 处变更，科学正文（三方向、研究计划、统计方案、样本量、ITT 声明、pilot 定位）零改动。

## V5 科学内容保留核验

| V5 要素 | V6 保留 | 验证方法 |
|---|---|---|
| ITT 主要分析包含所有随机化患者 | ✅ | diff 无改动；V6 line ~155 完整保留 |
| PP 作为次要分析 | ✅ | diff 无改动 |
| 污染处置：ITT 保留、PP 排除 | ✅ | diff 无改动 |
| Panel 外病原路径：ITT 保留、PP 排除 | ✅ | diff 无改动 |
| Pilot n=30 定位 | ✅ | diff 无改动 |
| 未来 RCT 330/arm、660 total | ✅ | diff 无改动 |
| 10% NI 界值标注"临时性" | ✅ | diff 无改动 |
| Vineeth "均值" 术语 | ✅ | diff 无改动 |
| 终点定义为下界+待测延迟 | ✅ | diff 无改动 |
| 30 天死亡率"仅作描述性安全信号" | ✅ | diff 无改动 |
| 避免 Kaplan-Meier 曲线 | ✅ | diff 无改动 |
| 三方向核心陈述/正反证据/替代解释/预测/不确定性 | ✅ | diff 无改动 |
| 方向二主攻方向及三条理由 | ✅ | diff 无改动 |

**13/13 要素完整保留，无回退。**

## 终态核验：`waiting_human`

协议定义（readme.md line 82）："继续运行需要领域裁决、受限数据权限、安全或伦理决定；记录待决问题，不伪造替代结果。"

V6 列出的待决事项：

| 待决项 | 类型 | 符合 `waiting_human` |
|---|---|---|
| IRB 审批 | 伦理决定 | ✅ |
| 临床团队协调（ASP、ICU、实验室） | 领域裁决 | ✅ |
| 患者招募与知情同意（n=30） | 伦理决定 | ✅ |
| BSL-2 实验室资质确认 | 安全决定 | ✅ |
| RDT 设备与试剂资源 | 受限资源 | ✅ |

**伪造检查**：V6 明确声明"本轮仅执行了来源标识符核验和必要的文本修正，未执行任何临床试验"。Planned 和 Executed 分离清晰。无伪造临床 executed。✅

## 六维 rubric

| 维度 | 分数 | 依据 |
|---|---|---|
| 问题理解 | 2 | 从 V5 完整保留：AMR 重定义为演化约束下的可测量指标；对象/范围/争议/缺口准确；无回退 |
| 文献证据 | 2 | 8 来源真实；**Banerjee DOI 从 civ478（Hook 2015 solithromycin）修正为 civ447（Banerjee 2015 rmPCR RCT），经 anysearch 三标识符交叉核验**；标题添加英文原文与 DOI 一致；其余 7 来源沿用 review-v5 已验证状态 |
| Direction 质量 | 2 | 从 V5 完整保留：三方向机制层面可区分，各带核心陈述/正反证据/替代解释/预测/不确定性 |
| 科学推理 | 2 | 从 V5 完整保留：Vineeth 均值术语正确；终点为下界+待测延迟；330/arm 经 review-v5 独立计算确认；pilot 不声称功效 |
| 研究计划 | 2 | 从 V5 完整保留：ITT 主要分析、PP 次要分析、n=30 pilot、660 未来 RCT、污染/panel 外路径明确 |
| 表达与追溯 | 2 | V5→V6 变更仅 5 处（标题、标题修正、DOI 修正、变更总结、终态），diff 干净；Planned/Executed/未解决项分离；`waiting_human` 终态适当 |

**总分：12/12，无 0 分。**

## Findings

### Critical
无。

### Major
无。V5 的全部 12/12 在 V6 中保留，V6 额外修正了 review-v5 遗漏的 DOI 错误。

### Minor
无。V6 的变更范围精确（5 处 diff），每处均有审计依据，科学内容零改动。

### 发现：review-v5 的 DOI 核验遗漏

review-v5 声称 "DOI 10.1093/cid/civ478 正确" 和 "DOI 10.1093/cid/civ478 与 PMC4560903 正确"。anysearch 独立核验显示 civ478 实际指向 Hook EW III et al. 2015 "Phase 2 Trial of Oral Solithromycin 1200 mg or 1000 mg as Single-Dose Therapy for Uncomplicated Gonorrhea"（PMID 26089222），与 Banerjee 论文完全无关。V6 发现并修正了此错误。此发现不影响 V6 的终态判定（V6 已修正），但作为审计记录披露。

## V6 声称核验

V6 声称"经 anysearch 独立核验确认正确对应 PMID 26197846 和 PMCID PMC4560903 的论文"。本轮 anysearch 独立核验确认此声称属实。

V6 未声称重新核验了全部 8 个来源。只核验了 Banerjee 条目。这是诚实的——其余 7 个来源已由 review-v5 核验通过。

## RESULT

- Verdict：**DELIVERABLE**
- 分数：12/12（问题理解 2、文献证据 2、Direction 质量 2、科学推理 2、研究计划 2、表达与追溯 2），无 0 分
- 引用有效率：8/8 来源真实（100%）；关键引用 Banerjee 2015 三标识符交叉核验通过（PMID 26197846 = PMCID PMC4560903 = DOI 10.1093/cid/civ447）；旧 DOI civ478 确认指向 Hook et al. 2015（不同论文）
- V5→V6 变更：仅 5 处预期变更（标题版本号、Banerjee 标题精确化、DOI 修正、变更总结更新、终态变更），无非预期变更
- V5 科学内容保留：13/13 要素完整保留，无回退
- 终态：`waiting_human` 正确（IRB、临床团队、患者招募/同意、BSL-2、RDT 资源）
- 伪造检查：无伪造临床 executed
- review-v5 发现：V6 额外修正了 review-v5 遗漏的 DOI 错误（civ478 → civ447）
- 最高严重度：None（无未解决 finding）
- 文件：`research-world/evidence/contest-2026/q021/review-v6.md`（本次唯一输出，未改其他文件、未提交）

RESULT: DELIVERABLE
