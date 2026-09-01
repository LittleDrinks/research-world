---
project: q098
role: independent-review
reviewed: v7.md
prior: v6.md
verdict: deliverable
---

# q098 V7 独立科学评审

## Rubric 评分（readme.md:64-73）

| 维度 | 分数 | 依据 |
|---|:---:|---|
| 问题理解 | 2/2 | 对象（睡眠）、范围（健康影响）、争议（机制不确定性）、知识缺口（横断面 vs 因果证据）准确呈现，未继承错误前提 |
| 文献证据 | 2/2 | 8/8 来源通过 DOI 抽查核验，关键断言（HOMA-IR 0.28、疫苗研究设计差异、类淋巴清除速率、三相耦合）均获确认；来源作用与局限显式标注；历史错引（Cappuccio、Ford）已删除 |
| Direction 质量 | 2/2 | 三个机制层面真正不同：突触稳态（神经可塑性）、类淋巴清除（代谢废物）、免疫-代谢调节（炎症/激素通路）；各含支持证据、限制/反证、区分性预测和实施负担；选择理由基于可行性而非证伪 |
| 科学推理 | 2/2 | 结论强度不超过证据：观察性设计显式声明不能建立因果；反向因果已承认；S6 青少年数据显式标注不用于成人样本量；负面对照分析纳入；失败路径（脱落、残余混杂）已处理 |
| 研究计划 | 2/2 | 数据（腕动计、血液标志物）、方法（ANCOVA、敏感性分析）、对照（DAG 协变量、负面对照）、判断方式（效应量、置信区间）、产物（可行性估计、方差）、资源（IRB、实验室）和风险（脱落、残余混杂）完整；所有项目为 planned，无 executed |
| 表达与追溯 | 2/2 | 问题→证据→三机制→选择→计划→局限形成单一主线；S1-S8 标识符可追溯至 frontmatter；V6→V7 变更说明记录版本谱系；artifact_stage 正确标记为 revision_candidate |

**总分：12/12**
**0 分项：无**

## 关键来源抽查

| ID | 核验动作 | 结果 | 作用/局限 |
|:---:|---|:---:|---|
| S1 | DOI 10.1016/j.neuron.2013.12.025 → PubMed/ScienceDirect 确认 authors、year、journal、pages | pass | 突触稳态假说核心来源；主要基于动物模型 |
| S2 | DOI 10.1126/science.1241224 → Science/PubMed 确认 authors、year、pages；~60% 间隙增加和 ~2× 清除速率与摘要一致 | pass | 类淋巴清除核心来源；小鼠模型 |
| S3 | DOI 10.1126/science.aax5440 → Science/PubMed 确认 authors、year、pages；NREM 三相耦合振荡获确认 | pass | 人类类淋巴证据；fMRI+EEG 同时记录 |
| S4 | DOI 10.1007/s00424-011-1044-0 → Springer/PubMed 确认 authors、year、journal、pages | pass | 睡眠-免疫综述 |
| S5 | DOI 10.7326/0003-4819-141-11-200412070-00008 → ACP/PubMed 确认 authors、year、title | pass | 睡眠限制与瘦素/饥饿素；12 名健康男性实验 |
| S6 | DOI 10.5665/sleep.2112 → Sleep/PubMed/PMC 确认 authors、year、pages；PMC 全文提取确认 HOMA-IR 3.179→2.896（差值 0.283）与"每减少 1 小时增加约 0.28"一致；横断面设计确认 | pass | 青少年睡眠-胰岛素抵抗；横断面，显式标注不用于成人样本量 |
| S7 | DOI 10.1001/jama.290.12.1593 → PubMed 确认 authors、year、journal、pages；实验性设计（接种后睡眠 vs 清醒）确认 | pass | 甲肝疫苗-睡眠实验 |
| S8 | DOI 10.5665/sleep.1808 → PubMed/PMC 确认 authors、year、pages；观察性设计（"natural environment"）确认 | pass | 乙肝疫苗-自然短睡眠观察 |

**分母/通过率：8/8（100%）**

## 三机制核验

| 机制 | 核心来源 | 区分性 | 选择理由 | 结论 |
|---|---|---|---|---|
| 突触稳态 | S1 | 神经可塑性层面 | 需 EEG/神经影像，成本高 | 保留为比较方向 |
| 类淋巴清除 | S2 + S3 | 代谢废物清除层面 | 需侵入性采样，伦理限制大 | 保留为比较方向 |
| 免疫-代谢调节 | S4 + S5 + S6 | 炎症/激素通路层面 | 腕动计+血液采样可行 | 选为研究计划方向 |

