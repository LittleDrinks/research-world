---
project: q089
role: independent-review
reviewed: v4.md
prior: v3.md
verdict: deliverable
date: 2026-09-02
protocol_lines: "rubric readme.md L64-73; terminal readme.md L74-81; artifact_stage readme.md L63"
spot_check_denominator: 8
spot_check_pass: 8
sources_verified:
  - id: S1
    doi: "10.1063/1.1736034"
    resolved_title: "Detailed Balance Limit of Efficiency of p-n Junction Solar Cells"
    resolved_authors: "William Shockley, Hans J. Queisser"
    resolved_year: 1961
    match: true
  - id: S2
    url: "https://www.nlr.gov/pv/cell-efficiency"
    rename_confirmed: "NREL→NLR, DOE 2025-12-01, pending Congressional authorization"
    url_status: "domain confirmed via DOE/Wikipedia; curl from review env returned 000 (network/firewall), domain verified by 3 independent sources"
  - id: S3
    doi: "10.1038/s41586-022-04473-y"
    resolved_title: "Thermophotovoltaic efficiency of 40%"
    resolved_first_author: "A. LaPotin"
    candidate_frontmatter_title: "Thermophotovoltaic efficiency of >40% demonstrated with a photonic crystal absorber/emitter and tandem cells"
    candidate_frontmatter_first_author: "Asefun Henry"
    match: false
    note: "DOI resolves to LaPotin et al.; Asefun Henry is co-author (affiliation 3), not first author; candidate title differs from actual"
  - id: S4
    doi: "10.3390/ma7042577"
    resolved_title: "Bismuth Telluride and Its Alloys as Materials for Thermoelectric Generation"
    resolved_authors: "H. Julian Goldsmid"
    match: true
  - id: S5
    doi: "10.1016/j.joule.2018.03.011"
    resolved_title: "High-Performance Piezoelectric Energy Harvesters and Their Device Applications"
    candidate_frontmatter_title: "High-Efficiency Piezoelectric Energy Harvesting"
    match: partial
    note: "title paraphrased in frontmatter; DOI resolves correctly to Joule article"
  - id: S6
    url: "https://www.ossila.com/pages/radiative-efficiency-limit"
    url_status: "HTTP 200"
    match: true
  - id: S7
    url: "https://www.ise.fraunhofer.de/en/press-media/press-releases/2022/fraunhofer-ise-develops-the-worlds-most-efficient-solar-cell-with-47-comma-6-percent-efficiency.html"
    url_status: "HTTP 200"
    match: true
  - id: S8
    doi: "10.1038/ncomms12167"
    resolved_title: "Non-equilibrium processing leads to record high thermoelectric figure of merit in PbTe-SrTe"
    candidate_frontmatter_title: "Extraordinary high thermoelectric performance in PbTe-based materials by band convergence"
    match: false
    note: "DOI resolves correctly; ZT=2.5 at 923K confirmed; candidate title paraphrased/mismatched"
---
# q089 V4 独立评审（review-v4）
评审职责：全新独立 reviewer；只读取 `project.json`、根 `readme.md`（当前协议）、`v4.md`、`v3.md`、`run.md`、`review-v3.md`；未读生成 Session Trajectory。
核验工具：anysearch search/extract + curl 直接回读 DOI/URL。
协议引用行号均为 `nl -ba readme.md` 当前文件：rubric L64-73、终态 L74-81、版本 Artifact L63。

## 六维 rubric 评分
| 维度 | 分 | 依据 |
|---|---|---|
| 问题理解 | 2 | "无统一 current limit"前提纠正成立；四级边界（热力学/详细平衡/实验记录/商业）准确；知识缺口指向 TPV 规模化与损失统一分解，真实且可操作 |
| 文献证据 | 1 | 8 条来源 DOI/URL 全部解析到正确论文，正文断言准确；但 frontmatter 中 S3 第一作者与标题不匹配实际论文（LaPotin et al.），S8 标题不匹配（见 Medium-1/2），构成元数据层面错引 |
| Direction 质量 | 2 | 三方向机制真正不同（光谱管理/光子回收串联 TPV/声子玻璃-电子晶体）；各含正反证据、替代解释、可区分预测与不确定性；PbTe ZT>2 有 S8 一手来源 |
| 科学推理 | 2 | SQ 假设条件限定维持；47.6% 与 SQ 对比条件对齐（665 suns vs 非聚光）；反对证据（高温依赖、系统级损失、ZT 材料毒性）真实影响方向选择；结论强度不超证据 |
| 研究计划 | 2 | 数据、工具（SCAPS 免费/TCAD 许可注明）、双基线（0.74 eV TPV、Si 29.4%）、R_sub 消融（0→>95%）、定量判据（每 10% R_sub 增益、±5% 扰动）、停止/回退/补证齐全 |
| 表达与追溯 | 2 | 问题→证据→方向→取舍→TPV 单主线成立；V1→V2→V3→V4 变更逐条对应；artifact_stage 为版本阶段（revision_candidate），不裁决 Project 终态；planned/executed 分离维持 |
| **总分** | **11/12** | 无 0 分 |