三方向在机制层面真正不同，选择基于可行性而非证伪其他假说。符合协议要求。

## HOMA-IR 计划与观察性边界核验

- **主要终点**：6 个月 HOMA-IR，前瞻性设计
- **统计方法**：ANCOVA 回归，显式称为"关联"或"时间预测"，绝不称为"因果效应"
- **样本量**：精度导向（Fisher-z SE），显式声明不冒充调整模型功效
- **S6 使用**：仅作为背景参考，显式声明不用于成人样本量计算
- **局限性**：残余混杂、反向因果、腕动计局限、外推限制均已声明
- **观察性边界**：全文未出现因果推断语言，观察性设计约束贯穿始终

**结论：HOMA-IR 计划在观察性边界内，无越界**

## V6→V7 漂移检查

| 检查项 | 结果 |
|---|---|
| 文献格式 | 参考文献节移至 YAML frontmatter，正文改用 S1-S8 标识符 |
| 三机制内容 | 突触稳态、类淋巴清除、免疫-代谢调节：科学内容逐字一致 |
| HOMA-IR 定量 | 0.28 单位/小时、Fisher-z 精度基准、120 完成者：一致 |
| 纳入/排除标准 | 18-45 岁、STOP-Bang 0-2、无糖尿病等：一致 |
| planned/executed 状态 | 所有项目仍为 planned，无 executed 项：一致 |
| 观察性边界声明 | "无法确立因果关系"等表述：一致 |
| 疫苗研究修正 | S7 实验性 vs S8 观察性：一致 |
| 历史错引删除 | Cappuccio、Ford 已删除：确认 |
| 新增科学内容 | 无 |
| 新增来源 | 无 |

**结论：仅来源投影与版本阶段修正，无科学漂移**

## artifact_stage 与终态

- v7 artifact_stage = `revision_candidate`：这是版本阶段，不是 Project 终态（readme.md:63）
- run.md 当前 status = `waiting_human`：正确反映 Project 终态
- v7 不改变终态理由：仍需 IRB、知情同意、腕动计和实验室资源
- 若 v7 被接受为 final，run.md 应更新 `final: v7.md`、`final_review: review-v7.md`

## 伪造执行检查

- 无模拟实验结果
- 无虚构数据
- 所有研究步骤标记为 planned
- 无 executed 项
- REVISION_RESULT: CANDIDATE 正确标记为候选

**结论：无伪造执行**

## Findings

### Critical
无。

### High
无。

### Medium
无。

### Low

**L1. v7.md 文件结构**：v7.md（274 行）在 V6→V7 变更说明后未附 v6 参考文献或状态声明节（v6 有此两节）。变更说明声称"完整保留"，但 v6 的状态声明节被移除。这不是科学漂移（状态声明是 v6 特有元数据），但与变更说明措辞略有出入。不影响科学内容或评分。

## V1→最终链完整性

| 版本 | 分数 | 关键修复 |
|---|:---:|---|
| V1 | 7/12 | 初始候选；因果过度、疫苗事实错误、样本量错误 |
| V2 | 8/12 | 修复因果和疫苗；引入两条定量错引 |
| V3 | 9/12 | 改为 precision pilot；Xie 错述修复 |
| V4 | 11/12 | 修复六项缺陷；8/8 引用 |
| V5 | 12/12 | 最终候选；最小修订 |
| V6 | 12/12 | 终态收口为 waiting_human |
| V7 | 12/12 | 来源投影至 frontmatter；无科学漂移 |

V1→V7 链不回退，分数单调递增或持平。

## Project Terminal Recommendation

**推荐终态：`waiting_human`**（与 run.md 当前 status 一致）

理由：
1. 研究计划已通过独立评审（12/12）
2. 继续执行需要 IRB 批准、参与者知情同意、腕动计设备和实验室资源
3. 观察性设计不能建立因果关系
4. 符合 readme.md:78 `waiting_human` 判定："继续运行需要领域裁决、受限数据权限、安全或伦理决定"

若 v7 被接受为 final，run.md frontmatter 应更新为：
```yaml
status: waiting_human
final: v7.md
final_review: review-v7.md
final_receipt: receipt-v6.md
```

RESULT: DELIVERABLE