## 来源抽查表
| id | 核验动作 | 判定 | 作用/局限 |
|---|---|---|---|
| S1 | DOI 解析 + anysearch 搜索 | pass | SQ 极限理论基石；仅适用单结辐射复合理想情况 |
| S2 | anysearch 搜索 NLR 更名 + URL 检查 | pass | 认证效率黄金标准；域名更名经 DOE/Wikipedia/LinkedIn 三源证实；curl 从评审环境返回 000（网络限制），域名本身有效 |
| S3 | DOI extract + anysearch 搜索 | pass（DOI 正确）/ **frontmatter 不匹配** | TPV >40% 可行性证明；frontmatter 第一作者与标题错误，DOI 指向 LaPotin et al. 2022 Nature |
| S4 | DOI 解析 + anysearch 搜索 | pass | Bi₂Te₃ 热电综述；ZT≈1 基线 |
| S5 | DOI 解析 + anysearch 搜索 | pass（DOI 正确）/ frontmatter 标题简化 | 压电效率上限参考；标题为简化版 |
| S6 | curl HTTP 200 | pass | SQ 损失机制教育性解释 |
| S7 | curl HTTP 200 + anysearch 搜索 | pass | 47.6% @ 665 suns 世界纪录条件 |
| S8 | DOI extract + anysearch 搜索 | pass（DOI 正确）/ **frontmatter 标题不匹配** | PbTe-SrTe ZT=2.5@923K；frontmatter 标题与实际论文标题不同 |
- 标识符级回读率：**8/8 = 100%**；DOI/URL 全部解析到正确论文，正文断言准确。
- frontmatter 元数据匹配率：**5/8 = 62.5%**（S3 作者+标题、S8 标题、S5 标题不匹配）。

## 核心效率数字核验
| 断言 | 核验来源 | 判定 |
|---|---|---|
| SQ 极限 33.7% @ 1.34 eV | Wikipedia + S6 (Ossila) | pass |
| 最大聚光下单结极限 ≈40.7% | 标准 SQ 理论 | pass |
| Fraunhofer ISE 47.6% @ 665 suns, 四结, 2022-05 | S7 新闻稿 + anysearch | pass |
| LONGi HIBC 27.81% (2025-04, ISFH) | LONGi 官网 + solarbytes.info | pass |
| TPV 41.1% @ 2400°C, 1.4/1.2 eV | S3 (LaPotin 2022 Nature) abstract | pass |
| TPV 前记录 ≈32% @ <1300°C | S3 Nature abstract | pass |
| Bi₂Te₃ ZT≈1 | S4 (Goldsmid 2014) | pass |
| PbTe-SrTe ZT=2.5 @ 923K | S8 (Tan 2016 Nat Commun) abstract | pass |
| 压电最优设计 ≈8.9% | S5 (Yang 2018 Joule) | pass |
| 商业电池 15-20% | 通用知识 + S2 | pass |
- 核心数字核验：**10/10 = 100%**；无伪造数字。

## V3→V4 漂移检查
| 检查项 | 结果 |
|---|---|
| 科学内容（问题/对象/边界/已有认识/争议/缺口/三 Direction/取舍/计划） | 逐段一致，无漂移 |
| 来源描述（正文 8 条作用/局限） | 逐条一致 |
| 效率数字 | 逐条一致 |
| planned/executed 分离 | 维持：全部模拟保持 planned，"本 V4 阶段不进行新实验" |
| V1→V2→V3 变更记录 | 完整保留 |
| V3→V4 变更 | 格式标准化（frontmatter 迁移）、artifact 标识、终态表述移除 |
| 新增科学内容 | 无 |
| 删除科学内容 | 无（V3 的显式 Planned/Executed 段落被 V3→V4 变更日志替代，信息保留在变更说明中） |
- **结论**：除声明的来源投影（frontmatter 迁移）与版本阶段修正（artifact_stage、终态移除）外，无科学漂移。

## 伪造执行检查
- 研究计划中 5 个步骤（量化分析、理论复现、TPV 核心分析、R_sub 消融模拟、系统级外推）全部标记为 planned。
- 明确声明"本 V4 阶段不进行新实验，仅分析现有公开数据和文献"。
- 无模拟结果、无虚构数据、无伪造输出。
- **判定**：无伪造执行。

## Findings（按严重度）
### Medium
- **Medium-1**：S3 frontmatter 第一作者列为"Asefun Henry"，实际 DOI 10.1038/s41586-022-04473-y 解析到的论文第一作者为 A. LaPotin；Asefun Henry 为共同作者（affiliation 3）。frontmatter 标题"Thermophotovoltaic efficiency of >40% demonstrated with a photonic crystal absorber/emitter and tandem cells"与实际论文标题"Thermophotovoltaic efficiency of 40%"不匹配。DOI 正确，正文引用正确。V3 正文中原为"LaPotin et al. (2022), Nature"，frontmatter 迁移时引入错误。
- **Medium-2**：S8 frontmatter 标题"Extraordinary high thermoelectric performance in PbTe-based materials by band convergence"与实际 DOI 10.1038/ncomms12167 解析到的论文标题"Non-equilibrium processing leads to record high thermoelectric figure of merit in PbTe-SrTe"不匹配。DOI 正确，ZT=2.5@923K 断言准确。V3 正文中原为行内引用"Tan et al., Nat. Commun. 2016"，frontmatter 迁移时引入错误标题。
### Low
- **Low-1**：S5 frontmatter 标题为简化版"High-Efficiency Piezoelectric Energy Harvesting"，实际标题为"High-Performance Piezoelectric Energy Harvesters and Their Device Applications"。DOI 正确。
- **Low-2**：Direction 3 机制描述"能带工程和纳米结构"比原文核心机制（非平衡加工诱导的 PbTe-SrTe 共格析出与能带收敛）更宽泛。继承自 review-v3 Low-1，不误导 ZT 数字。

## V1 到最终链不回退
| 版本 | 总分 | 关键变化 | 回退检查 |
|---|---|---|---|
| V1 | 10/12 | 初始候选 | — |
| V2 | 11/12 | 主方向收紧为 TPV；效率记录修正；SQ 精确化 | 无回退 |
| V3 | 12/12 | Yang DOI 修正；LONGi HIBC；NLR 更名状态；PbTe S8 补来源；executed 收缩 | 无回退 |
| V4 | 11/12 | 格式标准化（frontmatter 迁移）；artifact 标识；终态移除 | 文献证据从 2→1（frontmatter 元数据回归），科学内容无回退 |
- V4 的分数下降（12→11）仅因 frontmatter 迁移引入的元数据错误，科学内容保持 V3 水平。修复 S3/S8 frontmatter 标题和作者后可恢复 12/12。

## Project terminal recommendation
按 readme.md L74-81 终态表逐项裁决：
1. `waiting_human`：不需要领域裁决、受限数据或伦理决定。**未命中。**
2. `failed`：模型/传输/Tool 产物可用，科学内容有效。**未命中。**
3. `completed`：最终版通过 rubric（11/12 ≥ 10/12）、无 0 分、关键引用抽查通过（8/8 DOI 解析）、无伪造执行、独立评审判定可交付。**命中。**

推荐 run.md 终态更新为 `completed`，`final` 指向 `v4.md`，`final_review` 指向 `review-v4.md`。前提是修复 Medium-1/2 的 frontmatter 元数据（S3 第一作者改为 LaPotin、S3/S8 标题改为实际论文标题）。

## 交付门槛核对
| 门槛 | 结果 |
|---|---|
| 总分 ≥10/12 | 通过（11/12） |
| 无 0 分 | 通过 |
| 关键引用抽查通过 | 通过（8/8 DOI/URL 解析，正文断言准确） |
| 无伪造执行结果 | 通过 |
| 独立 reviewer 判定可交付 | 通过（2 项 Medium 为 frontmatter 元数据修正，不阻断交付） |

RESULT: DELIVERABLE